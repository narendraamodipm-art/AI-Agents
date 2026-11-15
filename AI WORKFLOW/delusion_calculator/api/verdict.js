// POST /api/verdict - asks Mistral for a witty verdict. Runs as a Vercel serverless
// function in production and is reused by server.js for local development.
// Needs the MISTRAL_API_KEY environment variable (never sent to the browser).

const MODEL = "ministral-8b-latest";

const SYSTEM_PROMPT = `You are the witty, brutally honest but good-natured host of a satirical Indian website called "Are Indian Women Delusional?".
A user has listed what they want in a husband, and a statistical model has estimated what share of Indian men match.
Write a short verdict (3-5 sentences, under 110 words) in playful Indian-English with light Hinglish.
Rules:
- Roast the EXPECTATIONS and the maths, never the user's worth, looks, caste, religion, region or women as a group.
- Mention the actual percentage / number of men and which 1-2 filters hurt the most.
- If the percentage is healthy (above ~5%), congratulate them for being realistic.
- End with one practical, kind tip (which filter to relax).
- Plain text only: no markdown, no asterisks, no bold, no hashtags, max 2 emojis. No profanity.`;

// Best-effort per-IP limit (per warm instance) to stop casual abuse of the API key.
const hits = new Map();
const LIMIT = 15, WINDOW_MS = 10 * 60 * 1000;
function rateLimited(ip) {
  const now = Date.now();
  const recent = (hits.get(ip) || []).filter((t) => now - t < WINDOW_MS);
  recent.push(now);
  hits.set(ip, recent);
  if (hits.size > 5000) hits.clear();
  return recent.length > LIMIT;
}

function send(res, status, obj) {
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.end(JSON.stringify(obj));
}

const clip = (v, n) => String(v ?? "").slice(0, n);

module.exports = async function handler(req, res) {
  if (req.method !== "POST") return send(res, 405, { error: "Method not allowed" });
  const ip = (req.headers["x-forwarded-for"] || req.socket?.remoteAddress || "?").split(",")[0].trim();
  if (rateLimited(ip)) return send(res, 429, { error: "Too many verdicts, take a chai break and try again in a few minutes" });

  let data = req.body;
  if (typeof data === "string") { try { data = JSON.parse(data); } catch { data = null; } }
  if (!data || typeof data !== "object") return send(res, 400, { error: "Invalid JSON" });

  const apiKey = process.env.MISTRAL_API_KEY;
  if (!apiKey) return send(res, 500, { error: "MISTRAL_API_KEY is not configured on the server" });

  const userMsg = `Her wishlist:\n${clip(JSON.stringify(data.criteria, null, 2), 1500)}\n\n` +
    `Result: ${clip(data.percent, 30)} of single Indian men aged 18-60 match (about ${clip(data.count, 30)} men).\n` +
    `Biggest filters (pool share kept by each): ${clip(JSON.stringify(data.filters), 600)}\n` +
    `Delusion level: ${clip(data.level, 60)}`;

  try {
    const r = await fetch("https://api.mistral.ai/v1/chat/completions", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiKey}` },
      body: JSON.stringify({
        model: MODEL,
        temperature: 0.9,
        max_tokens: 250,
        messages: [{ role: "system", content: SYSTEM_PROMPT }, { role: "user", content: userMsg }],
      }),
    });
    const j = await r.json();
    if (!r.ok) return send(res, r.status === 429 ? 429 : 502, { error: j.message || j.detail || "Mistral API error" });
    const text = (j.choices?.[0]?.message?.content || "").replace(/[*_#`]+/g, "").trim();
    send(res, 200, { verdict: text });
  } catch (e) {
    send(res, 502, { error: "Could not reach Mistral: " + e.message });
  }
};

module.exports.MODEL = MODEL;
