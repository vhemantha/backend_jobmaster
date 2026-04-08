from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.accounts.urls import notification_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/profiles/', include('apps.profiles.urls')),
    path('api/v1/jobs/', include('apps.jobs.urls')),
    path('api/v1/applications/', include('apps.applications.urls')),
    path('api/v1/ai/', include('apps.ai_engine.urls')),
    path('api/v1/notifications/', include((notification_urlpatterns, 'notifications'))),
    path('api/v1/cv-screening/', include('apps.cv_screening.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
