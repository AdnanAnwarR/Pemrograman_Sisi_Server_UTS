# EXPLAIN ANALYZE untuk pengujian index. Jalankan SEBELUM dan SESUDAH index dipasang.
# Jalankan: docker compose exec -T app python manage.py shell < benchmarks/shell/bench_index.py
from catalog.models import Course

# Catatan: course dengan nomor kelipatan 5 berstatus tidak aktif, jadi
# "Performance Course 5000" mengembalikan 0 baris; "5001" mengembalikan 1 baris.
qs = Course.objects.filter(is_active=True, title="Performance Course 5001")
print("Jumlah hasil:", qs.count())
print(qs.explain(analyze=True))
