# 07 — Attendance Logic

## Overview

There are two ways to mark attendance:

| Mode | How | Who triggers |
|------|-----|-------------|
| **Dashboard Live Capture** | Webcam stream → single photo → FAISS lookup | Admin, one student at a time |
| **Classroom Bulk** | One group photo → detect all faces → FAISS lookup for each | Admin, whole class at once |
| **Manual Override** | Admin edits record directly | Admin |

---

## The Golden Rule: One Record Per Student Per Day Per Subject

```python
class Attendance(models.Model):
    class Meta:
        unique_together = ['user', 'date', 'subject']
```

This database constraint means **you cannot insert two attendance rows for the same student on the same day for the same subject**.

The code uses `get_or_create()` everywhere to respect this:
- If no record exists → **create** (check-in)
- If record already exists → **update check_out_time** (check-out)

---

## Mode 1: Dashboard Live Capture (Kiosk Mode)

**UI:** Dashboard → Start Camera → Capture & Mark Attendance  
**API:** `POST /api/attendance/checkin/`

### Flow

```
1. Admin selects class/subject (UI only, not saved to DB currently)
2. Admin clicks "Start Camera" → browser requests webcam access
3. Admin points camera at student → clicks "Capture & Mark Attendance"
4. JavaScript captures current frame as JPEG blob
5. POST to /api/attendance/checkin/ with image, location, and subject
6. Server:
   a. InsightFace detects face (must be exactly 1)
   b. FAISS search → finds closest matching user
   c. Confidence check: must be ≥ 70%
   d. get_or_create Attendance record for (user, today, subject)
   e. If new → sets check_in_time, status (PRESENT or LATE)
   f. If exists → updates check_out_time
7. Response: { recognized, action, confidence, user, attendance }
8. Dashboard updates "Recognized Students" panel
```

### Late Detection

```python
late_cutoff = time(9, 15)   # 9:15 AM
attendance_status = 'LATE' if now_time > late_cutoff else 'PRESENT'
```

> This is hardcoded. See [10_WHAT_TO_ADD_REMOVE.md](./10_WHAT_TO_ADD_REMOVE.md) for making it configurable.

### Confidence Threshold

```python
if confidence < 70.0:   # 70% minimum (0–100 scale)
    return error "Face not recognized with sufficient confidence"
```

---

## Mode 2: Classroom Bulk Mode

**API:** `POST /api/attendance/classroom/`

### Flow

```
1. Admin uploads a single group photo of the classroom
2. Server uses InsightFace with det_size=(1280, 1280) for better detection
3. All faces in the photo are detected
4. Each face is matched against FAISS → confidence threshold 60%
5. A ClassSession record is created to track this bulk event
6. For each recognized face:
   get_or_create Attendance(user, today) → PRESENT or LATE
7. For each expected-but-not-recognized student:
   get_or_create Attendance(user, today) → ABSENT
8. Response includes summary + per-face bounding boxes
```

### ClassSession Record

Every classroom capture creates a `ClassSession`:
```
ClassSession
├── teacher (who triggered it)
├── date, start_time
├── location, subject
├── total_expected (from JS-provided student list)
├── total_detected (faces found in photo)
└── total_recognized (matched to DB users)
```

Each resulting `Attendance` record has `class_session` FK pointing to this session.

---

## Mode 3: Manual Override

**API:** `PATCH /api/attendance/records/<id>/`

Admin can override any attendance record:
```json
{
    "status": "PRESENT",
    "notes": "Student was present but camera failed"
}
```

The system automatically sets `attendance_mode = 'MANUAL'` and `marked_by = request.user`.

---

## Attendance Status Values

| Status | Meaning | Triggers |
|--------|---------|----------|
| `PRESENT` | On time | Check-in before 9:15 AM |
| `LATE` | Late | Check-in after 9:15 AM |
| `ABSENT` | Not present | Not detected in classroom photo, or manually set |
| `HALF_DAY` | Half day | Manual override only |

---

## Viewing Attendance

### Admin View — `/attendance/`

Shows a date-filtered table:
```
Date picker (default: today)
  ↓
Filter: students in admin's department
  ↓
Table: Roll No | Name | Check-in | Confidence | Status
  ↓
Stats: Total | Present | Absent
```

Also has "Export CSV" button and "Take Attendance" shortcut.

### Student View — `/my-attendance/`

Students see their own monthly calendar:
- Green days = PRESENT or LATE
- Red days = ABSENT
- White days = no record (weekend/holiday/not yet)

Month/year navigation supported.

---

## CSV Export

**URL:** `GET /api/attendance/report/export/?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD`  
**Auth:** Must be admin (`is_staff=True`)

Columns:
```
Date | Employee ID | Name | Department | Check-in | Check-out | Status | Mode | Confidence %
```

---

## Monthly Report — `/attendance/report/`

Shows per-student summary for a selected month:

```
For each student in department:
  present_days = count(status IN ['PRESENT','LATE'])
  late_days    = count(status == 'LATE')
  absent_days  = working_days - present_days
  percentage   = present_days / working_days * 100

Working days = Mon–Fri only (weekends excluded automatically)
```

---

## What "Working Days" Means

```python
working_days = sum(
    1 for d in range(1, days_in_month + 1)
    if date(year, month, d).weekday() < 5  # 0=Mon ... 4=Fri
)
```

Saturdays and Sundays are excluded. Holidays are **not** excluded (no holiday model exists yet).
