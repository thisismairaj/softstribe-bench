"""Chart: per test, how many times faster PostgreSQL was than MySQL (default settings, medians over two runs)."""
import csv, statistics
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
rows = [r for r in csv.DictReader(open("results.csv")) if (r["engine"] == "postgres" and r["run"] in ("default-1", "default-2")) or (r["engine"] == "mysql" and r["run"].startswith("default-connector"))]
med = lambda e, t: statistics.median(float(r["seconds"]) for r in rows if r["engine"] == e and r["test"] == t)
tests = [("load_csv", "Load a 1M-row CSV"), ("sum_by_category", "Total per category"), ("count_by_month", "Count per month"),
         ("join_country_segment", "Join + group by"), ("top_10_customers", "Top 10 customers"),
         ("filter_one_customer_no_index", "Filter one customer, no index"), ("insert_1000_single_rows", "1,000 single-row saves"),
         ("update_1000_rows_by_id", "1,000 updates by id"), ("insert_10000_rows_one_transaction", "10,000 rows, one transaction"),
         ("8_clients_4000_inserts", "8 clients writing at once")]
PG, MY = "#336791", "#E48E00"
data = []
for t, label in tests:
    p, m = med("postgres", t), med("mysql", t)
    data.append((label, m / p if p < m else p / m, "PostgreSQL" if p < m else "MySQL"))
data.reverse()
fig, ax = plt.subplots(figsize=(10, 6.2), dpi=150)
ax.barh(range(len(data)), [d[1] for d in data], color=[PG if d[2] == "PostgreSQL" else MY for d in data], height=0.62)
ax.set_yticks(range(len(data))); ax.set_yticklabels([d[0] for d in data], fontsize=11)
for i, d in enumerate(data):
    ax.text(d[1] + 0.08, i, f"{d[2]} {d[1]:.1f}x faster", va="center", fontsize=10.5, color="#1f2328")
ax.set_xlim(0, max(d[1] for d in data) * 1.45)
ax.set_xlabel("How many times faster the winner was (median of two runs, default settings)", fontsize=10.5, color="#5f6b7a")
for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=0); ax.grid(axis="x", color="#e3e8ef"); ax.set_axisbelow(True)
ax.set_title("PostgreSQL 19 vs MySQL 26.10 on the same 1 million rows", loc="left", fontsize=14, fontweight="bold", color="#1f2328")
plt.tight_layout(); plt.savefig("shots/chart.png", facecolor="white")
for d in reversed(data): print(d)
