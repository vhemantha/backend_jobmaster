from django.db import models

GEMINI_MODEL = 'gemini-2.5-flash'

SCREENING_STATUS = [
    ('pending',    'Pending'),
    ('processing', 'Processing'),
    ('completed',  'Completed'),
    ('failed',     'Failed'),
]

CV_CATEGORIES = [
    ('engineering',      'Engineering & Tech'),
    ('design',           'Design & Creative'),
    ('product',          'Product & Management'),
    ('marketing',        'Marketing & Growth'),
    ('sales',            'Sales & Business Dev'),
    ('finance',          'Finance & Accounting'),
    ('hr',               'HR & Recruitment'),
    ('operations',       'Operations & Logistics'),
    ('data',             'Data & Analytics'),
    ('customer_support', 'Customer Support'),
    ('legal',            'Legal & Compliance'),
    ('other',            'Other'),
]


class UploadedCV(models.Model):
    candidate_name = models.CharField(max_length=255)
    candidate_email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    category = models.CharField(
        max_length=50, choices=CV_CATEGORIES, default='other',
        help_text='Role category — used for basic filtering and grouping',
    )
    cv_file = models.FileField(upload_to='uploaded_cvs/')
    cv_text = models.TextField(blank=True)
    notes = models.TextField(blank=True, help_text='Internal notes about this CV')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, related_name='uploaded_cvs',
    )

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Uploaded CV'
        verbose_name_plural = 'Uploaded CVs'

    def __str__(self):
        return f"{self.candidate_name} ({self.get_category_display()})"

    @property
    def category_label(self):
        return dict(CV_CATEGORIES).get(self.category, self.category)


class CVScreeningResult(models.Model):
    cv = models.ForeignKey(
        UploadedCV, on_delete=models.CASCADE, related_name='screening_results',
    )
    job = models.ForeignKey(
        'jobs.Job', on_delete=models.CASCADE, related_name='cv_screening_results',
    )
    overall_score = models.FloatField(default=0)
    score_breakdown = models.JSONField(default=dict)
    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)
    recommendation = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    screened_at = models.DateTimeField(auto_now_add=True)
    gemini_model_used = models.CharField(max_length=50, default=GEMINI_MODEL)
    status = models.CharField(max_length=20, choices=SCREENING_STATUS, default='completed')
    error_message = models.TextField(blank=True)

    class Meta:
        unique_together = ('cv', 'job')
        ordering = ['-overall_score']
        verbose_name = 'CV Screening Result'
        verbose_name_plural = 'CV Screening Results'

    def __str__(self):
        return f"{self.cv.candidate_name} vs {self.job.title} — {self.overall_score:.0f}%"

    @property
    def match_label(self):
        if self.overall_score >= 80:
            return 'Strong Match'
        elif self.overall_score >= 60:
            return 'Good Match'
        elif self.overall_score >= 40:
            return 'Partial Match'
        return 'Low Match'
