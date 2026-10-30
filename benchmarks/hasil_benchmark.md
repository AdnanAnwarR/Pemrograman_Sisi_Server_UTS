# Hasil Benchmark Minggu 5

- Database: PostgreSQL 17.11 (Debian 17.11-1.pgdg13+2) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
- Waktu = median dari 7 kali pengulangan (setelah 1x warm-up)

## Dataset

| Tabel | Jumlah |
|---|---|
| Course (total) | 10005 |
| Course PERF | 10000 |
| Lecturer | 6 |
| Student | 51 |
| Lesson | 503 |
| Enrollment | 1001 |
| Assignment | 202 |
| Submission | 1002 |

## N+1 Query

| Percobaan | Query BEFORE | Query AFTER | Waktu BEFORE (ms) | Waktu AFTER (ms) |
|---|---|---|---|---|
| Course + Lecturer (100) | 101 | 1 | 44.176 | 2.785 |
| Course + Lesson (50) | 51 | 2 | 32.375 | 4.2 |

## Index

Index: `catalog_cou_is_acti_d7f8f8_idx` pada ['is_active', 'title']

### Query modul (judul 5000, is_active=True)
`Course.objects.filter(is_active=True, title='Performance Course 5000')` -> 0 baris

- EXPLAIN ANALYZE execution time BEFORE (tanpa index): 0.47 ms
- EXPLAIN ANALYZE execution time AFTER (dengan index): 0.015 ms
- Waktu ORM BEFORE/AFTER: 0.872 ms / 0.36 ms

EXPLAIN BEFORE:
```
Sort  (cost=239.07..239.08 rows=1 width=58) (actual time=0.474..0.475 rows=0 loops=1)
  Sort Key: code
  Sort Method: quicksort  Memory: 25kB
  ->  Seq Scan on catalog_course  (cost=0.00..239.06 rows=1 width=58) (actual time=0.473..0.473 rows=0 loops=1)
        Filter: (is_active AND ((title)::text = 'Performance Course 5000'::text))
        Rows Removed by Filter: 10005
Planning Time: 0.026 ms
Execution Time: 0.480 ms
```
EXPLAIN AFTER:
```
Sort  (cost=8.31..8.32 rows=1 width=58) (actual time=0.008..0.008 rows=0 loops=1)
  Sort Key: code
  Sort Method: quicksort  Memory: 25kB
  ->  Index Scan using catalog_cou_is_acti_d7f8f8_idx on catalog_course  (cost=0.29..8.30 rows=1 width=58) (actual time=0.007..0.007 rows=0 loops=1)
        Index Cond: ((is_active = true) AND ((title)::text = 'Performance Course 5000'::text))
Planning Time: 0.028 ms
Execution Time: 0.014 ms
```
### Query judul aktif (judul 5001, is_active=True)
`Course.objects.filter(is_active=True, title='Performance Course 5001')` -> 1 baris

- EXPLAIN ANALYZE execution time BEFORE (tanpa index): 0.445 ms
- EXPLAIN ANALYZE execution time AFTER (dengan index): 0.013 ms
- Waktu ORM BEFORE/AFTER: 0.883 ms / 0.4 ms

EXPLAIN BEFORE:
```
Sort  (cost=239.07..239.08 rows=1 width=58) (actual time=0.440..0.440 rows=1 loops=1)
  Sort Key: code
  Sort Method: quicksort  Memory: 25kB
  ->  Seq Scan on catalog_course  (cost=0.00..239.06 rows=1 width=58) (actual time=0.219..0.438 rows=1 loops=1)
        Filter: (is_active AND ((title)::text = 'Performance Course 5001'::text))
        Rows Removed by Filter: 10004
Planning Time: 0.023 ms
Execution Time: 0.445 ms
```
EXPLAIN AFTER:
```
Sort  (cost=8.31..8.32 rows=1 width=58) (actual time=0.008..0.008 rows=1 loops=1)
  Sort Key: code
  Sort Method: quicksort  Memory: 25kB
  ->  Index Scan using catalog_cou_is_acti_d7f8f8_idx on catalog_course  (cost=0.29..8.30 rows=1 width=58) (actual time=0.007..0.007 rows=1 loops=1)
        Index Cond: ((is_active = true) AND ((title)::text = 'Performance Course 5001'::text))
Planning Time: 0.024 ms
Execution Time: 0.013 ms
```
### EXPLAIN ANALYZE code='PERF05000' (index unique bawaan)
```
Index Scan using catalog_course_code_e109f879_like on catalog_course  (cost=0.29..8.30 rows=1 width=58) (actual time=0.003..0.003 rows=1 loops=1)
  Index Cond: ((code)::text = 'PERF05000'::text)
Planning Time: 0.017 ms
Execution Time: 0.007 ms
```
