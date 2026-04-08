from rest_framework import serializers
from .models import Job, JobCategory


class JobCategorySerializer(serializers.ModelSerializer):
    job_count = serializers.SerializerMethodField()

    class Meta:
        model = JobCategory
        fields = ('id', 'name', 'slug', 'icon', 'job_count')

    def get_job_count(self, obj):
        return obj.jobs.filter(status='active').count()


class EmployerBriefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    company_name = serializers.CharField()
    company_slug = serializers.SlugField()
    logo = serializers.ImageField()
    location = serializers.CharField()
    industry = serializers.CharField()


class JobListSerializer(serializers.ModelSerializer):
    """Abbreviated serializer for job cards."""
    employer_name = serializers.CharField(source='employer.company_name', read_only=True)
    employer_slug = serializers.CharField(source='employer.company_slug', read_only=True)
    employer_logo = serializers.ImageField(source='employer.logo', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    application_count = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = (
            'id', 'slug', 'title', 'employer_name', 'employer_slug', 'employer_logo',
            'category_name', 'location', 'job_type', 'work_mode', 'experience_level',
            'salary_min', 'salary_max', 'salary_currency', 'status',
            'application_count', 'created_at',
        )

    def get_application_count(self, obj):
        return obj.applications.count()


class JobDetailSerializer(serializers.ModelSerializer):
    """Full serializer for job detail page."""
    employer_name = serializers.CharField(source='employer.company_name', read_only=True)
    employer_slug = serializers.CharField(source='employer.company_slug', read_only=True)
    employer_logo = serializers.ImageField(source='employer.logo', read_only=True)
    employer_about = serializers.CharField(source='employer.about', read_only=True)
    employer_size = serializers.CharField(source='employer.company_size', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    application_count = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = (
            'id', 'slug', 'title',
            'employer_name', 'employer_slug', 'employer_logo', 'employer_about', 'employer_size',
            'category_name', 'description', 'responsibilities', 'requirements',
            'required_skills', 'nice_to_have_skills',
            'job_type', 'work_mode', 'experience_level', 'location',
            'salary_min', 'salary_max', 'salary_currency',
            'status', 'application_deadline', 'views_count',
            'application_count', 'created_at', 'updated_at',
        )

    def get_application_count(self, obj):
        return obj.applications.count()


class JobWriteSerializer(serializers.ModelSerializer):
    """For employer creating/editing jobs."""
    class Meta:
        model = Job
        fields = (
            'title', 'category', 'description', 'responsibilities', 'requirements',
            'required_skills', 'nice_to_have_skills',
            'job_type', 'work_mode', 'experience_level', 'location',
            'salary_min', 'salary_max', 'salary_currency',
            'status', 'application_deadline',
        )
