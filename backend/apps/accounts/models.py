from django.db import models
from django.contrib.auth.models import User


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    head = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='headed_department'
    )
    building = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.code} — {self.name}"


class UserProfile(models.Model):

    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('TEACHER', 'Teacher'),
        ('STUDENT', 'Student'),
        ('STAFF', 'Staff'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='members'
    )
    employee_id = models.CharField(max_length=50, unique=True)   # e.g. CS2024001
    phone = models.CharField(max_length=15, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')

    # Face enrollment
    is_face_enrolled = models.BooleanField(default=False)
    enrollment_date = models.DateTimeField(null=True, blank=True)

    # Profile photo (thumbnail, not used for recognition)
    profile_photo = models.ImageField(
        upload_to='profile_photos/', null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['employee_id']

    def __str__(self):
        return f"{self.employee_id} — {self.user.get_full_name()}"

    @property
    def full_name(self):
        return self.user.get_full_name()


class FaceEncoding(models.Model):
    """
    Stores the 512-dimensional face embedding for each enrolled photo.
    Each student has up to 10 encodings (one per enrollment photo).
    Also stores a final averaged embedding.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='face_encodings')
    
    # The 512-D embedding vector stored as JSON array
    embedding = models.JSONField()

    # Which photo number in enrollment sequence (1-10), 0 = averaged
    photo_number = models.IntegerField(default=0)

    # Quality score from InsightFace (0-1, higher is better)
    quality_score = models.FloatField(default=0.0)

    # Is this the final averaged embedding used for matching?
    is_primary = models.BooleanField(default=False)

    # Path to the original enrollment photo (auto-deleted after 30 days)
    photo_path = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['user', 'photo_number']

    def __str__(self):
        label = "Primary" if self.is_primary else f"Photo {self.photo_number}"
        return f"{self.user.username} — {label}"
