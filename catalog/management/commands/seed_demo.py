from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from catalog.models import Assignment, Course, Enrollment, Lesson, Submission
from users.models import User


def get_or_create_user(username, email, password, role, **extra):
    """Buat user hanya jika belum ada (idempotent)."""
    user = User.objects.filter(username=username).first()
    if user:
        return user
    return User.objects.create_user(
        username=username, email=email, password=password, role=role, **extra
    )


class Command(BaseCommand):
    help = (
        "Membuat sample data (User, Course, Lesson, Enrollment, Assignment, "
        "Submission) secara idempotent."
    )

    def handle(self, *args, **options):
        # 1. USER
        get_or_create_user(
            "admin", "admin@gmail.com", "admin12345", User.Role.ADMIN,
            is_staff=True, is_superuser=True,
        )
        lecturer = get_or_create_user(
            "suprayogi", "suprayogi@gmail.com", "12345", User.Role.LECTURER
        )
        student = get_or_create_user(
            "fauzan", "fauzan@gmail.com", "12345", User.Role.STUDENT
        )

        # 2. COURSE
        courses = [
            ("PSS01", "Pemrograman Sisi Server", "Belajar backend development dengan Django."),
            ("PSS02", "Django Framework", "Mempelajari framework Django dan struktur project."),
            ("PSS03", "Django ORM", "Mempelajari database dan ORM menggunakan Django."),
            ("PSS04", "REST API", "Mempelajari pembuatan REST API dengan Django."),
            ("PSS05", "Docker", "Mempelajari containerisasi aplikasi Django."),
        ]
        for code, title, description in courses:
            Course.objects.get_or_create(
                code=code,
                defaults={
                    "title": title,
                    "description": description,
                    "lecturer": lecturer,
                },
            )
        course = Course.objects.get(code="PSS01")

        # 3. LESSON
        lessons = [
            "Pengenalan Backend",
            "Pola Arsitektur Backend",
            "Containerisasi dengan Docker",
        ]
        for order, title in enumerate(lessons, start=1):
            Lesson.objects.get_or_create(
                course=course,
                order=order,
                defaults={"title": title, "content": f"Materi: {title}"},
            )

        # 4. ENROLLMENT
        Enrollment.objects.get_or_create(student=student, course=course)

        # 5. ASSIGNMENT
        assignment1, _ = Assignment.objects.get_or_create(
            course=course,
            title="Tugas Django ORM",
            defaults={
                "description": "Implementasikan model dan relationship menggunakan Django ORM.",
                "deadline": timezone.now() + timedelta(days=7),
            },
        )
        assignment2, _ = Assignment.objects.get_or_create(
            course=course,
            title="Tugas REST API",
            defaults={
                "description": "Buat REST API sederhana menggunakan Django.",
                "deadline": timezone.now() + timedelta(days=14),
            },
        )

        # 6. SUBMISSION
        Submission.objects.get_or_create(
            assignment=assignment1,
            student=student,
            defaults={
                "content": "Saya telah menyelesaikan implementasi Django ORM.",
                "grade": 87.5,
            },
        )
        Submission.objects.get_or_create(
            assignment=assignment2,
            student=student,
            defaults={
                "content": "Saya telah menyelesaikan REST API menggunakan Django.",
                "grade": 90.0,
            },
        )

        self.stdout.write(self.style.SUCCESS("Sample data berhasil dibuat."))
