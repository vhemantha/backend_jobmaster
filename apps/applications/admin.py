from django.contrib import admin
from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'job', 'status', 'ai_match_score', 'applied_at')
    list_filter = ('status',)
    search_fields = ('candidate__full_name', 'job__title')
    readonly_fields = ('ai_match_score', 'ai_score_breakdown', 'applied_at', 'updated_at')
