# AFTER: Course + Lesson dengan prefetch_related()
# Jalankan: docker compose exec -T app python manage.py shell < benchmarks/shell/bench_lesson_after.py
import time
from django.db import connection
from django.test.utils import CaptureQueriesContext
from catalog.models import Course

start = time.perf_counter()
with CaptureQueriesContext(connection) as ctx:
    courses = (
        Course.objects.filter(code__startswith="PERF")
        .order_by("code")
        .prefetch_related("lessons")[:50]
    )
    for course in courses:
        titles = [lesson.title for lesson in course.lessons.all()]
elapsed = time.perf_counter() - start

print("Jumlah Course:", len(courses))
print("Jumlah query AFTER:", len(ctx.captured_queries))
print("Waktu eksekusi:", round(elapsed, 4), "detik")
