# Automated testing
from datetime import timedelta

from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from catalog.models import Assignment, Course, Enrollment, Lesson, Submission
from users.models import User


class CourseTestCase(TestCase):
    def setUp(self):
        self.lecturer = User.objects.create_user(
            username="testlecturer",
            password="test12345",
            role="LECTURER",
        )

    # TEST 1: Course berhasil dibuat
    def test_course_created(self):
        course = Course.objects.create(
            code="TEST01",
            title="Test Course",
            lecturer=self.lecturer,
        )
        self.assertEqual(course.code, "TEST01")

    # TEST 2: Code Course harus unik
    def test_course_code_unique(self):
        Course.objects.create(
            code="TEST01",
            title="Course Pertama",
            lecturer=self.lecturer,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Course.objects.create(
                    code="TEST01",
                    title="Course Kedua",
                    lecturer=self.lecturer,
                )

    # TEST 3: Lesson berelasi dengan Course
    def test_lesson_relationship(self):
        course = Course.objects.create(
            code="TEST02",
            title="Course Django",
            lecturer=self.lecturer,
        )
        lesson = Lesson.objects.create(
            course=course,
            title="Pengenalan Django",
            order=1,
        )
        self.assertEqual(lesson.course, course)
        self.assertEqual(course.lessons.count(), 1)


class ExtraModelTests(TestCase):
    """Test tambahan di luar minimal tiga test."""

    def setUp(self):
        self.lecturer = User.objects.create_user(
            username="dosen", password="x", role=User.Role.LECTURER
        )
        self.student = User.objects.create_user(
            username="mhs", password="x", role=User.Role.STUDENT
        )
        self.course = Course.objects.create(
            code="X01", title="Course X", lecturer=self.lecturer
        )

    def test_default_role_is_student(self):
        user = User.objects.create_user(username="baru", password="x")
        self.assertEqual(user.role, User.Role.STUDENT)

    def test_enrollment_unique(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Enrollment.objects.create(student=self.student, course=self.course)

    def test_lesson_order_unique_per_course(self):
        Lesson.objects.create(course=self.course, title="A", content="a", order=1)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Lesson.objects.create(course=self.course, title="B", content="b", order=1)

    def test_submission_relationship(self):
        assignment = Assignment.objects.create(
            course=self.course,
            title="Tugas 1",
            deadline=timezone.now() + timedelta(days=1),
        )
        Submission.objects.create(
            assignment=assignment, student=self.student, content="ok", grade=80
        )
        self.assertEqual(assignment.submissions.count(), 1)
        self.assertEqual(self.student.submissions.count(), 1)

    def test_custom_manager_active(self):
        Course.objects.create(
            code="X02", title="Nonaktif", lecturer=self.lecturer, is_active=False
        )
        self.assertEqual(Course.objects.active().count(), 1)
        self.assertEqual(Course.objects.taught_by(self.lecturer).count(), 2)

    def test_select_related_uses_one_query(self):
        with self.assertNumQueries(1):
            for c in Course.objects.select_related("lecturer"):
                c.lecturer.username

    def test_seed_demo_is_idempotent(self):
        call_command("seed_demo", verbosity=0)
        first = (Course.objects.count(), Lesson.objects.count(),
                 Assignment.objects.count(), Submission.objects.count(),
                 Enrollment.objects.count())
        call_command("seed_demo", verbosity=0)
        second = (Course.objects.count(), Lesson.objects.count(),
                  Assignment.objects.count(), Submission.objects.count(),
                  Enrollment.objects.count())
        self.assertEqual(first, second)
