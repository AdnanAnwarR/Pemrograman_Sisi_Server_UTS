# BEFORE: Course + Lecturer tanpa optimasi (N+1)
# Jalankan: docker compose exec -T app python manage.py shell < benchmarks/shell/bench_lecturer_before.py
import time
from django.db import connection
from django.test.utils import CaptureQueriesContext
from catalog.models import Course

start = time.perf_counter()
with CaptureQueriesContext(connection) as ctx:
    result = []
    for course in Course.objects.filter(code__startswith="PERF").order_by("code")[:100]:
        result.append((course.title, course.lecturer.username))
elapsed = time.perf_counter() - start

print("Jumlah Course:", len(result))
print("Jumlah Query SQL:", len(ctx.captured_queries))
print("Waktu eksekusi:", round(elapsed, 4), "detik")
