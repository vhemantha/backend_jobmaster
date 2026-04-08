from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.register, name='auth-register'),
    path('login/', views.login, name='auth-login'),
    path('logout/', views.logout, name='auth-logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('me/', views.me, name='auth-me'),
]

notification_urlpatterns = [
    path('', views.notifications_list, name='notifications-list'),
    path('unread-count/', views.notifications_unread_count, name='notifications-unread-count'),
    path('read-all/', views.notifications_read_all, name='notifications-read-all'),
    path('<int:pk>/read/', views.notification_mark_read, name='notification-mark-read'),
]
