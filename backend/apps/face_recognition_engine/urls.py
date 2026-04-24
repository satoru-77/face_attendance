from django.urls import path
from . import views

urlpatterns = [
    path('enroll/start/', views.EnrollmentStartView.as_view(), name='enroll-start'),
    path('enroll/photo/', views.EnrollmentPhotoView.as_view(), name='enroll-photo'),
    path('enroll/complete/', views.EnrollmentCompleteView.as_view(), name='enroll-complete'),
    path('status/<int:user_id>/', views.EnrollmentStatusView.as_view(), name='enroll-status'),
]
