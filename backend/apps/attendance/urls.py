from django.urls import path
from . import views

urlpatterns = [
    # Attendance capture
    path('checkin/', views.KioskCheckinView.as_view(), name='checkin'),
    path('classroom/', views.ClassroomAttendanceView.as_view(), name='classroom'),

    # Records
    path('records/', views.AttendanceListView.as_view(), name='attendance-list'),
    path('records/<int:pk>/', views.AttendanceDetailView.as_view(), name='attendance-detail'),

    # Reports
    path('report/daily/', views.DailyReportView.as_view(), name='report-daily'),
    path('report/monthly/', views.MonthlyReportView.as_view(), name='api-report-monthly'),
    path('report/export/', views.ExportCSVView.as_view(), name='report-export'),

    # Dashboard
    path('stats/', views.DashboardStatsView.as_view(), name='stats'),
]
