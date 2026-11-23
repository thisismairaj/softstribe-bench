"""SQLite vs DuckDB on the same data. Runs inside Docker (see run.sh). Writes results.csv and versions.txt."""
import csv, os, random, sqlite3, statistics, time, datetime
import duckdb

OUT = "/work"   # CSVs and results (shared folder)
DB = "/db"     # databases on the container's own disk: the Windows shared folder makes every fsync slow
os.makedirs(DB, exist_ok=True)
N, CUST, RUNS = 1_000_000, 100_000, 10
random.seed(42)
cats = ["groceries", "rent", "transport", "dining", "utilities", "shopping", "health", "travel", "fees", "salary"]
tx, cu = f"{OUT}/transactions.csv", f"{OUT}/customers.csv"
if not os.path.exists(tx):
    d0 = datetime.date(2020, 1, 1)
    with open(tx, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "tx_date", "customer_id", "category", "amount"])
        for i in range(1, N + 1):
            w.writerow([i, (d0 + datetime.timedelta(days=random.randrange(1461))).isoformat(), random.randint(1, CUST), random.choice(cats), round(random.uniform(1, 2000), 2)])
    with open(cu, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["customer_id", "country", "segment"])
        for i in range(1, CUST + 1):
            w.writerow([i, random.choice(["PK", "US", "GB", "AE", "DE", "IN"]), random.choice(["retail", "business"])])

QUERIES = {
    "sum_by_category": "SELECT category, SUM(amount) FROM transactions GROUP BY category",
    "count_by_month": "SELECT substr(tx_date, 1, 7) AS m, COUNT(*) FROM transactions GROUP BY m ORDER BY m",
    "join_country_segment": "SELECT c.country, c.segment, SUM(t.amount) FROM transactions t JOIN customers c ON c.customer_id = t.customer_id GROUP BY c.country, c.segment",
    "top_10_customers": "SELECT customer_id, SUM(amount) s FROM transactions GROUP BY customer_id ORDER BY s DESC LIMIT 10",
    "point_lookup_by_id": "SELECT * FROM transactions WHERE id = 777777",
}

def timed(fn):
    t = time.perf_counter(); fn(); return time.perf_counter() - t

rows = []
def rec(engine, test, secs): rows.append({"engine": engine, "test": test, "seconds": round(secs, 6)})

# ---- SQLite: load with csv module + executemany in one transaction (the usual Python way) ----
for run in range(3):
    p = f"{DB}/sqlite.db"
    if os.path.exists(p): os.remove(p)
    def load_sqlite():
        con = sqlite3.connect(p)
        con.execute("CREATE TABLE transactions (id INTEGER PRIMARY KEY, tx_date TEXT, customer_id INTEGER, category TEXT, amount REAL)")
        con.execute("CREATE TABLE customers (customer_id INTEGER PRIMARY KEY, country TEXT, segment TEXT)")
        with open(tx) as f:
            r = csv.reader(f); next(r); con.executemany("INSERT INTO transactions VALUES (?,?,?,?,?)", r)
        with open(cu) as f:
            r = csv.reader(f); next(r); con.executemany("INSERT INTO customers VALUES (?,?,?)", r)
        con.commit(); con.close()
    rec("sqlite", "load_csv", timed(load_sqlite))
rec("sqlite", "file_size_mb", os.path.getsize(f"{DB}/sqlite.db") / 1e6)
con = sqlite3.connect(f"{DB}/sqlite.db")
for name, q in QUERIES.items():
    con.execute(q).fetchall()  # warm-up
    for _ in range(RUNS): rec("sqlite", name, timed(lambda: con.execute(q).fetchall()))
con.close()

# ---- DuckDB: load with read_csv (its documented way) ----
for run in range(3):
    p = f"{DB}/duck.duckdb"
    for ext in ("", ".wal"):
        if os.path.exists(p + ext): os.remove(p + ext)
    def load_duck():
        con = duckdb.connect(p)
        con.execute(f"CREATE TABLE transactions AS SELECT * FROM read_csv('{tx}', header=true, columns={{'id':'INTEGER','tx_date':'VARCHAR','customer_id':'INTEGER','category':'VARCHAR','amount':'DOUBLE'}})")
        con.execute(f"CREATE TABLE customers AS SELECT * FROM read_csv('{cu}', header=true, columns={{'customer_id':'INTEGER','country':'VARCHAR','segment':'VARCHAR'}})")
        con.execute("CHECKPOINT"); con.close()
    rec("duckdb", "load_csv", timed(load_duck))
