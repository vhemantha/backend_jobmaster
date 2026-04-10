import logging
import threading
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from django.db import close_old_connections
from django.http import FileResponse, HttpResponseRedirect
from django.conf import settings as django_settings

from .models import UploadedCV, CVScreeningResult, GEMINI_MODEL, CV_CATEGORIES
from .serializers import (
    UploadedCVSerializer,
    CVScreeningResultListSerializer,
    CVScreeningResultDetailSerializer,
)
from .services.gemini_screener import extract_pdf_text, screen_cv_against_job
from apps.jobs.models import Job
from apps.profiles.permissions import IsEmployer

logger = logging.getLogger(__name__)


def _run_gemini_background(result_pk, cv_text, job_pk):
    """Run Gemini screening in a daemon thread; update result when done."""
    close_old_connections()
    try:
        job = Job.objects.get(pk=job_pk)
        result_data = screen_cv_against_job(cv_text, job)
        CVScreeningResult.objects.filter(pk=result_pk).update(
            overall_score=result_data.get('overall_score', 0),
            score_breakdown=result_data.get('breakdown', {}),
            strengths=result_data.get('strengths', []),
            weaknesses=result_data.get('weaknesses', []),
            recommendation=result_data.get('recommendation', ''),
            summary=result_data.get('summary', ''),
            gemini_model_used=GEMINI_MODEL,
            status='completed',
            error_message='',
        )
        logger.info(f"Background screening completed for result_pk={result_pk}")
    except Exception as e:
        logger.error(f"Background screening failed for result_pk={result_pk}: {e}")
        CVScreeningResult.objects.filter(pk=result_pk).update(
            status='failed',
            error_message=str(e)[:500],
        )
    finally:
        close_old_connections()


def _is_employer(user):
    return user.is_authenticated and user.role == 'employer'


def _can_access_screening(user):
    return user.is_staff or _is_employer(user)


def _apply_score_filter(qs, params):
    """Filter queryset by min_score/max_score query params; silently ignores bad values."""
    try:
        min_score = float(params.get('min_score', 0))
        max_score = float(params.get('max_score', 100))
        return qs.filter(overall_score__gte=min_score, overall_score__lte=max_score)
    except ValueError:
        return qs


