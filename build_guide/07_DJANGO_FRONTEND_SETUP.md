# 07 — Django Templates + Tailwind CSS Frontend Setup

> **Goal:** Set up Tailwind CSS with Django templates, configure static files, and create the base layout that all pages inherit from.

---

## Overview

We are building the frontend **entirely in Django templates** (no React, no JavaScript framework). Tailwind CSS handles all styling via CDN for development.

**Pages we will build:**
| Page | URL | Who Sees It |
|------|-----|-------------|
| Login | `/login/` | Everyone |
| Dashboard | `/` | Admin, Teacher |
| Kiosk Check-in | `/kiosk/` | Public kiosk screen |
| Enrollment | `/enroll/` | Admin only |
| User Management | `/users/` | Admin only |
| Attendance Records | `/attendance/` | Admin, Teacher |
| Daily Report | `/reports/daily/` | Admin, Teacher |
| Monthly Report | `/reports/monthly/` | Admin, Teacher |
| My Attendance | `/my-attendance/` | Student |

---

## Step 1 — Create the `web` App

This app holds all Django template views.

```bash
# From backend/ with venv active:
python manage.py startapp web
mv web apps/web
```

Update `apps/web/apps.py`:
```python
from django.apps import AppConfig

class WebConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.web'
```

Add to `INSTALLED_APPS` in `settings.py`:
```python
'apps.web',
'widget_tweaks',
```

---

## Step 2 — Configure Templates and Static in settings.py

Update the `TEMPLATES` section in `settings.py`:

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],   # ← Add this line
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
```

Add at the bottom of `settings.py`:
```python
# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Auth redirects
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'
```

---

## Step 3 — Create Folder Structure

```bash
# From backend/ directory:
mkdir -p templates/base
mkdir -p templates/accounts
mkdir -p templates/dashboard
mkdir -p templates/attendance
mkdir -p templates/face_recognition
mkdir -p static/css
mkdir -p static/js
mkdir -p static/img
```

Final structure:
```
backend/
├── templates/
│   ├── base/
│   │   ├── base.html              ← Main layout (sidebar + topbar)
│   │   └── base_kiosk.html        ← Fullscreen kiosk layout
│   ├── accounts/
│   │   ├── login.html
│   │   └── profile.html
│   ├── dashboard/
│   │   └── index.html
│   ├── attendance/
│   │   ├── records.html
│   │   ├── daily_report.html
│   │   ├── monthly_report.html
│   │   └── my_attendance.html
│   └── face_recognition/
│       ├── kiosk.html
│       ├── enroll.html
│       └── users.html
└── static/
    ├── css/
    │   └── custom.css
    └── js/
        ├── kiosk.js
        └── enroll.js
```

---

## Step 4 — Add URLs for the Web App

Create `apps/web/urls.py`:

```python
# backend/apps/web/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.LoginPageView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Kiosk
    path('kiosk/', views.KioskView.as_view(), name='kiosk'),

    # Enrollment
    path('enroll/', views.EnrollmentView.as_view(), name='enroll'),

    # Users
    path('users/', views.UserListView.as_view(), name='users'),
    path('users/create/', views.UserCreateView.as_view(), name='user-create'),

    # Attendance
    path('attendance/', views.AttendanceRecordsView.as_view(), name='attendance'),
    path('reports/daily/', views.DailyReportView.as_view(), name='report-daily'),
    path('reports/monthly/', views.MonthlyReportView.as_view(), name='report-monthly'),
    path('my-attendance/', views.MyAttendanceView.as_view(), name='my-attendance'),
]
```

Update `face_attendance/urls.py`:

```python
# backend/face_attendance/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Web UI (template-based)
    path('', include('apps.web.urls')),

    # REST API (used by JS fetch in templates)
    path('api/auth/', include('apps.accounts.urls')),
    path('api/attendance/', include('apps.attendance.urls')),
    path('api/face/', include('apps.face_recognition_engine.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## Step 5 — Install django-widget-tweaks

```bash
pip install django-widget-tweaks==1.5.0
```

Add to `requirements.txt`:
```
django-widget-tweaks==1.5.0
```

---

## ✅ Pre-flight Checklist

- [ ] Created `apps/web/` app
- [ ] Updated `TEMPLATES` DIRS in settings.py
- [ ] Added `STATICFILES_DIRS` and `LOGIN_URL`
- [ ] Created all `templates/` subdirectories
- [ ] Created `static/css/` and `static/js/` directories
- [ ] Created `apps/web/urls.py`
- [ ] Updated root `urls.py`
- [ ] Installed `django-widget-tweaks`

---

**Next →** `08_DJANGO_VIEWS.md`
