from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Job, JobCategory, SavedJob
from .serializers import (
    JobListSerializer, JobDetailSerializer, JobWriteSerializer, JobCategorySerializer,
)
from .filters import JobFilter
from apps.profiles.permissions import IsEmployer, IsCandidate


@api_view(['GET'])
@permission_classes([AllowAny])
def job_list(request):
    """Public active job listing with filters."""
    qs = Job.objects.filter(status='active').select_related('employer', 'category')

    # Text search
    search = request.query_params.get('search', '')
    if search:
        from django.db.models import Q
        qs = qs.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(employer__company_name__icontains=search)
        )

    # Filters
    for field in ('job_type', 'work_mode', 'experience_level'):
        val = request.query_params.get(field)
        if val:
            qs = qs.filter(**{field: val})

    category = request.query_params.get('category')
    if category:
        qs = qs.filter(category__slug=category)

    location = request.query_params.get('location')
    if location:
        qs = qs.filter(location__icontains=location)

    salary_min = request.query_params.get('salary_min')
    if salary_min:
        qs = qs.filter(salary_min__gte=salary_min)

    salary_max = request.query_params.get('salary_max')
    if salary_max:
        qs = qs.filter(salary_max__lte=salary_max)

    # Date posted filter
    date_posted = request.query_params.get('date_posted')
    if date_posted:
        from django.utils import timezone
        import datetime
        days_map = {'1': 1, '7': 7, '30': 30}
        days = days_map.get(date_posted)
        if days:
            since = timezone.now() - datetime.timedelta(days=days)
            qs = qs.filter(created_at__gte=since)

    # Ordering
    ordering = request.query_params.get('ordering', '-created_at')
    if ordering in ('created_at', '-created_at', 'salary_min', '-salary_min', 'views_count', '-views_count'):
        qs = qs.order_by(ordering)

    # Pagination
    from utils.pagination import StandardPagination
    paginator = StandardPagination()
    page = paginator.paginate_queryset(qs, request)
    serializer = JobListSerializer(page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def job_featured(request):
    """Top 6 active jobs for landing page hero."""
    jobs = Job.objects.filter(status='active').select_related('employer', 'category').order_by('-created_at')[:6]
    return Response(JobListSerializer(jobs, many=True, context={'request': request}).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def job_categories(request):
    cats = JobCategory.objects.all()
    return Response(JobCategorySerializer(cats, many=True).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if job.status == 'active':
        Job.objects.filter(pk=pk).update(views_count=job.views_count + 1)
        job.refresh_from_db(fields=['views_count'])
    return Response(JobDetailSerializer(job, context={'request': request}).data)


@api_view(['GET'])
@permission_classes([IsEmployer])
def my_jobs(request):
    """Employer's own job postings."""
    try:
        employer = request.user.employer_profile
    except Exception:
        return Response({'detail': 'Employer profile not found.'}, status=status.HTTP_404_NOT_FOUND)
    jobs = employer.jobs.select_related('category').all()
    return Response(JobListSerializer(jobs, many=True, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsEmployer])
def job_create(request):
    try:
        employer = request.user.employer_profile
    except Exception:
        return Response({'detail': 'Create an employer profile first.'}, status=status.HTTP_400_BAD_REQUEST)
    serializer = JobWriteSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(employer=employer)
        return Response(JobDetailSerializer(serializer.instance, context={'request': request}).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'PATCH', 'DELETE'])
@permission_classes([IsEmployer])
def job_edit(request, pk):
    try:
        employer = request.user.employer_profile
    except Exception:
        return Response({'detail': 'Employer profile not found.'}, status=status.HTTP_404_NOT_FOUND)
    job = get_object_or_404(Job, pk=pk, employer=employer)

    if request.method == 'DELETE':
        job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    partial = request.method == 'PATCH'
    serializer = JobWriteSerializer(job, data=request.data, partial=partial)
    if serializer.is_valid():
        serializer.save()
        return Response(JobDetailSerializer(serializer.instance, context={'request': request}).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─── Saved Jobs ──────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsCandidate])
def saved_jobs(request):
    try:
        candidate = request.user.candidate_profile
    except Exception:
        return Response({'detail': 'Candidate profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        saved = SavedJob.objects.filter(candidate=candidate).select_related('job__employer', 'job__category')
        jobs = [s.job for s in saved]
        return Response(JobListSerializer(jobs, many=True, context={'request': request}).data)

    job_id = request.data.get('job_id')
    if not job_id:
        return Response({'detail': 'job_id required.'}, status=status.HTTP_400_BAD_REQUEST)
    job = get_object_or_404(Job, pk=job_id)
    _, created = SavedJob.objects.get_or_create(candidate=candidate, job=job)
    return Response({'saved': True, 'job_id': job.id}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsCandidate])
def unsave_job(request, job_id):
    try:
        candidate = request.user.candidate_profile
    except Exception:
        return Response({'detail': 'Candidate profile not found.'}, status=status.HTTP_404_NOT_FOUND)
    SavedJob.objects.filter(candidate=candidate, job_id=job_id).delete()
    return Response({'saved': False, 'job_id': job_id}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsCandidate])
def saved_job_ids(request):
    """Return just the list of saved job IDs for fast frontend lookups."""
    try:
        candidate = request.user.candidate_profile
    except Exception:
        return Response([], status=status.HTTP_200_OK)
    ids = list(SavedJob.objects.filter(candidate=candidate).values_list('job_id', flat=True))
    return Response(ids)


# ─── Employer Analytics ───────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsEmployer])
def employer_analytics(request):
    try:
        employer = request.user.employer_profile
    except Exception:
        return Response({'detail': 'Employer profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    from apps.applications.models import Application
    from django.db.models import Count
    from django.utils import timezone
    import datetime

    jobs = employer.jobs.all()
    total_jobs = jobs.count()
    active_jobs = jobs.filter(status='active').count()
    total_views = jobs.aggregate(v=models.Sum('views_count'))['v'] or 0

    apps_qs = Application.objects.filter(job__employer=employer)
    total_apps = apps_qs.count()

    # Applications by status
    by_status = dict(apps_qs.values_list('status').annotate(c=Count('id')).values_list('status', 'c'))

    # Top 5 jobs by applications
    top_jobs = list(
        jobs.annotate(app_count=Count('applications'))
            .order_by('-app_count')[:5]
            .values('id', 'title', 'app_count', 'views_count', 'status')
    )

    # Weekly applications (last 7 days)
    weekly = []
    today = timezone.now().date()
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        count = apps_qs.filter(applied_at__date=day).count()
        weekly.append({'date': day.strftime('%Y-%m-%d'), 'label': day.strftime('%a'), 'count': count})

    return Response({
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'total_applications': total_apps,
        'total_views': total_views,
        'applications_by_status': by_status,
        'top_jobs': top_jobs,
        'weekly_applications': weekly,
    })