class CVCategoriesView(APIView):
    """Return the list of CV categories — used to populate dropdowns."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([{'value': v, 'label': l} for v, l in CV_CATEGORIES])


class CVUploadView(APIView):
    """
    GET  — list CVs (admin sees all; employer sees their own).
    POST — upload one or more CVs in a single request.
             Accepts multiple files under the key `cv_files[]`.
             Shared fields (category, notes) apply to all files in the batch.
             Returns { created: [...], errors: [...] }.
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_staff:
            cvs = UploadedCV.objects.select_related('uploaded_by').all()
        elif _is_employer(request.user):
            cvs = UploadedCV.objects.select_related('uploaded_by').filter(uploaded_by=request.user)
        else:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        category = request.query_params.get('category')
        if category:
            cvs = cvs.filter(category=category)

        return Response(
            UploadedCVSerializer(cvs, many=True, context={'request': request}).data
        )

    def post(self, request):
        if not _can_access_screening(request.user):
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        files = request.FILES.getlist('cv_files')
        if not files:
            single = request.FILES.get('cv_file')
            if single:
                files = [single]
            else:
                return Response(
                    {'error': 'At least one PDF file is required (key: cv_files).'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        category = request.data.get('category', 'other')
        notes = request.data.get('notes', '')
        names = request.data.getlist('candidate_names')
        emails = request.data.getlist('candidate_emails')
        phones = request.data.getlist('candidate_phones')

        created_cvs = []
        errors = []

        for idx, file in enumerate(files):
            candidate_name = (
                names[idx] if idx < len(names) and names[idx].strip()
                else file.name.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')
            )
            candidate_email = emails[idx] if idx < len(emails) else ''
            phone = phones[idx] if idx < len(phones) else ''

            try:
                cv = UploadedCV.objects.create(
                    candidate_name=candidate_name,
                    candidate_email=candidate_email,
                    phone=phone,
                    category=category,
                    cv_file=file,
                    notes=notes,
                    uploaded_by=request.user,
                )
                cv.cv_text = extract_pdf_text(cv.cv_file.path)
                cv.save(update_fields=['cv_text'])
                created_cvs.append(cv)
            except Exception as e:
                logger.error(f"Bulk upload error for file {file.name}: {e}")
                errors.append({'file': file.name, 'error': str(e)})

        response_data = {
            'created': UploadedCVSerializer(
                created_cvs, many=True, context={'request': request}
            ).data,
            'errors': errors,
        }
        status_code = status.HTTP_201_CREATED if created_cvs else status.HTTP_400_BAD_REQUEST
        return Response(response_data, status=status_code)


class CVDetailView(APIView):
    """Admin: any CV. Employer: only CVs they uploaded."""
    permission_classes = [IsAuthenticated]

    def _get_cv(self, request, pk):
        if request.user.is_staff:
            return get_object_or_404(UploadedCV, pk=pk)
        elif _is_employer(request.user):
            return get_object_or_404(UploadedCV, pk=pk, uploaded_by=request.user)
        return None

    def get(self, request, pk):
        cv = self._get_cv(request, pk)
        if cv is None:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        return Response(UploadedCVSerializer(cv, context={'request': request}).data)

    def delete(self, request, pk):
        cv = self._get_cv(request, pk)
        if cv is None:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        cv.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CVDownloadView(APIView):
    """
    Stream a CV PDF as a file download.
    Admin: any CV.
    Employer: CVs they uploaded OR CVs that have a screening result against one of their jobs.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        cv = get_object_or_404(UploadedCV, pk=pk)

        if not request.user.is_staff:
            if not _is_employer(request.user):
                return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
            employer_owns = cv.uploaded_by_id == request.user.pk
            has_result = CVScreeningResult.objects.filter(
                cv=cv, job__employer__user=request.user
            ).exists()
            if not employer_owns and not has_result:
                return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        if not cv.cv_file:
            return Response({'error': 'No file attached to this CV.'}, status=status.HTTP_404_NOT_FOUND)

        safe_name = cv.candidate_name.replace(' ', '_')

        # Cloudinary stores files remotely — redirect to the signed URL.
        if getattr(django_settings, 'CLOUDINARY_CLOUD_NAME', ''):
            return HttpResponseRedirect(cv.cv_file.url)

        # Local disk (dev)
        try:
            response = FileResponse(cv.cv_file.open('rb'), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{safe_name}_CV.pdf"'
            return response
        except FileNotFoundError:
            return Response(
                {'error': 'File not found on disk. It may have been lost after a server restart.'},
                status=status.HTTP_404_NOT_FOUND,
            )


class CVScreenView(APIView):
    """
    Trigger Gemini AI screening for a CV + job pair.
    Admin: any CV vs any job.
    Employer: only their CVs vs their jobs.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not _can_access_screening(request.user):
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        cv_id = request.data.get('cv_id')
        job_id = request.data.get('job_id')
        if not cv_id or not job_id:
            return Response(
                {'error': 'Both cv_id and job_id are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.user.is_staff:
            cv = get_object_or_404(UploadedCV, pk=cv_id)
            job = get_object_or_404(Job, pk=job_id)
        else:
            cv = get_object_or_404(UploadedCV, pk=cv_id, uploaded_by=request.user)
            job = get_object_or_404(Job, pk=job_id, employer__user=request.user)

        if not cv.cv_text and cv.cv_file:
            cv.cv_text = extract_pdf_text(cv.cv_file.path)
            cv.save(update_fields=['cv_text'])

        if not cv.cv_text:
            return Response(
                {'error': 'Could not extract text from this CV. Ensure it is a text-based PDF.'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # Create/reset the result record immediately so the client has an ID to poll.
        result, _ = CVScreeningResult.objects.update_or_create(
            cv=cv, job=job,
            defaults={
                'overall_score': 0,
                'score_breakdown': {},
                'strengths': [],
                'weaknesses': [],
                'recommendation': '',
                'summary': '',
                'gemini_model_used': GEMINI_MODEL,
                'status': 'processing',
                'error_message': '',
            },
        )

        # Fire Gemini in a background thread so the response returns within Render's 30s window.
        t = threading.Thread(
            target=_run_gemini_background,
            args=(result.pk, cv.cv_text, job.pk),
            daemon=True,
        )
        t.start()

        return Response(
            CVScreeningResultDetailSerializer(result).data,
            status=status.HTTP_202_ACCEPTED,
        )


class JobScreeningResultsView(APIView):
    """Employer — CV screening results for one of their jobs, with score/category filtering."""
    permission_classes = [IsAuthenticated, IsEmployer]

    def get(self, request, job_id):
        job = get_object_or_404(Job, pk=job_id, employer__user=request.user)
        results = CVScreeningResult.objects.filter(job=job).select_related('cv', 'job')
        results = _apply_score_filter(results, request.query_params)

        category = request.query_params.get('category')
        if category:
            results = results.filter(cv__category=category)

        return Response(CVScreeningResultListSerializer(results, many=True).data)


class AllScreeningResultsView(APIView):
    """Admin — all screening results with optional filters."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        results = CVScreeningResult.objects.all().select_related('cv', 'job')
        results = _apply_score_filter(results, request.query_params)

        job_id = request.query_params.get('job_id')
        if job_id:
            results = results.filter(job_id=job_id)

        category = request.query_params.get('category')
        if category:
            results = results.filter(cv__category=category)

        return Response(CVScreeningResultListSerializer(results, many=True).data)


class ScreeningResultDetailView(APIView):
    """Full breakdown — admin or owning employer."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        result = get_object_or_404(
            CVScreeningResult.objects.select_related('cv', 'job'), pk=pk
        )

        if not request.user.is_staff:
            if not hasattr(request.user, 'employer_profile'):
                return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
            if result.job.employer.user_id != request.user.pk:
                return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        return Response(CVScreeningResultDetailSerializer(result).data)
