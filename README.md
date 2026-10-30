# Simple LMS: Pemrograman Sisi Server

Project latihan Simple LMS untuk mata kuliah Pemrograman Sisi Server. Dibangun dengan Django 5.2 dan PostgreSQL 17. Seluruh runtime dijalankan di Docker Compose, jadi Django dan PostgreSQL tidak perlu di-install di komputer host. Redis 7 juga disertakan untuk cache dan Django Debug Toolbar dipakai untuk profiling query.

- **Minggu 4:** Django, ORM, Custom User, dan model inti LMS (`Course`, `Lesson`, `Enrollment`, `Assignment`, `Submission`).
- **Minggu 5:** optimasi database (N+1 query, `select_related`, `prefetch_related`, `EXPLAIN ANALYZE`, dan index).

## Struktur Project

```
.
├── manage.py
├── config/                      # pengaturan project Django
├── users/                       # Custom User (role: ADMIN, LECTURER, STUDENT)
├── catalog/                     # model LMS, admin, test, dan management command
│   ├── models.py
│   ├── tests.py                 # test model dan relasi
│   ├── test_performance.py      # test N+1, select_related, prefetch_related, index
│   ├── migrations/
│   │   ├── 0001_initial.py
│   │   ├── 0002_initial.py
│   │   └── 0003_course_catalog_cou_is_acti_d7f8f8_idx.py
│   └── management/commands/
│       ├── seed_demo.py                   # sample data Minggu 4
│       ├── generate_performance_data.py   # 10.000 Course (Minggu 5)
│       ├── generate_relationship_data.py  # data relasi LMS (Minggu 5)
│       └── benchmark_week5.py             # benchmark BEFORE vs AFTER otomatis
├── benchmarks/
│   ├── shell/                   # skrip benchmark untuk Django Shell
│   │   ├── bench_lecturer_before.py
│   │   ├── bench_lecturer_after.py
│   │   ├── bench_lesson_before.py
│   │   ├── bench_lesson_after.py
│   │   ├── bench_lab_d.py
│   │   └── bench_index.py
│   ├── hasil_benchmark.md       # hasil benchmark (ringkasan)
│   ├── hasil_benchmark.json     # hasil benchmark (data mentah)
│   ├── hasil_test.txt           # output test
│   ├── checkpoint1.txt
│   ├── labD.txt
│   └── Laporan_Optimasi_Database_Minggu5.pdf
├── requirements.txt
├── Dockerfile
├── compose.yaml
├── .env.example                 # contoh isi .env (di-commit)
├── .env                         # tidak di-commit
└── .gitignore
```

## File yang Tidak Ikut Di-push

File `.env` **tidak di-commit** karena berisi kredensial lokal. Yang di-commit hanya `.env.example` sebagai contoh. File lain yang juga diabaikan ada di `.gitignore`:

```
.env
db.sqlite3
.venv/
venv/
__pycache__/
*.py[cod]
```

Database tidak ikut di-push karena datanya disimpan di Docker volume `postgres_data`. Untuk mendapatkannya, cukup jalankan migrasi dan generator data seperti di bawah.

## Menjalankan Project

### 1. Clone repository

```bash
git clone <URL_REPOSITORY_ANDA>
cd minggu-4
```

### 2. Buat file `.env`

File `.env` tidak ikut repository. Salin dari `.env.example`, lalu sesuaikan bila perlu:

```bash
cp .env.example .env
```

Isi `.env`:

```env
DB_NAME=lms_db
DB_USER=lms_user
DB_PASSWORD=lms_password
REDIS_URL=redis://redis:6379/1
```

`DB_HOST` tidak perlu diisi karena default-nya `db` (nama service PostgreSQL di Compose). Password di atas hanya contoh untuk development lokal; jangan pakai untuk production.

### 3. Build dan jalankan container

```bash
docker compose build
docker compose up -d
docker compose ps
```

Service `app`, `db`, dan `redis` harus berstatus **Up**. Aplikasi berjalan di http://localhost:8000.

### 4. Migrasi database

```bash
docker compose exec app python manage.py migrate
docker compose exec app python manage.py check
```

### 5. Isi sample data Minggu 4 (opsional)

```bash
docker compose exec app python manage.py seed_demo
```

Perintah ini aman dijalankan berulang (idempotent) dan membuat user `admin` / `admin12345` untuk development.

### 6. Buat superuser (opsional, untuk Django Admin)

```bash
docker compose exec app python manage.py createsuperuser
```

Login di http://localhost:8000/admin/. Role superuser dapat diubah menjadi ADMIN lewat Django Shell:

```bash
docker compose exec app python manage.py shell
```

```python
from users.models import User
u = User.objects.get(username="admin")
u.role = User.Role.ADMIN
u.save()
```

## Membuat Dataset Pengujian (Minggu 5)

Perintah di bawah aman dijalankan berulang (repeatable): data yang sudah ada tidak dibuat ulang. Urutannya harus seperti ini.

### 1. Buat 10.000 Course (kode `PERF00000` sampai `PERF09999`)

Perintah ini membutuhkan minimal satu User dengan role LECTURER (bisa dari `seed_demo`).

```bash
docker compose exec app python manage.py generate_performance_data
```

