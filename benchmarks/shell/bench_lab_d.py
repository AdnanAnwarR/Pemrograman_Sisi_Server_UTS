# Lab D: exists(), count(), values(), annotate()
# Jalankan: docker compose exec -T app python manage.py shell < benchmarks/shell/bench_lab_d.py
from django.db.models import Count
from catalog.models import Course, Enrollment

course = Course.objects.get(code="PERF00001")
print("A. Ada mahasiswa terdaftar:", Enrollment.objects.filter(course=course).exists())
print("B. Jumlah Course simulasi:", Course.objects.filter(code__startswith="PERF").count())

print("C. values():")
for row in Course.objects.filter(code__startswith="PERF").values("code", "title")[:5]:
    print("  ", row)

print("D. annotate():")
qs = (
    Course.objects.filter(code__startswith="PERF")
    .annotate(jumlah_mahasiswa=Count("enrollments"))
    .order_by("code")[:5]
)
for c in qs:
    print("  ", c.code, c.jumlah_mahasiswa)
