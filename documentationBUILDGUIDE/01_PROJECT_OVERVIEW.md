# 01 — Project Overview

## What is FaceTrack?

FaceTrack is a **department-scoped, face recognition–based attendance system** for colleges/schools.

A department admin (e.g., a CS professor) runs a server, registers students, captures 10 photos of each student's face to build their face embedding, and then uses a webcam to mark attendance in real time — either one person at a time (Kiosk mode) or the entire class at once (Classroom mode).

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Browser (Teacher/Admin)                │
│  Django HTML Templates + Tailwind CSS + Vanilla JS       │
│  Camera → captures frames → sends to API as JPEG        │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP (form POST / fetch API)
┌────────────────────▼────────────────────────────────────┐
│              Django Backend (port 8080)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Web Views   │  │  API Views   │  │  Face Engine  │  │
│  │  (HTML UI)   │  │  (REST/JSON) │  │  (Singleton)  │  │
│  └──────────────┘  └──────────────┘  └───────┬───────┘  │
│                                               │          │
│  ┌────────────────────────┐   ┌───────────────▼───────┐  │
│  │    PostgreSQL DB       │   │   InsightFace Model   │  │
│  │  users / profiles /   │   │   buffalo_l (5 ONNXs) │  │
│  │  attendance / sessions │   │   FAISS vector index  │  │
│  └────────────────────────┘   └───────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## User Roles

| Role | Who | What they can do |
|------|-----|-----------------|
| **ADMIN** | Department head/teacher | Register students, take attendance, view reports, export CSV |
| **STUDENT** | Enrolled student | View their own attendance calendar only |
| **TEACHER** | (reserved) | Same as ADMIN for now |
| **STAFF** | (reserved) | Future use |

> **Note:** Django's built-in `is_staff=True` is set for ADMIN role users so they can access Django admin panel.  
> Django's superuser (`is_superuser=True`) is the only one with full admin panel access.

---

## Key Flows

### Flow 1 — Admin Setup
```
SuperUser creates Department in /admin/
  → Admin registers via /register/ (self-service)
  → Admin logs in → Dashboard
```

### Flow 2 — Student Registration
```
Admin clicks "Register Student"
  → Fills name, roll number, email, password
  → Student account created (STUDENT role)
  → Auto-redirected to face enrollment page
  → 10 photos captured (different poses)
  → Face embedding computed + stored in FAISS
  → Student's is_face_enrolled = True
```

### Flow 3 — Taking Attendance
```
Admin opens Dashboard
  → Selects class/subject
  → Clicks "Start Camera"
  → Points camera at student
  → Clicks "Capture & Mark Attendance"
  → InsightFace detects face → FAISS lookup → finds student
  → Attendance record created (PRESENT/LATE)
  → Student appears in "Recognized Students" list
```

### Flow 4 — Student Views Their Attendance
```
Student logs in → auto-redirected to /my-attendance/
  → Sees monthly calendar with colored days
  → Green = Present, Yellow = Late, Red = Absent
```

---

## Technology Choices

| Tech | Why |
|------|-----|
| **InsightFace buffalo_l** | State-of-the-art face recognition, 512-D embeddings, works CPU-only |
| **FAISS IndexFlatIP** | Cosine similarity search, instant lookup even with 10,000 students |
| **PostgreSQL** | Relational DB for attendance records, supports unique_together constraints |
| **Django sessions** | Simple, no JWT needed for the browser UI (API uses JWT) |
| **Tailwind CSS (CDN)** | Rapid prototyping, orange brand theme |
