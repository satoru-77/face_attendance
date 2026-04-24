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
