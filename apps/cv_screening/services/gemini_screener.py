import json
import re
import logging

import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

GEMINI_MODEL = 'gemini-2.5-flash'

# Singleton — configured once on first use, not on every request.
_gemini_model = None


def _get_model():
    global _gemini_model
    if _gemini_model is None:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel(GEMINI_MODEL)
    return _gemini_model


def extract_pdf_text(file_path):
    """Extract plain text from a PDF file using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
        return '\n'.join(parts).strip()
    except Exception as e:
        logger.error(f"PDF extraction error for {file_path}: {e}")
        return ''


def screen_cv_against_job(cv_text, job):
    """
    Send CV text + job details to Gemini and return a structured scoring dict.

    Returns:
        {
            "overall_score": int,
            "breakdown": {
                "skills_match":     { score, weight, matched_skills, missing_skills, explanation },
                "experience_match": { score, weight, years_detected, experience_level_detected, explanation },
                "education_match":  { score, weight, education_detected, explanation },
                "keyword_relevance":{ score, weight, matched_keywords, explanation },
                "overall_fit":      { score, weight, explanation }
            },
            "strengths":      [str, ...],
            "weaknesses":     [str, ...],
            "recommendation": str,
            "summary":        str
        }
    """
    model = _get_model()

    required_skills = ', '.join(job.required_skills) if job.required_skills else 'Not specified'
    nice_to_have = ', '.join(job.nice_to_have_skills) if job.nice_to_have_skills else 'None'

    prompt = f"""You are a senior HR recruiter and talent acquisition expert. \
Analyze the CV below against the job description and return a precise, objective matching score.

=== JOB DETAILS ===
Title: {job.title}
Location: {job.location or 'Not specified'}
Work Mode: {job.work_mode}
Experience Level Required: {job.experience_level}
Job Type: {job.job_type}
Required Skills: {required_skills}
Nice-to-Have Skills: {nice_to_have}

Job Description:
{(job.description or '')[:2000]}

Requirements:
{(job.requirements or '')[:1500]}

Responsibilities:
{(job.responsibilities or '')[:1500]}

=== CANDIDATE CV ===
{cv_text[:8000]}

=== INSTRUCTIONS ===
Return ONLY a valid JSON object — no markdown fences, no text before or after.
Use this exact structure:

{{
  "overall_score": <integer 0-100>,
  "breakdown": {{
    "skills_match": {{
      "score": <integer 0-100>,
      "weight": 35,
      "matched_skills": ["skill1", "skill2"],
      "missing_skills": ["skill3"],
      "explanation": "One or two sentences on skill alignment."
    }},
    "experience_match": {{
      "score": <integer 0-100>,
      "weight": 25,
      "years_detected": <number or null>,
      "experience_level_detected": "<entry|mid|senior|lead|executive>",
      "explanation": "One or two sentences on experience alignment."
    }},
    "education_match": {{
      "score": <integer 0-100>,
      "weight": 20,
      "education_detected": "<degree and field found in CV>",
      "explanation": "One or two sentences on education alignment."
    }},
    "keyword_relevance": {{
      "score": <integer 0-100>,
      "weight": 15,
      "matched_keywords": ["keyword1", "keyword2"],
      "explanation": "One or two sentences on domain/keyword relevance."
    }},
    "overall_fit": {{
      "score": <integer 0-100>,
      "weight": 5,
      "explanation": "One or two sentences on general role fit."
    }}
  }},
  "strengths": ["Strength 1", "Strength 2", "Strength 3"],
  "weaknesses": ["Weakness 1", "Weakness 2"],
  "recommendation": "<Hire|Consider|Reject> — one sentence rationale.",
  "summary": "Two to three sentence overall assessment."
}}

The overall_score MUST equal:
round(skills_match.score*0.35 + experience_match.score*0.25 + education_match.score*0.20 + keyword_relevance.score*0.15 + overall_fit.score*0.05)"""

    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Strip markdown code fences if Gemini wraps output
    json_match = re.search(r'\{[\s\S]*\}', raw)
    if json_match:
        raw = json_match.group()

    data = json.loads(raw)

    # Recalculate from breakdown to guarantee formula consistency
    breakdown = data.get('breakdown', {})
    if breakdown:
        weights = {
            'skills_match': 0.35,
            'experience_match': 0.25,
            'education_match': 0.20,
            'keyword_relevance': 0.15,
            'overall_fit': 0.05,
        }
        data['overall_score'] = round(sum(
            breakdown.get(k, {}).get('score', 0) * w
            for k, w in weights.items()
        ))

    return data
