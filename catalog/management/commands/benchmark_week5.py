"""Benchmark BEFORE vs AFTER untuk Minggu 5 (N+1, prefetch, index).

Jalankan setelah dataset dibuat:
    docker compose exec app python manage.py benchmark_week5

Hasil ditulis ke benchmarks/hasil_benchmark.md dan benchmarks/hasil_benchmark.json.
Semua angka diukur langsung dari database; tidak ada angka yang ditulis manual.
"""
import json
import re
import statistics
import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.models import Count
from django.test.utils import CaptureQueriesContext

from catalog.models import (
    Assignment,
    Course,
    Enrollment,
    Lesson,
    Submission,
)
from users.models import User

REPEAT = 7  # jumlah pengulangan; yang dilaporkan adalah median


def measure(fn):
    """Jalankan fn() REPEAT kali (1x warm-up dibuang). Kembalikan (query, median_ms)."""
    fn()  # warm-up
    times, queries = [], None
    for _ in range(REPEAT):
        with CaptureQueriesContext(connection) as ctx:
            start = time.perf_counter()
            result = fn()
            elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
        queries = len(ctx.captured_queries)
    return {
        "queries": queries,
        "median_ms": round(statistics.median(times), 3),
        "min_ms": round(min(times), 3),
        "max_ms": round(max(times), 3),
        "rows": result,
    }


def improvement(before, after):
    if not before:
        return 0.0
    return round((before - after) / before * 100, 1)


def explain_stats(qs, analyze=True):
    """EXPLAIN (ANALYZE) beberapa kali; kembalikan plan teks + median execution time."""
    plan, exec_times = "", []
    for _ in range(REPEAT):
        plan = qs.explain(analyze=analyze)
        m = re.search(r"Execution Time: ([0-9.]+) ms", plan)
        if m:
            exec_times.append(float(m.group(1)))
    return plan, (round(statistics.median(exec_times), 3) if exec_times else None)


