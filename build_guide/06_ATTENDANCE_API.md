# 06 — Attendance API

> **Goal:** Build the attendance endpoints — kiosk check-in, classroom bulk mode, and reports.
> **Files to create:** `apps/attendance/serializers.py`, `apps/attendance/views.py`, `apps/attendance/urls.py`

---

## Overview of Endpoints

| Method | URL | Purpose | Auth |
|--------|-----|---------|------|
| POST | `/api/attendance/checkin/` | Kiosk face check-in | ✅ |
| POST | `/api/attendance/checkout/` | Kiosk check-out | ✅ |
| POST | `/api/attendance/classroom/` | Classroom bulk mode | ✅ Teacher |
| GET | `/api/attendance/records/` | List attendance records | ✅ |
| GET | `/api/attendance/records/<id>/` | Single record | ✅ |
| PATCH | `/api/attendance/records/<id>/` | Manual override | ✅ Admin |
| GET | `/api/attendance/report/daily/` | Daily report | ✅ |
| GET | `/api/attendance/report/monthly/` | Monthly summary | ✅ |
| GET | `/api/attendance/report/export/` | Export CSV | ✅ Admin |
| GET | `/api/attendance/stats/` | Dashboard stats | ✅ |

---

## File 1 — `apps/attendance/serializers.py`

```python
# backend/apps/attendance/serializers.py

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
```

---

## File 2 — `apps/attendance/views.py`

