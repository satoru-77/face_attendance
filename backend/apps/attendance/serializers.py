from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Attendance, ClassSession
from apps.accounts.serializers import UserSerializer


class AttendanceSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    employee_id = serializers.CharField(source='user.profile.employee_id', read_only=True)
    department = serializers.CharField(source='user.profile.department.name', read_only=True)
    marked_by_name = serializers.CharField(source='marked_by.get_full_name', read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id', 'user', 'user_name', 'employee_id', 'department',
            'date', 'check_in_time', 'check_out_time',
            'status', 'attendance_mode', 'confidence_score',
            'location', 'class_session',
            'marked_by', 'marked_by_name', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AttendanceUpdateSerializer(serializers.ModelSerializer):
    """For manual override by admin/teacher."""
    class Meta:
        model = Attendance
        fields = ['status', 'check_in_time', 'check_out_time', 'notes']


class ClassSessionSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    recognition_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = ClassSession
        fields = [
            'id', 'teacher', 'teacher_name',
            'date', 'start_time', 'location', 'subject',
            'total_expected', 'total_detected', 'total_recognized',
            'recognition_rate', 'created_at'
        ]
        read_only_fields = [
            'total_detected', 'total_recognized',
            'recognition_rate', 'created_at'
        ]


class DailyReportSerializer(serializers.Serializer):
    """For daily attendance summary."""
    date = serializers.DateField()
    total_users = serializers.IntegerField()
    present = serializers.IntegerField()
    absent = serializers.IntegerField()
    late = serializers.IntegerField()
    attendance_percentage = serializers.FloatField()
    records = AttendanceSerializer(many=True)


class MonthlyReportSerializer(serializers.Serializer):
    """For monthly summary per user."""
    user_id = serializers.IntegerField()
    user_name = serializers.CharField()
    employee_id = serializers.CharField()
    department = serializers.CharField()
    total_working_days = serializers.IntegerField()
    present_days = serializers.IntegerField()
    absent_days = serializers.IntegerField()
    late_days = serializers.IntegerField()
    attendance_percentage = serializers.FloatField()
