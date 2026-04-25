# 04 — User Roles and Auth

## Overview

Authentication uses **Django sessions** for the browser UI and **JWT tokens** for the REST API.

---

## Roles

```
Django built-in User
  └── UserProfile.role = ADMIN | TEACHER | STUDENT | STAFF
```

| Role | Login Destination | Access |
|------|-----------------|--------|
| **ADMIN** | `/` (Dashboard) | Full: students, attendance, reports, exports |
| **TEACHER** | `/` (Dashboard) | Same as ADMIN currently |
| **STUDENT** | `/my-attendance/` | Own attendance only — redirected automatically |
| **STAFF** | `/` (Dashboard) | Reserved for future use |

---

## Self-Registration Flow (`/register/`)

Admins **self-register** — no superuser required to create admin accounts.

```
GET  /register/  →  Show form (lists all Departments)
POST /register/  →  Validate + Create user + Create profile
                 →  Redirect to /login/
```

**Validations on POST:**
- `username` required, must be unique in `auth_user`
- `employee_id` required, must be unique in `accounts_userprofile`
- `password` must be ≥ 8 characters
- `password` and `password2` must match
- `department_id` must reference a valid existing Department

**What gets created:**
```python
User.objects.create_user(
    username=..., first_name=..., last_name=...,
    email=..., password=...,
    is_staff=True    # ← gives Django admin panel access
)
UserProfile.objects.create(
    user=user, employee_id=...,
    role='ADMIN', department=dept
)
```

> ⚠️ **Prerequisite:** At least one `Department` must exist before anyone can register. Create it via `/admin/` with a superuser.

---

## Login Flow (`/login/`)

```
GET  /login/  →  Show login form
POST /login/  →  authenticate(username, password)
             →  If STUDENT role → redirect to /my-attendance/
             →  Otherwise       → redirect to /dashboard/
```

**Error cases handled:**
- Wrong credentials → "Invalid credentials" message
- Inactive account → "Your account is inactive" message

---

## Logout

```
GET /logout/  →  Clears session → redirect to /login/
```

---

## JWT API Authentication

The REST API (under `/api/`) uses JWT tokens from `djangorestframework-simplejwt`.

```
POST /api/auth/login/
Body: { "username": "admin", "password": "pass" }
Response: { "access": "...", "refresh": "...", "user": {...} }
```

Token lifetimes (configured in `settings.py`):
- Access token: **1 hour**
- Refresh token: **7 days** (rotates + blacklisted after use)

Use the access token in subsequent requests:
```
Authorization: Bearer <access_token>
```

---

## Permission Matrix

| Endpoint | STUDENT | ADMIN/STAFF |
|----------|---------|------------|
| `/` Dashboard | ❌ (redirected) | ✅ |
| `/students/` | ❌ | ✅ |
| `/attendance/` | ❌ | ✅ |
| `/attendance/report/` | ❌ | ✅ |
| `/my-attendance/` | ✅ | ✅ (sees own) |
| `POST /api/attendance/checkin/` | ✅ | ✅ |
| `GET /api/attendance/records/` | ✅ (own only) | ✅ (all) |
| `GET /api/attendance/report/monthly/` | ✅ (own only) | ✅ (all) |
| `GET /api/attendance/report/export/` | ❌ | ✅ |
| `/admin/` | ❌ | ✅ (staff only) |

---

## Department Scoping

**Every admin is scoped to their department:**

```python
def get_admin_department(user):
    return user.profile.department  # e.g., Department "CS"
```

When an admin views students or attendance, it's filtered:
```python
User.objects.filter(profile__department=dept, profile__role='STUDENT')
```

This means:
- CS admin sees only CS students
- No cross-department access
- Superusers see everything
