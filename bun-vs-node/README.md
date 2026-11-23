# Bun vs Node.js (bench v1)

Article: https://softstribe.com/compare/bun-vs-node

- `Dockerfile`: debian:trixie-slim with Node.js 26.13.1 (official tarball, sha256 checked; bundled npm 11.20.0), Bun 1.4.5,
  hyperfine and wrk. `run.sh` runs `bench.sh` (2 CPUs, 4 GB) then the HTTP test (server alone on 1 CPU / 1 GB, wrk in a second container).
- `bench.sh`: answer checks (`cpu.mjs` checksum, `hello.ts` output), startup with hyperfine (30 runs), CPU script, npm vs bun installs
  (3 cold, 5 warm, order swapped), installed-version check.
- The article uses `runs/cpu30.json` (30 runs) for the CPU test; the first 10-run attempt was too noisy.
- `results.csv`: every run combined (startup, cpu, installs, http). `runs/`: the raw files.
