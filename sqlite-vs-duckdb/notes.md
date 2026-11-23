# sqlite-vs-duckdb benchmark notes (run 2026-11-23, laptop, Docker --cpus=2 --memory=4g, python:3.12-slim)
Versions: versions.txt. Raw: results.csv. Script: bench.py, run.sh.
- Run 1-2 discarded: databases on the Windows shared folder (bind mount) made every fsync slow (SQLite 14 ms per insert). Databases now on the container disk (/db).
- Analytics (1M rows): DuckDB 15-100x faster on group-by/join; load 0.9 s vs 4.0 s; file 8.1 MB vs 41.6 MB. Same results checked for all 5 queries.
- App-style: point lookup by id SQLite 11 us vs DuckDB 684 us; 10,000 inserts in one transaction SQLite 0.029 s vs DuckDB 12.7 s; 1,000 single-row commits both ~3.6-4.8 s (disk syncs dominate); SQLite WAL + synchronous=NORMAL 0.023 s.
