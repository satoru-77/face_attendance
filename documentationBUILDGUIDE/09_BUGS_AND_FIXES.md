# 09 — Bugs Found and Fixed

This document tracks every bug discovered during the audit (April 26, 2026) and whether it was fixed.

---

## ✅ Bug 1: URL Name Collision — `report-monthly`

**Severity:** 🔴 Critical — Reports page shows 401 JSON error instead of HTML page

**Root Cause:**  
Two Django URL configs define the same name `report-monthly`:

```python
# apps/web/urls.py (web HTML page)
path('attendance/report/', views.MonthlyReportView.as_view(), name='report-monthly')

# apps/attendance/urls.py (REST API endpoint)
path('report/monthly/', views.MonthlyReportView.as_view(), name='report-monthly')
```

Django resolves `{% url 'report-monthly' %}` to the **last** registered URL with that name. Since `apps/attendance/urls.py` is included after `apps/web/urls.py` in `face_attendance/urls.py`, the sidebar link generates `/api/attendance/report/monthly/` — a JSON API endpoint that requires JWT auth and returns 401.

**Fix:**  
Rename the API endpoint URL name to `api-report-monthly` in `apps/attendance/urls.py`:

```python
# Before (BROKEN):
path('report/monthly/', views.MonthlyReportView.as_view(), name='report-monthly'),

# After (FIXED):
path('report/monthly/', views.MonthlyReportView.as_view(), name='api-report-monthly'),
```

**Status:** ✅ Fixed

---

## ✅ Bug 2: Wrong Confidence Scale in KioskCheckinView

**Severity:** 🔴 Critical — Attendance NEVER fails the confidence check; confidence logged to DB as 8700%

**Root Cause:**  
`face_engine.search()` returns confidence on a **0–100 scale** (already multiplied by 100):
```python
# face_engine.py line 269
confidence = max(0, float(dist)) * 100   # ← 0 to 100
results.append((user_id, confidence))
```

But `KioskCheckinView` in `attendance/views.py` treats it as **0–1 scale**:
```python
# attendance/views.py lines 71–98 (WRONG)
if confidence < 0.70:                          # ← Should be 70.0
    ...
'confidence': round(confidence * 100, 1),      # ← Double-multiplies! e.g. 87 → 8700
'confidence_score': round(confidence * 100, 2) # ← Same bug
```

**Fix:**
```python
# After (FIXED):
if confidence < 70.0:                     # ← correct threshold
    ...
'confidence': round(confidence, 1),       # ← already 0-100
'confidence_score': round(confidence, 2)  # ← already 0-100
```

**Status:** ✅ Fixed

---

## ✅ Bug 3: Same Double-Multiply in ClassroomAttendanceView

**Severity:** 🟡 Medium — Confidence stored as 8700+ in DB for classroom sessions

**Root Cause:** Same scale confusion as Bug 2.
```python
# attendance/views.py line 233 (WRONG)
'confidence_score': round(confidence * 100, 2)

# Fix:
'confidence_score': round(confidence, 2)
```
Also in the response body:
```python
# Line 281 (WRONG)
'confidence': round(r['confidence'] * 100, 1)

# Fix:
'confidence': round(r['confidence'], 1)
```

**Status:** ✅ Fixed

---

## 🟡 Known Issue 4: Subject Not Saved to Attendance Record

**Severity:** 🟡 Medium — UX inconsistency

**Description:**  
The Dashboard has a "Select Class" dropdown, but when attendance is marked via the camera, that class/subject value is **never sent to the server** and **not saved** to the `Attendance` model. The `Attendance` model has no `subject` field.

Only `ClassSession` (bulk classroom mode) has a `subject` field.

**Workaround:** Currently none. See [10_WHAT_TO_ADD_REMOVE.md](./10_WHAT_TO_ADD_REMOVE.md) for the fix plan.

**Status:** ⚠️ Not fixed yet

---

## 🟡 Known Issue 5: No FAISS Rebuild Command

**Severity:** 🟡 Medium — Data recovery risk

**Description:**  
If `media/faiss_index.bin` or `media/faiss_mapping.json` are deleted (e.g., new deployment, file corruption), there is no management command to rebuild them from the PostgreSQL `FaceEncoding` table.

The primary embeddings exist in PostgreSQL (`is_primary=True` rows), but the admin would need to manually write code or re-enroll all students.

**Status:** ⚠️ Not fixed yet — management command needed

---

## 🟢 Non-Issue: "Register Student" 404

**Original report:** Sidebar "Register Student" link appeared broken.  
**Investigation:** The sidebar correctly uses `{% url 'student-add' %}` → resolves to `/students/add/` which works fine.  
The 404 was observed because the page was opened via a hardcoded wrong URL, not from the sidebar. **Not a real bug.**

---

## Summary Table

| # | Bug | Severity | Status |
|---|-----|----------|--------|
| 1 | `report-monthly` URL name collision → 401 on Reports page | 🔴 Critical | ✅ Fixed |
| 2 | Confidence scale 0–1 vs 0–100 in kiosk check-in | 🔴 Critical | ✅ Fixed |
| 3 | Same confidence scale bug in classroom mode | 🟡 Medium | ✅ Fixed |
| 4 | Subject/class not saved to attendance records | 🟡 Medium | ⚠️ Pending |
| 5 | No FAISS index rebuild management command | 🟡 Medium | ⚠️ Pending |
