from django.db import models
from apps.profiles.models import CandidateProfile
from apps.jobs.models import Job


class Application(models.Model):
    APPLIED = 'applied'
    REVIEWING = 'reviewing'
    SHORTLISTED = 'shortlisted'
    INTERVIEW = 'interview'
    OFFERED = 'offered'
    REJECTED = 'rejected'
    WITHDRAWN = 'withdrawn'
    STATUSES = [
        (APPLIED, 'Applied'),
        (REVIEWING, 'Under Review'),
        (SHORTLISTED, 'Shortlisted'),
        (INTERVIEW, 'Interview Scheduled'),
        (OFFERED, 'Offer Made'),
        (REJECTED, 'Rejected'),
        (WITHDRAWN, 'Withdrawn'),
    ]

    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUSES, default=APPLIED)
    cover_letter = models.TextField(blank=True)
    resume_snapshot = models.FileField(upload_to='resumes/snapshots/', blank=True, null=True)
    ai_match_score = models.FloatField(null=True, blank=True)
    ai_score_breakdown = models.JSONField(default=dict)
    employer_notes = models.TextField(blank=True)
    employer_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('candidate', 'job')
        ordering = ['-applied_at']

    def __str__(self):
        return f'{self.candidate.full_name} → {self.job.title}'
