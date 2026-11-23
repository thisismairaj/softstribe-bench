#!/bin/bash
# Real terminal sessions for the article: cached installs of the same 49 pinned packages, timed.
cd /w
python -m venv /tmp/warm >/dev/null; pip --python /tmp/warm/bin/python install -q -r requirements.txt >/dev/null 2>&1
uv venv -q /tmp/warmuv; uv pip install -q --python /tmp/warmuv/bin/python -r requirements.txt >/dev/null 2>&1; uv pip install -q --compile-bytecode --python /tmp/warmuv/bin/python --reinstall -r requirements.txt >/dev/null 2>&1   # fill uv cache in its own venv
run() { rm -rf /tmp/v; uv venv -q /tmp/v; echo "\$ $1"; { eval "time $2"; } 2>&1 | tail -6; echo; }
{ echo '$ pip --version'; pip --version | cut -d' ' -f1-2; echo
  run "time pip install -r requirements.txt" "pip --python /tmp/v/bin/python install -q -r requirements.txt"
} > data/shot-pip.txt
{ echo '$ uv --version'; uv --version; echo
  run "time uv pip install -r requirements.txt" "uv pip install --python /tmp/v/bin/python -r requirements.txt"
  run "time uv pip install --compile-bytecode -r requirements.txt" "uv pip install --compile-bytecode --python /tmp/v/bin/python -r requirements.txt"
} > data/shot-uv.txt
