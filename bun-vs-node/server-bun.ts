// Bun's own server API.
const body = JSON.stringify({ ok: true, msg: "hello" });
Bun.serve({ port: 3000, hostname: "0.0.0.0", fetch() { return new Response(body, { headers: { "content-type": "application/json" } }); } });
