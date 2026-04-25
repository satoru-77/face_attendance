# 05 — Student Registration

## Full Registration Flow

Student registration is a **2-step process:**

```
Step 1: Fill profile form → Account created
Step 2: Capture 10 face photos → Enrollment complete
```

This is triggered by clicking **"Register Student"** from the sidebar or the top button.

---

## Step 1 — Fill Profile Form

**URL:** `GET/POST /students/add/`  
**View:** `StudentAddView`

### Form Fields

| Field | Required | Notes |
|-------|----------|-------|
| First Name | ✅ | |
| Last Name | ✅ | |
| Username | ✅ | Must be unique in the system |
| Email | Optional | |
| Roll No / Employee ID | ✅ | Must be unique (e.g., CS2024001) |
| Phone | Optional | |
| Password | Optional | Defaults to `Student@123` if left blank |

### What Happens on Submit

```python
# 1. Validate
if User.objects.filter(username=username).exists(): → error
if UserProfile.objects.filter(employee_id=employee_id).exists(): → error

# 2. Create Django User
user = User.objects.create_user(
    username=username, first_name=..., last_name=...,
    email=..., password=password or 'Student@123'
)

# 3. Create UserProfile
UserProfile.objects.create(
    user=user,
    employee_id=employee_id,
    role='STUDENT',         ← locked to STUDENT
    department=dept,        ← admin's own department
    phone=phone,
    is_face_enrolled=False  ← default, changes after Step 2
)

# 4. Redirect to face enrollment
return redirect(f'/students/{user.pk}/?enroll=1')
```

> The student is assigned to **the same department as the logged-in admin** automatically. No department picker needed.

---

## Step 2 — Face Enrollment

**URL:** `GET /students/<pk>/?enroll=1`  
**View:** `StudentDetailView` (renders `students/detail.html` with `enroll_mode=True`)

The enrollment UI:
- Shows a webcam feed
- Guides through 10 poses:
  1. Look straight — neutral face
  2. Smile naturally
  3. Turn head slightly left
  4. Turn head slightly right
  5. Tilt head slightly up
  6. Tilt head slightly down
  7. Serious expression, straight
  8. Turn head left ~30°
  9. Turn head right ~30°
  10. Final photo — straight

### Enrollment API Calls (from JavaScript)

#### 1. Start Enrollment
```
POST /api/face/enroll/start/
Body: { "user_id": <pk> }
```
Clears any existing `FaceEncoding` rows for this user.

#### 2. Capture Each Photo (called 10 times)
```
POST /api/face/enroll/photo/
Form data:
  - user_id: <pk>
  - photo_number: 1..10
  - image: <JPEG blob from webcam>
```

**What happens:**
```python
# InsightFace processes the image
result = face_engine.process_enrollment_photo(image_bytes)

# Saves to DB
FaceEncoding.objects.create(
    user=user,
    embedding=result['embedding'],  # 512-D list
    photo_number=photo_number,      # 1-10
    quality_score=result['quality_score'],
    is_primary=False
)
```

Returns error if:
- No face detected
- Multiple faces detected
- Face quality score < 0.5

#### 3. Complete Enrollment (after all 10 photos)
```
POST /api/face/enroll/complete/
Body: { "user_id": <pk> }
```

**What happens:**
```python
# Fetch all non-primary encodings (minimum 5 required)
encodings = FaceEncoding.objects.filter(user=user, is_primary=False)

# Average all embeddings
averaged = face_engine.average_embeddings(embeddings_list)

# Save averaged as the primary embedding
FaceEncoding.objects.create(
    user=user, embedding=averaged.tolist(),
    photo_number=0, is_primary=True
)

# Add to FAISS in-memory index + persist to disk
face_engine.add_to_index(user.id, averaged)

# Mark student as enrolled
profile.is_face_enrolled = True
profile.enrollment_date = datetime.now()
profile.save()
```

---

## Re-Enrollment

If a student needs to re-enroll (e.g., changed appearance, previous enrollment failed):

1. Go to `/students/<pk>/` → click "Train Face"
2. The system calls `enroll/start/` first which **deletes all existing FaceEncoding rows** for that user
3. Re-runs the 10-photo capture
4. On `enroll/complete/`, the old FAISS entry is removed and new one added

```python
# In face_engine.add_to_index():
self._remove_user_from_index(user_id)  # Rebuilds FAISS without old entry
# Then adds new embedding
```

---

## Face Status on Student List

| Status | Meaning | Display |
|--------|---------|---------|
| Pending | `is_face_enrolled = False` | Orange "Pending" badge |
| Enrolled | `is_face_enrolled = True` | Green "Enrolled" badge |

---

## Student Login

Students use the **same login page** (`/login/`).

Default password: `Student@123` (set during registration unless admin specifies one).

After login, students are automatically redirected to `/my-attendance/` — they cannot access the dashboard, student list, or reports.
