"""
JobMasters Mock AI Matching Engine
===================================
Four-factor weighted scoring algorithm:
  Overall = (Skill × 0.50) + (Experience × 0.25) + (Keyword × 0.20) + (Location × 0.05)
"""
import re
from .skill_taxonomy import normalize_skill

STOP_WORDS = {
    'the', 'and', 'or', 'in', 'at', 'of', 'to', 'a', 'an', 'is', 'are',
    'we', 'you', 'will', 'must', 'have', 'has', 'be', 'our', 'your',
    'with', 'for', 'on', 'as', 'by', 'this', 'that', 'from', 'about',
    'who', 'what', 'when', 'where', 'how', 'which', 'can', 'not',
}

EXPERIENCE_RANGES = {
    'entry':     (0, 2),
    'mid':       (2, 5),
    'senior':    (5, 10),
    'lead':      (8, 15),
    'executive': (12, 50),
}


def _skill_score(candidate_skills: list, required: list, nice: list) -> dict:
    normalized_cand = {normalize_skill(s) for s in candidate_skills}
    norm_req = [normalize_skill(s) for s in required]
    norm_nice = [normalize_skill(s) for s in nice]

    if not norm_req:
        return {'score': 50.0, 'matched': list(norm_nice & normalized_cand), 'missing': []}

    matched_req = [s for s in norm_req if s in normalized_cand]
    matched_nice = [s for s in norm_nice if s in normalized_cand]
    missing_req = [s for s in norm_req if s not in normalized_cand]

    required_score = (len(matched_req) / len(norm_req)) * 100
    nice_bonus = min(len(matched_nice) * 5, 15)
    raw = min(required_score + nice_bonus, 100.0)

    return {
        'score': round(raw, 2),
        'matched': matched_req + matched_nice,
        'missing': missing_req,
    }


def _experience_score(candidate_years: int, job_level: str) -> float:
    min_exp, max_exp = EXPERIENCE_RANGES.get(job_level, (2, 5))
    if candidate_years >= min_exp:
        if candidate_years <= max_exp * 2:
            return 100.0
        return 70.0  # significantly overqualified
    ratio = candidate_years / max(min_exp, 1)
    return round(min(ratio * 100, 95.0), 2)


def _keyword_score(candidate_profile: dict, job: dict) -> float:
    def tokenize(text: str) -> set:
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9+#.\-]{2,}\b', text.lower())
        return {w for w in words if w not in STOP_WORDS}

    job_text = ' '.join([
        job.get('description', ''),
        job.get('requirements', ''),
        job.get('responsibilities', ''),
        ' '.join(job.get('required_skills', [])),
    ])
    cand_text = ' '.join([
        candidate_profile.get('bio', ''),
        candidate_profile.get('headline', ''),
        ' '.join(candidate_profile.get('skills', [])),
    ])

    job_kw = tokenize(job_text)
    cand_kw = tokenize(cand_text)

    if not job_kw:
        return 50.0

    overlap = job_kw & cand_kw
    return round(min((len(overlap) / len(job_kw)) * 100, 100.0), 2)


def _location_score(candidate_location: str, job_location: str, work_mode: str) -> float:
    if work_mode == 'remote':
        return 100.0
    if not candidate_location or not job_location:
        return 50.0
    cand_tokens = set(candidate_location.lower().replace(',', '').split())
    job_tokens = set(job_location.lower().replace(',', '').split())
    if cand_tokens & job_tokens:
        return 100.0
    return 25.0


def calculate_match_score(candidate_profile: dict, job: dict) -> dict:
    """
    Master scoring function.

    candidate_profile keys: skills, experience_years, bio, headline, location
    job keys: required_skills, nice_to_have_skills, experience_level,
              description, requirements, responsibilities, location, work_mode
    """
    skill_result = _skill_score(
        candidate_profile.get('skills', []),
        job.get('required_skills', []),
        job.get('nice_to_have_skills', []),
    )
    exp = _experience_score(
        candidate_profile.get('experience_years', 0),
        job.get('experience_level', 'mid'),
    )
    kw = _keyword_score(candidate_profile, job)
    loc = _location_score(
        candidate_profile.get('location', ''),
        job.get('location', ''),
        job.get('work_mode', 'onsite'),
    )

    overall = round(
        skill_result['score'] * 0.50 +
        exp * 0.25 +
        kw * 0.20 +
        loc * 0.05,
        1,
    )

    if overall >= 80:
        label = 'Strong Match'
    elif overall >= 60:
        label = 'Good Match'
    elif overall >= 40:
        label = 'Partial Match'
    else:
        label = 'Low Match'

    return {
        'overall_score': overall,
        'label': label,
        'breakdown': {
            'skill_score': skill_result['score'],
            'experience_score': exp,
            'keyword_score': kw,
            'location_score': loc,
        },
        'matched_skills': skill_result['matched'],
        'missing_skills': skill_result['missing'],
    }