```python
# backend/apps/attendance/views.py

import csv
import io
import logging
from datetime import date, datetime, time, timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from django.http import HttpResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser

import numpy as np

from .models import Attendance, ClassSession
from .serializers import (
    AttendanceSerializer, AttendanceUpdateSerializer,
    ClassSessionSerializer
)
from apps.accounts.models import UserProfile, FaceEncoding
from apps.face_recognition_engine.face_engine import face_engine

logger = logging.getLogger(__name__)


# ─── Kiosk Check-in ───────────────────────────────────────────────────────────

class KioskCheckinView(APIView):
    """
    POST /api/attendance/checkin/
    Form data: image (file), location (optional)

    Workflow:
    1. Receive image from kiosk webcam
    2. Detect face → Get embedding
    3. Search FAISS for matching user
    4. Create/update Attendance record
    5. Return recognized user info
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        image_file = request.FILES.get('image')
        location = request.data.get('location', '')

        if not image_file:
            return Response({'error': 'Image is required.'}, status=400)

        image_bytes = image_file.read()

        # Detect single face
        face, error = face_engine.detect_single_face(image_bytes)
        if error:
            return Response({'error': error, 'recognized': False}, status=400)

        # Get embedding and search
        embedding = face_engine.get_embedding(face)
        results = face_engine.search(embedding, top_k=1)

        if not results:
            return Response({
                'recognized': False,
                'error': 'No enrolled users found. Please enroll first.'
            }, status=404)

        user_id, confidence = results[0]

        # Confidence threshold: 70%
        if confidence < 0.70:
            return Response({
                'recognized': False,
                'confidence': round(confidence * 100, 1),
                'error': f'Face not recognized with sufficient confidence ({round(confidence * 100, 1)}%). Try again with better lighting.'
            }, status=400)

        try:
            user = User.objects.select_related('profile__department').get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found in database.'}, status=404)

        today = date.today()
        now_time = datetime.now().time()

        # Determine if late (after 9:15 AM)
        late_cutoff = time(9, 15)
        attendance_status = 'LATE' if now_time > late_cutoff else 'PRESENT'

        # Get or create today's attendance record
        attendance, created = Attendance.objects.get_or_create(
            user=user,
            date=today,
            defaults={
                'check_in_time': now_time,
                'status': attendance_status,
                'attendance_mode': 'KIOSK',
                'confidence_score': round(confidence * 100, 2),
                'location': location,
            }
        )

        if not created:
            # Already checked in today — update check-out time
            attendance.check_out_time = now_time
            attendance.save(update_fields=['check_out_time'])
            action = 'checked_out'
        else:
            action = 'checked_in'

        return Response({
            'recognized': True,
            'action': action,
            'confidence': round(confidence * 100, 1),
            'user': {
                'id': user.id,
                'name': user.get_full_name(),
                'employee_id': user.profile.employee_id if hasattr(user, 'profile') else '',
                'department': user.profile.department.name if hasattr(user, 'profile') and user.profile.department else '',
                'role': user.profile.role if hasattr(user, 'profile') else '',
            },
            'attendance': AttendanceSerializer(attendance).data
        })


# ─── Checkout ─────────────────────────────────────────────────────────────────

class KioskCheckoutView(APIView):
    """
    POST /api/attendance/checkout/
    Body: { "user_id": 5 }
    Manual check-out (for use when kiosk check-out not used).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.data.get('user_id', request.user.id)
        today = date.today()

        try:
            attendance = Attendance.objects.get(user_id=user_id, date=today)
        except Attendance.DoesNotExist:
            return Response({'error': 'No check-in record found for today.'}, status=404)

        attendance.check_out_time = datetime.now().time()
        attendance.save(update_fields=['check_out_time'])

        return Response({
            'success': True,
            'check_out_time': str(attendance.check_out_time),
            'message': f'Checked out successfully.'
        })


# ─── Classroom Bulk Mode ───────────────────────────────────────────────────────

class ClassroomAttendanceView(APIView):
    """
    POST /api/attendance/classroom/
    Form data: image (group photo), location, subject, expected_students (JSON array of user_ids)

    Workflow:
    1. Receive classroom group photo
    2. Detect ALL faces in photo
    3. Match each face against FAISS
    4. Create attendance records for recognized users
    5. Mark absent for unrecognized users (from expected list)
    6. Return session summary
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        image_file = request.FILES.get('image')
        location = request.data.get('location', '')
        subject = request.data.get('subject', '')
        expected_ids_raw = request.data.get('expected_students', '[]')

        if not image_file:
            return Response({'error': 'Classroom photo is required.'}, status=400)

        # Parse expected student list
        import json
        try:
            expected_ids = json.loads(expected_ids_raw) if isinstance(expected_ids_raw, str) else expected_ids_raw
        except json.JSONDecodeError:
            expected_ids = []

        image_bytes = image_file.read()
        today = date.today()
        now_time = datetime.now().time()

        # Run face recognition on classroom photo
        results = face_engine.process_classroom_photo(image_bytes)

        if results.get('error'):
            return Response({'error': results['error']}, status=400)

        # Create ClassSession record
        session = ClassSession.objects.create(
            teacher=request.user,
            date=today,
            start_time=now_time,
            location=location,
            subject=subject,
            total_expected=len(expected_ids),
            total_detected=results['total_detected'],
            total_recognized=len(results['recognized']),
        )

        # Mark PRESENT for recognized students
        present_user_ids = []
        attendance_records = []

        for rec in results['recognized']:
            user_id = rec['user_id']
            confidence = rec['confidence']

            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                continue

            late_cutoff = time(9, 15)
            att_status = 'LATE' if now_time > late_cutoff else 'PRESENT'

            attendance, created = Attendance.objects.get_or_create(
                user=user,
                date=today,
                defaults={
                    'check_in_time': now_time,
                    'status': att_status,
                    'attendance_mode': 'CLASSROOM',
                    'confidence_score': round(confidence * 100, 2),
                    'location': location,
                    'class_session': session,
                    'marked_by': request.user,
                }
            )
            present_user_ids.append(user_id)
            attendance_records.append(attendance)

        # Mark ABSENT for expected students not recognized
        absent_count = 0
        if expected_ids:
            for uid in expected_ids:
                if uid not in present_user_ids:
                    try:
                        user = User.objects.get(pk=uid)
                        Attendance.objects.get_or_create(
                            user=user,
                            date=today,
                            defaults={
                                'status': 'ABSENT',
                                'attendance_mode': 'CLASSROOM',
                                'confidence_score': 0.0,
                                'location': location,
                                'class_session': session,
                                'marked_by': request.user,
                            }
                        )
                        absent_count += 1
                    except User.DoesNotExist:
                        pass

        return Response({
            'success': True,
            'session_id': session.id,
            'summary': {
                'total_expected': len(expected_ids),
                'total_detected': results['total_detected'],
                'total_recognized': len(results['recognized']),
                'total_present': len(present_user_ids),
                'total_absent': absent_count,
                'total_unknown_faces': len(results['unknown']),
                'recognition_rate': session.recognition_rate,
            },
            'recognized_users': [
                {
                    'user_id': r['user_id'],
                    'confidence': round(r['confidence'] * 100, 1),
                    'bbox': r['bbox']
                }
                for r in results['recognized']
            ],
            'unknown_faces': results['unknown'],
        })


# ─── Attendance Records ────────────────────────────────────────────────────────

class AttendanceListView(generics.ListAPIView):
    """
    GET /api/attendance/records/
    Query params: user_id, date, date_from, date_to, status, department_id
    """
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Attendance.objects.select_related(
            'user__profile__department', 'class_session', 'marked_by'
        )

        # Non-admin users can only see their own records
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)
        else:
            user_id = self.request.query_params.get('user_id')
            if user_id:
                qs = qs.filter(user_id=user_id)

        date_str = self.request.query_params.get('date')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        status_filter = self.request.query_params.get('status')
        department = self.request.query_params.get('department_id')

        if date_str:
            try:
                qs = qs.filter(date=date_str)
            except ValueError:
                pass
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        if status_filter:
            qs = qs.filter(status=status_filter.upper())
        if department:
            qs = qs.filter(user__profile__department_id=department)

        return qs.order_by('-date', '-check_in_time')


class AttendanceDetailView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/attendance/records/<id>/  → Get record
    PATCH /api/attendance/records/<id>/  → Manual override (admin/teacher)
    """
    queryset = Attendance.objects.select_related('user__profile__department')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AttendanceUpdateSerializer
        return AttendanceSerializer

    def update(self, request, *args, **kwargs):
        attendance = self.get_object()
        serializer = AttendanceUpdateSerializer(attendance, data=request.data, partial=True)
        if serializer.is_valid():
            attendance = serializer.save()
            # Record who made the override
            attendance.marked_by = request.user
            attendance.attendance_mode = 'MANUAL'
            attendance.save(update_fields=['marked_by', 'attendance_mode'])
            return Response(AttendanceSerializer(attendance).data)
        return Response(serializer.errors, status=400)


# ─── Reports ───────────────────────────────────────────────────────────────────

class DailyReportView(APIView):
    """
    GET /api/attendance/report/daily/?date=2024-12-11&department_id=1
    Returns summary of attendance for a specific day.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_str = request.query_params.get('date', str(date.today()))
        department_id = request.query_params.get('department_id')

        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

        # Get all users in department (or all)
        users_qs = User.objects.filter(is_active=True).select_related('profile')
        if department_id:
            users_qs = users_qs.filter(profile__department_id=department_id)

        total_users = users_qs.count()

        # Get attendance records for this day
        records = Attendance.objects.filter(
            date=report_date,
            user__in=users_qs
        ).select_related('user__profile__department')

        present_count = records.filter(status='PRESENT').count()
        late_count = records.filter(status='LATE').count()
        absent_count = total_users - records.count()

        attendance_pct = round(
            ((present_count + late_count) / total_users * 100) if total_users > 0 else 0,
            1
        )

        return Response({
            'date': date_str,
            'total_users': total_users,
            'present': present_count,
            'late': late_count,
            'absent': absent_count,
            'attendance_percentage': attendance_pct,
            'records': AttendanceSerializer(records, many=True).data
        })


class MonthlyReportView(APIView):
    """
    GET /api/attendance/report/monthly/?year=2024&month=12&department_id=1
    Returns per-student attendance summary for a month.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        year = int(request.query_params.get('year', date.today().year))
        month = int(request.query_params.get('month', date.today().month))
        department_id = request.query_params.get('department_id')

        import calendar
        _, days_in_month = calendar.monthrange(year, month)
        working_days = sum(
            1 for d in range(1, days_in_month + 1)
            if date(year, month, d).weekday() < 5  # Mon-Fri
        )

        users_qs = User.objects.filter(is_active=True).select_related('profile__department')
        if department_id:
            users_qs = users_qs.filter(profile__department_id=department_id)
        if not request.user.is_staff:
            users_qs = users_qs.filter(pk=request.user.pk)

        report = []
        for user in users_qs:
            records = Attendance.objects.filter(
                user=user,
                date__year=year,
                date__month=month
            )
            present = records.filter(status__in=['PRESENT', 'LATE']).count()
            late = records.filter(status='LATE').count()
            absent = working_days - present

            report.append({
                'user_id': user.id,
                'user_name': user.get_full_name(),
                'employee_id': user.profile.employee_id if hasattr(user, 'profile') else '',
                'department': user.profile.department.name if hasattr(user, 'profile') and user.profile.department else '',
                'total_working_days': working_days,
                'present_days': present,
                'absent_days': max(absent, 0),
                'late_days': late,
                'attendance_percentage': round((present / working_days * 100) if working_days > 0 else 0, 1)
            })

        return Response({
            'year': year,
            'month': month,
            'working_days': working_days,
            'report': sorted(report, key=lambda x: x['employee_id'])
        })


class ExportCSVView(APIView):
    """
    GET /api/attendance/report/export/?date_from=2024-12-01&date_to=2024-12-31
    Returns a downloadable CSV file.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        department_id = request.query_params.get('department_id')

        qs = Attendance.objects.select_related('user__profile__department').all()

        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        if department_id:
            qs = qs.filter(user__profile__department_id=department_id)

        qs = qs.order_by('date', 'user__profile__employee_id')

        # Build CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Date', 'Employee ID', 'Name', 'Department',
            'Check-in', 'Check-out', 'Status', 'Mode', 'Confidence %'
        ])

        for record in qs:
            profile = getattr(record.user, 'profile', None)
            writer.writerow([
                record.date,
                profile.employee_id if profile else '',
                record.user.get_full_name(),
                profile.department.name if profile and profile.department else '',
                record.check_in_time or '',
                record.check_out_time or '',
                record.status,
                record.attendance_mode,
                round(record.confidence_score, 1),
            ])

        output.seek(0)
        filename = f"attendance_{date_from or 'all'}_{date_to or 'all'}.csv"
        response = HttpResponse(output, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class DashboardStatsView(APIView):
    """
    GET /api/attendance/stats/
    Returns quick summary stats for the dashboard.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = date.today()

        total_users = User.objects.filter(is_active=True).count()
        enrolled_users = UserProfile.objects.filter(is_face_enrolled=True).count()

        today_records = Attendance.objects.filter(date=today)
        today_present = today_records.filter(status__in=['PRESENT', 'LATE']).count()
        today_late = today_records.filter(status='LATE').count()

        # Last 7 days average
        seven_days_ago = today - timedelta(days=7)
        weekly_records = Attendance.objects.filter(
            date__gte=seven_days_ago,
            status__in=['PRESENT', 'LATE']
        ).count()
        avg_daily = round(weekly_records / 7, 1)

        return Response({
            'today': str(today),
            'total_users': total_users,
            'enrolled_users': enrolled_users,
            'enrollment_rate': round((enrolled_users / total_users * 100) if total_users > 0 else 0, 1),
            'today_present': today_present,
            'today_late': today_late,
            'today_absent': total_users - today_present,
            'today_attendance_rate': round((today_present / total_users * 100) if total_users > 0 else 0, 1),
            'weekly_avg_daily_attendance': avg_daily,
        })
```

