#!/bin/sh
# Like-for-like follow-up: uv with --compile-bytecode (pip compiles .pyc at install by default; uv does not).
# Appends rows with tool "uv-compile" to data/results.csv.
set -e
cd /w
OUT=data/results.csv
now() { date +%s.%N; }
t() { tool=$1; test=$2; run=$3; shift 3; s=$(now); "$@" >/dev/null 2>&1; e=$(now); echo "$tool,$test,$run,$(echo "$e - $s" | bc -l)" >> $OUT; }
for r in 1 2 3; do rm -rf /tmp/v; uv venv -q /tmp/v; uv cache clean >/dev/null 2>&1; pip cache purge >/dev/null 2>&1 || true
  t uv-compile install_cold $r uv pip install -q --compile-bytecode --python /tmp/v/bin/python -r requirements.txt; done
for r in 1 2 3 4 5; do rm -rf /tmp/v; uv venv -q /tmp/v
  t uv-compile install_warm $r uv pip install -q --compile-bytecode --python /tmp/v/bin/python -r requirements.txt; done
echo "uv --compile-bytecode venv $(du -sm /tmp/v | cut -f1) MB" >> data/check.txt
# names normalised (PyYAML vs pyyaml, typing_extensions vs typing-extensions)
python3 -c "
n=lambda f: sorted(l.strip().lower().replace('_','-') for l in open(f) if l.strip())
print('same packages after normalising names:', n('data/freeze-pip.txt')==n('data/freeze-uv.txt'))" >> data/check.txt
cat data/check.txt
