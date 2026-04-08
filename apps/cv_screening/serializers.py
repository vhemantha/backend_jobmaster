from rest_framework import serializers
from .models import UploadedCV, CVScreeningResult, CV_CATEGORIES


class UploadedCVSerializer(serializers.ModelSerializer):
    uploaded_by_email = serializers.SerializerMethodField()
    screening_count = serializers.SerializerMethodField()
    category_label = serializers.CharField(read_only=True)

    class Meta:
        model = UploadedCV
        fields = [
            'id', 'candidate_name', 'candidate_email', 'phone',
            'category', 'category_label',
            'cv_file', 'notes', 'uploaded_at',
            'uploaded_by_email', 'screening_count',
        ]
        read_only_fields = ['uploaded_at', 'uploaded_by_email', 'screening_count', 'category_label']

    def get_uploaded_by_email(self, obj):
        return obj.uploaded_by.email if obj.uploaded_by else None

    def get_screening_count(self, obj):
        return obj.screening_results.count()


class CVScreeningResultListSerializer(serializers.ModelSerializer):
    cv_id = serializers.IntegerField(source='cv.id')
    cv_candidate_name = serializers.CharField(source='cv.candidate_name')
    cv_candidate_email = serializers.CharField(source='cv.candidate_email')
    cv_category = serializers.CharField(source='cv.category')
    cv_category_label = serializers.CharField(source='cv.category_label')
    job_id = serializers.IntegerField(source='job.id')
    job_title = serializers.CharField(source='job.title')
    match_label = serializers.CharField(read_only=True)

    class Meta:
        model = CVScreeningResult
        fields = [
            'id', 'cv_id', 'cv_candidate_name', 'cv_candidate_email',
            'cv_category', 'cv_category_label',
            'job_id', 'job_title',
            'overall_score', 'match_label',
            'recommendation', 'screened_at',
        ]


class CVScreeningResultDetailSerializer(serializers.ModelSerializer):
    cv = UploadedCVSerializer(read_only=True)
    job_id = serializers.IntegerField(source='job.id')
    job_title = serializers.CharField(source='job.title')
    match_label = serializers.CharField(read_only=True)

    class Meta:
        model = CVScreeningResult
        fields = [
            'id', 'cv', 'job_id', 'job_title',
            'overall_score', 'match_label',
            'score_breakdown', 'strengths', 'weaknesses',
            'recommendation', 'summary',
            'screened_at', 'gemini_model_used',
        ]
