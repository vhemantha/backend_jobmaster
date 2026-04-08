from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_list, name='job-list'),
    path('featured/', views.job_featured, name='job-featured'),
    path('categories/', views.job_categories, name='job-categories'),
    path('my/', views.my_jobs, name='my-jobs'),
    path('saved/', views.saved_jobs, name='saved-jobs'),
    path('saved/ids/', views.saved_job_ids, name='saved-job-ids'),
    path('saved/<int:job_id>/', views.unsave_job, name='unsave-job'),
    path('analytics/', views.employer_analytics, name='employer-analytics'),
    path('create/', views.job_create, name='job-create'),
    path('<int:pk>/', views.job_detail, name='job-detail'),
    path('<int:pk>/edit/', views.job_edit, name='job-edit'),
]
