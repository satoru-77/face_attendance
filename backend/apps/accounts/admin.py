from django.contrib import admin
from .models import Department, UserProfile, FaceEncoding


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'building', 'head']
    search_fields = ['name', 'code']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'full_name', 'role', 'department', 'is_face_enrolled']
    list_filter = ['role', 'department', 'is_face_enrolled']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name', 'user__email']


@admin.register(FaceEncoding)
class FaceEncodingAdmin(admin.ModelAdmin):
    list_display = ['user', 'photo_number', 'quality_score', 'is_primary', 'created_at']
    list_filter = ['is_primary']
