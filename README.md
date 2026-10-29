# Simple LMS — Minggu 4: Django Framework & ORM

Pemrograman Sisi Server (A11.64707) — Modul Praktikum 4.
Django + PostgreSQL berjalan penuh di Docker (tidak perlu install Django/PostgreSQL di host).

## Model
`User` (role ADMIN/LECTURER/STUDENT), `Course`, `Lesson`, `Enrollment`, `Assignment`, `Submission`.

## Cara menjalankan
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

## Test (minimal 3, total 10)
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
