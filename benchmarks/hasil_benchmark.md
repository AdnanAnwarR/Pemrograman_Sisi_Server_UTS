# Hasil Benchmark Minggu 5

- Database: PostgreSQL 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1) on x86_64-pc-linux-gnu, compiled by gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0, 64-bit
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
| Course + Lecturer (100) | 101 | 1 | 54.782 | 2.632 |
| Course + Lesson (50) | 51 | 2 | 42.319 | 6.074 |

## Index

Index: `catalog_cou_is_acti_d7f8f8_idx` pada ['is_active', 'title']

### Query modul (judul 5000, is_active=True)
`Course.objects.filter(is_active=True, title='Performance Course 5000')` -> 0 baris

- EXPLAIN ANALYZE execution time BEFORE (tanpa index): 0.603 ms
- EXPLAIN ANALYZE execution time AFTER (dengan index): 0.018 ms
- Waktu ORM BEFORE/AFTER: 1.025 ms / 0.448 ms

EXPLAIN BEFORE:
```
Sort  (cost=239.07..239.08 rows=1 width=58) (actual time=0.594..0.595 rows=0 loops=1)
  Sort Key: code
  Sort Method: quicksort  Memory: 25kB
  ->  Seq Scan on catalog_course  (cost=0.00..239.06 rows=1 width=58) (actual time=0.592..0.592 rows=0 loops=1)
        Filter: (is_active AND ((title)::text = 'Performance Course 5000'::text))
        Rows Removed by Filter: 10005
Planning Time: 0.041 ms
Execution Time: 0.603 ms
```
EXPLAIN AFTER:
```
Sort  (cost=8.31..8.32 rows=1 width=58) (actual time=0.009..0.009 rows=0 loops=1)
  Sort Key: code
  Sort Method: quicksort  Memory: 25kB
  ->  Index Scan using catalog_cou_is_acti_d7f8f8_idx on catalog_course  (cost=0.29..8.30 rows=1 width=58) (actual time=0.007..0.007 rows=0 loops=1)
        Index Cond: ((is_active = true) AND ((title)::text = 'Performance Course 5000'::text))
Planning Time: 0.046 ms
Execution Time: 0.018 ms
```
### Query judul aktif (judul 5001, is_active=True)
`Course.objects.filter(is_active=True, title='Performance Course 5001')` -> 1 baris

- EXPLAIN ANALYZE execution time BEFORE (tanpa index): 0.568 ms
- EXPLAIN ANALYZE execution time AFTER (dengan index): 0.022 ms
- Waktu ORM BEFORE/AFTER: 1.143 ms / 0.503 ms

EXPLAIN BEFORE:
```
Sort  (cost=239.07..239.08 rows=1 width=58) (actual time=0.540..0.541 rows=1 loops=1)
  Sort Key: code
  Sort Method: quicksort  Memory: 25kB
  ->  Seq Scan on catalog_course  (cost=0.00..239.06 rows=1 width=58) (actual time=0.267..0.537 rows=1 loops=1)
        Filter: (is_active AND ((title)::text = 'Performance Course 5001'::text))
        Rows Removed by Filter: 10004
Planning Time: 0.037 ms
Execution Time: 0.549 ms
```
EXPLAIN AFTER:
```
Sort  (cost=8.31..8.32 rows=1 width=58) (actual time=0.013..0.013 rows=1 loops=1)
  Sort Key: code
  Sort Method: quicksort  Memory: 25kB
  ->  Index Scan using catalog_cou_is_acti_d7f8f8_idx on catalog_course  (cost=0.29..8.30 rows=1 width=58) (actual time=0.009..0.010 rows=1 loops=1)
        Index Cond: ((is_active = true) AND ((title)::text = 'Performance Course 5001'::text))
Planning Time: 0.044 ms
Execution Time: 0.022 ms
```
### EXPLAIN ANALYZE code='PERF05000' (index unique bawaan)
```
Index Scan using catalog_course_code_e109f879_like on catalog_course  (cost=0.29..8.30 rows=1 width=58) (actual time=0.006..0.006 rows=1 loops=1)
  Index Cond: ((code)::text = 'PERF05000'::text)
Planning Time: 0.028 ms
Execution Time: 0.013 ms
```
