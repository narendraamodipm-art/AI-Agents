// Aditi voice chatbot front end: browser speech recognition -> /api/chat (Mistral) -> browser text-to-speech.
// "बात शुरू करें" opens the mic and keeps it open (pausing only while Aditi thinks and speaks)
// until the user presses "बात बंद करें". Speech recognition works in Chrome and Edge.

const $ = (id) => document.getElementById(id);
const chatEl = $("chat"), statusEl = $("status"), stageEl = $("stage"), avatarWrap = $("avatarWrap");
const talkBtn = $("talk"), talkLabel = $("talkLabel"), textEl = $("text"), speakEl = $("speakReplies");
const LANG = "hi-IN";

const history = [];            // [{role: "user"|"assistant", content}]
let active = false;            // conversation (mic) switched on by the user
let busy = false;              // waiting for the AI
let speaking = false;
let listening = false;
let interimEl = null;
let restartTimer = null;

const setStatus = (t) => (statusEl.textContent = t);
const setState = (s) => (stageEl.dataset.state = s);   // off | listening | thinking | speaking

function addMsg(role, text) {
  $("hint")?.remove();
  const div = document.createElement("div");
  div.className = "msg " + role;
  div.textContent = text;
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
  return div;
}

// ---------- text-to-speech ----------
let voices = [];
function loadVoices() { voices = speechSynthesis.getVoices(); }
if ("speechSynthesis" in window) { loadVoices(); speechSynthesis.onvoiceschanged = loadVoices; }

// Prefer a female Hindi voice for Aditi: Microsoft Swara (Edge/Windows) or Google Hindi (Chrome).
function pickVoice(lang) {
  const base = lang.split("-")[0];
  const hindi = voices.filter((v) => v.lang.replace("_", "-").startsWith(base));
  return hindi.find((v) => /swara|kalpana|female/i.test(v.name) && /natural|online/i.test(v.name))
    || hindi.find((v) => /swara|kalpana|female/i.test(v.name))
    || hindi.find((v) => /google/i.test(v.name))
    || hindi.find((v) => !/madhur|hemant|male/i.test(v.name))
    || hindi[0];
}

function speak(text) {
  return new Promise((resolve) => {
    if (!speakEl.checked || !("speechSynthesis" in window) || !text) return resolve();
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = LANG;
    const v = pickVoice(LANG);
    if (v) u.voice = v;
    u.onend = u.onerror = () => { speaking = false; resolve(); };
    speaking = true;
    setState("speaking");
    setStatus("अदिति बोल रही है… (रोकने के लिए चेहरे पर दबाएँ)");
    speechSynthesis.speak(u);
  });
}
function stopSpeaking() {
  if ("speechSynthesis" in window) speechSynthesis.cancel();
  speaking = false;
}
avatarWrap.addEventListener("click", () => { if (speaking) stopSpeaking(); });   // interrupt Aditi

// ---------- speech recognition (stays on while the conversation is active) ----------
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let rec = null;
if (SR) {
  rec = new SR();
  rec.lang = LANG;
  rec.interimResults = true;
  rec.continuous = false;          // each sentence ends after a pause; we restart it ourselves
  rec.onstart = () => { listening = true; setState("listening"); setStatus("सुन रही हूँ… बोलिए"); };
  rec.onresult = (e) => {
    let finalText = "", interim = "";
    for (const r of e.results) (r.isFinal ? (finalText += r[0].transcript) : (interim += r[0].transcript));
    if (!interimEl) interimEl = addMsg("user interim", "");
    interimEl.textContent = finalText || interim;
    if (finalText) interimEl.dataset.final = finalText.trim();
  };
  rec.onerror = (e) => {
    if (e.error === "not-allowed" || e.error === "service-not-allowed") {
      stopConversation("माइक की अनुमति नहीं मिली। ऊपर एड्रेस बार में माइक के निशान पर क्लिक करके अनुमति दें।");
    } else if (e.error === "network") {
      stopConversation("आवाज़ पहचानने वाली सेवा तक नहीं पहुँच पाए। ब्रेव जैसे ब्राउज़र इसे रोकते हैं, यह पेज गूगल क्रोम या एज में खोलें।");
    }
    // "no-speech" and "aborted" are normal: onend simply starts listening again
  };
  rec.onend = () => {
    listening = false;
    const said = interimEl?.dataset.final;
    if (interimEl && !said) interimEl.remove();
    if (interimEl && said) { interimEl.classList.remove("interim"); interimEl.textContent = said; }
    interimEl = null;
    if (said) sendMessage(said, true);
    else scheduleListen();
  };
}

function listen() {
  clearTimeout(restartTimer);
  if (!rec || !active || busy || speaking || listening) return;
  try { rec.start(); } catch { /* already running */ }
}
function scheduleListen() {
  clearTimeout(restartTimer);
  if (active) restartTimer = setTimeout(listen, 250);
}

function startConversation() {
  if (!rec) {
    setStatus("इस ब्राउज़र में माइक नहीं चलता। गूगल क्रोम या एज इस्तेमाल करें, या नीचे लिखें।");
    return;
  }
  active = true;
  avatarWrap.hidden = false;
  talkBtn.classList.add("on");
  talkLabel.textContent = "बात बंद करें";
  setStatus("माइक चालू हो रहा है…");
  listen();
}

function stopConversation(message) {
  active = false;
  clearTimeout(restartTimer);
  if (listening) rec.abort();
  stopSpeaking();
  avatarWrap.hidden = true;
  talkBtn.classList.remove("on");
  talkLabel.textContent = "बात शुरू करें";
  setState("off");
  setStatus(message || "बातचीत बंद है। दोबारा शुरू करने के लिए बटन दबाइए।");
}

talkBtn.addEventListener("click", () => (active ? stopConversation() : startConversation()));

// ---------- talking to the AI ----------
async function sendMessage(text, alreadyShown = false) {
  text = text.trim();
  if (!text || busy) return;
  if (!alreadyShown) addMsg("user", text);
  history.push({ role: "user", content: text });
  busy = true;
  if (listening) rec.abort();          // don't listen while waiting for the reply
  setState("thinking");
  setStatus("अदिति सोच रही है…");
  let reply = "";
  try {
    const r = await fetch("api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: history.slice(-20) }),
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(j.error || "सर्वर से जवाब नहीं आया।");
    reply = j.reply;
    history.push({ role: "assistant", content: reply });
    addMsg("bot", reply);
  } catch (e) {
    history.pop();                     // let the user retry the same message
    addMsg("error", "जवाब नहीं मिला। " + (/[ऀ-ॿ]/.test(e.message) ? e.message : "इंटरनेट कनेक्शन जाँचें और दोबारा कोशिश करें।"));
  } finally {
    busy = false;
  }
  if (reply && active) await speak(reply);
  else if (reply) speak(reply);        // typed message with the mic off: still read the reply aloud

  if (active) { setState("listening"); scheduleListen(); }
  else { setState("off"); setStatus(avatarWrap.hidden ? "बात करने के लिए नीचे का बटन दबाइए" : ""); }
}

$("form").addEventListener("submit", (e) => {
  e.preventDefault();
  const t = textEl.value;
  textEl.value = "";
  stopSpeaking();
  sendMessage(t);
});

$("clear").addEventListener("click", () => {
  stopSpeaking();
  history.length = 0;
  chatEl.innerHTML = '<p class="hint" id="hint">नई बातचीत शुरू। बोलिए या नीचे लिखिए।</p>';
  if (active) scheduleListen();
});
