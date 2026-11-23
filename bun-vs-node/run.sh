#!/bin/sh
# Bun vs Node.js. Part 1: startup, CPU and installs in one container (2 CPUs, 4 GB).
# Part 2: HTTP throughput. The server runs alone in a container with 1 CPU and 1 GB; wrk runs in a second container
# (1 CPU) on the same Docker network, so the load generator never shares the server's CPU.
set -e
W="$(pwd -W 2>/dev/null || pwd)"
rm -rf data; mkdir -p data
MSYS_NO_PATHCONV=1 docker build -q -t bunnode . >/dev/null
MSYS_NO_PATHCONV=1 docker run --rm --cpus=2 --memory=4g -v "$W:/w" bunnode sh /w/bench.sh

docker network create bunnet >/dev/null 2>&1 || true
echo "variant,run,requests_per_sec,latency_p50,latency_p99,non2xx" > data/http.csv
for v in node-http bun-node-http bun-serve; do
  case $v in
    node-http) CMD="node server.mjs" ;;
    bun-node-http) CMD="bun server.mjs" ;;
    bun-serve) CMD="bun server-bun.ts" ;;
  esac
  docker rm -f srv >/dev/null 2>&1 || true
  MSYS_NO_PATHCONV=1 docker run -d --name srv --network bunnet --cpus=1 --memory=1g -v "$W:/w" -w /w bunnode $CMD >/dev/null
  sleep 3
  MSYS_NO_PATHCONV=1 docker run --rm --network bunnet bunnode sh -c "curl -s -i http://srv:3000/" > data/http-response-$v.txt
  MSYS_NO_PATHCONV=1 docker run --rm --network bunnet --cpus=1 bunnode wrk -t2 -c64 -d5s http://srv:3000/ >/dev/null   # warm-up
  for r in 1 2 3; do
    MSYS_NO_PATHCONV=1 docker run --rm --network bunnet --cpus=1 bunnode wrk -t2 -c64 -d15s --latency http://srv:3000/ > data/wrk-$v-$r.txt
    rps=$(grep "Requests/sec" data/wrk-$v-$r.txt | awk '{print $2}')
    p50=$(grep " 50%" data/wrk-$v-$r.txt | awk '{print $2}')
    p99=$(grep " 99%" data/wrk-$v-$r.txt | awk '{print $2}')
    bad=$(grep -c "Non-2xx" data/wrk-$v-$r.txt || true)
    echo "$v,$r,$rps,$p50,$p99,$bad" >> data/http.csv
  done
  docker rm -f srv >/dev/null
done
cat data/http.csv
