from django.contrib import admin
from .models import Attendance, ClassSession


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'check_in_time', 'status', 'attendance_mode', 'confidence_score']
    list_filter = ['status', 'attendance_mode', 'date']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    date_hierarchy = 'date'


@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = ['date', 'start_time', 'location', 'subject', 'total_recognized', 'total_detected']
    list_filter = ['date']
