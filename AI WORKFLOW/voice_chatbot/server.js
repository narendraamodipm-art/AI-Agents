// Local development server (zero dependencies): serves the page and the /api/chat function.
// Run:  node server.js   then open http://localhost:3001 in Chrome or Edge.
// In production, deploy this folder to Vercel, which serves api/chat.js as a serverless function.
const http = require("http");
const fs = require("fs");
const path = require("path");
const chat = require("./api/chat");

const PORT = process.env.PORT || 3001;
const ROOT = __dirname;

// Load MISTRAL_API_KEY from the repo-root .env (two levels up) or a local .env, unless already set.
for (const file of [path.resolve(ROOT, "..", "..", ".env"), path.resolve(ROOT, ".env")]) {
  if (!fs.existsSync(file)) continue;
  for (const line of fs.readFileSync(file, "utf8").split(/\r?\n/)) {
    const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/);
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^["']|["']$/g, "");
  }
}

const MIME = { ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8" };
const PUBLIC = new Set(["index.html", "style.css", "app.js"]);

http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);

  if (url.pathname === "/api/chat") {
    let body = "";
    for await (const chunk of req) {
      body += chunk;
      if (body.length > 100000) { res.writeHead(413); return res.end("Payload too large"); }
    }
    req.body = body;
    return chat(req, res);
  }
  if (req.method !== "GET") { res.writeHead(405); return res.end("Method not allowed"); }

  const rel = url.pathname === "/" ? "index.html" : decodeURIComponent(url.pathname).replace(/^\/+/, "");
  if (!PUBLIC.has(rel)) { res.writeHead(404); return res.end("Not found"); }
  const file = path.join(ROOT, rel);
  fs.readFile(file, (err, buf) => {
    if (err) { res.writeHead(404); return res.end("Not found"); }
    res.writeHead(200, { "Content-Type": MIME[path.extname(file)] });
    res.end(buf);
  });
}).listen(PORT, () => {
  console.log(`Voice chatbot running at http://localhost:${PORT}`);
  console.log(process.env.MISTRAL_API_KEY ? `Mistral models: ${chat.MODEL}` : "WARNING: MISTRAL_API_KEY not found - replies will fail.");
});
