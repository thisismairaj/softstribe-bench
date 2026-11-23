#!/bin/sh
# One database at a time: official image, default settings, 2 CPUs and 4 GB, data in a Docker volume (not a
# Windows shared folder). The client runs in its own container on the same network. Data: the 1M-row CSVs from
# ../sqlite-vs-duckdb/data (same file as the SQLite vs DuckDB test). Results in ./data.
set -e
PG=postgres:19.0
MY=mysql:26.10.0
MODE=${MODE:-default}; TAG=${TAG:-1}
OUTDIR=data/$MODE-$TAG
mkdir -p $OUTDIR
rm -f $OUTDIR/*
if [ $MODE = tuned ]; then PGARGS="-c shared_buffers=1GB"; MYARGS="--innodb-buffer-pool-size=2G"; else PGARGS=""; MYARGS=""; fi
docker network create benchnet >/dev/null 2>&1 || true
CSV="$(cd ../sqlite-vs-duckdb/data && pwd -W 2>/dev/null || pwd)"
docker build -q -t benchclient -f Dockerfile.client . >/dev/null
for ENGINE in ${ENGINES:-postgres mysql}; do
  docker rm -f db >/dev/null 2>&1 || true
  docker volume rm -f benchvol >/dev/null 2>&1 || true
  if [ $ENGINE = postgres ]; then
    MSYS_NO_PATHCONV=1 docker run -d --name db --network benchnet --cpus=2 --memory=4g -v benchvol:/var/lib/postgresql \
      -e POSTGRES_PASSWORD=bench -e POSTGRES_DB=bench $PG $PGARGS >/dev/null
    until docker exec db pg_isready -U postgres -d bench >/dev/null 2>&1; do sleep 1; done
  else
    MSYS_NO_PATHCONV=1 docker run -d --name db --network benchnet --cpus=2 --memory=4g -v benchvol:/var/lib/mysql \
      -e MYSQL_ROOT_PASSWORD=bench -e MYSQL_DATABASE=bench $MY --local-infile=1 $MYARGS >/dev/null
    until docker exec db mysql -uroot -pbench -e "SELECT 1" bench >/dev/null 2>&1; do sleep 2; done
  fi
  sleep 20
  echo "$ENGINE idle $(docker stats --no-stream --format '{{.MemUsage}}' db)" >> $OUTDIR/idle.txt
  MSYS_NO_PATHCONV=1 docker run --rm --network benchnet --cpus=2 -e ENGINE=$ENGINE -e MYDRIVER=${MYDRIVER:-} -v "$CSV:/data:ro" \
    -v "$(pwd -W 2>/dev/null || pwd)/$OUTDIR:/out" -v "$(pwd -W 2>/dev/null || pwd)/bench.py:/bench.py:ro" benchclient python /bench.py
  echo "$ENGINE after-tests $(docker stats --no-stream --format '{{.MemUsage}}' db)" >> $OUTDIR/idle.txt
  docker rm -f db >/dev/null
  docker volume rm -f benchvol >/dev/null
done
for i in $PG $MY; do echo "$i image_bytes $(docker image inspect $i --format '{{.Size}}')" >> $OUTDIR/idle.txt; done
cat $OUTDIR/idle.txt
