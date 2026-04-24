# 05 — Auth & Accounts API

> **Goal:** Build JWT authentication + user management REST API endpoints.
> **Files to create:** `apps/accounts/urls.py`, `apps/accounts/views.py`, `apps/accounts/serializers.py`

---

## Overview of Endpoints

| Method | URL | Purpose | Auth Required |
|--------|-----|---------|--------------|
| POST | `/api/auth/login/` | Get JWT token pair | ❌ No |
| POST | `/api/auth/refresh/` | Refresh access token | ❌ No |
| POST | `/api/auth/logout/` | Blacklist refresh token | ✅ Yes |
| GET | `/api/auth/me/` | Get current user info | ✅ Yes |
| GET | `/api/auth/users/` | List all users (Admin) | ✅ Admin |
| POST | `/api/auth/users/` | Create user (Admin) | ✅ Admin |
| GET | `/api/auth/users/<id>/` | Get specific user | ✅ Yes |
| PUT | `/api/auth/users/<id>/` | Update user | ✅ Admin |
| DELETE | `/api/auth/users/<id>/` | Delete user | ✅ Admin |
| GET | `/api/auth/departments/` | List departments | ✅ Yes |
| POST | `/api/auth/departments/` | Create department | ✅ Admin |

---

## File 1 — `apps/accounts/serializers.py`

```python
# backend/apps/accounts/serializers.py

from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Department, UserProfile, FaceEncoding


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'building', 'head', 'created_at']
        read_only_fields = ['created_at']


class UserProfileSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_code = serializers.CharField(source='department.code', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'employee_id', 'phone', 'role',
            'department', 'department_name', 'department_code',
            'is_face_enrolled', 'enrollment_date',
            'profile_photo', 'created_at', 'updated_at'
        ]
        read_only_fields = ['is_face_enrolled', 'enrollment_date', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Read serializer — returns user + profile info."""
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email',
            'first_name', 'last_name', 'full_name',
            'is_active', 'date_joined', 'profile'
        ]
        read_only_fields = ['date_joined']

    def get_full_name(self, obj):
        return obj.get_full_name()


class UserCreateSerializer(serializers.ModelSerializer):
    """Write serializer — creates user + profile together."""
    # Profile fields flattened into this serializer
    employee_id = serializers.CharField(write_only=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    role = serializers.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        write_only=True,
        default='STUDENT'
    )
    department_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password', 'employee_id', 'phone', 'role', 'department_id'
        ]

    def validate_employee_id(self, value):
        if UserProfile.objects.filter(employee_id=value).exists():
            raise serializers.ValidationError(f"Employee ID '{value}' already exists.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(f"Username '{value}' already exists.")
        return value

    def create(self, validated_data):
        # Extract profile fields
        employee_id = validated_data.pop('employee_id')
        phone = validated_data.pop('phone', '')
        role = validated_data.pop('role', 'STUDENT')
        department_id = validated_data.pop('department_id', None)
        password = validated_data.pop('password')

        # Create Django User
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        # Create UserProfile
        department = None
        if department_id:
            try:
                department = Department.objects.get(pk=department_id)
            except Department.DoesNotExist:
                pass

        UserProfile.objects.create(
            user=user,
            employee_id=employee_id,
            phone=phone,
            role=role,
            department=department
        )

        return user


class LoginResponseSerializer(serializers.Serializer):
    """Used only for documentation/response shaping."""
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
```

---

## File 2 — `apps/accounts/views.py`

