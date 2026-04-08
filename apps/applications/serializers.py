from rest_framework import serializers
from .models import Application
from apps.jobs.serializers import JobListSerializer
from apps.profiles.serializers import CandidateProfilePublicSerializer


class ApplicationCandidateSerializer(serializers.ModelSerializer):
    """Candidate's own view of an application."""
    job = JobListSerializer(read_only=True)
    job_id = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=__import__('apps.jobs.models', fromlist=['Job']).Job.objects.all(),
        source='job',
    )
    match_label = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = (
            'id', 'job', 'job_id', 'status', 'cover_letter',
            'ai_match_score', 'ai_score_breakdown', 'match_label',
            'applied_at', 'updated_at',
        )
        read_only_fields = ('id', 'status', 'ai_match_score', 'ai_score_breakdown', 'applied_at', 'updated_at')

    def get_match_label(self, obj):
        score = obj.ai_match_score
        if score is None:
            return None
        if score >= 80:
            return 'Strong Match'
        if score >= 60:
            return 'Good Match'
        if score >= 40:
            return 'Partial Match'
        return 'Low Match'


class ApplicationEmployerSerializer(serializers.ModelSerializer):
    """Employer's view of an application — includes candidate profile."""
    candidate = CandidateProfilePublicSerializer(read_only=True)
    match_label = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = (
            'id', 'candidate', 'status', 'cover_letter', 'resume_snapshot',
            'ai_match_score', 'ai_score_breakdown', 'match_label',
            'employer_notes', 'employer_rating',
            'applied_at', 'updated_at',
        )
        read_only_fields = ('id', 'candidate', 'ai_match_score', 'ai_score_breakdown', 'applied_at')

    def get_match_label(self, obj):
        score = obj.ai_match_score
        if score is None:
            return None
        if score >= 80:
            return 'Strong Match'
        if score >= 60:
            return 'Good Match'
        if score >= 40:
            return 'Partial Match'
        return 'Low Match'
