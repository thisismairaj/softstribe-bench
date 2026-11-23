# uv vs pip (bench v1)

Article: https://softstribe.com/compare/uv-vs-pip

- `Dockerfile`: python:3.13-slim with pip 26.3 and uv 0.13.9 pinned. `run.sh` runs `bench.sh` with `--cpus=2 --memory=4g`.
- `bench.sh`: venv creation, cold installs (3 rounds, caches cleared), warm installs (5), resolving from `requirements.in` (5),
  tool order swapped each round; then checks both tools installed the same packages (`freeze-*.txt`, names normalised).
- `bench-compile.sh`: the like-for-like round, uv with `--compile-bytecode` (pip compiles .pyc at install by default; uv does not).
- `requirements.in` (12 packages) pins to `requirements.txt` (49 packages).
- `results.csv`: every timed run. `check.txt`: package check and environment sizes. `shots.sh`: the terminal sessions in the article.
- Cold installs depend on your connection; the cached numbers are the reliable comparison.
