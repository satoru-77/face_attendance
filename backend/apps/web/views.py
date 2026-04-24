import calendar
import json
import logging
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View

from apps.accounts.models import Department, UserProfile, FaceEncoding
from apps.attendance.models import Attendance

logger = logging.getLogger(__name__)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_admin_department(user):
    """Return the Department this admin manages, or None."""
    try:
        return user.profile.department
    except Exception:
        return None

def dept_context(user):
    dept = get_admin_department(user)
    return {
        'my_department': dept,
        'user_role': user.profile.role if hasattr(user, 'profile') else 'ADMIN',
    }


# ─── Login ────────────────────────────────────────────────────────────────────

class LoginPageView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'accounts/login.html')

    def post(self, request):
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, 'Invalid credentials. Please try again.')
            return render(request, 'accounts/login.html')
        if not user.is_active:
            messages.error(request, 'Your account is inactive. Contact support.')
            return render(request, 'accounts/login.html')

        login(request, user)

        try:
            if user.profile.role == 'STUDENT':
                return redirect('my-attendance')
        except Exception:
            pass
        return redirect('dashboard')


def logout_view(request):
    logout(request)
    return redirect('login')


# ─── Department Admin Self-Registration ───────────────────────────────────────

class RegisterAdminView(View):
    """
    GET  /register/ → Show registration form
    POST /register/ → Create dept admin account
    """
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        departments = Department.objects.all()
        return render(request, 'accounts/register.html', {'departments': departments})

    def post(self, request):
        first_name  = request.POST.get('first_name', '').strip()
        last_name   = request.POST.get('last_name', '').strip()
        username    = request.POST.get('username', '').strip()
        email       = request.POST.get('email', '').strip()
        password    = request.POST.get('password', '')
        password2   = request.POST.get('password2', '')
        dept_id     = request.POST.get('department_id')
        employee_id = request.POST.get('employee_id', '').strip()

        departments = Department.objects.all()
        errors = []

        if not username:            errors.append('Username is required.')
        if User.objects.filter(username=username).exists():
            errors.append(f"Username '{username}' is already taken.")
        if not employee_id:         errors.append('Employee ID is required.')
        if UserProfile.objects.filter(employee_id=employee_id).exists():
            errors.append(f"Employee ID '{employee_id}' already exists.")
        if len(password) < 8:       errors.append('Password must be at least 8 characters.')
        if password != password2:   errors.append('Passwords do not match.')
        if not dept_id:             errors.append('Please select your department.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'accounts/register.html', {'departments': departments})

        dept = get_object_or_404(Department, pk=dept_id)

        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            is_staff=True,          # dept admins get staff access
        )
        UserProfile.objects.create(
            user=user,
            employee_id=employee_id,
            role='ADMIN',
            department=dept,
        )

        messages.success(request, f'Account created! Welcome, {first_name}. Please sign in.')
        return redirect('login')


# ─── Dashboard ────────────────────────────────────────────────────────────────

class DashboardView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request):
        try:
            role = request.user.profile.role
            if role == 'STUDENT':
                return redirect('my-attendance')
        except Exception:
            pass

        dept = get_admin_department(request.user)
        today = date.today()

        # Students in this department
        students_qs = User.objects.filter(
            profile__role='STUDENT',
            is_active=True,
            **(({'profile__department': dept}) if dept else {})
        ).select_related('profile__department')

        total_students  = students_qs.count()
        enrolled_count  = students_qs.filter(profile__is_face_enrolled=True).count()

        today_records = Attendance.objects.filter(
            date=today,
            user__in=students_qs
        )
        present_today = today_records.filter(status__in=['PRESENT', 'LATE']).count()
        absent_today  = total_students - present_today

        # Last 7 days chart
        chart_labels, chart_present, chart_absent = [], [], []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            p = Attendance.objects.filter(
                date=d, user__in=students_qs, status__in=['PRESENT', 'LATE']
            ).count()
            chart_labels.append(d.strftime('%a %d'))
            chart_present.append(p)
            chart_absent.append(max(total_students - p, 0))

        # Recent check-ins
        recent = today_records.select_related(
            'user__profile__department'
        ).order_by('-check_in_time')[:8]

        ctx = {
            'total_students': total_students,
            'enrolled_count': enrolled_count,
            'unenrolled_count': total_students - enrolled_count,
            'present_today': present_today,
            'absent_today': absent_today,
            'attendance_rate': round((present_today / total_students * 100) if total_students else 0, 1),
            'enrollment_rate': round((enrolled_count / total_students * 100) if total_students else 0, 1),
            'recent_checkins': recent,
            'chart_labels':  json.dumps(chart_labels),
            'chart_present': json.dumps(chart_present),
            'chart_absent':  json.dumps(chart_absent),
            'today': today,
            **dept_context(request.user),
        }
        return render(request, 'dashboard/index.html', ctx)


