# Simple LMS — Minggu 4 & 5: Django ORM + Database Optimization

Pemrograman Sisi Server (A11.64707) — Modul Praktikum 4 (ORM) dan 5 (Database Optimization).
Django + PostgreSQL berjalan penuh di Docker (tidak perlu install Django/PostgreSQL di host).

## Struktur Project

```
.
├── manage.py
├── config/                      # pengaturan project Django
├── users/                       # Custom User (role: ADMIN, LECTURER, STUDENT)
├── catalog/                     # model LMS, admin, test, dan management command
│   ├── models.py
│   ├── tests.py / test_performance.py
│   ├── migrations/
│   └── management/commands/
│       ├── seed_demo.py                   # sample data Minggu 4
│       ├── generate_performance_data.py   # 10.000 Course (Minggu 5)
│       ├── generate_relationship_data.py  # data relasi LMS (Minggu 5)
│       └── benchmark_week5.py             # benchmark BEFORE vs AFTER otomatis
├── benchmarks/
│   ├── shell/                   # skrip untuk Django Shell (lihat bagian Minggu 5)
│   └── ...                      # hasil benchmark dan laporan
├── requirements.txt / Dockerfile / compose.yaml
└── .env                         # tidak di-commit (contoh: .env.example)
```

## Menjalankan Project

1. Buat file `.env` di root project (salin dari `.env.example`):
   ```
   DB_NAME=lms_db
   DB_USER=lms_user
   DB_PASSWORD=lms_password
   REDIS_URL=redis://redis:6379/1
   ```
2. `docker compose build` lalu `docker compose up -d` dan `docker compose ps` (service `app`, `db`, `redis` harus **Up**). Aplikasi di http://localhost:8000.
3. Hentikan container dengan `docker compose down`. Tambahkan `-v` hanya jika ingin menghapus seluruh data database.

## Model
`User` (role ADMIN/LECTURER/STUDENT), `Course`, `Lesson`, `Enrollment`, `Assignment`, `Submission`.

## Perintah Minggu 4
```bash
docker compose build
docker compose up -d
docker compose ps

docker compose exec app python manage.py migrate
docker compose exec app python manage.py check
docker compose exec app python manage.py seed_demo      # aman dijalankan berulang (idempotent)
docker compose exec app python manage.py createsuperuser
```
Admin: http://localhost:8000/admin/ (seed membuat user `admin` / `admin12345` untuk development).

Pastikan superuser ber-role ADMIN:
```bash
docker compose exec app python manage.py shell
>>> from users.models import User
>>> u = User.objects.get(username="admin"); u.role = User.Role.ADMIN; u.save()
```

## Test (minimal 3, total 18)
```bash
docker compose exec app python manage.py test catalog
```

## Verifikasi versi
```bash
docker compose exec app python --version
docker compose exec app python -m django --version
docker compose exec db psql --version
docker compose exec db psql -U lms_user -d lms_db
```

## Latihan ORM (Django Shell)
```python
from django.db import connection, reset_queries
from catalog.models import Course

course = Course.objects.get(code="PSS01")
course.lessons.all()                                   # reverse FK traversal
Course.objects.active()                                # custom QuerySet/Manager

reset_queries()
for c in Course.objects.all(): c.lecturer.username     # N+1
print(len(connection.queries))
reset_queries()
for c in Course.objects.select_related("lecturer"): c.lecturer.username
print(len(connection.queries))                         # 1 query
# prefetch_related("lessons") untuk relasi reverse/banyak
```

## Catatan
- `.env` hanya untuk development lokal; jangan commit credential asli (sudah ada di `.gitignore`).
- Custom User didefinisikan sebelum migration pertama (`AUTH_USER_MODEL = "users.User"`).
- Migration sudah disertakan di repo agar setup dapat direproduksi.

## Minggu 5 — Database Optimization

Dependency baru (`django-debug-toolbar`, `django-redis`) dan service `redis` sudah ada, jadi rebuild dulu:
```bash
docker compose build app
docker compose up -d
docker compose exec app python manage.py migrate        # termasuk index Course(is_active, title)
```

### 1. Buat dataset (repeatable, aman dijalankan berulang)
```bash
docker compose exec app python manage.py seed_demo                       # jika belum ada dosen
docker compose exec app python manage.py generate_performance_data       # 10.000 Course PERF
docker compose exec app python manage.py generate_relationship_data      # 5 dosen, 50 mhs, 1.000 enrollment, 500 lesson, 200 assignment, 1.000 submission
```

### 2. Ulangi benchmark BEFORE vs AFTER
```bash
docker compose exec app python manage.py benchmark_week5
```
Hasil ditulis ke `benchmarks/hasil_benchmark.md` dan `.json`. Command ini mengukur:
- Course + Lecturer: N+1 vs `select_related()`
- Course + Lesson: N+1 vs `prefetch_related()`
- Index `(is_active, title)`: `EXPLAIN ANALYZE` dengan index dilepas sementara vs dipasang (index dikembalikan otomatis)

Waktu bergantung komputer; jumlah query dan jenis scan (Seq Scan -> Index Scan) yang perlu dibandingkan.

### 3. Profiling manual (Django Shell)
```python
from django.db import connection
from django.test.utils import CaptureQueriesContext
from catalog.models import Course

with CaptureQueriesContext(connection) as ctx:
    rows = [(c.title, c.lecturer.username)
            for c in Course.objects.filter(code__startswith="PERF").order_by("code")[:100]]
print(len(rows), len(ctx.captured_queries))   # BEFORE: 101 query
```
Debug Toolbar: buka http://localhost:8000/admin/ saat `DEBUG=True` (jika tidak muncul di Docker, pakai `CaptureQueriesContext`).


### 4. Skrip Django Shell (bukti BEFORE/AFTER untuk laporan)
Skrip di `benchmarks/shell/` mencetak jumlah Course, jumlah query, dan waktu eksekusi. Jalankan dari root project dengan data dan kondisi yang sama; waktu berbeda di tiap komputer, jadi ulangi beberapa kali.
```bash
# Course + Lecturer (select_related)
docker compose exec -T app python manage.py shell < benchmarks/shell/bench_lecturer_before.py
docker compose exec -T app python manage.py shell < benchmarks/shell/bench_lecturer_after.py

# Course + Lesson (prefetch_related)
docker compose exec -T app python manage.py shell < benchmarks/shell/bench_lesson_before.py
docker compose exec -T app python manage.py shell < benchmarks/shell/bench_lesson_after.py

# exists(), count(), values(), annotate()
docker compose exec -T app python manage.py shell < benchmarks/shell/bench_lab_d.py
```

### 5. EXPLAIN sebelum dan sesudah index (lewat migrasi)
Index ada di migrasi `catalog/0003`. Untuk membandingkan secara manual:
```bash
# BEFORE: lepas index
docker compose exec app python manage.py migrate catalog 0002
docker compose exec -T app python manage.py shell < benchmarks/shell/bench_index.py

# AFTER: pasang index kembali
docker compose exec app python manage.py migrate
docker compose exec -T app python manage.py shell < benchmarks/shell/bench_index.py
```
(`benchmark_week5` di atas melakukan hal yang sama secara otomatis tanpa menyentuh migrasi.)

### Catatan temuan
Generator membuat course dengan `i % 5 == 0` tidak aktif, sehingga `title="Performance Course 5000"` + `is_active=True`
mengembalikan 0 baris. Benchmark juga menguji judul aktif (`...5001`) yang mengembalikan 1 baris.

Laporan PDF: `benchmarks/Laporan_Optimasi_Database_Minggu5.pdf` (isi Kelas dan link repository sebelum dikumpulkan).
