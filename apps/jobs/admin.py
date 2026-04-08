from django.contrib import admin
from .models import Job, JobCategory


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'employer', 'status', 'job_type', 'work_mode', 'experience_level', 'created_at')
    list_filter = ('status', 'job_type', 'work_mode', 'experience_level')
    search_fields = ('title', 'employer__company_name')
    readonly_fields = ('slug', 'views_count', 'created_at', 'updated_at')
