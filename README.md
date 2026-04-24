# FaceTrack — AI-Powered Classroom Attendance System

> Automatically mark student attendance using live face recognition.  
> Department admins register students (with face training), then point a classroom camera to mark the entire class present in one scan.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.0-092E20?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![InsightFace](https://img.shields.io/badge/InsightFace-0.7.3-FF6B35)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Table of Contents

1. [Features](#features)
2. [System Requirements](#system-requirements)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [Step-by-Step Setup](#step-by-step-setup)
   - [1. Install PostgreSQL](#1-install-postgresql)
   - [2. Clone the Repository](#2-clone-the-repository)
   - [3. Set Up Python Environment](#3-set-up-python-environment)
   - [4. Configure Environment Variables](#4-configure-environment-variables)
   - [5. Set Up the Database](#5-set-up-the-database)
   - [6. Run Migrations](#6-run-migrations)
   - [7. Create a Superuser](#7-create-a-superuser)
   - [8. Seed Departments](#8-seed-departments)
   - [9. Run the Development Server](#9-run-the-development-server)
6. [How to Use](#how-to-use)
7. [GPU Acceleration (Optional)](#gpu-acceleration-optional)
8. [Environment Variables Reference](#environment-variables-reference)
9. [Common Errors & Fixes](#common-errors--fixes)
10. [Pushing to GitHub](#pushing-to-github)
11. [Contributing](#contributing)

---

## Features

- 🎓 **Department-scoped admin accounts** — CS, MCA, IT, ECE, MBA each have their own admin
- 📸 **Face enrollment** — Capture 10 photos per student, trained via InsightFace `buffalo_l` model
- 🎯 **Classroom bulk recognition** — Point camera → click Scan → all faces recognized & marked present simultaneously
- 📊 **Live capture dashboard** — Shows In Class / Present / Absent updating in real-time after each scan
- 📅 **Attendance records** — Daily and monthly reports with CSV export
- 🔐 **Secure** — Each admin only sees their own department's students

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10 / Ubuntu 20.04 / macOS 12 | Windows 11 / Ubuntu 22.04 |
| Python | 3.10 | 3.11 |
| RAM | 4 GB | 8 GB+ |
| Storage | 2 GB free (for models) | 5 GB+ |
| Camera | Any USB webcam | 1080p webcam |
| GPU | Not required | NVIDIA GPU (for faster recognition) |

---

## Tech Stack

This is a **full-stack Django project** — Django handles both the API logic *and* renders the HTML pages (server-side). There is no separate JavaScript frontend framework.

| Layer | Technology |
|-------|-----------|
| Web Framework | Django 5.0 (views, templates, routing) |
| REST API | Django REST Framework (for face recognition AJAX calls) |
| Database | PostgreSQL 16 |
| Face Recognition | InsightFace `buffalo_l` (detection + 512-dim embedding) |
| Vector Search | FAISS-CPU (fast nearest-neighbour face matching) |
| Image Processing | OpenCV + Pillow |
| UI / Styling | Django Templates + Tailwind CSS (via CDN, no build step) |
| Icons | Phosphor Icons |
| Charts | Chart.js |

---

## Project Structure

> **Why is everything inside `backend/`?**  
> The project was initially scaffolded with a `backend/` folder in anticipation of adding a separate React/Next.js frontend later. That never happened — Django templates handle the UI instead. So `backend/` is effectively the entire application. The empty `frontend/` folder can be safely ignored or deleted.

```
face_attendance/              ← Git repository root
├── backend/                  ← The entire Django application lives here
│   ├── manage.py             ← Run all Django commands from here
│   ├── requirements.txt      ← Python dependencies
│   ├── .env                  ← Your local config (gitignored)
│   ├── .env.example          ← Template — copy this to .env
│   │
│   ├── face_attendance/      ← Django project config
│   │   ├── settings.py       ← Database, installed apps, auth settings
│   │   ├── urls.py           ← Root URL routing
│   │   └── wsgi.py
│   │
│   ├── apps/                 ← Django applications
│   │   ├── accounts/         ← User, Department, UserProfile models + auth API
│   │   ├── attendance/       ← Attendance records, ClassSession, reports API
│   │   ├── face_recognition_engine/  ← InsightFace wrapper + FAISS index
│   │   └── web/              ← Page views (dashboard, students, attendance pages)
│   │
│   ├── templates/            ← HTML templates (rendered by Django)
│   │   ├── base/base.html    ← Master layout: left sidebar + topbar
│   │   ├── accounts/         ← login.html, register.html
│   │   ├── dashboard/        ← index.html — camera capture + live stats
│   │   ├── students/         ← list.html, add.html, detail.html + face training
│   │   └── attendance/       ← list.html, monthly.html
│   │
│   ├── static/               ← CSS, JS, image assets
│   └── media/                ← Uploaded face photos (gitignored)
│
├── build_guide/              ← Developer documentation & design notes
├── .gitignore
└── README.md
```

> **All commands** (`manage.py`, `pip install`, etc.) are run from inside the `backend/` directory.

---

## Step-by-Step Setup

### 1. Install PostgreSQL

#### Windows

1. Download the installer from **https://www.postgresql.org/download/windows/**
2. Run the installer — note down:
   - Installation port: `5432` (default)
   - Superuser password (remember this!)
3. During install, also install **pgAdmin 4** (bundled — useful for GUI)
4. After install, open **pgAdmin 4** or **SQL Shell (psql)** from the Start Menu

#### macOS

```bash
brew install postgresql@16
brew services start postgresql@16
```

#### Ubuntu / Debian

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib -y
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

---

**Create the database and user:**

Open psql (Windows: search "SQL Shell" in Start Menu):

```sql
-- Log in as postgres superuser
-- Windows: open SQL Shell and press Enter for all prompts except Password
-- Linux/Mac:
sudo -u postgres psql

-- Inside psql:
CREATE DATABASE face_attendance_db;
CREATE USER face_admin WITH PASSWORD 'yourpassword123';
GRANT ALL PRIVILEGES ON DATABASE face_attendance_db TO face_admin;
ALTER DATABASE face_attendance_db OWNER TO face_admin;
\q
```

> 💡 Note down: `DB_NAME=face_attendance_db`, `DB_USER=face_admin`, `DB_PASSWORD=yourpassword123`

---

### 2. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/face_attendance.git
cd face_attendance
```

---

### 3. Set Up Python Environment

> **Requires Python 3.10 or 3.11.** Check with `python --version`.  
> If needed, download from https://www.python.org/downloads/

```bash
# Navigate to the backend
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

> ⚠️ **InsightFace requires `cmake` and C++ build tools on Windows.**  
> If `pip install insightface` fails:
> 1. Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) → select "Desktop development with C++"
> 2. Install cmake: `pip install cmake` then retry

> ⚠️ **`faiss-cpu` may need special handling on some systems:**
> ```bash
> pip install faiss-cpu --no-build-isolation
> ```

---

### 4. Configure Environment Variables

```bash
# Still inside backend/
cp .env.example .env   # Windows: copy .env.example .env
```

Open `backend/.env` in any text editor and fill in your values:

```env
SECRET_KEY=django-insecure-replace-me-with-50-random-chars
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=face_attendance_db
DB_USER=face_admin
DB_PASSWORD=yourpassword123
DB_HOST=localhost
DB_PORT=5432

MEDIA_ROOT=media/
INSIGHTFACE_MODEL=buffalo_l
```

> 🔑 Generate a secure `SECRET_KEY`:
> ```bash
> python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```

---

### 5. Set Up the Database

Verify PostgreSQL is running and your credentials work:

```bash
# Windows — check service is running:
Get-Service postgresql*   # in PowerShell

# Linux/Mac:
sudo systemctl status postgresql
```

---

### 6. Run Migrations

```bash
# Inside backend/ with venv active
python manage.py migrate
```

Expected output:
```
Applying accounts.0001_initial... OK
Applying attendance.0001_initial... OK
...
```

> 🤖 **First run only:** InsightFace will download the `buffalo_l` model (~500 MB) automatically. This takes 2–5 minutes depending on your internet speed. It only happens once — files are cached in `backend/.insightface/`.

---

### 7. Create a Superuser

```bash
python manage.py createsuperuser
```

You'll be prompted:
```
Username: admin
Email: admin@yourschool.edu
Password: (choose a strong password)
```

This gives you access to `/admin/` (Django admin panel).

---

### 8. Seed Departments

Run this one-time script to create the default departments:

```bash
python -c "
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'face_attendance.settings'
django.setup()
from apps.accounts.models import Department
depts = [
    ('CS',  'Computer Science'),
    ('MCA', 'Master of Computer Applications'),
    ('IT',  'Information Technology'),
    ('ECE', 'Electronics and Communication'),
    ('MBA', 'Master of Business Administration'),
]
for code, name in depts:
    d, created = Department.objects.get_or_create(code=code, defaults={'name': name})
    print(('Created' if created else 'Exists'), code, '-', name)
print('Done!')
"
```

---

### 9. Run the Development Server

```bash
python manage.py runserver
```

Open your browser and go to: **http://localhost:8000**

You'll see the **FaceTrack login page**.

---

## How to Use

### First time setup (after running the server):

#### 1. Register a Department Admin
- Go to **http://localhost:8000/register/**
- Select your department (e.g. "CS — Computer Science")
- Fill in your name, username, and password
- Click **Create Admin Account**

#### 2. Log In
- Go to **http://localhost:8000/login/**
- Sign in with the credentials you just created

#### 3. Register Students
- Click **"Register Student"** (top-right button or left sidebar)
- Fill in: Name, Username, Roll Number, Email, Phone
- Click **"Save & Proceed to Face Training"**
- On the student detail page → click **"Train Face Recognition"**
- Click **"Start Camera"**
- Capture **10 photos** following the pose instructions
- Click **"Save & Train Model"** — wait for InsightFace to process

#### 4. Take Classroom Attendance
- Go to the **Dashboard** (Home)
- Click **"Start Camera"** → point the camera at the class
- Select the **Subject/Class** from the dropdown
- Click **"Capture & Mark Attendance"**
- All recognized students are marked **Present** instantly
- The **Capture Details** panel updates live (In Class / Present / Absent)

#### 5. View Reports
- **Attendance** page: Filter by date, see who's present/absent
- **Reports** page: Monthly breakdown with attendance percentage per student

---

## GPU Acceleration (Optional)

If you have an **NVIDIA GPU**, face recognition will be significantly faster:

```bash
pip uninstall onnxruntime faiss-cpu -y
pip install onnxruntime-gpu==1.18.0
pip install faiss-gpu==1.7.4  # Linux only — on Windows use faiss-cpu
```

Make sure you have:
- NVIDIA driver ≥ 525
- CUDA Toolkit 11.8 or 12.x — https://developer.nvidia.com/cuda-downloads
- cuDNN 8.x — https://developer.nvidia.com/cudnn

---

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key (keep private!) | `django-insecure-abc...xyz` |
| `DEBUG` | `True` for dev, `False` for production | `True` |
| `ALLOWED_HOSTS` | Comma-separated allowed hostnames | `localhost,127.0.0.1` |
| `DB_NAME` | PostgreSQL database name | `face_attendance_db` |
| `DB_USER` | PostgreSQL username | `face_admin` |
| `DB_PASSWORD` | PostgreSQL password | `yourpassword123` |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `MEDIA_ROOT` | Path for uploaded face photos | `media/` |
| `INSIGHTFACE_MODEL` | Model name (don't change) | `buffalo_l` |

---

## Common Errors & Fixes

### `psycopg2.OperationalError: could not connect to server`
- PostgreSQL is not running → Start it:
  - **Windows:** `net start postgresql-x64-16` (or start via Services)
  - **Linux:** `sudo systemctl start postgresql`
- Wrong credentials in `.env` → double-check `DB_USER` and `DB_PASSWORD`

---

### `ModuleNotFoundError: No module named 'insightface'`
- Virtual environment not activated → run `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)

---

### InsightFace model download stuck or fails
- Check internet connection
- Manually download from https://github.com/deepinsight/insightface → place in `backend/.insightface/models/buffalo_l/`

---

### `django.db.utils.ProgrammingError: permission denied`
```sql
-- Run in psql as superuser:
GRANT ALL ON SCHEMA public TO face_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO face_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO face_admin;
```

---

### Camera not working in browser
- Browser requires **HTTPS** for camera access on non-localhost origins
- On `localhost` it works over HTTP — make sure you're using `http://localhost:8000` not `127.0.0.1:8000` (Chrome sometimes blocks camera on `127.0.0.1`)
- Allow camera when the browser asks for permission

---

### `faiss-cpu` install fails on Windows
```bash
pip install faiss-cpu --no-build-isolation
```

---

## Pushing to GitHub

> Do this **once**, before your first commit.

### Step 1 — Install Git

Download from **https://git-scm.com/downloads** and install with default options.  
Verify: `git --version`

---

### Step 2 — Create a GitHub Account

Go to **https://github.com** → Sign Up (free).

---

### Step 3 — Create a New Repository on GitHub

1. Click the **`+`** icon (top right) → **New repository**
2. Fill in:
   - **Repository name:** `face_attendance`
   - **Description:** AI-powered classroom attendance with face recognition
   - **Visibility:** Public or Private (your choice)
   - ❌ Do **NOT** tick "Add a README" or "Add .gitignore" — we already have these
3. Click **Create repository**
4. GitHub will show you a page with the remote URL — copy it, e.g.:
   ```
   https://github.com/YOUR_USERNAME/face_attendance.git
   ```

---

### Step 4 — Configure Git (first time only)

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

---

### Step 5 — Commit and Push

Open a terminal in the project root (`face_attendance/`):

```bash
# 1. Initialise git (skip if already done)
git init

# 2. Stage everything (.gitignore will automatically exclude secrets/venv/models)
git add -A

# 3. Check what's being committed (optional but recommended)
git status

# 4. Create your first commit
git commit -m "Initial commit: FaceTrack face attendance system"

# 5. Rename default branch to 'main'
git branch -M main

# 6. Link to your GitHub repo (paste YOUR URL from Step 3)
git remote add origin https://github.com/YOUR_USERNAME/face_attendance.git

# 7. Push!
git push -u origin main
```

GitHub will ask for your username + password. For the password, use a **Personal Access Token** (not your account password):
- GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token
- Tick: `repo` scope → Generate → copy the token and use it as the password

---

### Step 6 — Verify

Refresh your GitHub repo page — you should see all your files, including the `README.md` rendered at the bottom.

> ✅ Check that these are **NOT** visible in GitHub (the `.gitignore` should have excluded them):
> - `backend/.env`
> - `backend/venv/`
> - `backend/.insightface/`
> - `backend/db.sqlite3`
> - `backend/media/` (except the empty `.gitkeep` file)

---

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to your fork: `git push origin feature/your-feature`
5. Open a Pull Request

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

> Built with ❤️ using Django + InsightFace. Designed for educational institutions needing efficient, automated attendance tracking.