---

## File 3 — `apps/attendance/urls.py`

```python
# backend/apps/attendance/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Attendance capture
    path('checkin/', views.KioskCheckinView.as_view(), name='checkin'),
    path('checkout/', views.KioskCheckoutView.as_view(), name='checkout'),
    path('classroom/', views.ClassroomAttendanceView.as_view(), name='classroom'),

    # Records
    path('records/', views.AttendanceListView.as_view(), name='attendance-list'),
    path('records/<int:pk>/', views.AttendanceDetailView.as_view(), name='attendance-detail'),

    # Reports
    path('report/daily/', views.DailyReportView.as_view(), name='report-daily'),
    path('report/monthly/', views.MonthlyReportView.as_view(), name='report-monthly'),
    path('report/export/', views.ExportCSVView.as_view(), name='report-export'),

    # Dashboard
    path('stats/', views.DashboardStatsView.as_view(), name='stats'),
]
```

---

## Step — Test the Attendance API

### Kiosk Check-in (with image)
```bash
curl -X POST http://localhost:8000/api/attendance/checkin/ \
  -H "Authorization: Bearer <token>" \
  -F "image=@/path/to/face_photo.jpg" \
  -F "location=Main Gate"
```

### Get today's attendance stats
```bash
curl http://localhost:8000/api/attendance/stats/ \
  -H "Authorization: Bearer <token>"
```

### Daily report
```bash
curl "http://localhost:8000/api/attendance/report/daily/?date=2024-12-11" \
  -H "Authorization: Bearer <token>"
```

### Monthly report
```bash
curl "http://localhost:8000/api/attendance/report/monthly/?year=2024&month=12" \
  -H "Authorization: Bearer <token>"
```

### Export CSV
```bash
curl "http://localhost:8000/api/attendance/report/export/?date_from=2024-12-01&date_to=2024-12-31" \
  -H "Authorization: Bearer <token>" \
  -o attendance_report.csv
```

---

## Step — Manual Attendance Override

To manually correct an attendance record:

```bash
curl -X PATCH http://localhost:8000/api/attendance/records/15/ \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "PRESENT", "notes": "Student was present but camera had issues."}'
```

---

**Next →** `07_REACT_FRONTEND.md`
