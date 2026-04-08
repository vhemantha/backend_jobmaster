from django.db import models
from django.conf import settings


class CandidateProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='candidate_profile')
    full_name = models.CharField(max_length=150)
    headline = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    skills = models.JSONField(default=list)
    experience_years = models.PositiveIntegerField(default=0)
    education = models.JSONField(default=list)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    is_open_to_work = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.full_name} — Candidate'

    @property
    def completion_score(self):
        score = 0
        if self.full_name:
            score += 15
        if self.headline:
            score += 10
        if self.bio:
            score += 10
        if self.location:
            score += 5
        if self.avatar:
            score += 5
        if self.resume:
            score += 20
        if self.skills:
            score += 15
        if self.education:
            score += 10
        if self.linkedin_url or self.github_url:
            score += 10
        return min(score, 100)


class EmployerProfile(models.Model):
    COMPANY_SIZES = [
        ('1-10', '1-10'),
        ('11-50', '11-50'),
        ('51-200', '51-200'),
        ('201-500', '201-500'),
        ('501-1000', '501-1000'),
        ('1000+', '1000+'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employer_profile')
    company_name = models.CharField(max_length=200)
    company_slug = models.SlugField(unique=True)
    tagline = models.CharField(max_length=250, blank=True)
    about = models.TextField(blank=True)
    industry = models.CharField(max_length=100, blank=True)
    company_size = models.CharField(max_length=20, choices=COMPANY_SIZES, blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='avatars/', blank=True, null=True)
    location = models.CharField(max_length=150, blank=True)
    founded_year = models.PositiveIntegerField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.company_name} — Employer'
