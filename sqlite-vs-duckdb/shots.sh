#!/bin/sh
# Real CLI sessions for the article's terminal screenshots: each CLI loads the same CSV with its own import command,
# then runs the same query with its timer on. Output saved to data/cli-sqlite.txt and data/cli-duckdb.txt.
MSYS_NO_PATHCONV=1 docker run --rm --cpus=2 --memory=4g -v "$(pwd)/data:/work" python:3.13-slim sh -c '
  set -e
  apt-get update -qq >/dev/null && apt-get install -y -qq gcc wget unzip >/dev/null
  cd /tmp && wget -q https://sqlite.org/2026/sqlite-amalgamation-3540100.zip && unzip -q sqlite-amalgamation-3540100.zip
  gcc -O2 sqlite-amalgamation-3540100/shell.c sqlite-amalgamation-3540100/sqlite3.c -o /usr/local/bin/sqlite3 -lm -lpthread
  wget -q https://github.com/duckdb/duckdb/releases/download/v2.0.1/duckdb-cli-linux-amd64.tar.gz && tar xzf duckdb-cli-linux-amd64.tar.gz -C /usr/local/bin
  mkdir -p /db && cd /db
  Q="SELECT category, round(SUM(amount), 2) AS total FROM transactions GROUP BY category ORDER BY total DESC;"
  printf ".echo on\n.timer on\n.mode table\nCREATE TABLE transactions (id INTEGER PRIMARY KEY, tx_date TEXT, customer_id INTEGER, category TEXT, amount REAL);\n.import --csv --skip 1 /work/transactions.csv transactions\n%s\n" "$Q" > s.sql
  printf ".echo on\n.timer on\n.mode table\nCREATE TABLE transactions AS SELECT * FROM read_csv(\047/work/transactions.csv\047);\n%s\n" "$Q" > d.sql
  { echo "sqlite3 --version"; sqlite3 --version | cut -d" " -f1; echo; sqlite3 bank.db < s.sql; } > /work/cli-sqlite.txt 2>&1
  { echo "duckdb --version"; duckdb --version; echo; duckdb bank.duckdb < d.sql; } > /work/cli-duckdb.txt 2>&1
  cat /work/cli-sqlite.txt /work/cli-duckdb.txt'
