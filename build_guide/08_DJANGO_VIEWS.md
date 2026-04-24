# 08 — Django Web Views (`apps/web/views.py`)

> **Goal:** Write all the Python view functions that render templates, pass context data, and handle form submissions.

---

## File — `apps/web/views.py`

```python
# backend/apps/web/views.py

import calendar
import json
import logging
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from apps.accounts.models import Department, UserProfile, FaceEncoding
from apps.attendance.models import Attendance, ClassSession

logger = logging.getLogger(__name__)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def is_admin(user):
    return user.is_staff or user.is_superuser

def is_teacher(user):
    try:
        return user.profile.role in ['ADMIN', 'TEACHER'] or user.is_staff
    except Exception:
        return user.is_staff

def get_sidebar_context(user):
    """Returns context needed by the sidebar (role, unread counts, etc.)"""
    try:
        role = user.profile.role
    except Exception:
        role = 'ADMIN' if user.is_staff else 'STUDENT'
    return {'user_role': role}


# ─── Auth Views ───────────────────────────────────────────────────────────────

class LoginPageView(View):
    """GET /login/  →  POST /login/"""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'accounts/login.html')

    def post(self, request):
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'accounts/login.html')

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'accounts/login.html')

        if not user.is_active:
            messages.error(request, 'Your account is disabled. Contact the administrator.')
            return render(request, 'accounts/login.html')

        login(request, user)

        # Redirect based on role
        try:
            role = user.profile.role
            if role == 'STUDENT':
                return redirect('my-attendance')
        except Exception:
            pass

        return redirect('dashboard')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')


# ─── Dashboard ────────────────────────────────────────────────────────────────

class DashboardView(LoginRequiredMixin, View):
    """GET /  →  Main dashboard with stats"""

    def get(self, request):
        if not is_teacher(request.user):
            return redirect('my-attendance')

        today = date.today()

        # Stats
        total_users = User.objects.filter(is_active=True).count()
        enrolled_users = UserProfile.objects.filter(is_face_enrolled=True).count()

        today_records = Attendance.objects.filter(date=today)
        today_present = today_records.filter(status__in=['PRESENT', 'LATE']).count()
        today_late = today_records.filter(status='LATE').count()
        today_absent = total_users - today_present

        # Enrollment rate
        enrollment_rate = round((enrolled_users / total_users * 100) if total_users else 0, 1)
        attendance_rate = round((today_present / total_users * 100) if total_users else 0, 1)

        # Recent check-ins (last 10)
        recent_checkins = Attendance.objects.filter(
            date=today
        ).select_related('user__profile__department').order_by('-check_in_time')[:10]

        # Last 7 days chart data
        chart_labels = []
        chart_present = []
        chart_absent = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            count_present = Attendance.objects.filter(
                date=d, status__in=['PRESENT', 'LATE']
            ).count()
            chart_labels.append(d.strftime('%a'))
            chart_present.append(count_present)
            chart_absent.append(max(total_users - count_present, 0))

        # Department breakdown
        departments = Department.objects.all()
        dept_stats = []
        for dept in departments:
            dept_users = User.objects.filter(
                profile__department=dept, is_active=True
            ).count()
            dept_present = today_records.filter(
                user__profile__department=dept,
                status__in=['PRESENT', 'LATE']
            ).count()
            if dept_users > 0:
                dept_stats.append({
                    'name': dept.name,
                    'code': dept.code,
                    'total': dept_users,
                    'present': dept_present,
                    'rate': round(dept_present / dept_users * 100, 1)
                })

        context = {
            'total_users': total_users,
            'enrolled_users': enrolled_users,
            'enrollment_rate': enrollment_rate,
            'today_present': today_present,
            'today_late': today_late,
            'today_absent': today_absent,
            'attendance_rate': attendance_rate,
            'recent_checkins': recent_checkins,
            'chart_labels': json.dumps(chart_labels),
            'chart_present': json.dumps(chart_present),
            'chart_absent': json.dumps(chart_absent),
            'dept_stats': dept_stats,
            'today': today,
            **get_sidebar_context(request.user),
        }
        return render(request, 'dashboard/index.html', context)


# ─── Kiosk View ───────────────────────────────────────────────────────────────

class KioskView(View):
    """
    GET /kiosk/
    Fullscreen kiosk page — no login required (runs on dedicated tablet).
    JavaScript handles camera capture and API calls.
    """

    def get(self, request):
        return render(request, 'face_recognition/kiosk.html', {
            'location': request.GET.get('location', 'Main Gate'),
        })


# ─── Enrollment ───────────────────────────────────────────────────────────────

class EnrollmentView(LoginRequiredMixin, View):
    """
    GET  /enroll/  →  Show enrollment page with user list
    """

    def get(self, request):
        if not is_admin(request.user):
            messages.error(request, 'Admin access required.')
            return redirect('dashboard')

        # Users not yet enrolled
        unenrolled = User.objects.filter(
            profile__is_face_enrolled=False, is_active=True
        ).select_related('profile__department').order_by('profile__employee_id')

        enrolled = User.objects.filter(
            profile__is_face_enrolled=True, is_active=True
        ).select_related('profile__department').order_by('profile__employee_id')

        context = {
            'unenrolled_users': unenrolled,
            'enrolled_users': enrolled,
            'unenrolled_count': unenrolled.count(),
            'enrolled_count': enrolled.count(),
            **get_sidebar_context(request.user),
        }
        return render(request, 'face_recognition/enroll.html', context)


# ─── User Management ──────────────────────────────────────────────────────────

class UserListView(LoginRequiredMixin, View):
    """GET /users/"""

    def get(self, request):
        if not is_admin(request.user):
            messages.error(request, 'Admin access required.')
            return redirect('dashboard')

        # Filters
        role = request.GET.get('role', '')
        dept_id = request.GET.get('department', '')
        search = request.GET.get('search', '')
        enrolled = request.GET.get('enrolled', '')

        users = User.objects.select_related('profile__department').filter(is_active=True)

        if role:
            users = users.filter(profile__role=role)
        if dept_id:
            users = users.filter(profile__department_id=dept_id)
        if search:
            users = users.filter(first_name__icontains=search) | \
                    users.filter(last_name__icontains=search) | \
                    users.filter(profile__employee_id__icontains=search)
        if enrolled == 'true':
            users = users.filter(profile__is_face_enrolled=True)
        elif enrolled == 'false':
            users = users.filter(profile__is_face_enrolled=False)

        users = users.order_by('profile__employee_id')

        departments = Department.objects.all()

        context = {
            'users': users,
            'departments': departments,
            'total': users.count(),
            'filters': {
                'role': role,
                'department': dept_id,
                'search': search,
                'enrolled': enrolled,
            },
            **get_sidebar_context(request.user),
        }
        return render(request, 'face_recognition/users.html', context)


class UserCreateView(LoginRequiredMixin, View):
    """GET/POST /users/create/"""

    def get(self, request):
        if not is_admin(request.user):
            return redirect('dashboard')
        departments = Department.objects.all()
        return render(request, 'face_recognition/user_create.html', {
            'departments': departments,
            **get_sidebar_context(request.user),
        })

    def post(self, request):
        if not is_admin(request.user):
            return redirect('dashboard')

        # Pull form data
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        employee_id = request.POST.get('employee_id', '').strip()
        role = request.POST.get('role', 'STUDENT')
        department_id = request.POST.get('department_id')
        phone = request.POST.get('phone', '').strip()

        # Validation
        errors = []
        if not username:
            errors.append('Username is required.')
        if User.objects.filter(username=username).exists():
            errors.append(f"Username '{username}' already exists.")
        if not employee_id:
            errors.append('Employee ID is required.')
        if UserProfile.objects.filter(employee_id=employee_id).exists():
            errors.append(f"Employee ID '{employee_id}' already exists.")
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')

        if errors:
            departments = Department.objects.all()
            for e in errors:
                messages.error(request, e)
            return render(request, 'face_recognition/user_create.html', {
                'departments': departments,
                **get_sidebar_context(request.user),
            })

        # Create user
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
        )

        dept = None
        if department_id:
            try:
                dept = Department.objects.get(pk=department_id)
            except Department.DoesNotExist:
                pass

        UserProfile.objects.create(
            user=user,
            employee_id=employee_id,
            role=role,
            department=dept,
            phone=phone,
        )

        messages.success(request, f"User '{user.get_full_name()}' created successfully.")
        return redirect('users')


# ─── Attendance Records ───────────────────────────────────────────────────────

class AttendanceRecordsView(LoginRequiredMixin, View):
    """GET /attendance/"""

    def get(self, request):
        if not is_teacher(request.user):
            return redirect('my-attendance')

        # Filters
        date_str = request.GET.get('date', str(date.today()))
        dept_id = request.GET.get('department', '')
        status_filter = request.GET.get('status', '')
        user_search = request.GET.get('search', '')

        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            report_date = date.today()

        records = Attendance.objects.filter(date=report_date).select_related(
            'user__profile__department', 'marked_by'
        )

        if dept_id:
            records = records.filter(user__profile__department_id=dept_id)
        if status_filter:
            records = records.filter(status=status_filter)
        if user_search:
            records = records.filter(
                user__first_name__icontains=user_search
            ) | records.filter(
                user__last_name__icontains=user_search
            ) | records.filter(
                user__profile__employee_id__icontains=user_search
            )

        records = records.order_by('user__profile__employee_id')

        # Stats for the day
        total_users = User.objects.filter(is_active=True).count()
        present_count = records.filter(status__in=['PRESENT', 'LATE']).count()
        late_count = records.filter(status='LATE').count()
        absent_count = total_users - present_count

        departments = Department.objects.all()

        context = {
            'records': records,
            'report_date': report_date,
            'total_users': total_users,
            'present_count': present_count,
            'late_count': late_count,
            'absent_count': absent_count,
            'departments': departments,
            'filters': {
                'date': date_str,
                'department': dept_id,
                'status': status_filter,
                'search': user_search,
            },
            **get_sidebar_context(request.user),
        }
        return render(request, 'attendance/records.html', context)


class DailyReportView(LoginRequiredMixin, View):
    """GET /reports/daily/"""

    def get(self, request):
        if not is_teacher(request.user):
            return redirect('my-attendance')

        date_str = request.GET.get('date', str(date.today()))
        dept_id = request.GET.get('department', '')

        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            report_date = date.today()

        users_qs = User.objects.filter(is_active=True).select_related('profile__department')
        if dept_id:
            users_qs = users_qs.filter(profile__department_id=dept_id)

        total_users = users_qs.count()
        records = Attendance.objects.filter(
            date=report_date, user__in=users_qs
        ).select_related('user__profile__department')

        present = records.filter(status='PRESENT').count()
        late = records.filter(status='LATE').count()
        absent = total_users - records.count()
        rate = round(((present + late) / total_users * 100) if total_users else 0, 1)

        departments = Department.objects.all()

        # Hour-by-hour chart
        hour_data = {}
        for record in records.filter(check_in_time__isnull=False):
            hour = record.check_in_time.hour
            hour_data[hour] = hour_data.get(hour, 0) + 1

        hour_labels = [f'{h:02d}:00' for h in range(6, 20)]
        hour_counts = [hour_data.get(h, 0) for h in range(6, 20)]

        context = {
            'report_date': report_date,
            'total_users': total_users,
            'present': present,
            'late': late,
            'absent': absent,
            'attendance_rate': rate,
            'records': records.order_by('user__profile__employee_id'),
            'departments': departments,
            'selected_dept': dept_id,
            'hour_labels': json.dumps(hour_labels),
            'hour_counts': json.dumps(hour_counts),
            **get_sidebar_context(request.user),
        }
        return render(request, 'attendance/daily_report.html', context)


class MonthlyReportView(LoginRequiredMixin, View):
    """GET /reports/monthly/"""

    def get(self, request):
        if not is_teacher(request.user):
            return redirect('my-attendance')

        year = int(request.GET.get('year', date.today().year))
        month = int(request.GET.get('month', date.today().month))
        dept_id = request.GET.get('department', '')

        _, days_in_month = calendar.monthrange(year, month)
        working_days = sum(
            1 for d in range(1, days_in_month + 1)
            if date(year, month, d).weekday() < 5
        )

        users_qs = User.objects.filter(is_active=True).select_related('profile__department')
        if dept_id:
            users_qs = users_qs.filter(profile__department_id=dept_id)

        report_rows = []
        for user in users_qs.order_by('profile__employee_id'):
            records = Attendance.objects.filter(
                user=user, date__year=year, date__month=month
            )
            present = records.filter(status__in=['PRESENT', 'LATE']).count()
            late = records.filter(status='LATE').count()
            absent = max(working_days - present, 0)
            pct = round((present / working_days * 100) if working_days else 0, 1)

            try:
                emp_id = user.profile.employee_id
                dept_name = user.profile.department.name if user.profile.department else '—'
                role = user.profile.role
            except Exception:
                emp_id = '—'
                dept_name = '—'
                role = '—'

            report_rows.append({
                'user': user,
                'employee_id': emp_id,
                'department': dept_name,
                'role': role,
                'present': present,
                'late': late,
                'absent': absent,
                'working_days': working_days,
                'percentage': pct,
            })

        departments = Department.objects.all()
        year_range = list(range(date.today().year - 2, date.today().year + 1))
        month_names = [(i, calendar.month_name[i]) for i in range(1, 13)]

        context = {
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'working_days': working_days,
            'report_rows': report_rows,
            'departments': departments,
            'selected_dept': dept_id,
            'year_range': year_range,
            'month_names': month_names,
            **get_sidebar_context(request.user),
        }
        return render(request, 'attendance/monthly_report.html', context)


class MyAttendanceView(LoginRequiredMixin, View):
    """GET /my-attendance/  — Student's own record"""

    def get(self, request):
        year = int(request.GET.get('year', date.today().year))
        month = int(request.GET.get('month', date.today().month))

        _, days_in_month = calendar.monthrange(year, month)
        working_days = sum(
            1 for d in range(1, days_in_month + 1)
            if date(year, month, d).weekday() < 5
        )

        records = Attendance.objects.filter(
            user=request.user, date__year=year, date__month=month
        ).order_by('date')

        present = records.filter(status__in=['PRESENT', 'LATE']).count()
        late = records.filter(status='LATE').count()
        absent = max(working_days - present, 0)
        pct = round((present / working_days * 100) if working_days else 0, 1)

        # Build calendar grid
        cal = calendar.monthcalendar(year, month)
        attendance_by_date = {r.date.day: r for r in records}

        month_names = [(i, calendar.month_name[i]) for i in range(1, 13)]
        year_range = list(range(date.today().year - 2, date.today().year + 1))

        context = {
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'working_days': working_days,
            'present': present,
            'late': late,
            'absent': absent,
            'attendance_percentage': pct,
            'records': records,
            'calendar': cal,
            'attendance_by_date': attendance_by_date,
            'today': date.today(),
            'month_names': month_names,
            'year_range': year_range,
            **get_sidebar_context(request.user),
        }
        return render(request, 'attendance/my_attendance.html', context)
```

---

## ✅ What These Views Do

- `LoginPageView` — Authenticates user, redirects students to their own page
- `DashboardView` — Stats, recent check-ins, 7-day chart, dept breakdown
- `KioskView` — No login needed, fullscreen camera page
- `EnrollmentView` — Shows enrolled/unenrolled lists for admin
- `UserListView` — Filterable user table with search
- `UserCreateView` — Create new user with profile
- `AttendanceRecordsView` — Day-filtered attendance table
- `DailyReportView` — Daily summary with hourly chart
- `MonthlyReportView` — Per-student monthly breakdown
- `MyAttendanceView` — Student calendar view of own attendance

---

**Next →** `09_BASE_TEMPLATES.md`
