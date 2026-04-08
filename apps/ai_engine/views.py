from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from apps.jobs.models import Job
from apps.jobs.serializers import JobListSerializer
from apps.profiles.models import CandidateProfile
from apps.profiles.serializers import CandidateProfilePublicSerializer
from apps.profiles.permissions import IsCandidate, IsEmployer
from .matcher import calculate_match_score


def _profile_to_dict(profile):
    return {
        'skills': profile.skills,
        'experience_years': profile.experience_years,
        'bio': profile.bio,
        'headline': profile.headline,
        'location': profile.location,
    }


def _job_to_dict(job):
    return {
        'required_skills': job.required_skills,
        'nice_to_have_skills': job.nice_to_have_skills,
        'experience_level': job.experience_level,
        'description': job.description,
        'requirements': job.requirements,
        'responsibilities': job.responsibilities,
        'location': job.location,
        'work_mode': job.work_mode,
    }


@api_view(['POST'])
@permission_classes([IsCandidate])
def match_score(request):
    """Score logged-in candidate against a specific job."""
    try:
        profile = request.user.candidate_profile
    except Exception:
        return Response({'detail': 'Candidate profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    job_id = request.data.get('job_id')
    if not job_id:
        return Response({'detail': 'job_id required.'}, status=status.HTTP_400_BAD_REQUEST)

    job = get_object_or_404(Job, pk=job_id)
    result = calculate_match_score(_profile_to_dict(profile), _job_to_dict(job))
    return Response({'job_id': job_id, **result})


@api_view(['GET'])
@permission_classes([IsCandidate])
def recommendations(request):
    """Return top scored active jobs for the logged-in candidate.

    Query params:
      limit     — max results (default 20, max 50)
      min_score — only include jobs at or above this score (default 0)
    """
    try:
        profile = request.user.candidate_profile
    except Exception:
        return Response({'detail': 'Candidate profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        limit = min(int(request.query_params.get('limit', 20)), 50)
    except ValueError:
        limit = 20

    try:
        min_score = float(request.query_params.get('min_score', 0))
    except ValueError:
        min_score = 0.0

    candidate_dict = _profile_to_dict(profile)
    jobs = Job.objects.filter(status='active').select_related('employer', 'category')

    scored = []
    for job in jobs:
        result = calculate_match_score(candidate_dict, _job_to_dict(job))
        if result['overall_score'] >= min_score:
            scored.append((result['overall_score'], job, result))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:limit]

    data = []
    for score, job, result in top:
        job_data = JobListSerializer(job, context={'request': request}).data
        job_data['match_score'] = result['overall_score']
        job_data['match_label'] = result['label']
        job_data['match_breakdown'] = result['breakdown']
        job_data['matched_skills'] = result['matched_skills']
        job_data['missing_skills'] = result['missing_skills']
        data.append(job_data)

    return Response({'count': len(scored), 'results': data})


@api_view(['GET'])
@permission_classes([IsEmployer])
def job_candidate_matches(request, job_id):
    """Return all open-to-work candidates ranked by AI match score against a job.

    Only the employer who owns the job can call this endpoint.

    Query params:
      limit     — max results (default 30, max 100)
      min_score — only include candidates at or above this score (default 0)
    """
    try:
        employer = request.user.employer_profile
    except Exception:
        return Response({'detail': 'Employer profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    job = get_object_or_404(Job, pk=job_id, employer=employer)

    try:
        limit = min(int(request.query_params.get('limit', 30)), 100)
    except ValueError:
        limit = 30

    try:
        min_score = float(request.query_params.get('min_score', 0))
    except ValueError:
        min_score = 0.0

    job_dict = _job_to_dict(job)
    candidates = CandidateProfile.objects.filter(is_open_to_work=True).select_related('user')

    scored = []
    for candidate in candidates:
        result = calculate_match_score(_profile_to_dict(candidate), job_dict)
        if result['overall_score'] >= min_score:
            scored.append((result['overall_score'], candidate, result))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:limit]

    data = []
    for score, candidate, result in top:
        cand_data = CandidateProfilePublicSerializer(candidate, context={'request': request}).data
        cand_data['match_score'] = result['overall_score']
        cand_data['match_label'] = result['label']
        cand_data['match_breakdown'] = result['breakdown']
        cand_data['matched_skills'] = result['matched_skills']
        cand_data['missing_skills'] = result['missing_skills']
        data.append(cand_data)

    return Response({
        'count': len(scored),
        'job_title': job.title,
        'results': data,
    })
