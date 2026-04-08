from django.urls import path
from . import views

urlpatterns = [
    path('match-score/', views.match_score, name='ai-match-score'),
    path('recommendations/', views.recommendations, name='ai-recommendations'),
    path('job-candidates/<int:job_id>/', views.job_candidate_matches, name='ai-job-candidates'),
]
