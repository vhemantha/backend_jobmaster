from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Application
from .serializers import ApplicationCandidateSerializer, ApplicationEmployerSerializer
from apps.profiles.permissions import IsCandidate, IsEmployer
from apps.jobs.models import Job
from apps.ai_engine.matcher import calculate_match_score


def _score_and_save(application, candidate, job):
    """Compute AI score and persist it on the application."""
    candidate_dict = {
        'skills': candidate.skills,
        'experience_years': candidate.experience_years,
        'bio': candidate.bio,
        'headline': candidate.headline,
        'location': candidate.location,
    }
    job_dict = {
        'required_skills': job.required_skills,
        'nice_to_have_skills': job.nice_to_have_skills,
        'experience_level': job.experience_level,
        'description': job.description,
        'requirements': job.requirements,
        'responsibilities': job.responsibilities,
        'location': job.location,
        'work_mode': job.work_mode,
    }
    result = calculate_match_score(candidate_dict, job_dict)
    application.ai_match_score = result['overall_score']
    application.ai_score_breakdown = result['breakdown']
    application.save(update_fields=['ai_match_score', 'ai_score_breakdown'])


# ─── Candidate views ──────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsCandidate])
def apply(request):
    try:
        candidate = request.user.candidate_profile
    except Exception:
        return Response({'detail': 'Create a candidate profile first.'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = ApplicationCandidateSerializer(data=request.data)
    if serializer.is_valid():
        job = serializer.validated_data['job']
        if Application.objects.filter(candidate=candidate, job=job).exists():
            return Response({'detail': 'You have already applied to this job.'}, status=status.HTTP_400_BAD_REQUEST)
        app = serializer.save(candidate=candidate)
        _score_and_save(app, candidate, job)
        app.refresh_from_db()
        return Response(ApplicationCandidateSerializer(app).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsCandidate])
def my_applications(request):
    try:
        candidate = request.user.candidate_profile
    except Exception:
        return Response({'detail': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    status_filter = request.query_params.get('status')
    apps = candidate.applications.select_related('job', 'job__employer', 'job__category')
    if status_filter:
        apps = apps.filter(status=status_filter)

    return Response(ApplicationCandidateSerializer(apps, many=True).data)


@api_view(['GET', 'DELETE'])
@permission_classes([IsCandidate])
def my_application_detail(request, pk):
    try:
        candidate = request.user.candidate_profile
    except Exception:
        return Response({'detail': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    app = get_object_or_404(Application, pk=pk, candidate=candidate)

    if request.method == 'DELETE':
        app.status = Application.WITHDRAWN
        app.save(update_fields=['status'])
        return Response({'detail': 'Application withdrawn.'})

    return Response(ApplicationCandidateSerializer(app).data)


# ─── Employer views ───────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsEmployer])
def job_applications(request, job_id):
    try:
        employer = request.user.employer_profile
    except Exception:
        return Response({'detail': 'Employer profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    job = get_object_or_404(Job, pk=job_id, employer=employer)
    apps = job.applications.select_related('candidate', 'candidate__user').order_by('-ai_match_score')
    return Response(ApplicationEmployerSerializer(apps, many=True).data)


@api_view(['GET'])
@permission_classes([IsEmployer])
def job_application_detail(request, job_id, app_id):
    try:
        employer = request.user.employer_profile
    except Exception:
        return Response({'detail': 'Employer profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    job = get_object_or_404(Job, pk=job_id, employer=employer)
    app = get_object_or_404(Application, pk=app_id, job=job)
    return Response(ApplicationEmployerSerializer(app).data)


@api_view(['PATCH'])
@permission_classes([IsEmployer])
def update_application_status(request, job_id, app_id):
    try:
        employer = request.user.employer_profile
    except Exception:
        return Response({'detail': 'Employer profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    job = get_object_or_404(Job, pk=job_id, employer=employer)
    app = get_object_or_404(Application, pk=app_id, job=job)

    new_status = request.data.get('status')
    valid_statuses = [s[0] for s in Application.STATUSES]
    if new_status not in valid_statuses:
        return Response({'detail': f'Invalid status. Choose from: {valid_statuses}'}, status=status.HTTP_400_BAD_REQUEST)

    app.status = new_status
    app.save(update_fields=['status'])

    # Auto-create notification for candidate
    try:
        from apps.accounts.models import Notification
        status_label = new_status.replace('_', ' ').title()
        Notification.objects.create(
            user=app.candidate.user,
            type=Notification.APPLICATION_UPDATE,
            title=f'Application {status_label}',
            message=f'Your application for {job.title} at {job.employer.company_name} has been {status_label.lower()}.',
            link='/candidate/applications',
        )
    except Exception:
        pass  # Never let notification failure break the status update

    return Response(ApplicationEmployerSerializer(app).data)


@api_view(['PATCH'])
@permission_classes([IsEmployer])
def update_application_notes(request, job_id, app_id):
    try:
        employer = request.user.employer_profile
    except Exception:
        return Response({'detail': 'Employer profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    job = get_object_or_404(Job, pk=job_id, employer=employer)
    app = get_object_or_404(Application, pk=app_id, job=job)

    notes = request.data.get('employer_notes', '')
    rating = request.data.get('employer_rating')

    app.employer_notes = notes
    if rating is not None:
        app.employer_rating = rating
    app.save(update_fields=['employer_notes', 'employer_rating'])
    return Response(ApplicationEmployerSerializer(app).data)
