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
