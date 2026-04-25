# 03 — Setup and Run

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | 3.11 recommended |
| PostgreSQL | 14+ | Must be running on localhost:5432 |
| Git | Any | For cloning |
| RAM | 4 GB min | InsightFace loads ~500 MB of ONNX models |
| CPU | Any x86_64 | GPU optional (see GPU note) |

---

## 1. Clone the Repo

```bash
git clone <repo-url>
cd face_attendance
```

---

## 2. Create the PostgreSQL Database

Open psql or pgAdmin and run:

```sql
CREATE USER nishi WITH PASSWORD 'nishi1234';
CREATE DATABASE face_attendance_db OWNER nishi;
GRANT ALL PRIVILEGES ON DATABASE face_attendance_db TO nishi;
```

> These credentials must match `backend/.env` (see step 4).

---

## 3. Set Up Python Virtual Environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

---

## 4. Configure Environment Variables

Copy the example and edit:

```bash
cp .env.example .env
```

Edit `backend/.env`:

```ini
SECRET_KEY=django-insecure-change-this-to-a-random-string-in-production-abc123xyz
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=face_attendance_db
DB_USER=nishi
DB_PASSWORD=nishi1234
DB_HOST=localhost
DB_PORT=5432

MEDIA_ROOT=media/
INSIGHTFACE_MODEL=buffalo_l
```

---

## 5. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note:** This installs `insightface`, `onnxruntime`, `faiss-cpu`, `opencv-python`, etc.  
> For GPU support, replace:
> - `onnxruntime` → `onnxruntime-gpu`
> - `faiss-cpu` → `faiss-gpu`

---

## 6. InsightFace Model (buffalo_l)

The model files are stored in `backend/.insightface/models/buffalo_l/`.

Expected files:
```
.insightface/models/buffalo_l/
├── 1k3d68.onnx        (143 MB) — 3D landmark detection
├── 2d106det.onnx      (  5 MB) — 2D landmark detection
├── det_10g.onnx       ( 17 MB) — Face detection
├── genderage.onnx     (  1 MB) — Gender/age
└── w600k_r50.onnx     (174 MB) — Face recognition (embeddings)
```

If files are missing, InsightFace will auto-download on first run (~340 MB).

---

## 7. Apply Database Migrations

```bash
python manage.py migrate
```

This creates all tables:
- `accounts_department`
- `accounts_userprofile`
- `accounts_faceencoding`
- `attendance_attendance`
- `attendance_classsession`

---

## 8. Create Superuser

```bash
python manage.py createsuperuser
```

Enter username, email, password. This superuser can:
- Access `/admin/`
- Create Departments
- Create initial admin accounts

---

## 9. Create Department(s) via Admin

Go to `http://localhost:8080/admin/` → Login with superuser.

Under **Accounts → Departments**, create your department:

| Field | Example value |
|-------|--------------|
| Name | Computer Science |
| Code | CS |
| Building | Block A (optional) |

> **This step is required** before any admin can self-register.

---

## 10. (Optional) Load Seed Data

```bash
python seed_data.py
```

Creates sample students (Priya Sharma, etc.) and departments for testing.

---

## 11. Run the Server

```bash
python manage.py runserver 8080
```

> **Note:** First startup takes 15–30 seconds while InsightFace loads all 5 ONNX models into memory. Subsequent requests are instant.

Open: `http://localhost:8080`

---

## Startup Time Breakdown

| Component | Time |
|-----------|------|
| Django startup | < 1s |
| InsightFace model loading (5 ONNX files) | 10–30s |
| FAISS index loading from disk | < 1s |
| **Total until first request** | ~15–30s |

---

## File Structure Reference

```
face_attendance/
├── backend/                    ← Django project root
│   ├── .env                    ← Secret config (never commit)
│   ├── .insightface/           ← Model cache
│   │   └── models/buffalo_l/   ← 5 ONNX files
│   ├── apps/
│   │   ├── accounts/           ← User, Profile, FaceEncoding models
│   │   ├── attendance/         ← Attendance, ClassSession models + API
│   │   ├── face_recognition_engine/  ← InsightFace + FAISS
│   │   └── web/                ← HTML views (login, dashboard, etc.)
│   ├── face_attendance/        ← Django settings, urls
│   ├── media/                  ← Uploaded files + FAISS index
│   ├── static/                 ← CSS, JS, images
│   ├── templates/              ← HTML templates
│   ├── manage.py
│   └── requirements.txt
├── documentationBUILDGUIDE/    ← This folder
└── README.md
```
