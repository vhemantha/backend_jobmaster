from django.db import models
from apps.profiles.models import CandidateProfile, EmployerProfile


class JobCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name_plural = 'Job Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Job(models.Model):
    FULL_TIME = 'full_time'
    PART_TIME = 'part_time'
    CONTRACT = 'contract'
    INTERNSHIP = 'internship'
    FREELANCE = 'freelance'
    JOB_TYPES = [
        (FULL_TIME, 'Full Time'), (PART_TIME, 'Part Time'),
        (CONTRACT, 'Contract'), (INTERNSHIP, 'Internship'),
        (FREELANCE, 'Freelance'),
    ]

    REMOTE = 'remote'
    ONSITE = 'onsite'
    HYBRID = 'hybrid'
    WORK_MODES = [
        (REMOTE, 'Remote'), (ONSITE, 'On-site'), (HYBRID, 'Hybrid'),
    ]

    ENTRY = 'entry'
    MID = 'mid'
    SENIOR = 'senior'
    LEAD = 'lead'
    EXECUTIVE = 'executive'
    EXP_LEVELS = [
        (ENTRY, 'Entry Level'), (MID, 'Mid Level'), (SENIOR, 'Senior'),
        (LEAD, 'Lead'), (EXECUTIVE, 'Executive'),
    ]

    DRAFT = 'draft'
    ACTIVE = 'active'
    CLOSED = 'closed'
    STATUSES = [(DRAFT, 'Draft'), (ACTIVE, 'Active'), (CLOSED, 'Closed')]

    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, related_name='jobs')
    category = models.ForeignKey(JobCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs')
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    responsibilities = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    required_skills = models.JSONField(default=list)
    nice_to_have_skills = models.JSONField(default=list)
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, default=FULL_TIME)
    work_mode = models.CharField(max_length=20, choices=WORK_MODES, default=ONSITE)
    experience_level = models.CharField(max_length=20, choices=EXP_LEVELS, default=MID)
    location = models.CharField(max_length=150)
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=10, default='USD')
    status = models.CharField(max_length=20, choices=STATUSES, default=DRAFT)
    application_deadline = models.DateField(null=True, blank=True)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} @ {self.employer.company_name}'

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base = slugify(f'{self.title}-{self.employer.company_name}')
            slug = base
            counter = 1
            while Job.objects.filter(slug=slug).exists():
                slug = f'{base}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class SavedJob(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('candidate', 'job')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.candidate.full_name} saved {self.job.title}'
