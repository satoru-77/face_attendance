# 11 — Kiosk & Enrollment Templates

> **Goal:** Build the fullscreen kiosk check-in page and the face enrollment page with webcam capture.
> **Files to create:**
> - `templates/face_recognition/kiosk.html`
> - `templates/face_recognition/enroll.html`
> - `templates/face_recognition/users.html`
> - `templates/face_recognition/user_create.html`
> - `static/js/kiosk.js`
> - `static/js/enroll.js`

---

## Design Principles (from Documentation)

- **Kiosk**: Dark (`#0f172a` bg), fullscreen, auto-capture, shows recognition result with name/dept/confidence
- **Enrollment**: 10-photo sequence with progress bar, pose guidance overlays, quality feedback
- **Color scheme**: Blue primary `#3B82F6`, Green success `#10B981`, Yellow warning `#F59E0B`, Red danger `#EF4444`

---

## File 1 — `templates/face_recognition/kiosk.html`

```html
{% extends 'base/base_kiosk.html' %}
{% block content %}
<!-- Kiosk full-screen layout with dark background -->
{% endblock %}
```
*(See actual file for full code)*

---

## File 2 — `templates/face_recognition/enroll.html`
10-photo enrollment wizard with webcam capture, progress bar, and pose guidance.

---

## File 3 — `templates/face_recognition/users.html`
Admin user list with filters and face enrollment status badges.

---

## File 4 — `templates/face_recognition/user_create.html`
Form to create a new user with profile and department assignment.

---

## File 5 — `static/js/kiosk.js`
Handles webcam stream, auto-capture when face is detected, API call to `/api/attendance/checkin/`, and result display.

---

## File 6 — `static/js/enroll.js`
Step-by-step 10-photo capture, progress tracking, pose instructions, and API call to `/api/face/enroll/`.

---

**Next →** `12_ATTENDANCE_TEMPLATES.md`
