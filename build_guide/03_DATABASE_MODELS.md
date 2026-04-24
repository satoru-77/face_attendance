# 03 — Database Models (Complete Code)

> **Goal:** Define all database tables as Django models. Copy each file exactly.

---

## File 1 — `apps/accounts/models.py`

```python
# backend/apps/accounts/models.py

from django.db import models
from django.contrib.auth.models import User


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    head = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='headed_department'
    )
    building = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.code} — {self.name}"


class UserProfile(models.Model):

    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('TEACHER', 'Teacher'),
        ('STUDENT', 'Student'),
        ('STAFF', 'Staff'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='members'
    )
    employee_id = models.CharField(max_length=50, unique=True)   # e.g. CS2024001
    phone = models.CharField(max_length=15, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')

    # Face enrollment
    is_face_enrolled = models.BooleanField(default=False)
    enrollment_date = models.DateTimeField(null=True, blank=True)

    # Profile photo (thumbnail, not used for recognition)
    profile_photo = models.ImageField(
        upload_to='profile_photos/', null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['employee_id']

    def __str__(self):
        return f"{self.employee_id} — {self.user.get_full_name()}"

    @property
    def full_name(self):
        return self.user.get_full_name()


class FaceEncoding(models.Model):
    """
    Stores the 512-dimensional face embedding for each enrolled photo.
    Each student has up to 10 encodings (one per enrollment photo).
    Also stores a final averaged embedding.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='face_encodings')
    
    # The 512-D embedding vector stored as JSON array
    embedding = models.JSONField()

    # Which photo number in enrollment sequence (1-10), 0 = averaged
    photo_number = models.IntegerField(default=0)

    # Quality score from InsightFace (0-1, higher is better)
    quality_score = models.FloatField(default=0.0)

    # Is this the final averaged embedding used for matching?
    is_primary = models.BooleanField(default=False)

    # Path to the original enrollment photo (auto-deleted after 30 days)
    photo_path = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['user', 'photo_number']

    def __str__(self):
        label = "Primary" if self.is_primary else f"Photo {self.photo_number}"
        return f"{self.user.username} — {label}"
```

---

## File 2 — `apps/attendance/models.py`

```python
# backend/apps/attendance/models.py

from django.db import models
from django.contrib.auth.models import User


class Attendance(models.Model):

    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
        ('HALF_DAY', 'Half Day'),
    ]

    MODE_CHOICES = [
        ('KIOSK', 'Kiosk (Individual)'),
        ('CLASSROOM', 'Classroom (Bulk)'),
        ('MANUAL', 'Manual Override'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()

    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PRESENT')
    attendance_mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='KIOSK')

    # Face recognition confidence (0-100%)
    confidence_score = models.FloatField(default=0.0)

    # Capture info
    location = models.CharField(max_length=100, blank=True)

    # Check-in photo path (auto-deleted after 30 days)
    checkin_photo = models.ImageField(upload_to='checkin_photos/%Y/%m/', null=True, blank=True)

    # For classroom mode: which session created this
    class_session = models.ForeignKey(
        'ClassSession', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='attendances'
    )

    # Manual override info
    marked_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='marked_attendances'
    )
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # One record per user per day
        unique_together = ['user', 'date']
        ordering = ['-date', '-check_in_time']

    def __str__(self):
        return f"{self.user.username} — {self.date} — {self.status}"


class ClassSession(models.Model):
    """
    Represents a classroom bulk attendance capture event.
    One ClassSession creates many Attendance records.
    """
    # Who triggered this (teacher)
    teacher = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='class_sessions'
    )

    date = models.DateField()
    start_time = models.TimeField()

    # Room/location info
    location = models.CharField(max_length=100, blank=True)
    subject = models.CharField(max_length=100, blank=True)

    # Stats
    total_expected = models.IntegerField(default=0)
    total_detected = models.IntegerField(default=0)
    total_recognized = models.IntegerField(default=0)

    # The classroom photo used for this session
    classroom_photo = models.ImageField(
        upload_to='classroom_photos/%Y/%m/', null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f"Session — {self.date} {self.start_time} ({self.location})"

    @property
    def recognition_rate(self):
        if self.total_detected == 0:
            return 0
        return round((self.total_recognized / self.total_detected) * 100, 1)
```

---

## File 3 — Register models in admin

### `apps/accounts/admin.py`

```python
# backend/apps/accounts/admin.py

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
```

### `apps/attendance/admin.py`

```python
# backend/apps/attendance/admin.py

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
```

---

## Step — Create apps/__init__.py files

Each app's directory needs `__init__.py`. When you run `startapp`, Django creates these automatically. But for the `apps/` folder itself, create:

```bash
# From backend/ directory:
touch apps/__init__.py
```

Also, update the `apps.py` file in each app. For example, `apps/accounts/apps.py`:

```python
# backend/apps/accounts/apps.py
from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
```

Do the same for `apps/attendance/apps.py`:
```python
from django.apps import AppConfig

class AttendanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.attendance'
```

And `apps/face_recognition_engine/apps.py`:
```python
from django.apps import AppConfig

class FaceRecognitionEngineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.face_recognition_engine'
```

---

## Step — Run Migrations

```bash
# From backend/ with venv activated:
python manage.py makemigrations accounts
python manage.py makemigrations attendance
python manage.py makemigrations face_recognition_engine
python manage.py migrate
```

Expected output:
```
Applying accounts.0001_initial... OK
Applying attendance.0001_initial... OK
Running deferred SQL... OK
```

---

## Step — Add sample data (optional)

Create `backend/seed_data.py` for testing:

```python
# backend/seed_data.py
# Run with: python seed_data.py (from backend/ with venv active)

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'face_attendance.settings')
django.setup()

from django.contrib.auth.models import User
from apps.accounts.models import Department, UserProfile

# Create departments
cs = Department.objects.get_or_create(name='Computer Science', code='CS', building='Block A')[0]
ec = Department.objects.get_or_create(name='Electronics', code='EC', building='Block B')[0]

print(f"Created departments: {cs}, {ec}")

# Create a test teacher
user, created = User.objects.get_or_create(
    username='teacher001',
    defaults={
        'first_name': 'Rajesh',
        'last_name': 'Kumar',
        'email': 'rajesh@college.edu',
    }
)
if created:
    user.set_password('teacher123')
    user.save()
    UserProfile.objects.create(
        user=user,
        department=cs,
        employee_id='T001',
        role='TEACHER',
        phone='9876543210'
    )
    print("Created teacher: teacher001 / teacher123")

# Create a test student
student, created = User.objects.get_or_create(
    username='CS2024001',
    defaults={
        'first_name': 'Priya',
        'last_name': 'Sharma',
        'email': 'priya@college.edu',
    }
)
if created:
    student.set_password('student123')
    student.save()
    UserProfile.objects.create(
        user=student,
        department=cs,
        employee_id='CS2024001',
        role='STUDENT',
    )
    print("Created student: CS2024001 / student123")

print("Seed data complete!")
```

Run with:
```bash
python seed_data.py
```

---

**Next →** `04_FACE_RECOGNITION_ENGINE.md`
