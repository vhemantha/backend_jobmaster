from rest_framework import serializers
from .models import CandidateProfile, EmployerProfile


class CandidateProfileSerializer(serializers.ModelSerializer):
    completion_score = serializers.ReadOnlyField()
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = CandidateProfile
        fields = (
            'id', 'email', 'full_name', 'headline', 'bio', 'location',
            'avatar', 'resume', 'skills', 'experience_years', 'education',
            'linkedin_url', 'github_url', 'portfolio_url', 'is_open_to_work',
            'completion_score', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'email', 'completion_score', 'created_at', 'updated_at')


class CandidateProfilePublicSerializer(serializers.ModelSerializer):
    """Minimal public view for employers browsing candidates."""
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = CandidateProfile
        fields = (
            'id', 'email', 'full_name', 'headline', 'location',
            'avatar', 'skills', 'experience_years', 'linkedin_url',
            'github_url', 'portfolio_url', 'is_open_to_work',
        )


class EmployerProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = EmployerProfile
        fields = (
            'id', 'email', 'company_name', 'company_slug', 'tagline', 'about',
            'industry', 'company_size', 'website', 'logo', 'location',
            'founded_year', 'linkedin_url', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'email', 'company_slug', 'created_at', 'updated_at')

    def create(self, validated_data):
        from django.utils.text import slugify
        import uuid
        name = validated_data.get('company_name', '')
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while EmployerProfile.objects.filter(company_slug=slug).exists():
            slug = f'{base_slug}-{counter}'
            counter += 1
        validated_data['company_slug'] = slug
        return super().create(validated_data)
