from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Course
from users.models import User


class Command(BaseCommand):
    help = "Buat dataset Course performa (10.000 course PERF) tanpa duplikasi"

    def handle(self, *args, **options):
        # 1. Cari dosen yang sudah tersedia
        lecturer = User.objects.filter(role="LECTURER").order_by("id").first()
        if lecturer is None:
            self.stderr.write(
                "Buat minimal satu User dengan role LECTURER terlebih dahulu "
                "(jalankan: python manage.py seed_demo)."
            )
            return

        # 2. Ambil kode Course performa yang sudah ada
        existing = set(
            Course.objects.filter(code__startswith="PERF").values_list(
                "code", flat=True
            )
        )

        # 3. Siapkan 10.000 Course
        rows = [
            Course(
                code=f"PERF{i:05d}",
                title=f"Performance Course {i}",
                lecturer=lecturer,
                is_active=(i % 5 != 0),
            )
            for i in range(10000)
            if f"PERF{i:05d}" not in existing
        ]

        # 4. Simpan secara batch ke PostgreSQL
        with transaction.atomic():
            Course.objects.bulk_create(rows, batch_size=500)

        # 5. Tampilkan hasil
        self.stdout.write(
            self.style.SUCCESS(
                f"Course baru: {len(rows)}; total Course: {Course.objects.count()}"
            )
        )