rec("duckdb", "file_size_mb", os.path.getsize(f"{DB}/duck.duckdb") / 1e6)
con = duckdb.connect(f"{DB}/duck.duckdb", read_only=True)
for name, q in QUERIES.items():
    con.execute(q).fetchall()
    for _ in range(RUNS): rec("duckdb", name, timed(lambda: con.execute(q).fetchall()))
con.close()

# ---- App-style work (where SQLite is meant to shine): 1,000 single-row inserts, each its own transaction,
# and 1,000 updates by primary key, each its own transaction. Fresh copies so the analytics files stay as loaded.
import shutil
def oltp(engine):
    if engine == "sqlite":
        shutil.copy(f"{DB}/sqlite.db", f"{DB}/oltp.db"); con = sqlite3.connect(f"{DB}/oltp.db", isolation_level=None)
    else:
        shutil.copy(f"{DB}/duck.duckdb", f"{DB}/oltp.duckdb"); con = duckdb.connect(f"{DB}/oltp.duckdb")
    def ins():
        for i in range(1000):
            con.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?)", [N + 1 + i, "2024-01-01", 5, "fees", 1.5])
    def upd():
        for i in range(1, 1001):
            con.execute("UPDATE transactions SET amount = amount + 1 WHERE id = ?", [i * 997])
    def batch():
        con.execute("BEGIN")
        for i in range(10000):
            con.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?)", [N + 5001 + i, "2024-01-01", 5, "fees", 1.5])
        con.execute("COMMIT")
    for _ in range(3):
        rec(engine, "insert_10000_rows_one_transaction", timed(batch))
        con.execute("DELETE FROM transactions WHERE id > ?", [N])
    for _ in range(3):
        rec(engine, "insert_1000_single_rows", timed(ins))
        con.execute("DELETE FROM transactions WHERE id > ?", [N])
        rec(engine, "update_1000_rows_by_id", timed(upd))
    con.close()
oltp("sqlite"); oltp("duckdb")
# SQLite in the mode its docs recommend for apps: WAL journal, synchronous=NORMAL
shutil.copy(f"{DB}/sqlite.db", f"{DB}/wal.db"); con = sqlite3.connect(f"{DB}/wal.db", isolation_level=None)
con.execute("PRAGMA journal_mode=WAL"); con.execute("PRAGMA synchronous=NORMAL")
for _ in range(3):
    def ins():
        for i in range(1000):
            con.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?)", [N + 1 + i, "2024-01-01", 5, "fees", 1.5])
    rec("sqlite_wal", "insert_1000_single_rows", timed(ins))
    con.execute("DELETE FROM transactions WHERE id > ?", [N])
con.close()

# ---- Same answers? ----
a = sqlite3.connect(f"{DB}/sqlite.db"); b = duckdb.connect(f"{DB}/duck.duckdb", read_only=True)
for name, q in QUERIES.items():
    ra = sorted(tuple(round(x, 2) if isinstance(x, float) else x for x in r) for r in a.execute(q).fetchall())
    rb = sorted(tuple(round(x, 2) if isinstance(x, float) else x for x in r) for r in b.execute(q).fetchall())
    print("same result" if ra == rb else "DIFFERENT", name)

with open(f"{OUT}/results.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["engine", "test", "seconds"]); w.writeheader(); w.writerows(rows)
with open(f"{OUT}/versions.txt", "w") as f:
    f.write(f"sqlite {sqlite3.sqlite_version}\nduckdb {duckdb.__version__}\npython {os.sys.version.split()[0]}\nrows {N} customers {CUST} runs {RUNS}\n")
print(open(f"{OUT}/versions.txt").read())
summ = {}
for r in rows: summ.setdefault((r["engine"], r["test"]), []).append(r["seconds"])
for (e, t), v in sorted(summ.items(), key=lambda x: (x[0][1], x[0][0])): print(f"{t:22s} {e:7s} median {statistics.median(v):.6f}  min {min(v):.6f}")
