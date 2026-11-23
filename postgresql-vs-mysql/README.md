# PostgreSQL vs MySQL (bench v1)

Article: https://softstribe.com/compare/postgresql-vs-mysql

- `run.sh`: starts each official image alone (`postgres:19.0`, `mysql:26.10.0`), default settings, `--cpus=2
  --memory=4g`, data in a Docker volume, then runs `bench.py` from a client container. `MODE=tuned` sets
  `shared_buffers=1GB` and `innodb_buffer_pool_size=2G`. `MYDRIVER=connector` uses Oracle's mysql-connector-python
  (C extension) instead of PyMySQL. `ENGINES=mysql` runs one engine only.
- Needs the CSVs from `../sqlite-vs-duckdb/data` (run that benchmark once first).
- `results.csv`: every run combined (column `run`, and `mysql_driver`). Per-run files, answers and memory readings
  are in `runs/`.
- The article uses PostgreSQL rounds `default-1`, `default-2` and MySQL rounds `default-connector1`,
  `default-connector2`; the PyMySQL and tuned rounds are kept for comparison.
- `shots.sh`: the psql and mysql sessions shown as screenshots. `chart.py`: the article's chart.
