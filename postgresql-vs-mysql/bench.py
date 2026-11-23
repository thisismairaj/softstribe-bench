"""PostgreSQL vs MySQL on the same data, default server settings. Runs in a client container (see run.sh).
ENGINE env = postgres | mysql. Appends to /out/results.csv."""
import csv, json, os, statistics, threading, time
from decimal import Decimal

ENGINE = os.environ["ENGINE"]
OUT, DATA, RUNS = "/out", "/data", 10
if ENGINE == "postgres":
    import psycopg

    def connect():
        return psycopg.connect("host=db user=postgres password=bench dbname=bench", autocommit=True)
elif os.environ.get("MYDRIVER") == "connector":  # Oracle's official driver, compiled C extension
    import mysql.connector

    def connect():
        return mysql.connector.connect(host="db", user="root", password="bench", database="bench", autocommit=True,
                                       allow_local_infile=True, use_pure=False)
else:
    import pymysql

    def connect():
        return pymysql.connect(host="db", user="root", password="bench", database="bench", autocommit=True, local_infile=True)


def timed(fn):
    t = time.perf_counter()
    fn()
    return time.perf_counter() - t


rows = []


def rec(test, secs):
    rows.append({"engine": ENGINE, "test": test, "seconds": round(secs, 6)})


con = connect()
cur = con.cursor()
DDL = [
    "DROP TABLE IF EXISTS transactions",
    "DROP TABLE IF EXISTS customers",
    "CREATE TABLE transactions (id INTEGER PRIMARY KEY, tx_date VARCHAR(10), customer_id INTEGER, category VARCHAR(20), amount NUMERIC(12,2))",
    "CREATE TABLE customers (customer_id INTEGER PRIMARY KEY, country VARCHAR(2), segment VARCHAR(10))",
]


def load():
    for d in DDL:
        cur.execute(d)
    for tbl, f in (("transactions", "transactions.csv"), ("customers", "customers.csv")):
        if ENGINE == "postgres":  # COPY: Postgres's bulk-load path
            with cur.copy(f"COPY {tbl} FROM STDIN WITH (FORMAT csv, HEADER true)") as cp:
                with open(f"{DATA}/{f}", "rb") as fh:
                    while chunk := fh.read(1 << 20):
                        cp.write(chunk)
        else:  # LOAD DATA: MySQL's bulk-load path
            cur.execute(f"LOAD DATA LOCAL INFILE '{DATA}/{f}' INTO TABLE {tbl} "
                        "FIELDS TERMINATED BY ',' LINES TERMINATED BY '\\r\\n' IGNORE 1 LINES")  # the CSV has CRLF endings


for _ in range(3):
    rec("load_csv", timed(load))
cur.execute("ANALYZE transactions" if ENGINE == "postgres" else "ANALYZE TABLE transactions")
if ENGINE == "mysql":
    cur.fetchall()
if ENGINE == "postgres":
    cur.execute("SELECT pg_total_relation_size('transactions')")
else:
    cur.execute("SELECT data_length + index_length FROM information_schema.tables "
                "WHERE table_schema='bench' AND table_name='transactions'")
rec("table_size_mb", float(cur.fetchone()[0]) / 1e6)

Q = {
    "sum_by_category": "SELECT category, SUM(amount) FROM transactions GROUP BY category",
    "count_by_month": "SELECT SUBSTRING(tx_date, 1, 7) AS m, COUNT(*) FROM transactions GROUP BY SUBSTRING(tx_date, 1, 7) ORDER BY m",
    "join_country_segment": "SELECT c.country, c.segment, SUM(t.amount) FROM transactions t JOIN customers c "
                            "ON c.customer_id = t.customer_id GROUP BY c.country, c.segment",
    "top_10_customers": "SELECT customer_id, SUM(amount) AS s FROM transactions GROUP BY customer_id ORDER BY s DESC LIMIT 10",
    "point_lookup_by_id": "SELECT * FROM transactions WHERE id = 777777",
    "filter_one_customer_no_index": "SELECT COUNT(*), SUM(amount) FROM transactions WHERE customer_id = 4242",
}


def norm(r):
    return tuple(str(round(float(x), 2)) if isinstance(x, (float, Decimal)) else str(x) for x in r)


answers = {}
for name, q in Q.items():
    cur.execute(q)
    answers[name] = sorted(norm(r) for r in cur.fetchall())  # warm-up run, also the answer check
    for _ in range(RUNS):
        rec(name, timed(lambda: (cur.execute(q), cur.fetchall())))
cur.execute("CREATE INDEX ix_tx_customer ON transactions (customer_id)")
q = Q["filter_one_customer_no_index"]
cur.execute(q)
cur.fetchall()
for _ in range(RUNS):
    rec("filter_one_customer_with_index", timed(lambda: (cur.execute(q), cur.fetchall())))


def ins1000():  # each statement its own commit, like most apps
    for i in range(1000):
        cur.execute("INSERT INTO transactions VALUES (%s, %s, %s, %s, %s)", (2_000_000 + i, "2024-01-01", 5, "fees", 1.5))


def upd1000():
    for i in range(1, 1001):
        cur.execute("UPDATE transactions SET amount = amount + 1 WHERE id = %s", (i * 997,))


def batch10k():
    cur.execute("BEGIN" if ENGINE == "postgres" else "START TRANSACTION")
    for i in range(10000):
        cur.execute("INSERT INTO transactions VALUES (%s, %s, %s, %s, %s)", (3_000_000 + i, "2024-01-01", 5, "fees", 1.5))
    cur.execute("COMMIT")


def concurrent():  # 8 clients at once, each 500 single-row inserts on its own connection
    def worker(w):
        c = connect()
        k = c.cursor()
        for i in range(500):
            k.execute("INSERT INTO transactions VALUES (%s, %s, %s, %s, %s)", (4_000_000 + w * 1000 + i, "2024-01-01", 5, "fees", 1.5))
        c.close()
    ts = [threading.Thread(target=worker, args=(w,)) for w in range(8)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()


for _ in range(3):
    rec("insert_1000_single_rows", timed(ins1000))
    cur.execute("DELETE FROM transactions WHERE id >= 2000000")
    rec("update_1000_rows_by_id", timed(upd1000))
    rec("insert_10000_rows_one_transaction", timed(batch10k))
    cur.execute("DELETE FROM transactions WHERE id >= 2000000")
    rec("8_clients_4000_inserts", timed(concurrent))
    cur.execute("DELETE FROM transactions WHERE id >= 2000000")

cur.execute("SELECT version()")
ver = cur.fetchone()[0]
if ENGINE == "mysql":
    ver += " driver=" + (os.environ.get("MYDRIVER") or "pymysql")
    if os.environ.get("MYDRIVER") == "connector":
        import mysql.connector
        ver += " " + mysql.connector.__version__ + " c_ext=" + str(type(con).__name__)
first = not os.path.exists(f"{OUT}/results.csv")
with open(f"{OUT}/results.csv", "a", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["engine", "test", "seconds"])
    if first:
        w.writeheader()
    w.writerows(rows)
json.dump(answers, open(f"{OUT}/answers-{ENGINE}.json", "w"), indent=0)
with open(f"{OUT}/versions.txt", "a") as f:
    f.write(f"{ENGINE}: {ver}\n")
summ = {}
for r in rows:
    summ.setdefault(r["test"], []).append(r["seconds"])
for t, v in summ.items():
    print(f"{ENGINE:8s} {t:34s} median {statistics.median(v):.6f}")
