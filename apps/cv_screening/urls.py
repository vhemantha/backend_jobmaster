from django.urls import path
from . import views

urlpatterns = [
    # Shared
    path('categories/', views.CVCategoriesView.as_view(), name='cv-categories'),

    # Admin + Employer
    path('cvs/', views.CVUploadView.as_view(), name='cv-list-upload'),
    path('cvs/<int:pk>/', views.CVDetailView.as_view(), name='cv-detail'),
    path('screen/', views.CVScreenView.as_view(), name='cv-screen'),

    # Employer
    path('job/<int:job_id>/results/', views.JobScreeningResultsView.as_view(), name='job-screening-results'),

    # Admin
    path('results/', views.AllScreeningResultsView.as_view(), name='all-screening-results'),

    # Shared (admin + owning employer)
    path('results/<int:pk>/', views.ScreeningResultDetailView.as_view(), name='screening-result-detail'),
]