# ─── Student List ──────────────────────────────────────────────────────────────

class StudentListView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request):
        dept = get_admin_department(request.user)
        search = request.GET.get('q', '')
        enrolled_filter = request.GET.get('enrolled', '')

        qs = User.objects.filter(
            profile__role='STUDENT', is_active=True,
            **(({'profile__department': dept}) if dept else {})
        ).select_related('profile__department').order_by('profile__employee_id')

        if search:
            qs = qs.filter(first_name__icontains=search) | \
                 qs.filter(last_name__icontains=search) | \
                 qs.filter(profile__employee_id__icontains=search)
        if enrolled_filter == 'yes':
            qs = qs.filter(profile__is_face_enrolled=True)
        elif enrolled_filter == 'no':
            qs = qs.filter(profile__is_face_enrolled=False)

        ctx = {
            'students': qs,
            'total': qs.count(),
            'search': search,
            'enrolled_filter': enrolled_filter,
            **dept_context(request.user),
        }
        return render(request, 'students/list.html', ctx)


# ─── Add Student (Registration + Face Capture in one flow) ────────────────────

class StudentAddView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request):
        dept = get_admin_department(request.user)
        pose_list = [
            'Look straight — neutral face',
            'Smile naturally',
            'Turn head slightly left',
            'Turn head slightly right',
            'Tilt head slightly up',
            'Tilt head slightly down',
            'Serious expression, straight',
            'Turn head left ~30°',
            'Turn head right ~30°',
            'Final photo — straight',
        ]
        return render(request, 'students/add.html', {
            'department': dept,
            'pose_list': pose_list,
            **dept_context(request.user),
        })

    def post(self, request):
        """Step 1: Create student account. Face photos captured via API calls from JS."""
        dept = get_admin_department(request.user)

        first_name  = request.POST.get('first_name', '').strip()
        last_name   = request.POST.get('last_name', '').strip()
        username    = request.POST.get('username', '').strip()
        email       = request.POST.get('email', '').strip()
        password    = request.POST.get('password', 'Student@123')
        employee_id = request.POST.get('employee_id', '').strip()
        phone       = request.POST.get('phone', '').strip()

        errors = []
        if User.objects.filter(username=username).exists():
            errors.append(f"Username '{username}' already taken.")
        if UserProfile.objects.filter(employee_id=employee_id).exists():
            errors.append(f"Employee ID '{employee_id}' already exists.")

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'students/add.html', {
                'department': dept, **dept_context(request.user)
            })

        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
        )
        UserProfile.objects.create(
            user=user,
            employee_id=employee_id,
            role='STUDENT',
            department=dept,
            phone=phone,
        )

        messages.success(request, f"Student '{first_name} {last_name}' registered. Now capture face photos.")
        # Redirect to the face capture page for this newly created student
        return redirect(f'/students/{user.pk}/?enroll=1')


