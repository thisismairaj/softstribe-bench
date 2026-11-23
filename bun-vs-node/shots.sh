#!/bin/bash
# Real terminal sessions for the article: warm installs (cache and lockfile present, node_modules removed), timed.
cd /tmp && mkdir -p n b && cp /w/package.json n/ && cp /w/package.json b/
(cd n && npm install --no-audit --no-fund --loglevel=error >/dev/null 2>&1); (cd b && bun install --silent >/dev/null 2>&1)
rm -rf n/node_modules b/node_modules
cd /tmp/n && { echo '$ npm --version'; npm --version; echo '$ time npm install'; { time npm install --no-audit --no-fund; } 2>&1; } > /w/data/shot-npm.txt
cd /tmp/b && { echo '$ bun --version'; bun --version; echo '$ time bun install'; { time bun install; } 2>&1; } > /w/data/shot-bun.txt
