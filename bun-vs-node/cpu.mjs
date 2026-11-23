// Same CPU work on both runtimes: build 300,000 records, JSON round trip, sort, aggregate, hash.
import { createHash } from "node:crypto";
const n = 300_000, cats = ["groceries", "rent", "transport", "dining", "fees"];
let seed = 42; const rnd = () => (seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648;
const rows = Array.from({ length: n }, (_, i) => ({ id: i, cat: cats[Math.floor(rnd() * 5)], amount: Math.round(rnd() * 200000) / 100 }));
const back = JSON.parse(JSON.stringify(rows));
back.sort((a, b) => b.amount - a.amount || a.id - b.id);
const totals = {};
for (const r of back) totals[r.cat] = Math.round(((totals[r.cat] || 0) + r.amount) * 100) / 100;
console.log(createHash("sha256").update(JSON.stringify(totals) + back[0].id + back[n - 1].id).digest("hex").slice(0, 16));
