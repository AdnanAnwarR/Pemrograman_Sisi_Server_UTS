"""Test Minggu 5: bukti N+1, select_related/prefetch_related, index, dan generator data."""
from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from catalog.models import Assignment, Course, Enrollment, Lesson, Submission
from users.models import User


class QueryOptimizationTests(TestCase):
    N = 5

    @classmethod
    def setUpTestData(cls):
        cls.lecturer = User.objects.create_user(
            username="lec", password="x", role=User.Role.LECTURER
        )
        for i in range(cls.N):
            course = Course.objects.create(
                code=f"T{i:02d}", title=f"T{i}", lecturer=cls.lecturer
            )
            for order in range(1, 4):
                Lesson.objects.create(
                    course=course, title=f"L{order}", content="x", order=order
                )

    def test_n_plus_1_lecturer_before(self):
        with CaptureQueriesContext(connection) as ctx:
            for c in Course.objects.all():
                c.lecturer.username
        self.assertEqual(len(ctx.captured_queries), 1 + self.N)

    def test_select_related_lecturer_after(self):
        with CaptureQueriesContext(connection) as ctx:
            for c in Course.objects.select_related("lecturer"):
                c.lecturer.username
        self.assertEqual(len(ctx.captured_queries), 1)

    def test_n_plus_1_lessons_before(self):
        with CaptureQueriesContext(connection) as ctx:
            for c in Course.objects.all():
                [l.title for l in c.lessons.all()]
        self.assertEqual(len(ctx.captured_queries), 1 + self.N)

    def test_prefetch_related_lessons_after(self):
        with CaptureQueriesContext(connection) as ctx:
            for c in Course.objects.prefetch_related("lessons"):
                [l.title for l in c.lessons.all()]
        self.assertEqual(len(ctx.captured_queries), 2)

    def test_exists_count_values_annotate(self):
        self.assertFalse(Enrollment.objects.exists())
        self.assertEqual(Course.objects.count(), self.N)
        self.assertEqual(
            set(Course.objects.values("code", "title")[0]), {"code", "title"}
        )


class IndexTests(TestCase):
    def test_index_declared_on_model(self):
        fields = [tuple(i.fields) for i in Course._meta.indexes]
        self.assertIn(("is_active", "title"), fields)

    def test_index_exists_in_database(self):
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(
                cursor, Course._meta.db_table
            )
        cols = [tuple(c["columns"]) for c in constraints.values() if c["index"]]
        self.assertIn(("is_active", "title"), cols)


class GeneratorTests(TestCase):
    def test_generators_create_expected_data_and_are_repeatable(self):
        User.objects.create_user(username="lec", password="x", role="LECTURER")
        call_command("generate_performance_data", verbosity=0)
        self.assertEqual(Course.objects.filter(code__startswith="PERF").count(), 10000)

        def counts():
            return (
                User.objects.count(),
                Enrollment.objects.count(),
                Lesson.objects.count(),
                Assignment.objects.count(),
                Submission.objects.count(),
            )

        call_command("generate_relationship_data", verbosity=0)
        first = counts()
        # 1 dosen awal + 5 dosen + 50 mahasiswa = 56 user
        self.assertEqual(first, (56, 1000, 500, 200, 1000))

        # repeatable: dijalankan lagi tidak menambah data
        call_command("generate_performance_data", verbosity=0)
        call_command("generate_relationship_data", verbosity=0)
        self.assertEqual(counts(), first)
        self.assertEqual(Course.objects.filter(code__startswith="PERF").count(), 10000)
