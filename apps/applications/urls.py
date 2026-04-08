from django.urls import path
from . import views

urlpatterns = [
    # Candidate
    path('', views.apply, name='apply'),
    path('my/', views.my_applications, name='my-applications'),
    path('my/<int:pk>/', views.my_application_detail, name='my-application-detail'),
    # Employer
    path('job/<int:job_id>/', views.job_applications, name='job-applications'),
    path('job/<int:job_id>/<int:app_id>/', views.job_application_detail, name='job-application-detail'),
    path('job/<int:job_id>/<int:app_id>/status/', views.update_application_status, name='update-app-status'),
    path('job/<int:job_id>/<int:app_id>/notes/', views.update_application_notes, name='update-app-notes'),
]
