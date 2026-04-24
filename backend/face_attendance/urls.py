# backend/face_attendance/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Web UI (template-based)
    path('', include('apps.web.urls')),

    # API routes
    path('api/auth/', include('apps.accounts.urls')),
    path('api/attendance/', include('apps.attendance.urls')),
    path('api/face/', include('apps.face_recognition_engine.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
