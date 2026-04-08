import django_filters
from .models import Job


class JobFilter(django_filters.FilterSet):
    salary_min = django_filters.NumberFilter(field_name='salary_min', lookup_expr='gte')
    salary_max = django_filters.NumberFilter(field_name='salary_max', lookup_expr='lte')
    location = django_filters.CharFilter(field_name='location', lookup_expr='icontains')

    class Meta:
        model = Job
        fields = ['category', 'job_type', 'work_mode', 'experience_level', 'status']
