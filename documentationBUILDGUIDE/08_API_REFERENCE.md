# 08 — API Reference

All API endpoints are under `/api/`. Browser UI uses Django sessions (no token needed). API clients need JWT Bearer tokens.

---

## Authentication Endpoints

### POST `/api/auth/login/`
Get JWT tokens.
```json
// Request
{ "username": "admin", "password": "pass123" }

// Response 200
{
  "access": "<jwt_access_token>",
  "refresh": "<jwt_refresh_token>",
  "user": {
    "id": 1,
    "username": "admin",
    "full_name": "Admin User",
    "employee_id": "CS001",
    "role": "ADMIN",
    "department": "Computer Science",
    "is_face_enrolled": false
  }
}
```

### POST `/api/auth/logout/`
Blacklist refresh token. Requires `Authorization: Bearer <access>`.
```json
// Request
{ "refresh": "<refresh_token>" }
// Response 200
{ "message": "Logged out successfully." }
```

### GET `/api/auth/me/`
Get current user's profile.

---

## User Management Endpoints (Admin only)

### GET `/api/auth/users/`
List all users. Query params: `role`, `department`, `search`, `enrolled`.

### POST `/api/auth/users/`
Create a user.
```json
{
  "username": "student1",
  "first_name": "Ravi",
  "last_name": "Kumar",
  "email": "ravi@college.edu",
  "password": "Student@123",
  "employee_id": "CS2024002",
  "role": "STUDENT",
  "department_id": 1
}
```

### GET/PUT/DELETE `/api/auth/users/<id>/`
Retrieve, update, or deactivate a user.

### GET `/api/auth/departments/`
List all departments.

---

## Face Enrollment Endpoints

### POST `/api/face/enroll/start/`
Initialize enrollment (clears old encodings).
```json
// Request
{ "user_id": 5 }
// Response
{ "message": "Ready to enroll Priya Sharma.", "user_id": 5, "total_photos_needed": 10 }
```

### POST `/api/face/enroll/photo/`
Submit one enrollment photo. Call this 10 times.
```
Form data (multipart):
  user_id:      5
  photo_number: 1   (1–10)
  image:        <JPEG file>
```
```json
// Response 200
{
  "success": true,
  "photo_number": 1,
  "quality_score": 0.94,
  "message": "Photo 1/10 captured successfully."
}
// Response 400 (no face / multiple faces / low quality)
{ "error": "No face detected. Please ensure your face is clearly visible." }
```

### POST `/api/face/enroll/complete/`
Average embeddings + add to FAISS index. Call after all photos.
```json
// Request
{ "user_id": 5 }
// Response 200
{
  "success": true,
  "message": "Priya Sharma enrolled successfully.",
  "photos_used": 10,
  "user_id": 5
}
// Response 400 (too few photos)
{ "error": "Need at least 5 photos. Only 3 captured." }
```

### GET `/api/face/status/<user_id>/`
Check enrollment status.
```json
{
  "user_id": 5,
  "is_enrolled": true,
  "enrollment_date": "2026-04-26T00:00:00Z",
  "photos_captured": 10
}
```

---

## Attendance Endpoints

### POST `/api/attendance/checkin/`
Kiosk mode: Identify student and mark attendance.
```
Form data (multipart):
  image:    <JPEG from webcam>
  location: "Room 201"  (optional)
  subject:  "CS101"     (optional)
```
```json
// Response 200 — recognized
{
  "recognized": true,
  "action": "checked_in",       // or "checked_out"
  "confidence": 87.3,           // 0–100%
  "user": {
    "id": 5,
    "name": "Priya Sharma",
    "employee_id": "CS2024001",
    "department": "Computer Science",
    "role": "STUDENT"
  },
  "attendance": {
    "id": 42,
    "date": "2026-04-26",
    "status": "PRESENT",
    "check_in_time": "09:10:00",
    "check_out_time": null,
    "attendance_mode": "KIOSK",
    "confidence_score": 87.3
  }
}

// Response 400 — not recognized
{ "recognized": false, "confidence": 45.1, "error": "Face not recognized..." }

// Response 400 — no face
{ "recognized": false, "error": "No face detected..." }
```

### POST `/api/attendance/classroom/`
Bulk attendance from group photo.
```
Form data (multipart):
  image:             <JPEG group photo>
  location:          "Room 101"
  subject:           "Data Structures"
  expected_students: "[3, 5, 8, 12]"  (JSON array of user IDs)
```

### GET `/api/attendance/records/`
List attendance records. Query params: `user_id`, `date`, `date_from`, `date_to`, `status`, `department_id`.

### PATCH `/api/attendance/records/<id>/`
Manual override.
```json
{ "status": "PRESENT", "notes": "Camera failed, student was present" }
```

### GET `/api/attendance/report/daily/?date=2026-04-26`
Daily summary for a date.

### GET `/api/attendance/report/monthly/?year=2026&month=4`
Per-student monthly summary.

### GET `/api/attendance/report/export/?date_from=2026-04-01&date_to=2026-04-30`
CSV download. Admin only.

### GET `/api/attendance/stats/`
Quick dashboard stats (total users, enrolled, today present/absent).

---

## Error Response Format

All errors return:
```json
{ "error": "Human-readable error message." }
```

HTTP status codes used:
- `200` Success
- `201` Created
- `400` Bad request (validation error, face not detected, etc.)
- `401` Unauthorized (not logged in)
- `403` Forbidden (wrong role)
- `404` Not found
