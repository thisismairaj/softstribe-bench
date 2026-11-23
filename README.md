# softstribe-bench

Benchmarks behind the measured comparisons on [Softstribe](https://softstribe.com/compare), by Muhammad Mairaj.
Every number on those pages comes from the scripts and raw results in this repo, so you can check them or rerun them.

| Benchmark | Article | What it measures |
|---|---|---|
| [sqlite-vs-duckdb](sqlite-vs-duckdb/) | [SQLite vs DuckDB: We Benchmarked Both on 1 Million Rows](https://softstribe.com/compare/sqlite-vs-duckdb) | CSV load, analytical queries, single-row reads and writes, file size |
| [postgresql-vs-mysql](postgresql-vs-mysql/) | [PostgreSQL vs MySQL: I Benchmarked Both on 1 Million Rows](https://softstribe.com/compare/postgresql-vs-mysql) | Bulk load, reports, single-row writes, 8 concurrent clients, idle memory, image size |

## How these are run

- Everything runs in Docker, one engine at a time, limited to 2 CPUs and 4 GB of memory.
- Same generated data for every test: 1,000,000 bank-style transactions and 100,000 customers from a fixed random
  seed (42), built by `sqlite-vs-duckdb/bench.py` on its first run.
- Queries: 10 timed runs after one warm-up; loads and writes: 3 runs. Results are medians.
- Answers are compared between engines before any timing is trusted.
- Databases live on the container's disk or a Docker volume, not a host folder (on Docker for Windows a host folder
  makes every disk sync slow and skews write tests).

## Rerun

Needs Docker and a POSIX shell (Git Bash works on Windows).

```sh
cd sqlite-vs-duckdb && ./run.sh            # also generates the CSVs into sqlite-vs-duckdb/data
cd ../postgresql-vs-mysql && ./run.sh      # default settings; MODE=tuned ./run.sh for the memory-tuned round
```

Your seconds will differ on other hardware. The pattern between engines is what the articles rely on.

## Changes

Each benchmark has a bench version, shown at the bottom of its article under "Changes to this page". A change of
method bumps the version; reruns and corrections are listed there too.

## Licence

MIT, see [LICENSE](LICENSE).
