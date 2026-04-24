from django.urls import path
from . import views

urlpatterns = [
    # ── Public ────────────────────────────────────────────
    path('login/',    views.LoginPageView.as_view(),    name='login'),
    path('register/', views.RegisterAdminView.as_view(), name='register'),
    path('logout/',   views.logout_view,                name='logout'),

    # ── Dashboard ──────────────────────────────────────────
    path('', views.DashboardView.as_view(), name='dashboard'),

    # ── Students ───────────────────────────────────────────
    path('students/',             views.StudentListView.as_view(),   name='students'),
    path('students/add/',         views.StudentAddView.as_view(),    name='student-add'),
    path('students/<int:pk>/',    views.StudentDetailView.as_view(), name='student-detail'),

    # ── Attendance ─────────────────────────────────────────
    path('attendance/',           views.AttendanceListView.as_view(),    name='attendance'),
    path('attendance/take/',      views.TakeAttendanceView.as_view(),    name='attendance-take'),
    path('attendance/report/',    views.MonthlyReportView.as_view(),     name='report-monthly'),

    # ── My Attendance (students) ────────────────────────────
    path('my-attendance/', views.MyAttendanceView.as_view(), name='my-attendance'),
]