class Command(BaseCommand):
    help = "Benchmark BEFORE vs AFTER: select_related, prefetch_related, index"

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            raise CommandError("Benchmark ini harus dijalankan pada PostgreSQL.")
        n_perf = Course.objects.filter(code__startswith="PERF").count()
        if n_perf < 10000:
            raise CommandError(
                "Dataset belum lengkap. Jalankan generate_performance_data dan "
                "generate_relationship_data terlebih dahulu."
            )

        with connection.cursor() as cur:
            cur.execute("SELECT version()")
            pg_version = cur.fetchone()[0]

        data = {
            "postgres": pg_version,
            "repeat": REPEAT,
            "dataset": {
                "Course (total)": Course.objects.count(),
                "Course PERF": n_perf,
                "Lecturer": User.objects.filter(role="LECTURER").count(),
                "Student": User.objects.filter(role="STUDENT").count(),
                "Lesson": Lesson.objects.count(),
                "Enrollment": Enrollment.objects.count(),
                "Assignment": Assignment.objects.count(),
                "Submission": Submission.objects.count(),
            },
        }

        # ------------------------------------------------------------------
        # 1. Course + Lecturer (select_related)
        # ------------------------------------------------------------------
        def lecturer_before():
            qs = Course.objects.filter(code__startswith="PERF").order_by("code")[:100]
            return len([(c.title, c.lecturer.username) for c in qs])

        def lecturer_after():
            qs = (
                Course.objects.filter(code__startswith="PERF")
                .order_by("code")
                .select_related("lecturer")[:100]
            )
            return len([(c.title, c.lecturer.username) for c in qs])

        b, a = measure(lecturer_before), measure(lecturer_after)
        data["course_lecturer"] = {
            "before": b,
            "after": a,
            "query_improvement_pct": improvement(b["queries"], a["queries"]),
            "time_improvement_pct": improvement(b["median_ms"], a["median_ms"]),
        }

        # ------------------------------------------------------------------
        # 2. Course + Lesson (prefetch_related)
        # ------------------------------------------------------------------
        def lesson_before():
            qs = Course.objects.filter(code__startswith="PERF").order_by("code")[:50]
            return len([[l.title for l in c.lessons.all()] for c in qs])

        def lesson_after():
            qs = (
                Course.objects.filter(code__startswith="PERF")
                .order_by("code")
                .prefetch_related("lessons")[:50]
            )
            return len([[l.title for l in c.lessons.all()] for c in qs])

        b, a = measure(lesson_before), measure(lesson_after)
        data["course_lesson"] = {
            "before": b,
            "after": a,
            "query_improvement_pct": improvement(b["queries"], a["queries"]),
            "time_improvement_pct": improvement(b["median_ms"], a["median_ms"]),
        }

        # ------------------------------------------------------------------
        # 3. Teknik lain (Lab D)
        # ------------------------------------------------------------------
        course = Course.objects.get(code="PERF00001")
        lab_d = {}
        with CaptureQueriesContext(connection) as ctx:
            lab_d["exists"] = Enrollment.objects.filter(course=course).exists()
        lab_d["exists_queries"] = len(ctx.captured_queries)
        with CaptureQueriesContext(connection) as ctx:
            lab_d["count"] = Course.objects.filter(code__startswith="PERF").count()
        lab_d["count_queries"] = len(ctx.captured_queries)
        with CaptureQueriesContext(connection) as ctx:
            lab_d["values"] = list(
                Course.objects.filter(code__startswith="PERF").values("code", "title")[:5]
            )
        lab_d["values_queries"] = len(ctx.captured_queries)
        with CaptureQueriesContext(connection) as ctx:
            lab_d["annotate"] = [
                (c.code, c.jumlah_mahasiswa)
                for c in Course.objects.filter(code__startswith="PERF")
                .annotate(jumlah_mahasiswa=Count("enrollments"))
                .order_by("code")[:5]
            ]
        lab_d["annotate_queries"] = len(ctx.captured_queries)
        data["lab_d"] = lab_d

        # ------------------------------------------------------------------
        # 4. Index (EXPLAIN ANALYZE sebelum vs sesudah)
        # ------------------------------------------------------------------
        index = next(i for i in Course._meta.indexes)
        # Catatan: i % 5 == 0 -> is_active=False, sehingga "Performance Course 5000"
        # TIDAK aktif dan query pada modul mengembalikan 0 baris. Kita uji juga
        # judul aktif ("Performance Course 5001") yang mengembalikan 1 baris.
        cases = [
            ("Query modul (judul 5000, is_active=True)", "Performance Course 5000"),
            ("Query judul aktif (judul 5001, is_active=True)", "Performance Course 5001"),
        ]
        qs_code = Course.objects.filter(code="PERF05000")

        with connection.cursor() as cur:
            cur.execute("SELECT to_regclass(%s)", [index.name])
            had_index = cur.fetchone()[0] is not None

        data["index"] = {"name": index.name, "fields": list(index.fields), "cases": []}
        before = {}
        try:
            # BEFORE: index sementara dilepas, kondisi data & query identik
            if had_index:
                with connection.schema_editor() as editor:
                    editor.remove_index(Course, index)
            with connection.cursor() as cur:
                cur.execute("ANALYZE catalog_course")
            for label, title in cases:
                qs = Course.objects.filter(is_active=True, title=title)
                plan, t = explain_stats(qs)
                before[label] = (plan, t, measure(lambda qs=qs: len(list(qs.all()))))
        finally:
            # AFTER: index dipasang kembali
            with connection.schema_editor() as editor:
                editor.add_index(Course, index)
            with connection.cursor() as cur:
                cur.execute("ANALYZE catalog_course")
        for label, title in cases:
            qs = Course.objects.filter(is_active=True, title=title)
            plan_a, t_a = explain_stats(qs)
            orm_a = measure(lambda qs=qs: len(list(qs.all())))
            plan_b, t_b, orm_b = before[label]
            data["index"]["cases"].append(
                {
                    "label": label,
                    "query": f"Course.objects.filter(is_active=True, title={title!r})",
                    "rows": orm_a["rows"],
                    "plan_before": plan_b,
                    "plan_after": plan_a,
                    "exec_ms_before": t_b,
                    "exec_ms_after": t_a,
                    "orm_ms_before": orm_b["median_ms"],
                    "orm_ms_after": orm_a["median_ms"],
                    "time_improvement_pct": improvement(t_b, t_a),
                }
            )
        plan_code, t_code = explain_stats(qs_code)
        data["index"]["plan_code_unique"] = plan_code
        data["index"]["exec_ms_code_unique"] = t_code

        # ------------------------------------------------------------------
        # Simpan & tampilkan
        # ------------------------------------------------------------------
        out_dir = Path(settings.BASE_DIR) / "benchmarks"
        out_dir.mkdir(exist_ok=True)
        (out_dir / "hasil_benchmark.json").write_text(
            json.dumps(data, indent=2, default=str), encoding="utf-8"
        )
        md = self.render_markdown(data)
        (out_dir / "hasil_benchmark.md").write_text(md, encoding="utf-8")
        self.stdout.write(md)
        self.stdout.write(self.style.SUCCESS("Disimpan di benchmarks/hasil_benchmark.(md|json)"))

    @staticmethod
    def render_markdown(d):
        cl, ls, ix = d["course_lecturer"], d["course_lesson"], d["index"]
        lines = [
            "# Hasil Benchmark Minggu 5",
            "",
            f"- Database: {d['postgres']}",
            f"- Waktu = median dari {d['repeat']} kali pengulangan (setelah 1x warm-up)",
            "",
            "## Dataset",
            "",
            "| Tabel | Jumlah |",
            "|---|---|",
        ]
        lines += [f"| {k} | {v} |" for k, v in d["dataset"].items()]
        lines += [
            "",
            "## N+1 Query",
            "",
            "| Percobaan | Query BEFORE | Query AFTER | Waktu BEFORE (ms) | Waktu AFTER (ms) |",
            "|---|---|---|---|---|",
            f"| Course + Lecturer (100) | {cl['before']['queries']} | {cl['after']['queries']} | {cl['before']['median_ms']} | {cl['after']['median_ms']} |",
            f"| Course + Lesson (50) | {ls['before']['queries']} | {ls['after']['queries']} | {ls['before']['median_ms']} | {ls['after']['median_ms']} |",
            "",
            "## Index",
            "",
            f"Index: `{ix['name']}` pada {ix['fields']}",
            "",
        ]
        for c in ix["cases"]:
            lines += [
                f"### {c['label']}",
                f"`{c['query']}` -> {c['rows']} baris",
                "",
                f"- EXPLAIN ANALYZE execution time BEFORE (tanpa index): {c['exec_ms_before']} ms",
                f"- EXPLAIN ANALYZE execution time AFTER (dengan index): {c['exec_ms_after']} ms",
                f"- Waktu ORM BEFORE/AFTER: {c['orm_ms_before']} ms / {c['orm_ms_after']} ms",
                "",
                "EXPLAIN BEFORE:",
                "```",
                c["plan_before"],
                "```",
                "EXPLAIN AFTER:",
                "```",
                c["plan_after"],
                "```",
            ]
        lines += [
            "### EXPLAIN ANALYZE code='PERF05000' (index unique bawaan)",
            "```",
            ix["plan_code_unique"],
            "```",
        ]
        return "\n".join(lines) + "\n"
