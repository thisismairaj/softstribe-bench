# SQLite vs DuckDB (bench v1)

Article: https://softstribe.com/compare/sqlite-vs-duckdb

- `bench.py`: generates the data (first run), loads it into both engines, runs the queries and write tests, checks
  that both return the same answers, writes `data/results.csv` and `data/versions.txt`.
- `run.sh`: runs it in `python:3.13-slim` with `--cpus=2 --memory=4g`, SQLite 3.54.1 built from the official
  amalgamation, DuckDB 2.0.1 from PyPI.
- `shots.sh`: the command-line sessions shown as screenshots in the article.
- `chart.py`: the chart in the article, from `results.csv`.
- `results.csv`, `versions.txt`: the published run. `notes.md`: what was discarded and why.
