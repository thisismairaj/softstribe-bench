#!/bin/sh
# Same limits for both engines: 2 CPUs, 4 GB RAM. CSVs and results land in ./data; databases stay on the container disk.
# SQLite: the current release built from the official amalgamation (default compile options + the usual
# SQLITE_ENABLE_FTS5/JSON flags are not needed for this test) and loaded by Python's sqlite3 module via LD_LIBRARY_PATH.
mkdir -p data
MSYS_NO_PATHCONV=1 docker run --rm --cpus=2 --memory=4g -v "$(pwd)/data:/work" -v "$(pwd)/bench.py:/bench.py:ro" python:3.13-slim sh -c '
  set -e
  apt-get update -qq >/dev/null && apt-get install -y -qq gcc wget unzip >/dev/null
  cd /tmp && wget -q https://sqlite.org/2026/sqlite-amalgamation-3540100.zip && unzip -q sqlite-amalgamation-3540100.zip
  cd sqlite-amalgamation-3540100 && gcc -O2 -shared -fPIC -DSQLITE_THREADSAFE=1 sqlite3.c -o /usr/local/lib/libsqlite3.so.0 -lm -lpthread
  pip install -q --root-user-action=ignore duckdb==2.0.1
  LD_LIBRARY_PATH=/usr/local/lib python /bench.py'