class StudentDetailView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, pk):
        student = get_object_or_404(User, pk=pk, profile__role='STUDENT')
        enroll = request.GET.get('enroll', '0')
        today = date.today()

        recent_att = Attendance.objects.filter(user=student).order_by('-date')[:10]

        ctx = {
            'student': student,
            'enroll_mode': enroll == '1',
            'recent_attendance': recent_att,
            **dept_context(request.user),
        }
        return render(request, 'students/detail.html', ctx)


# ─── Take Classroom Attendance ────────────────────────────────────────────────

class TakeAttendanceView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request):
        dept = get_admin_department(request.user)
        ctx = {
            'department': dept,
            **dept_context(request.user),
        }
        return render(request, 'attendance/take.html', ctx)


# ─── Attendance List ──────────────────────────────────────────────────────────

class AttendanceListView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request):
        dept = get_admin_department(request.user)
        date_str = request.GET.get('date', str(date.today()))

        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            report_date = date.today()

        students_qs = User.objects.filter(
            profile__role='STUDENT', is_active=True,
            **(({'profile__department': dept}) if dept else {})
        )

        records = Attendance.objects.filter(
            date=report_date, user__in=students_qs
        ).select_related('user__profile__department').order_by('user__profile__employee_id')

        total = students_qs.count()
        present = records.filter(status__in=['PRESENT', 'LATE']).count()

        ctx = {
            'records': records,
            'report_date': report_date,
            'total_students': total,
            'present_count': present,
            'absent_count': total - present,
            'date_str': date_str,
            **dept_context(request.user),
        }
        return render(request, 'attendance/list.html', ctx)


# ─── Monthly Report ───────────────────────────────────────────────────────────

class MonthlyReportView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request):
        dept = get_admin_department(request.user)
        year  = int(request.GET.get('year', date.today().year))
        month = int(request.GET.get('month', date.today().month))

        _, days_in_month = calendar.monthrange(year, month)
        working_days = sum(
            1 for d in range(1, days_in_month + 1)
            if date(year, month, d).weekday() < 5
        )

        students_qs = User.objects.filter(
            profile__role='STUDENT', is_active=True,
            **(({'profile__department': dept}) if dept else {})
        ).select_related('profile')

        rows = []
        for student in students_qs.order_by('profile__employee_id'):
            recs = Attendance.objects.filter(user=student, date__year=year, date__month=month)
            present = recs.filter(status__in=['PRESENT', 'LATE']).count()
            late    = recs.filter(status='LATE').count()
            absent  = max(working_days - present, 0)
            rows.append({
                'student': student,
                'employee_id': student.profile.employee_id,
                'present': present,
                'late': late,
                'absent': absent,
                'working_days': working_days,
                'percentage': round((present / working_days * 100) if working_days else 0, 1),
            })

        month_names = [(i, calendar.month_name[i]) for i in range(1, 13)]
        year_range  = list(range(date.today().year - 1, date.today().year + 1))

        ctx = {
            'rows': rows,
            'year': year, 'month': month,
            'month_name': calendar.month_name[month],
            'working_days': working_days,
            'month_names': month_names,
            'year_range': year_range,
            **dept_context(request.user),
        }
        return render(request, 'attendance/monthly.html', ctx)


# ─── My Attendance (Student) ──────────────────────────────────────────────────

class MyAttendanceView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request):
        year  = int(request.GET.get('year', date.today().year))
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
        cal_grid = calendar.monthcalendar(year, month)
        att_by_day = {r.date.day: r for r in records}

        month_names = [(i, calendar.month_name[i]) for i in range(1, 13)]
        year_range  = list(range(date.today().year - 1, date.today().year + 1))

        ctx = {
            'year': year, 'month': month,
            'month_name': calendar.month_name[month],
            'working_days': working_days,
            'present': present,
            'absent': max(working_days - present, 0),
            'attendance_pct': round((present / working_days * 100) if working_days else 0, 1),
            'records': records,
            'calendar': cal_grid,
            'att_by_day': att_by_day,
            'today': date.today(),
            'month_names': month_names,
            'year_range': year_range,
            **dept_context(request.user),
        }
        return render(request, 'attendance/my_attendance.html', ctx)
