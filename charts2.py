"""Charts for uv-vs-pip and bun-vs-node. Run from compare-pages/bench with matplotlib."""
import csv
import json
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def style(ax, title):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color="#e3e8ef")
    ax.set_axisbelow(True)
    ax.set_title(title, loc="left", fontsize=14, fontweight="bold", color="#1f2328")


# ---- uv vs pip: seconds per task, three ways ----
m = {}
for r in csv.DictReader(open("uv-vs-pip/data/results.csv")):
    m.setdefault((r["test"], r["tool"]), []).append(float(r["seconds"]))
med = {k: statistics.median(v) for k, v in m.items()}
rows = [("Install, cached downloads", "install_warm"), ("Install from scratch", "install_cold"),
        ("Resolve versions", "resolve"), ("Create a virtual environment", "venv_create")]
tools = [("pip", "pip", "#8a94a6"), ("uv-compile", "uv --compile-bytecode", "#1D52DE"), ("uv", "uv (default)", "#00BBA2")]
fig, ax = plt.subplots(figsize=(10, 5.6), dpi=150)
h = 0.26
for j, (key, label, col) in enumerate(tools):
    ys, xs = [], []
    for i, (_, t) in enumerate(rows):
        if (t, key) in med:
            ys.append(i + (1 - j) * h)
            xs.append(med[(t, key)])
    ax.barh(ys, xs, height=h, color=col, label=label)
    for y, x in zip(ys, xs):
        ax.text(x * 1.12, y, f"{x:.2f} s" if x < 10 else f"{x:.0f} s", va="center", fontsize=9.5, color="#1f2328")
ax.set_xscale("log")
ax.set_yticks(range(len(rows)))
ax.set_yticklabels([r[0] for r in rows], fontsize=11)
ax.set_xticks([0.01, 0.1, 1, 10, 100])
ax.set_xticklabels(["0.01 s", "0.1 s", "1 s", "10 s", "100 s"])
ax.set_xlim(0.008, 900)
ax.invert_yaxis()
ax.set_xlabel("Seconds, log scale (median; 49 packages; lower is better)", fontsize=10.5, color="#5f6b7a")
ax.legend(frameon=False, fontsize=10.5, loc="lower right")
style(ax, "uv 0.13.9 vs pip 26.3 on the same 49 packages")
plt.tight_layout()
plt.savefig("uv-vs-pip/shots/chart.png", facecolor="white")
print({k: round(v, 3) for k, v in med.items()})

# ---- Bun vs Node: how many times faster the winner was ----
def hf(path, name):
    for r in json.load(open(path))["results"]:
        if r["command"] == name:
            return r["mean"]
start = {n: hf("bun-vs-node/data/startup.json", n) for n in ("node -e 0", "bun -e 0", "node hello.ts", "bun hello.ts")}
cpu = {n: hf("bun-vs-node/data/cpu30.json", n) for n in ("node cpu.mjs", "bun cpu.mjs")}
ins = {}
for r in csv.DictReader(open("bun-vs-node/data/install.csv")):
    ins.setdefault((r["tool"], r["mode"]), []).append(float(r["seconds"]))
ins = {k: statistics.median(v) for k, v in ins.items()}
http = {}
for r in csv.DictReader(open("bun-vs-node/data/http.csv")):
    http.setdefault(r["variant"], []).append(float(r["requests_per_sec"]))
http = {k: statistics.median(v) for k, v in http.items()}
data = [
    ("Start an empty script", start["node -e 0"] / start["bun -e 0"]),
    ("Run a TypeScript file", start["node hello.ts"] / start["bun hello.ts"]),
    ("CPU-heavy script", cpu["node cpu.mjs"] / cpu["bun cpu.mjs"]),
    ("Install, from scratch", ins[("npm", "cold")] / ins[("bun", "cold")]),
    ("Install, cache and lockfile", ins[("npm", "warm")] / ins[("bun", "warm")]),
    ("HTTP, same node:http code", http["bun-node-http"] / http["node-http"]),
    ("HTTP, Bun.serve vs node:http", http["bun-serve"] / http["node-http"]),
]
fig, ax = plt.subplots(figsize=(10, 5.4), dpi=150)
ax.barh(range(len(data)), [d[1] for d in data], color="#00BBA2", height=0.6)
ax.set_xscale("log")
ax.set_yticks(range(len(data)))
ax.set_yticklabels([d[0] for d in data], fontsize=11)
for i, d in enumerate(data):
    ax.text(d[1] * 1.08, i, f"Bun {d[1]:.1f}x faster", va="center", fontsize=10.5, color="#1f2328")
ax.set_xticks([1, 10, 100])
ax.set_xticklabels(["1x", "10x", "100x"])
ax.set_xlim(1, 200)
ax.invert_yaxis()
ax.set_xlabel("How many times faster Bun was than Node.js and npm (log scale)", fontsize=10.5, color="#5f6b7a")
style(ax, "Bun 1.4.5 vs Node.js 26.13.1")
plt.tight_layout()
plt.savefig("bun-vs-node/shots/chart.png", facecolor="white")
print("start", {k: round(v * 1000, 1) for k, v in start.items()}, "cpu", {k: round(v * 1000) for k, v in cpu.items()})
print("install", {k: round(v, 2) for k, v in ins.items()}, "http", {k: round(v) for k, v in http.items()})
print([(d[0], round(d[1], 2)) for d in data])
