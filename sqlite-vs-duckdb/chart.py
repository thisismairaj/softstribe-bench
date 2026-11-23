"""Chart for the article: per test, how many times faster the winner was. Reads results.csv (medians)."""
import csv, statistics, collections
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
m = collections.defaultdict(list)
for r in csv.DictReader(open("results.csv")): m[(r["engine"], r["test"])].append(float(r["seconds"]))
med = {k: statistics.median(v) for k, v in m.items()}
tests = [("load_csv", "Load a 1M-row CSV"), ("sum_by_category", "Total per category"), ("count_by_month", "Count per month"),
         ("join_country_segment", "Join + group by"), ("top_10_customers", "Top 10 customers"),
         ("point_lookup_by_id", "Fetch one row by id"), ("insert_10000_rows_one_transaction", "Insert 10,000 rows, one transaction")]
SQ, DK = "#1D52DE", "#00BBA2"
rows = []
for t, label in tests:
    s, d = med[("sqlite", t)], med[("duckdb", t)]
    rows.append((label, s / d if d < s else d / s, "DuckDB" if d < s else "SQLite"))
rows.reverse()
fig, ax = plt.subplots(figsize=(10, 5.6), dpi=150)
y = range(len(rows))
ax.barh(y, [r[1] for r in rows], color=[DK if r[2] == "DuckDB" else SQ for r in rows], height=0.62)
ax.set_xscale("log"); ax.set_yticks(list(y)); ax.set_yticklabels([r[0] for r in rows], fontsize=11)
for i, r in enumerate(rows):
    ax.text(r[1] * 1.08, i, f"{r[2]} {r[1]:,.0f}x faster" if r[1] >= 10 else f"{r[2]} {r[1]:.1f}x faster", va="center", fontsize=10.5, color="#1f2328")
ax.set_xlim(1, max(r[1] for r in rows) * 12)
ax.set_xticks([1, 10, 100, 1000]); ax.set_xticklabels(["1x", "10x", "100x", "1000x"])
ax.set_xlabel("How many times faster the winner was (log scale, median of runs)", fontsize=10.5, color="#5f6b7a")
for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=0); ax.grid(axis="x", color="#e3e8ef"); ax.set_axisbelow(True)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=DK, label="DuckDB faster"), Patch(color=SQ, label="SQLite faster")], loc="upper right", frameon=False, fontsize=10.5)
ax.set_title("SQLite vs DuckDB on the same 1 million rows", loc="left", fontsize=14, fontweight="bold", color="#1f2328")
plt.tight_layout(); plt.savefig("shots/chart.png", facecolor="white")
for r in rows: print(r)
