// POST /api/chat - sends the conversation to Mistral and returns the assistant's reply.
// Runs as a Vercel serverless function in production and is reused by server.js locally.
// Needs the MISTRAL_API_KEY environment variable (never sent to the browser).

// The free Mistral key allows only 2 requests per minute PER MODEL, so when one model is
// rate-limited (429) we try the next. Best model first.
const MODELS = ["mistral-small-latest", "ministral-8b-latest", "open-mistral-nemo", "ministral-3b-latest"];
const MODEL = MODELS.join(" -> ");

const SYSTEM_PROMPT = `Your name is Aditi (अदिति). You are a friendly, warm, helpful female voice assistant who speaks Hindi.
Everything you write is read aloud by a Hindi text-to-speech voice.
- ALWAYS reply in Hindi written in Devanagari script, even if the user speaks English or Hinglish. Never use Roman (English) letters.
- Use simple, everyday spoken Hindi. Common English words (phone, computer, internet) are fine, but write them in Devanagari: फ़ोन, कंप्यूटर, इंटरनेट.
- Speak as a woman (for example "मैं कर सकती हूँ", not "कर सकता हूँ").
- Keep answers short and conversational: usually 1-3 sentences. Give more detail only when the user asks for it.
- Plain spoken text only: no markdown, bullet points, tables, code blocks, URLs or emojis.
- If someone asks your name, say you are Aditi.
- If you did not understand (speech recognition can mishear words), ask briefly what they meant.
- For today's date, day or time, use ONLY the "current date and time" given below. Never guess a date.
- You have no internet access. For live information (news, weather right now, prices, cricket scores) say honestly that you don't have live information; never make it up.`;

// Today's date and time in India, in Hindi, e.g. "शनिवार, 21 नवंबर 2026, शाम 3:45".
function nowInIndia() {
  const d = new Date();
  const date = new Intl.DateTimeFormat("hi-IN", { timeZone: "Asia/Kolkata", weekday: "long", day: "numeric", month: "long", year: "numeric" }).format(d);
  const time = new Intl.DateTimeFormat("hi-IN", { timeZone: "Asia/Kolkata", hour: "numeric", minute: "2-digit", dayPeriod: "short" }).format(d);
  return `${date}, ${time} (भारतीय समय)`;
}

const MAX_MESSAGES = 20;      // only the most recent turns are sent to the model
const MAX_CHARS = 2000;       // per message

// Best-effort per-IP limit (per warm instance) to stop casual abuse of the API key.
const hits = new Map();
const LIMIT = 40, WINDOW_MS = 10 * 60 * 1000;
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

// Keep only well-formed user/assistant text turns, newest last, starting with a user turn.
function cleanHistory(messages) {
  if (!Array.isArray(messages)) return [];
  const out = messages
    .filter((m) => m && (m.role === "user" || m.role === "assistant") && typeof m.content === "string" && m.content.trim())
    .map((m) => ({ role: m.role, content: m.content.slice(0, MAX_CHARS) }))
    .slice(-MAX_MESSAGES);
  while (out.length && out[0].role !== "user") out.shift();
  return out;
}

module.exports = async function handler(req, res) {
  if (req.method !== "POST") return send(res, 405, { error: "यह तरीका मान्य नहीं है।" });
  const ip = (req.headers["x-forwarded-for"] || req.socket?.remoteAddress || "?").split(",")[0].trim();
  if (rateLimited(ip)) return send(res, 429, { error: "बहुत ज़्यादा संदेश भेजे गए हैं। कुछ मिनट रुककर कोशिश करें।" });

  let data = req.body;
  if (typeof data === "string") { try { data = JSON.parse(data); } catch { data = null; } }
  const history = cleanHistory(data && data.messages);
  if (!history.length || history[history.length - 1].role !== "user") return send(res, 400, { error: "कम से कम एक संदेश भेजिए।" });

  const apiKey = (process.env.MISTRAL_API_KEY || "").replace(/^﻿/, "").trim();
  if (!apiKey) {
    console.error("MISTRAL_API_KEY is not configured on the server");
    return send(res, 500, { error: "सर्वर पर एआई की चाबी सेट नहीं है।" });
  }

  try {
    for (const model of MODELS) {
      const r = await fetch("https://api.mistral.ai/v1/chat/completions", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiKey}` },
        body: JSON.stringify({
          model,
          temperature: 0.7,
          max_tokens: 400,
          messages: [{ role: "system", content: `${SYSTEM_PROMPT}\n\nCurrent date and time: ${nowInIndia()}` }, ...history],
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (r.status === 429) continue;   // this model's per-minute quota is used up; try the next
      if (!r.ok) {
        console.error("Mistral API error:", r.status, j.message || j.detail);
        return send(res, 502, { error: "एआई सेवा में दिक्कत आई। थोड़ी देर बाद कोशिश करें।" });
      }
      const text = (j.choices?.[0]?.message?.content || "")
        .replace(/[*_#`]+/g, "")
        .replace(/[\p{Extended_Pictographic}\u{1F3FB}-\u{1F3FF}️‍]/gu, "")   // emojis would be read aloud
        .replace(/\bAditi\b/gi, "अदिति")                               // keep her name in Devanagari
        .replace(/[ \t]+\n/g, "\n")
        .trim();
      return send(res, 200, { reply: text || "माफ़ कीजिए, इस पर मेरे पास कहने को कुछ नहीं है।", model });
    }
    send(res, 429, { error: "अभी बहुत सारे सवाल आ गए हैं। लगभग एक मिनट रुककर फिर से पूछिए।" });
  } catch (e) {
    console.error("Could not reach Mistral:", e.message);
    send(res, 502, { error: "एआई सेवा तक नहीं पहुँच पाए। इंटरनेट जाँचकर दोबारा कोशिश करें।" });
  }
};

module.exports.MODEL = MODEL;
