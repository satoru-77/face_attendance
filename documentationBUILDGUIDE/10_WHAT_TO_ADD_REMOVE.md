# 10 — What to Add, Remove, and Improve

## 🔴 Must Fix (Broken Logic)

### Already Fixed in this Session:
- ✅ URL name collision for Reports page
- ✅ Confidence scale bug (0–1 vs 0–100) in check-in and classroom views

---

## 🟡 Should Add (Missing Features)

### ✅ 1. Subject/Period Saved to Attendance
**Problem:** The "Select Class" UI exists but does nothing.  
**Fixed:**
- Added `subject` field to `Attendance` model
- Passing `subject` from JS to the API
- Storing it in the `get_or_create` defaults

### ✅ 2. FAISS Rebuild Management Command
**Problem:** If FAISS files are lost, all enrolled students must re-enroll.  
**Added:** `python manage.py rebuild_faiss`
```python
# management/commands/rebuild_faiss.py
from apps.accounts.models import FaceEncoding
from apps.face_recognition_engine.face_engine import face_engine
import numpy as np

for enc in FaceEncoding.objects.filter(is_primary=True):
    emb = np.array(enc.embedding, dtype=np.float32)
    face_engine.add_to_index(enc.user_id, emb)
```

### 3. Configurable Late Cutoff Time
**Problem:** Late cutoff is hardcoded as `time(9, 15)` in two places.  
**Fix:** Add to `ClassSession` or a separate `Settings` model, or at minimum add to `.env`:
```python
LATE_CUTOFF_HOUR = 9
LATE_CUTOFF_MINUTE = 15
```

### 4. Student Can Change Their Password
**Problem:** Students are given a default password `Student@123` but have no way to change it via the UI.  
**Add:** A password change page at `/my-account/change-password/`

### 5. Department Head Assignment
**Problem:** `Department.head` field exists in the model but is never set or used anywhere.  
**Either:** Use it (set head when admin registers, check permissions) **or** remove the field.

### 6. Profile Photo Display
**Problem:** `UserProfile.profile_photo` field exists but is never used in any template.  
**Add:** Show it in `students/detail.html` and `students/list.html` student cards.

### 7. Attendance Edit from UI
**Problem:** The attendance list page shows records but has no edit button.  
**Add:** An "Override" button on each row → modal with status/notes form → PATCH to API.

---

## 🟢 Nice to Have (Enhancements)

### ✅ 8. Multi-Period Attendance Per Day
**Fixed:** Changed the unique constraint to `['user', 'date', 'subject']` and added `subject` field to `Attendance`.

### 9. Holiday Calendar
**Problem:** Monthly reports count all weekdays as working days, ignoring public holidays.  
**Add:** A `Holiday` model (date, name) and filter these out from working day counts.

### 10. Email Notifications
**Add:** Send email when:
- Student is marked ABSENT 3+ consecutive days
- Student's attendance drops below 75%
- New student is enrolled (send credentials)

### 11. Bulk Student Import (CSV)
**Add:** Upload a CSV with student names, roll numbers, emails → create all accounts at once. Much faster than one-by-one registration.

### 12. Camera Auto-Capture Mode
**Enhancement:** Instead of clicking "Capture & Mark Attendance" every time, auto-trigger when a face is detected with sufficient quality score. Useful for high-traffic entry points.

### 13. Live Preview of Who's Been Marked
**Enhancement:** The "Recognized Students" panel on Dashboard only shows today's captures from the current session. Should show all of today's attendees from the DB.

---

## 🔴 Remove (Unnecessary / Confusing)

### ✅ Removed: `base_kiosk.html`
A separate kiosk base template existed (`templates/base/base_kiosk.html`) but no view used it.  
**Action:** Deleted it.

### ✅ Removed: `attendance/daily_report.html` and `attendance/records.html`
Two duplicate templates existed for attendance viewing (`daily_report.html`, `records.html`) alongside the working `list.html` and `monthly.html`.  
**Action:** Deleted orphan templates.

### ✅ Removed: `attendance/monthly_report.html`
There were TWO monthly report templates: `monthly.html` (used) and `monthly_report.html` (orphan).  
**Action:** Deleted the orphan.

### ✅ Removed: `KioskCheckoutView`
`POST /api/attendance/checkout/` existed but was not called from any UI template.  
**Action:** Removed this endpoint and its URL.

### ✅ Removed: `ClassSession.classroom_photo` Field
The `classroom_photo` field on `ClassSession` was declared but never populated by any view.  
**Action:** Removed the field via migration.

### ✅ Removed: Duplicate `MonthlyReportView` name in attendance API urls
The API endpoint `path('report/monthly/', ...)` used the name `report-monthly` which caused Bug 1.  
Already renamed to `api-report-monthly`.

---

## Summary Checklist

| Priority | Item | Effort |
|----------|------|--------|
| 🔴 Must | Add `subject` to Attendance + wire up UI | 2h |
| 🔴 Must | Add FAISS rebuild command | 30m |
| 🔴 Must | Delete orphan templates | 15m |
| 🟡 Should | Configurable late cutoff | 30m |
| 🟡 Should | Student password change page | 1h |
| 🟡 Should | Attendance manual override in UI | 1h |
| 🟡 Should | Wire up KioskCheckoutView or remove it | 30m |
| 🟢 Nice | Bulk CSV student import | 2h |
| 🟢 Nice | Holiday calendar | 2h |
| 🟢 Nice | Auto-capture mode on dashboard | 1h |
