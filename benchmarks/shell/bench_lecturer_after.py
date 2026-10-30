# AFTER: Course + Lecturer dengan select_related()
# Jalankan: docker compose exec -T app python manage.py shell < benchmarks/shell/bench_lecturer_after.py
import time
from django.db import connection
from django.test.utils import CaptureQueriesContext
from catalog.models import Course

start = time.perf_counter()
with CaptureQueriesContext(connection) as ctx:
    result = []
    courses = (
        Course.objects.filter(code__startswith="PERF")
        .order_by("code")
        .select_related("lecturer")[:100]
    )
    for course in courses:
        result.append((course.title, course.lecturer.username))
elapsed = time.perf_counter() - start

print("Jumlah Course:", len(result))
print("Jumlah Query SQL:", len(ctx.captured_queries))
print("Waktu eksekusi:", round(elapsed, 4), "detik")
