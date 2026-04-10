import logging
from django.contrib import admin
from django.utils.html import format_html
from .models import UploadedCV, CVScreeningResult
from .services.gemini_screener import extract_pdf_text, screen_cv_against_job

logger = logging.getLogger(__name__)


# ── Actions ──────────────────────────────────────────────────────────────────

@admin.action(description='Extract / re-extract text from PDF')
def extract_text_action(modeladmin, request, queryset):
    updated = 0
    for cv in queryset:
        if cv.cv_file:
            text = extract_pdf_text(cv.cv_file)
            UploadedCV.objects.filter(pk=cv.pk).update(cv_text=text)
            updated += 1
    modeladmin.message_user(request, f'Extracted text for {updated} CV(s).')


@admin.action(description='Re-screen selected results with Gemini AI')
def rescreen_action(modeladmin, request, queryset):
    success, failed = 0, 0
    for result in queryset:
        try:
            cv = result.cv
            if not cv.cv_text and cv.cv_file:
                cv.cv_text = extract_pdf_text(cv.cv_file)
                UploadedCV.objects.filter(pk=cv.pk).update(cv_text=cv.cv_text)
            data = screen_cv_against_job(cv.cv_text, result.job)
            CVScreeningResult.objects.filter(pk=result.pk).update(
                overall_score=data.get('overall_score', 0),
                score_breakdown=data.get('breakdown', {}),
                strengths=data.get('strengths', []),
                weaknesses=data.get('weaknesses', []),
                recommendation=data.get('recommendation', ''),
                summary=data.get('summary', ''),
            )
            success += 1
        except Exception as e:
            logger.error(f'Re-screen failed for result {result.pk}: {e}')
            failed += 1
    msg = f'Re-screened {success} result(s).'
    if failed:
        msg += f' {failed} failed — check server logs.'
    modeladmin.message_user(request, msg)


# ── UploadedCV Admin ──────────────────────────────────────────────────────────

@admin.register(UploadedCV)
class UploadedCVAdmin(admin.ModelAdmin):
    list_display = [
        'candidate_name', 'candidate_email', 'category',
        'text_status', 'screening_count', 'uploaded_at', 'uploaded_by',
    ]
    list_filter = ['category', 'uploaded_at']
    search_fields = ['candidate_name', 'candidate_email']
    readonly_fields = ['cv_text', 'uploaded_at', 'uploaded_by']
    actions = [extract_text_action]
    fieldsets = (
        ('Candidate Info', {'fields': ('candidate_name', 'candidate_email', 'phone', 'category')}),
        ('CV File', {'fields': ('cv_file', 'cv_text')}),
        ('Admin Notes', {'fields': ('notes',)}),
        ('Meta', {'fields': ('uploaded_at', 'uploaded_by'), 'classes': ('collapse',)}),
    )

    def text_status(self, obj):
        if obj.cv_text:
            return format_html('<span style="color:green;">✓ Extracted ({} chars)</span>', len(obj.cv_text))
        return format_html('<span style="color:orange;">⚠ Not extracted</span>')
    text_status.short_description = 'Text'

    def screening_count(self, obj):
        return obj.screening_results.count()
    screening_count.short_description = '# Screenings'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
        if obj.cv_file and not obj.cv_text:
            text = extract_pdf_text(obj.cv_file)
            UploadedCV.objects.filter(pk=obj.pk).update(cv_text=text)
            obj.cv_text = text


# ── CVScreeningResult Admin ───────────────────────────────────────────────────

@admin.register(CVScreeningResult)
class CVScreeningResultAdmin(admin.ModelAdmin):
    list_display = [
        'cv', 'job', 'score_bar', 'match_label_display',
        'recommendation_short', 'screened_at',
    ]
    list_filter = ['job', 'screened_at']
    search_fields = ['cv__candidate_name', 'job__title']
    readonly_fields = [
        'score_breakdown_pretty', 'strengths', 'weaknesses',
        'screened_at', 'gemini_model_used',
    ]
    actions = [rescreen_action]
    fieldsets = (
        ('Match', {'fields': ('cv', 'job', 'overall_score')}),
        ('Gemini Output', {'fields': (
            'score_breakdown_pretty', 'strengths', 'weaknesses',
            'recommendation', 'summary',
        )}),
        ('Meta', {'fields': ('screened_at', 'gemini_model_used'), 'classes': ('collapse',)}),
    )

    def score_bar(self, obj):
        s = obj.overall_score
        color = '#8ED9C1' if s >= 80 else ('#FFEB5B' if s >= 60 else ('#DB7BB1' if s >= 40 else '#FF6B6B'))
        return format_html(
            '<div style="background:#eee;border-radius:4px;width:130px;height:20px;">'
            '<div style="background:{};width:{}%;height:100%;border-radius:4px;'
            'text-align:center;font-size:11px;line-height:20px;font-weight:bold;">{:.0f}%</div>'
            '</div>',
            color, min(s, 100), s,
        )
    score_bar.short_description = 'Score'

    def match_label_display(self, obj):
        labels = {
            'Strong Match': '#8ED9C1',
            'Good Match': '#FFEB5B',
            'Partial Match': '#DB7BB1',
            'Low Match': '#FF6B6B',
        }
        label = obj.match_label
        color = labels.get(label, '#ccc')
        return format_html(
            '<span style="background:{};padding:2px 8px;border-radius:4px;font-size:11px;">{}</span>',
            color, label,
        )
    match_label_display.short_description = 'Label'

    def recommendation_short(self, obj):
        r = obj.recommendation
        return r[:70] + '…' if len(r) > 70 else r
    recommendation_short.short_description = 'Recommendation'

    def score_breakdown_pretty(self, obj):
        import json
        return format_html(
            '<pre style="font-size:12px;max-height:400px;overflow:auto;">{}</pre>',
            json.dumps(obj.score_breakdown, indent=2),
        )
    score_breakdown_pretty.short_description = 'Score Breakdown (JSON)'
