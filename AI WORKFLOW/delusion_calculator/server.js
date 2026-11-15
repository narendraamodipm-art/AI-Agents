// Local development server (zero dependencies): serves the static site and the /api/verdict function.
// Run:  node server.js   then open http://localhost:3000
// In production the site is deployed on Vercel, which serves api/verdict.js as a serverless function.
const http = require("http");
const fs = require("fs");
const path = require("path");
const verdict = require("./api/verdict");

const PORT = process.env.PORT || 3000;
const ROOT = __dirname;

// Load MISTRAL_API_KEY from the repo-root .env (two levels up) or a local .env, unless already set.
for (const file of [path.resolve(ROOT, "..", "..", ".env"), path.resolve(ROOT, ".env")]) {
  if (!fs.existsSync(file)) continue;
  for (const line of fs.readFileSync(file, "utf8").split(/\r?\n/)) {
    const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/);
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^["']|["']$/g, "");
  }
}

const MIME = { ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp", ".ico": "image/x-icon" };
const PUBLIC = new Set(["index.html", "style.css", "app.js"]);

http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);

  if (url.pathname === "/api/verdict") {
    let body = "";
    for await (const chunk of req) {
      body += chunk;
      if (body.length > 20000) { res.writeHead(413); return res.end("Payload too large"); }
    }
    req.body = body;
    return verdict(req, res);
  }
  if (req.method !== "GET") { res.writeHead(405); return res.end("Method not allowed"); }

  const rel = url.pathname === "/" ? "index.html" : decodeURIComponent(url.pathname).replace(/^\/+/, "");
  const file = path.resolve(ROOT, rel);
  const allowed = PUBLIC.has(rel) || (rel.startsWith("memes/") && file.startsWith(path.join(ROOT, "memes") + path.sep));
  if (!allowed) { res.writeHead(404); return res.end("Not found"); }
  fs.readFile(file, (err, buf) => {
    if (err) { res.writeHead(404); return res.end("Not found"); }
    res.writeHead(200, { "Content-Type": MIME[path.extname(file).toLowerCase()] || "application/octet-stream" });
    res.end(buf);
  });
}).listen(PORT, () => {
  console.log(`Delusion Calculator running at http://localhost:${PORT}`);
  console.log(process.env.MISTRAL_API_KEY ? `Mistral model: ${verdict.MODEL}` : "WARNING: MISTRAL_API_KEY not found - AI verdicts will fail.");
});
