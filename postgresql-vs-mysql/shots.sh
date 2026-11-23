#!/bin/sh
# Real CLI sessions for the article's terminal screenshots. Each server: official image, default settings,
# 2 CPUs / 4 GB. Load the same CSV with each client's own command, then run the same join with the timer on.
# Output: data/cli-postgres.txt, data/cli-mysql.txt
set -e
export MSYS_NO_PATHCONV=1
PG=postgres:19.0
MY=mysql:26.10.0
CSV="$(cd ../sqlite-vs-duckdb/data && pwd -W 2>/dev/null || pwd)"
Q="SELECT c.country, c.segment, SUM(t.amount) AS total
FROM transactions t JOIN customers c ON c.customer_id = t.customer_id
GROUP BY c.country, c.segment ORDER BY total DESC LIMIT 5;"
DDL="CREATE TABLE transactions (id INTEGER PRIMARY KEY, tx_date VARCHAR(10),
  customer_id INTEGER, category VARCHAR(20), amount NUMERIC(12,2));
CREATE TABLE customers (customer_id INTEGER PRIMARY KEY,
  country VARCHAR(2), segment VARCHAR(10));"

docker rm -f shotdb >/dev/null 2>&1 || true
MSYS_NO_PATHCONV=1 docker run -d --name shotdb --cpus=2 --memory=4g -v "$CSV:/data:ro" -e POSTGRES_PASSWORD=bench -e POSTGRES_DB=bench $PG >/dev/null
until docker exec shotdb pg_isready -U postgres -d bench >/dev/null 2>&1; do sleep 1; done; sleep 5
printf '%s\n' "$DDL" "\\copy transactions FROM '/data/transactions.csv' WITH (FORMAT csv, HEADER true)" \
  "\\copy customers FROM '/data/customers.csv' WITH (FORMAT csv, HEADER true)" "ANALYZE;" "\\timing on" "$Q" > pg.sql
docker cp pg.sql shotdb:/tmp/pg.sql >/dev/null
{ echo "psql --version"; docker exec shotdb psql --version; echo; docker exec shotdb psql -U postgres -d bench -e -f /tmp/pg.sql; } > data/cli-postgres.txt 2>&1
docker rm -f shotdb >/dev/null

MSYS_NO_PATHCONV=1 docker run -d --name shotdb --cpus=2 --memory=4g -v "$CSV:/data:ro" -e MYSQL_ROOT_PASSWORD=bench -e MYSQL_DATABASE=bench $MY --local-infile=1 >/dev/null
until docker exec shotdb mysql -uroot -pbench -e "SELECT 1" bench >/dev/null 2>&1; do sleep 2; done; sleep 5
printf '%s\n' "$DDL" \
  "LOAD DATA LOCAL INFILE '/data/transactions.csv' INTO TABLE transactions FIELDS TERMINATED BY ',' LINES TERMINATED BY '\\r\\n' IGNORE 1 LINES;" \
  "LOAD DATA LOCAL INFILE '/data/customers.csv' INTO TABLE customers FIELDS TERMINATED BY ',' LINES TERMINATED BY '\\r\\n' IGNORE 1 LINES;" \
  "ANALYZE TABLE transactions, customers;" "$(printf %b "$Q")" > my.sql
docker cp my.sql shotdb:/tmp/my.sql >/dev/null
{ echo "mysql --version"; docker exec shotdb mysql --version; echo; docker exec shotdb sh -c "mysql -uroot -pbench --local-infile=1 --table -vvv bench < /tmp/my.sql" 2>&1 | grep -v "Using a password"; } > data/cli-mysql.txt 2>&1
docker rm -f shotdb >/dev/null
rm -f pg.sql my.sql
cat data/cli-postgres.txt; echo ======; cat data/cli-mysql.txt
