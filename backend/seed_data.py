import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'face_attendance.settings')
django.setup()

from django.contrib.auth.models import User
from apps.accounts.models import Department, UserProfile

# Create departments
cs = Department.objects.get_or_create(name='Computer Science', code='CS', building='Block A')[0]
ec = Department.objects.get_or_create(name='Electronics', code='EC', building='Block B')[0]

print(f"Created departments: {cs}, {ec}")

# Create a test teacher
user, created = User.objects.get_or_create(
    username='teacher001',
    defaults={
        'first_name': 'Rajesh',
        'last_name': 'Kumar',
        'email': 'rajesh@college.edu',
    }
)
if created:
    user.set_password('teacher123')
    user.save()
    UserProfile.objects.create(
        user=user,
        department=cs,
        employee_id='T001',
        role='TEACHER',
        phone='9876543210'
    )
    print("Created teacher: teacher001 / teacher123")

# Create a test student
student, created = User.objects.get_or_create(
    username='CS2024001',
    defaults={
        'first_name': 'Priya',
        'last_name': 'Sharma',
        'email': 'priya@college.edu',
    }
)
if created:
    student.set_password('student123')
    student.save()
    UserProfile.objects.create(
        user=student,
        department=cs,
        employee_id='CS2024001',
        role='STUDENT',
    )
    print("Created student: CS2024001 / student123")

print("Seed data complete!")
