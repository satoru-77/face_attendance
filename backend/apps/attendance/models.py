from django.db import models
from django.contrib.auth.models import User


class Attendance(models.Model):

    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
        ('HALF_DAY', 'Half Day'),
    ]

    MODE_CHOICES = [
        ('KIOSK', 'Kiosk (Individual)'),
        ('CLASSROOM', 'Classroom (Bulk)'),
        ('MANUAL', 'Manual Override'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()

    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PRESENT')
    attendance_mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='KIOSK')

    # Face recognition confidence (0-100%)
    confidence_score = models.FloatField(default=0.0)

    # Capture info
    location = models.CharField(max_length=100, blank=True)

    # Check-in photo path (auto-deleted after 30 days)
    checkin_photo = models.ImageField(upload_to='checkin_photos/%Y/%m/', null=True, blank=True)

    # For classroom mode: which session created this
    class_session = models.ForeignKey(
        'ClassSession', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='attendances'
    )

    # Manual override info
    marked_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='marked_attendances'
    )
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # One record per user per day
        unique_together = ['user', 'date']
        ordering = ['-date', '-check_in_time']

    def __str__(self):
        return f"{self.user.username} — {self.date} — {self.status}"


class ClassSession(models.Model):
    """
    Represents a classroom bulk attendance capture event.
    One ClassSession creates many Attendance records.
    """
    # Who triggered this (teacher)
    teacher = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='class_sessions'
    )

    date = models.DateField()
    start_time = models.TimeField()

    # Room/location info
    location = models.CharField(max_length=100, blank=True)
    subject = models.CharField(max_length=100, blank=True)

    # Stats
    total_expected = models.IntegerField(default=0)
    total_detected = models.IntegerField(default=0)
    total_recognized = models.IntegerField(default=0)

    # The classroom photo used for this session
    classroom_photo = models.ImageField(
        upload_to='classroom_photos/%Y/%m/', null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f"Session — {self.date} {self.start_time} ({self.location})"

    @property
    def recognition_rate(self):
        if self.total_detected == 0:
            return 0
        return round((self.total_recognized / self.total_detected) * 100, 1)
