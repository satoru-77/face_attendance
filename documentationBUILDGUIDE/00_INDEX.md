# FaceTrack — Documentation Build Guide

> **Project:** FaceTrack Face Recognition Attendance System  
> **Stack:** Django 5 · PostgreSQL · InsightFace (buffalo_l) · FAISS · OpenCV  
> **Server:** `http://localhost:8080`

---

## 📚 Documentation Index

| # | File | What It Covers |
|---|------|----------------|
| 01 | [01_PROJECT_OVERVIEW.md](./01_PROJECT_OVERVIEW.md) | What the system is, roles, architecture overview |
| 02 | [02_DATABASE_SCHEMA.md](./02_DATABASE_SCHEMA.md) | All models, fields, relationships, constraints |
| 03 | [03_SETUP_AND_RUN.md](./03_SETUP_AND_RUN.md) | Prerequisites, installation, running the server |
| 04 | [04_USER_ROLES_AND_AUTH.md](./04_USER_ROLES_AND_AUTH.md) | Roles, login/register logic, permissions |
| 05 | [05_STUDENT_REGISTRATION.md](./05_STUDENT_REGISTRATION.md) | Full student registration + face enrollment flow |
| 06 | [06_FACE_ENROLLMENT.md](./06_FACE_ENROLLMENT.md) | InsightFace model, FAISS index, enrollment API |
| 07 | [07_ATTENDANCE_LOGIC.md](./07_ATTENDANCE_LOGIC.md) | How attendance is marked, checked, exported |
| 08 | [08_API_REFERENCE.md](./08_API_REFERENCE.md) | All API endpoints with request/response examples |
| 09 | [09_BUGS_AND_FIXES.md](./09_BUGS_AND_FIXES.md) | Known bugs, what was fixed, what to add/remove |
| 10 | [10_WHAT_TO_ADD_REMOVE.md](./10_WHAT_TO_ADD_REMOVE.md) | Roadmap, improvements, cleanup checklist |

---

## 🚦 Quick Status

| Component | Status |
|-----------|--------|
| Django server (port 8080) | ✅ Running |
| PostgreSQL database | ✅ Connected |
| InsightFace buffalo_l model | ✅ Loaded (5 ONNX models) |
| FAISS index | ✅ Initialized |
| Login / Register | ✅ Working |
| Student registration | ✅ Working |
| Face enrollment (10-photo) | ✅ Working |
| Live attendance capture | ✅ Working |
| Attendance list/export | ✅ Working |
| Monthly reports page | ✅ Fixed (was 401) |
| Register Student sidebar link | ✅ Fixed (was 404) |