```python
# backend/apps/accounts/views.py

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.pagination import PageNumberPagination

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import Department, UserProfile
from .serializers import (
    UserSerializer, UserCreateSerializer,
    DepartmentSerializer
)


# ─── Authentication Views ──────────────────────────────────────────────────────

class LoginView(APIView):
    """
    POST /api/auth/login/
    Body: { "username": "...", "password": "..." }
    Returns: { "access": "...", "refresh": "...", "user": {...} }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)

        if user is None:
            return Response(
                {'error': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'error': 'Account is disabled. Contact admin.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Body: { "refresh": "<refresh_token>" }
    Blacklists the refresh token.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully.'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MeView(APIView):
    """
    GET /api/auth/me/
    Returns the currently authenticated user's full profile.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        """Allow user to update their own profile (phone, etc.)"""
        profile = request.user.profile
        phone = request.data.get('phone')
        if phone is not None:
            profile.phone = phone
            profile.save()
        return Response(UserSerializer(request.user).data)


# ─── User Management Views ─────────────────────────────────────────────────────

class UserListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/auth/users/  → List all users (admin only)
    POST /api/auth/users/  → Create new user (admin only)
    """
    queryset = User.objects.select_related('profile__department').all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        return [IsAuthenticated(), IsAdminUser()]

    def list(self, request, *args, **kwargs):
        # Optional filters
        role = request.query_params.get('role')
        department = request.query_params.get('department')
        search = request.query_params.get('search')
        enrolled = request.query_params.get('enrolled')  # 'true' or 'false'

        qs = self.queryset

        if role:
            qs = qs.filter(profile__role=role.upper())
        if department:
            qs = qs.filter(profile__department_id=department)
        if search:
            qs = qs.filter(
                first_name__icontains=search
            ) | qs.filter(
                last_name__icontains=search
            ) | qs.filter(
                profile__employee_id__icontains=search
            )
        if enrolled == 'true':
            qs = qs.filter(profile__is_face_enrolled=True)
        elif enrolled == 'false':
            qs = qs.filter(profile__is_face_enrolled=False)

        serializer = UserSerializer(qs, many=True)
        return Response({
            'count': qs.count(),
            'results': serializer.data
        })

    def create(self, request, *args, **kwargs):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/auth/users/<id>/  → Get user
    PUT    /api/auth/users/<id>/  → Update user (admin)
    DELETE /api/auth/users/<id>/  → Delete user (admin)
    """
    queryset = User.objects.select_related('profile__department').all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        user = self.get_object()

        # Update Django User fields
        for field in ['first_name', 'last_name', 'email']:
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save()

        # Update profile fields
        if hasattr(user, 'profile'):
            profile = user.profile
            for field in ['phone', 'role', 'department']:
                if field in request.data:
                    if field == 'department':
                        try:
                            profile.department_id = int(request.data[field])
                        except (ValueError, TypeError):
                            pass
                    else:
                        setattr(profile, field, request.data[field])
            profile.save()

        return Response(UserSerializer(user).data)

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response({'error': 'Admin access required.'}, status=403)
        return super().destroy(request, *args, **kwargs)


# ─── Department Views ──────────────────────────────────────────────────────────

class DepartmentListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/auth/departments/  → List all departments
    POST /api/auth/departments/  → Create department (admin)
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/DELETE /api/auth/departments/<id>/"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
```

---

## File 3 — `apps/accounts/urls.py`

```python
# backend/apps/accounts/urls.py

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('me/', views.MeView.as_view(), name='me'),

    # Users
    path('users/', views.UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),

    # Departments
    path('departments/', views.DepartmentListCreateView.as_view(), name='department-list'),
    path('departments/<int:pk>/', views.DepartmentDetailView.as_view(), name='department-detail'),
]
```

---

## Step — Enable JWT Token Blacklisting

For logout to work (blacklisting refresh tokens), you must add the blacklist app.

Update `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    'rest_framework_simplejwt.token_blacklist',   # ← ADD THIS
]
```

Then run:
```bash
python manage.py migrate
```

---

## Step — Test the Auth API

With your server running (`python manage.py runserver`), test in another terminal:

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "teacher001", "password": "teacher123"}'
```

Expected response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "teacher001",
    "full_name": "Rajesh Kumar",
    "profile": {
      "role": "TEACHER",
      "employee_id": "T001",
      "is_face_enrolled": false
    }
  }
}
```

### Get current user
```bash
curl http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer <access_token_here>"
```

### Create a user (Admin only)
```bash
curl -X POST http://localhost:8000/api/auth/users/ \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "CS2024002",
    "email": "ananya@college.edu",
    "first_name": "Ananya",
    "last_name": "Singh",
    "password": "student123",
    "employee_id": "CS2024002",
    "role": "STUDENT",
    "department_id": 1
  }'
```

---

## Bulk User Import (Optional — for production)

Create `backend/import_students.py`:

```python
# backend/import_students.py
# Usage: python import_students.py students.csv

import os
import sys
import csv
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'face_attendance.settings')
django.setup()

from django.contrib.auth.models import User
from apps.accounts.models import Department, UserProfile

def import_from_csv(filepath):
    """
    CSV format:
    username,first_name,last_name,email,employee_id,role,department_code,password
    CS2024001,Priya,Sharma,priya@college.edu,CS2024001,STUDENT,CS,student123
    """
    created = 0
    errors = []

    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                dept = Department.objects.get(code=row['department_code'])
            except Department.DoesNotExist:
                errors.append(f"Department not found: {row['department_code']}")
                continue

            if User.objects.filter(username=row['username']).exists():
                errors.append(f"User already exists: {row['username']}")
                continue

            user = User.objects.create_user(
                username=row['username'],
                email=row['email'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                password=row['password']
            )

            UserProfile.objects.create(
                user=user,
                employee_id=row['employee_id'],
                role=row.get('role', 'STUDENT'),
                department=dept
            )
            created += 1
            print(f"✅ Created: {user.get_full_name()} ({row['employee_id']})")

    print(f"\nDone! Created {created} users.")
    if errors:
        print(f"Errors ({len(errors)}):")
        for e in errors:
            print(f"  ❌ {e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python import_students.py students.csv")
        sys.exit(1)
    import_from_csv(sys.argv[1])
```

---

**Next →** `06_ATTENDANCE_API.md`
