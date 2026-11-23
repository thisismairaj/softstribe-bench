// node:http server, runs unchanged on Node and on Bun.
import http from "node:http";
const body = JSON.stringify({ ok: true, msg: "hello" });
http.createServer((req, res) => { res.writeHead(200, { "content-type": "application/json" }); res.end(body); }).listen(3000, "0.0.0.0");
