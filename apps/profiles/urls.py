from django.urls import path
from . import views

urlpatterns = [
    path('candidate/me/', views.candidate_profile_me, name='candidate-profile-me'),
    path('candidate/<int:pk>/', views.candidate_profile_detail, name='candidate-profile-detail'),
    path('employer/me/', views.employer_profile_me, name='employer-profile-me'),
    path('employer/<slug:slug>/', views.employer_profile_public, name='employer-profile-public'),
]
