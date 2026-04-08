from django.contrib import admin
from .models import CandidateProfile, EmployerProfile


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'location', 'experience_years', 'is_open_to_work')
    search_fields = ('full_name', 'user__email')


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'company_slug', 'industry', 'location')
    search_fields = ('company_name', 'user__email')
    prepopulated_fields = {'company_slug': ('company_name',)}
