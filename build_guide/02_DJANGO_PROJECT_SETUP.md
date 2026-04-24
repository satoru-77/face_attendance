# 02 — Django Project Setup (Virtual Environment + Structure)

> **Goal:** Create the Django project inside a virtual environment with all dependencies installed.

---

## 📁 Final Project Structure

```
face_attendance/                  ← Root project folder
│
├── backend/                      ← Django project lives here
│   ├── venv/                     ← Virtual environment (DO NOT commit)
│   ├── manage.py
│   ├── requirements.txt
│   ├── face_attendance/          ← Django settings package
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── accounts/             ← Users, Auth, Profiles
│   │   ├── attendance/           ← Attendance records
│   │   └── face_recognition/     ← InsightFace + FAISS engine
│   └── media/                    ← Uploaded photos
│
└── frontend/                     ← React project lives here
    ├── public/
    └── src/
```

---

## Step 1 — Create Root Project Folder

```bash
# Navigate to where you want the project
cd Desktop   # or wherever you prefer

mkdir face_attendance
cd face_attendance
mkdir backend frontend
cd backend
```

---

## Step 2 — Create Virtual Environment

```bash
# Inside the backend/ folder:

# Windows
python -m venv venv

# macOS / Linux / WSL2
python3.11 -m venv venv
```

### Activate the virtual environment:

```bash
# Windows (Command Prompt)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# macOS / Linux / WSL2
source venv/bin/activate
```

✅ You should now see `(venv)` at the start of your terminal prompt.

**IMPORTANT:** Always activate the virtual environment before running any Python commands for this project.

---

## Step 3 — Create requirements.txt

Create a file called `requirements.txt` inside `backend/`:

```txt
# requirements.txt

# Django Core
Django==5.0.4
djangorestframework==3.15.1
django-cors-headers==4.3.1
djangorestframework-simplejwt==5.3.1

# Database
psycopg2-binary==2.9.9

# Environment Variables
python-decouple==3.8

# Face Recognition
insightface==0.7.3
onnxruntime==1.18.0

# Note: If you have an NVIDIA GPU, replace onnxruntime with:
# onnxruntime-gpu==1.18.0

# Vector Search
faiss-cpu==1.8.0

# Note: If you have an NVIDIA GPU, replace faiss-cpu with:
# faiss-gpu==1.7.4

# Image Processing
opencv-python==4.9.0.80
Pillow==10.3.0
numpy==1.26.4

# Utilities
python-dateutil==2.9.0
```

---

## Step 4 — Install All Dependencies

With your venv activated:

```bash
pip install -r requirements.txt
```

⚠️ This will take **5-15 minutes** depending on your internet speed. The InsightFace and FAISS packages are large.

If you get an error on **insightface** on Windows, try:
```bash
pip install cmake
pip install insightface==0.7.3
```

If you get an error on **faiss-cpu**, try:
```bash
pip install faiss-cpu --no-binary :all:
```

---

## Step 5 — Create the Django Project

```bash
# Still inside backend/ with venv activated:
django-admin startproject face_attendance .
```

This creates `manage.py` and `face_attendance/` folder at the current level.

---

## Step 6 — Create Django Apps

```bash
mkdir apps
cd apps
touch __init__.py

python ../manage.py startapp accounts
python ../manage.py startapp attendance  
python ../manage.py startapp face_recognition_engine

# Move them into apps/ folder manually or use:
cd ..
python manage.py startapp accounts apps/accounts
python manage.py startapp attendance apps/attendance
python manage.py startapp face_recognition_engine apps/face_recognition_engine
```

**Simpler approach — run from backend/ folder:**
```bash
# From backend/ directory:
mkdir -p apps
python manage.py startapp accounts
python manage.py startapp attendance
python manage.py startapp face_recognition_engine
mv accounts apps/
mv attendance apps/
mv face_recognition_engine apps/
```

---

## Step 7 — Create PostgreSQL Database

Open a terminal (not your venv one) and run:

```bash
# Connect to PostgreSQL
psql -U postgres

# Inside psql shell:
CREATE DATABASE face_attendance_db;
CREATE USER face_admin WITH PASSWORD 'yourpassword123';
GRANT ALL PRIVILEGES ON DATABASE face_attendance_db TO face_admin;
\q
```

---

## Step 8 — Create .env File

Create a file called `.env` inside `backend/`:

```env
# backend/.env

SECRET_KEY=django-insecure-change-this-to-a-random-string-in-production-abc123xyz
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=face_attendance_db
DB_USER=face_admin
DB_PASSWORD=yourpassword123
DB_HOST=localhost
DB_PORT=5432

# Media files
MEDIA_ROOT=media/

# InsightFace model (buffalo_l downloads automatically)
INSIGHTFACE_MODEL=buffalo_l
```

Create `.gitignore` too:
```bash
# Create backend/.gitignore
echo "venv/
__pycache__/
*.pyc
.env
media/
*.sqlite3
.DS_Store" > .gitignore
```

---

## Step 9 — Configure settings.py

Replace the contents of `backend/face_attendance/settings.py` with:

```python
# backend/face_attendance/settings.py

from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    
    # Our apps
    'apps.accounts',
    'apps.attendance',
    'apps.face_recognition_engine',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',   # Must be first
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'face_attendance.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'face_attendance.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'   # Change to your timezone
USE_I18N = True
USE_TZ = True

# Static & Media files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# JWT Settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# CORS Settings (allow React frontend)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True

# InsightFace model directory
INSIGHTFACE_MODEL_DIR = BASE_DIR / '.insightface'
INSIGHTFACE_MODEL_NAME = config('INSIGHTFACE_MODEL', default='buffalo_l')

# FAISS index file location
FAISS_INDEX_PATH = BASE_DIR / 'media' / 'faiss_index.bin'
FAISS_MAPPING_PATH = BASE_DIR / 'media' / 'faiss_mapping.json'
```

---

## Step 10 — Configure urls.py

Replace `backend/face_attendance/urls.py`:

```python
# backend/face_attendance/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API routes
    path('api/auth/', include('apps.accounts.urls')),
    path('api/attendance/', include('apps.attendance.urls')),
    path('api/face/', include('apps.face_recognition_engine.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## Step 11 — Create media directory and test

```bash
# From backend/ directory:
mkdir -p media

# Test the setup
python manage.py check
```

You should see: `System check identified no issues (0 silenced).`

---

## Step 12 — Run initial migration

```bash
python manage.py migrate
```

---

## Step 13 — Create superuser

```bash
python manage.py createsuperuser
# Enter username, email, password when prompted
```

---

## Step 14 — Test the server

```bash
python manage.py runserver
```

Open http://localhost:8000/admin — you should see the Django admin login page. ✅

---

**Next →** `03_DATABASE_MODELS.md`
