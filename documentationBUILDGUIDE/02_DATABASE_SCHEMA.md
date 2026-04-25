# 02 — Database Schema

## Overview

The database uses **PostgreSQL**. There are 5 main tables across 2 apps:

```
apps/accounts/   → Department, UserProfile, FaceEncoding
apps/attendance/ → Attendance, ClassSession
```

Plus Django's built-in `auth_user` table.

---

## Entity Relationship Diagram

```
auth_user (Django built-in)
  ├──1:1── UserProfile  ←──── Department (FK)
  ├──1:N── FaceEncoding
  ├──1:N── Attendance ──FK──→ ClassSession
  └──1:N── ClassSession (as teacher)
```

---

## Table: `auth_user` (Django built-in)

| Field | Type | Notes |
|-------|------|-------|
| id | INT PK | Auto |
| username | VARCHAR(150) | Unique, login credential |
| first_name | VARCHAR(150) | Student/admin's first name |
| last_name | VARCHAR(150) | Student/admin's last name |
| email | VARCHAR(254) | Optional but recommended |
| password | VARCHAR(128) | Hashed (Django PBKDF2) |
| is_active | BOOL | False = soft-deleted |
| is_staff | BOOL | True for ADMIN role users |
| is_superuser | BOOL | True only for Django superuser |

---

## Table: `accounts_department`

| Field | Type | Notes |
|-------|------|-------|
| id | INT PK | Auto |
| name | VARCHAR(100) | Unique. e.g., "Computer Science" |
| code | VARCHAR(20) | Unique. e.g., "CS" |
| head_id | FK → auth_user | Optional, department head |
| building | VARCHAR(100) | Optional. e.g., "Block A" |
| created_at | DATETIME | Auto |

> **Must be created by superuser via `/admin/` before any admin can register.**

---

## Table: `accounts_userprofile`

| Field | Type | Notes |
|-------|------|-------|
| id | INT PK | Auto |
| user_id | FK → auth_user (CASCADE) | 1:1 |
| department_id | FK → department (SET NULL) | Can be null |
| employee_id | VARCHAR(50) | **Unique**. Roll number / staff ID |
| phone | VARCHAR(15) | Optional |
| role | VARCHAR(20) | ADMIN / TEACHER / STUDENT / STAFF |
| is_face_enrolled | BOOL | True after face enrollment complete |
| enrollment_date | DATETIME | When enrollment was completed |
| profile_photo | ImageField | Thumbnail only (not used for recognition) |
| created_at / updated_at | DATETIME | Auto |

> **Critical:** Every `auth_user` must have exactly one `UserProfile`. This is enforced by the registration views but NOT at the database level (no DB constraint). The code uses `get_or_create` defensively.

---

## Table: `accounts_faceencoding`

| Field | Type | Notes |
|-------|------|-------|
| id | INT PK | Auto |
| user_id | FK → auth_user (CASCADE) | Deletes all encodings if user deleted |
| embedding | JSONField | 512-element float array |
| photo_number | INT | 1-10 = individual photos, 0 = averaged (primary) |
| quality_score | FLOAT | InsightFace detection confidence (0.0–1.0) |
| is_primary | BOOL | True = the averaged embedding used for matching |
| photo_path | VARCHAR(255) | Path to enrollment photo (optional) |
| created_at | DATETIME | Auto |

> **Key invariant:** Each enrolled student has exactly 1 row with `is_primary=True` and up to 10 rows with `is_primary=False`.  
> The `is_primary=True` embedding is what gets added to the FAISS index.

---

## Table: `attendance_attendance`

| Field | Type | Notes |
|-------|------|-------|
| id | INT PK | Auto |
| user_id | FK → auth_user (CASCADE) | The student |
| date | DATE | The attendance date |
| check_in_time | TIME | When they checked in |
| check_out_time | TIME | When they checked out (nullable) |
| status | VARCHAR(20) | PRESENT / ABSENT / LATE / HALF_DAY |
| attendance_mode | VARCHAR(20) | KIOSK / CLASSROOM / MANUAL |
| confidence_score | FLOAT | FAISS similarity score × 100 (0–100%) |
| subject | VARCHAR(100) | Subject name |
| location | VARCHAR(100) | Room/location string |
| checkin_photo | ImageField | Photo taken at check-in |
| class_session_id | FK → ClassSession (SET NULL) | Which session created this |
| marked_by_id | FK → auth_user (SET NULL) | Admin who triggered it |
| notes | TEXT | Manual override reason |
| created_at / updated_at | DATETIME | Auto |

### **Critical Constraint:**
```python
unique_together = ['user', 'date', 'subject']
```
**One attendance record per student per day per subject.** If a student scans twice for the same class on the same day:
- First scan → creates the record (check_in_time set)
- Second scan → updates check_out_time only

---

## Table: `attendance_classsession`

| Field | Type | Notes |
|-------|------|-------|
| id | INT PK | Auto |
| teacher_id | FK → auth_user (SET NULL) | Who triggered the session |
| date | DATE | Session date |
| start_time | TIME | Session start time |
| location | VARCHAR(100) | Room |
| subject | VARCHAR(100) | Subject name |
| total_expected | INT | How many students expected |
| total_detected | INT | How many faces detected in photo |
| total_recognized | INT | How many faces matched to known students |
| created_at | DATETIME | Auto |

---

## Important Relationships

```
Department → has many → UserProfile (members)
User → has one → UserProfile
User → has many → FaceEncoding (up to 10 + 1 primary)
User → has many → Attendance (one per day)
User → has many → ClassSession (as teacher)
ClassSession → has many → Attendance (records it created)
```

---

## FAISS Index (In-Memory + Persisted to Disk)

The FAISS index is **NOT in PostgreSQL**. It lives in:
- `backend/media/faiss_index.bin` — the binary vector index
- `backend/media/faiss_mapping.json` — maps FAISS position → Django user_id

```json
// faiss_mapping.json example:
{"0": 3, "1": 5, "2": 8}
// FAISS position 0 → user_id 3
// FAISS position 1 → user_id 5
```

> **Important:** If you delete a user from the DB but don't re-save the FAISS index, stale entries will remain. The enrollment flow handles this via `_remove_user_from_index()` during re-enrollment.
