#!/bin/sh
# Bun vs Node.js inside one container (see Dockerfile), run by run.sh. Writes into /w/data.
set -e
cd /w
mkdir -p data
{ echo "node $(node --version)"; echo "npm $(npm --version)"; echo "bun $(bun --version)"; } > data/versions.txt

# 1. Same answers? (CPU script checksum and TypeScript output must match)
{ echo "node cpu: $(node cpu.mjs)"; echo "bun  cpu: $(bun cpu.mjs)"; echo "node ts:  $(node hello.ts 2>&1)"; echo "bun  ts:  $(bun hello.ts)"; } > data/answers.txt

# 2. Startup and CPU work, measured by hyperfine (no shell in between)
hyperfine -N --warmup 5 --runs 30 --export-json data/startup.json \
  'node -e 0' 'bun -e 0' 'node hello.ts' 'bun hello.ts' > data/startup.txt
hyperfine -N --warmup 2 --runs 10 --export-json data/cpu.json 'node cpu.mjs' 'bun cpu.mjs' > data/cpu.txt

# 3. Package install: cold (no cache, no lockfile) and warm (cache and lockfile kept, node_modules removed).
#    Order alternates each round. Each tool installs into its own copy of the project.
OUT=data/install.csv; echo "tool,mode,run,seconds" > $OUT
now() { date +%s.%N; }
mkdir -p /tmp/npmproj /tmp/bunproj; cp package.json /tmp/npmproj/; cp package.json /tmp/bunproj/
run_install() { # tool mode run
  if [ $1 = npm ]; then cd /tmp/npmproj; s=$(now); npm install --no-audit --no-fund --loglevel=error >/dev/null 2>&1; e=$(now)
  else cd /tmp/bunproj; s=$(now); bun install --silent >/dev/null 2>&1; e=$(now); fi
  cd /w; echo "$1,$2,$3,$(echo "$e - $s" | bc -l)" >> $OUT
}
for mode in cold warm; do
  N=5; [ $mode = cold ] && N=3
  for r in $(seq 1 $N); do
    for tool in npm bun; do
      [ $((r % 2)) -eq 0 ] && tool=$( [ $tool = npm ] && echo bun || echo npm )
      if [ $tool = npm ]; then rm -rf /tmp/npmproj/node_modules; [ $mode = cold ] && { rm -f /tmp/npmproj/package-lock.json; npm cache clean --force >/dev/null 2>&1; }
      else rm -rf /tmp/bunproj/node_modules; [ $mode = cold ] && { rm -f /tmp/bunproj/bun.lock /tmp/bunproj/bun.lockb; bun pm cache rm >/dev/null 2>&1 || true; }; fi
      run_install $tool $mode $r
    done
  done
done
# Same packages? Compare top-level installed versions.
for d in npmproj bunproj; do
  (cd /tmp/$d && for p in $(node -e "const p=require('./package.json');console.log(Object.keys({...p.dependencies,...p.devDependencies}).join(' '))"); do
     echo "$p $(node -p "require('./node_modules/$p/package.json').version")"; done) > data/installed-$d.txt
done
cmp -s data/installed-npmproj.txt data/installed-bunproj.txt && echo "same top-level versions: yes" >> data/answers.txt || echo "same top-level versions: NO" >> data/answers.txt
echo "node_modules: npm $(du -sm /tmp/npmproj/node_modules | cut -f1) MB, bun $(du -sm /tmp/bunproj/node_modules | cut -f1) MB" >> data/answers.txt
echo "packages in node_modules: npm $(find /tmp/npmproj/node_modules -name package.json -maxdepth 3 | wc -l), bun $(find /tmp/bunproj/node_modules -name package.json -maxdepth 3 | wc -l)" >> data/answers.txt
cat data/versions.txt data/answers.txt
