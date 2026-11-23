#!/bin/sh
# uv vs pip inside one container (python:3.13-slim + pip and uv pinned in the Dockerfile), run by run.sh.
# Each round alternates which tool goes first, so network swings hit both. Writes /w/data/results.csv.
set -e
cd /w
OUT=data/results.csv
mkdir -p data
[ -f $OUT ] || echo "tool,test,run,seconds" > $OUT
RUNS=${RUNS:-5}
COLD_RUNS=${COLD_RUNS:-3}   # cold installs download everything, so fewer rounds
now() { date +%s.%N; }
t() { # tool test run command...
  tool=$1; test=$2; run=$3; shift 3
  s=$(now); "$@" >/dev/null 2>&1; e=$(now)
  echo "$tool,$test,$run,$(echo "$e - $s" | bc -l)" >> $OUT
}
pipclear() { pip cache purge >/dev/null 2>&1 || true; }
uvclear() { uv cache clean >/dev/null 2>&1 || true; }

for r in $(seq 1 $RUNS); do
  for tool in pip uv; do
    [ $((r % 2)) -eq 0 ] && tool=$( [ $tool = pip ] && echo uv || echo pip )
    rm -rf /tmp/v
    if [ $tool = pip ]; then t pip venv_create $r python -m venv /tmp/v
    else t uv venv_create $r uv venv -q /tmp/v; fi
  done
done

for mode in cold warm; do
  N=$RUNS; [ $mode = cold ] && N=$COLD_RUNS
  for r in $(seq 1 $N); do
    for tool in pip uv; do
      [ $((r % 2)) -eq 0 ] && tool=$( [ $tool = pip ] && echo uv || echo pip )
      rm -rf /tmp/v; uv venv -q /tmp/v
      if [ $mode = cold ]; then pipclear; uvclear; fi
      if [ $tool = pip ]; then t pip install_$mode $r pip --python /tmp/v/bin/python install -q -r requirements.txt
      else t uv install_$mode $r uv pip install -q --python /tmp/v/bin/python -r requirements.txt; fi
    done
  done
done

# Resolve the unpinned list from scratch (warm caches): pip's dry run vs uv's compile
for r in $(seq 1 $RUNS); do
  for tool in pip uv; do
    [ $((r % 2)) -eq 0 ] && tool=$( [ $tool = pip ] && echo uv || echo pip )
    rm -rf /tmp/v; uv venv -q /tmp/v
    if [ $tool = pip ]; then t pip resolve $r pip --python /tmp/v/bin/python install -q --dry-run --ignore-installed -r requirements.in
    else t uv resolve $r uv pip compile -q --python /tmp/v/bin/python requirements.in -o /tmp/lock.txt; fi
  done
done

# Same result? Install with each tool into its own venv and compare the package lists.
rm -rf /tmp/vp /tmp/vu; uv venv -q /tmp/vp; uv venv -q /tmp/vu
pip --python /tmp/vp/bin/python install -q -r requirements.txt
uv pip install -q --python /tmp/vu/bin/python -r requirements.txt
pip --python /tmp/vp/bin/python freeze | sort > data/freeze-pip.txt
uv pip freeze --python /tmp/vu/bin/python | sort > data/freeze-uv.txt
python3 -c "n=lambda f: sorted(l.strip().lower().replace('_','-') for l in open(f) if l.strip()); print('same packages (names normalised):', n('data/freeze-pip.txt')==n('data/freeze-uv.txt'))" > data/check.txt
echo "pip venv $(du -sm /tmp/vp | cut -f1) MB, uv venv $(du -sm /tmp/vu | cut -f1) MB" >> data/check.txt
echo "packages: $(wc -l < data/freeze-pip.txt)" >> data/check.txt
{ pip --version; uv --version; python --version; } > data/versions.txt
cat data/check.txt data/versions.txt