### 2. Buat data relasi untuk 100 Course PERF pertama

```bash
docker compose exec app python manage.py generate_relationship_data
```

Data yang dibuat: 5 dosen simulasi, 50 mahasiswa simulasi, 1.000 Enrollment, 500 Lesson, 200 Assignment, dan 1.000 Submission.

### 3. Cek jumlah data

```bash
docker compose exec app python manage.py shell -c "from catalog.models import Course; print(Course.objects.count())"
```

Hasil yang diharapkan: `10005` Course (10.000 PERF + 5 Course dari `seed_demo`).

## Mengulang Benchmark

Jalankan dari root project. Gunakan data dan kondisi yang sama saat membandingkan BEFORE dan AFTER. Waktu eksekusi bisa sedikit berbeda di tiap komputer, jadi sebaiknya jalankan beberapa kali dan catat rata-ratanya.

Cara paling praktis, semua benchmark dijalankan otomatis dan hasilnya ditulis ke `benchmarks/hasil_benchmark.md` dan `.json`:

```bash
docker compose exec app python manage.py benchmark_week5
```

Atau jalankan skrip shell satu per satu:

### Course + Lecturer (`select_related`)

```bash
docker compose exec -T app python manage.py shell < benchmarks/shell/bench_lecturer_before.py
docker compose exec -T app python manage.py shell < benchmarks/shell/bench_lecturer_after.py
```

### Course + Lesson (`prefetch_related`)

```bash
docker compose exec -T app python manage.py shell < benchmarks/shell/bench_lesson_before.py
docker compose exec -T app python manage.py shell < benchmarks/shell/bench_lesson_after.py
```

### Teknik lain: `exists`, `count`, `values`, `annotate`

```bash
docker compose exec -T app python manage.py shell < benchmarks/shell/bench_lab_d.py
```

### Database Index (`EXPLAIN`)

Index didefinisikan di `catalog/models.py` pada class `Meta` milik `Course`:

```python
indexes = [
    models.Index(fields=["is_active", "title"]),
]
```

Index tersebut dibuat oleh migrasi `catalog/0003`. Untuk membandingkan sebelum dan sesudah index, lepas migrasi index, jalankan benchmark, pasang kembali, lalu jalankan benchmark lagi:

```bash
# BEFORE: lepas index
docker compose exec app python manage.py migrate catalog 0002
docker compose exec -T app python manage.py shell < benchmarks/shell/bench_index.py

# AFTER: pasang index
docker compose exec app python manage.py migrate
docker compose exec -T app python manage.py shell < benchmarks/shell/bench_index.py
```

Catatan: `benchmark_week5` melakukan perbandingan index yang sama secara otomatis tanpa menyentuh migrasi.

## Hasil Benchmark

Hasil dari satu kali percobaan pada dataset 10.005 Course dengan PostgreSQL 17.11. Waktu = median dari 7 kali pengulangan setelah 1x warm-up. Angka waktu dapat berbeda pada komputer lain.

| Percobaan | BEFORE | AFTER |
|---|---|---|
| Course + Lecturer (100 Course) | 101 query, 44,176 ms | 1 query, 2,785 ms |
| Course + Lesson (50 Course) | 51 query, 32,375 ms | 2 query, 4,200 ms |
| Index (`is_active`, `title`) | Seq Scan, cost 239.07, 0,480 ms | Index Scan, cost 8.31, 0,014 ms |

Ringkasan dataset: 10.005 Course, 6 Lecturer, 51 Student, 503 Lesson, 1.001 Enrollment, 202 Assignment, 1.002 Submission.

Kesimpulan singkat:

- `select_related()` memakai SQL JOIN, cocok untuk relasi ForeignKey (Course ke Lecturer). Query turun dari 101 menjadi 1.
- `prefetch_related()` mengambil relasi satu-ke-banyak dengan satu query tambahan (Course ke Lesson). Query turun dari 51 menjadi 2.
- Index mengubah rencana query dari Seq Scan menjadi Index Scan. Trade-off: ruang penyimpanan tambahan dan biaya INSERT, UPDATE, dan DELETE yang lebih besar.

Detail lengkap (termasuk output `EXPLAIN ANALYZE`) ada di `benchmarks/hasil_benchmark.md`.

## Menjalankan Test

```bash
docker compose exec app python manage.py test catalog
```

Hasil yang diharapkan: `Ran 18 tests ... OK` (10 test model di `tests.py` dan 8 test optimasi di `test_performance.py`).

## Verifikasi Versi

```bash
docker compose exec app python --version
docker compose exec app python -m django --version
docker compose exec db psql --version
```

## Catatan

- File `.env` tidak boleh di-commit. Gunakan `.env.example` sebagai template.
- File migrasi di `users/migrations/` dan `catalog/migrations/` ikut di-commit agar project dapat direproduksi.
- Custom User didefinisikan sebelum migration pertama (`AUTH_USER_MODEL = "users.User"`).
- Untuk menghentikan container: `docker compose down`. Tambahkan `-v` hanya jika ingin menghapus seluruh data database (volume `postgres_data`).
- Jika port `8000` sudah dipakai aplikasi lain, ubah mapping port di `compose.yaml` (misalnya `"8001:8000"`).
