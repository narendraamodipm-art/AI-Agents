// Are Indian Women Delusional? - husband reality calculator.
// The percentage is computed locally from rough Indian population estimates;
// the AI (Mistral via server.js) only writes the verdict.

const INDIAN_MEN_18_60 = 430_000_000; // approx. men aged 18-60 in India

// Age bands: [from, to, share of men 18-60 (relative), share unmarried, income multiplier vs overall median]
const AGE_BANDS = [
  [18, 20, 8.0, 0.97, 0.40],
  [21, 25, 13.0, 0.78, 0.70],
  [26, 30, 12.5, 0.42, 1.00],
  [31, 35, 12.0, 0.14, 1.20],
  [36, 40, 11.0, 0.06, 1.30],
  [41, 45, 10.0, 0.04, 1.30],
  [46, 50, 9.0, 0.03, 1.25],
  [51, 55, 8.0, 0.025, 1.20],
  [56, 60, 6.5, 0.02, 1.15],
];
const INCOME_MEDIAN_LPA = 3.0; // overall median annual income of earning men (lakhs)
const INCOME_SIGMA = 0.95;     // log-normal spread
const HEIGHT_MEAN = 165.5, HEIGHT_SD = 7.0; // cm, NFHS-5 ballpark
const LOOKS_MEAN = 5, LOOKS_SD = 1.7;

const TYPE_RATES = {
  family:      ["Family oriented", 0.60],
  smart:       ["Smart / Intelligent", 0.35],
  romantic:    ["Romantic", 0.40],
  emotional:   ["Emotionally available", 0.30],
  caring:      ["Caring", 0.50],
  goodlooking: ["Good looking", 0.25],
  funny:       ["Funny", 0.40],
};
const LOYALTY = { any: ["Any", 1], loyal: ["Loyal", 0.70], ultra: ["Never looks at other women", 0.30] };
const DRESSING = { any: ["Any", 1], decent: ["Decent", 0.60], stylish: ["Stylish", 0.25], model: ["Model-level drip", 0.04] };
const EDUCATION = { any: ["Any", 1], grad: ["Graduate", 0.30], pg: ["Post-graduate", 0.10], elite: ["IIT / IIM / foreign degree", 0.006] };
const HABITS = { any: ["Any", 1], nosmoke: ["Doesn't smoke", 0.65], clean: ["No smoking, no drinking", 0.45] };

// ---------- maths ----------
function erf(x) { // Abramowitz-Stegun 7.1.26
  const s = Math.sign(x); x = Math.abs(x);
  const t = 1 / (1 + 0.3275911 * x);
  const y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x);
  return s * y;
}
const normCdf = (z) => 0.5 * (1 + erf(z / Math.SQRT2));
const pAbove = (x, mean, sd) => 1 - normCdf((x - mean) / sd);

function ageBand(age) { return AGE_BANDS.find(([a, b]) => age >= a && age <= b); }

// Returns fraction of ALL men 18-60 who are in the age range, single, and earn >= salary.
function agePoolShares(min, max, salary) {
  const total = AGE_BANDS.reduce((s, [a, b, w]) => s + w, 0);
  let inAge = 0, single = 0, earning = 0;
  for (let age = min; age <= max; age++) {
    const [a, b, w, unmarried, mult] = ageBand(age);
    const share = (w / (b - a + 1)) / total;
    const pInc = salary > 0 ? 1 - normCdf(Math.log(salary / (INCOME_MEDIAN_LPA * mult)) / INCOME_SIGMA) : 1;
    inAge += share;
    single += share * unmarried;
    earning += share * unmarried * pInc;
  }
  return { inAge, single, earning };
}

// Base pool = all SINGLE (unmarried) men aged 18-60, so "no filters" = 100%.
const SINGLE_SHARE = agePoolShares(18, 60, 0).single;
const SINGLE_MEN = INDIAN_MEN_18_60 * SINGLE_SHARE; // ~12.6 crore

function calculate(c) {
  const { single, earning } = agePoolShares(c.ageMin, c.ageMax, c.salary);
  let p = single / SINGLE_SHARE;
  const steps = [["All single men 18–60", 1]];
  if (c.ageMin > 18 || c.ageMax < 60) steps.push([`Aged ${c.ageMin}–${c.ageMax}`, p]);
  if (c.salary > 0) { p = earning / SINGLE_SHARE; steps.push([`Earns ${c.salaryLabel}`, p]); }
  if (c.height > 0) { p *= pAbove(c.height, HEIGHT_MEAN, HEIGHT_SD); steps.push([`At least ${c.heightLabel}`, p]); }
  if (c.looks > 0) { p *= pAbove(c.looks - 0.5, LOOKS_MEAN, LOOKS_SD); steps.push([`Looks ${c.looks}/10 or better`, p]); }

  if (c.types.length) {
    // traits are somewhat correlated, so soften the pure product a bit
    const prod = c.types.reduce((s, t) => s * TYPE_RATES[t][1], 1);
    p *= Math.pow(prod, 0.85);
    steps.push([c.types.map((t) => TYPE_RATES[t][0]).join(" + "), p]);
  }
  for (const [key, table, label] of [["loyalty", LOYALTY, "Loyalty"], ["dressing", DRESSING, "Dressing"], ["education", EDUCATION, "Education"], ["habits", HABITS, "Habits"]]) {
    const [name, rate] = table[c[key]];
    if (rate < 1) { p *= rate; steps.push([`${label}: ${name}`, p]); }
  }
  return { fraction: p, steps };
}

// [label, colour class, meme key]
function level(pct) {
  if (pct >= 5) return ["Totally realistic 💚", "good", "realistic"];
  if (pct >= 1) return ["Slightly optimistic 🙂", "ok", "optimistic"];
  if (pct >= 0.1) return ["Mildly delusional 🤔", "warn", "mild"];
  if (pct >= 0.01) return ["Very delusional 😬", "bad", "very"];
  if (pct >= 0.001) return ["Extremely delusional 🚩", "bad", "extreme"];
  return ["Certified delusional 🦄", "unicorn", "certified"];
}

// Meme cards per level. To use your own picture, drop memes/<key>.jpg (e.g. memes/certified.jpg) next to index.html.
const MEMES = {
  realistic:  { art: "😎👍", top: "REALISTIC STANDARDS?", bottom: "IN THIS ECONOMY? RESPECT." },
  optimistic: { art: "🙂☕", top: "NOT BAD, BETA", bottom: "AUNTY APPROVES… MOSTLY" },
  mild:       { art: "🤔📉", top: "HMM…", bottom: "THODA ADJUST KARO NA" },
  very:       { art: "🔍😬", top: "SEARCHING FOR HIM", bottom: "LIKE A NEEDLE IN A HAYSTACK" },
  extreme:    { art: "🧐🌌", top: "HE EXISTS", bottom: "IN ANOTHER DIMENSION" },
  certified:  { art: "🦄✨", top: "HE'S NOT REAL", bottom: "HE CAN'T HURT YOU" },
};
const MEME_CLASS = { good: "lv-good", ok: "lv-ok", warn: "lv-warn", bad: "lv-bad", unicorn: "lv-unicorn" };

function fmtPct(f) {
  const pct = f * 100;
  if (pct >= 10) return pct.toFixed(1) + "%";
  if (pct >= 1) return pct.toFixed(2) + "%";
  if (pct === 0) return "0%";
  const digits = Math.min(8, Math.max(2, -Math.floor(Math.log10(pct)) + 1));
  return pct.toFixed(digits) + "%";
}
function fmtCount(n) {
  n = Math.round(n);
  if (n >= 1e7) return (n / 1e7).toFixed(2) + " crore";
  if (n >= 1e5) return (n / 1e5).toFixed(2) + " lakh";
  return n.toLocaleString("en-IN");
}

// ---------- UI ----------
const $ = (id) => document.getElementById(id);
const ageMin = $("ageMin"), ageMax = $("ageMax"), looks = $("looks");
const typeBoxes = [...document.querySelectorAll("#types input:not(#typeAll)")];
const isNarrow = () => window.matchMedia("(max-width: 1100px)").matches;
const missingMemeImgs = new Set();

function syncAge(e) {
  let a = +ageMin.value, b = +ageMax.value;
  if (a > b) { if (e && e.target === ageMin) ageMax.value = b = a; else ageMin.value = a = b; }
  $("ageOut").textContent = `${a} – ${b} yrs`;
  const span = +ageMin.max - +ageMin.min;
  $("ageFill").style.left = ((a - ageMin.min) / span) * 100 + "%";
  $("ageFill").style.right = (100 - ((b - ageMin.min) / span) * 100) + "%";
  // keep the thumb you can grab on top when both meet
  ageMin.style.zIndex = a >= +ageMax.max - 1 ? 3 : 1;
}
function syncLooks() {
  const v = +looks.value;
  $("looksOut").textContent = v === 0 ? "Doesn't matter" : `${v} / 10`;
  looks.style.setProperty("--p", v * 10 + "%");
}

const radio = (name) => document.querySelector(`input[name="${name}"]:checked`).value;
function readCriteria() {
  const sel = (id) => $(id).options[$(id).selectedIndex].text;
  return {
    ageMin: +ageMin.value, ageMax: +ageMax.value,
    salary: +$("salary").value, salaryLabel: sel("salary"),
    height: +$("height").value, heightLabel: sel("height"),
    looks: +looks.value,
    types: typeBoxes.filter((b) => b.checked).map((b) => b.value),
    loyalty: radio("loyalty"), dressing: radio("dressing"),
    education: radio("education"), habits: radio("habits"),
  };
}

function renderFunnel(steps) {
  const ol = $("funnel");
  ol.innerHTML = "";
  steps.forEach(([label, frac], i) => {
    const li = document.createElement("li");
    li.style.animationDelay = i * 30 + "ms";
    const w = Math.max(0.6, Math.min(100, Math.sqrt(frac) * 100)); // sqrt scale so tiny values stay visible
    li.innerHTML = `<span></span><span class="val"></span><div class="bar"><i style="width:${w}%"></i></div>`;
    li.children[0].textContent = label;
    li.children[1].textContent = `${fmtPct(frac)} · ${fmtCount(frac * SINGLE_MEN)}`;
    ol.appendChild(li);
  });
}

// delusion position on a log scale: 10%+ -> 0 (left), 0.0001% or less -> 1 (right).
// Level boundaries land at 6%, 20%, 40%, 60%, 80% to match the meter colours.
function delusionPos(pct) {
  if (pct <= 0) return 1;
  return 1 - Math.max(0, Math.min(1, (Math.log10(pct) + 4) / 5));
}

// ---------- 100 men grid ----------
const menEl = $("men"), tip = $("tip");
const men = Array.from({ length: 100 }, (_, i) => {
  const s = document.createElement("span");
  s.className = "man";
  s.dataset.idx = i + 1;
  s.innerHTML = '<svg viewBox="0 0 24 32" aria-hidden="true"><use href="#manIcon"/></svg>';
  menEl.appendChild(s);
  return s;
});

function renderMen(steps, fraction) {
  // Round the surviving count after each filter (stays monotonic), so each filter "rejects" whole men.
  const R = steps.map(([, f], i) => (i === 0 ? 100 : Math.round(f * 100)));
  const groups = [];
  for (let i = 1; i < steps.length; i++) groups.push({ label: steps[i][0], n: R[i - 1] - R[i], key: "g" + i });
  const survivors = R[R.length - 1];

  // Fill order: matches first, then the men rejected by the latest filters (closest to the line).
  const order = [];
  for (let k = 0; k < survivors; k++) order.push({ key: "match", label: null });
  for (let i = groups.length - 1; i >= 0; i--) for (let k = 0; k < groups[i].n; k++) order.push(groups[i]);
  men.forEach((m, i) => {
    const g = order[i] || { key: "match" };
    m.classList.toggle("match", g.key === "match");
    m.dataset.group = g.key;
    m.dataset.reason = g.key === "match" ? "" : g.label;
  });

  $("menMatch").textContent = survivors;
  const oneIn = fraction > 0 ? Math.round(1 / fraction) : Infinity;
  $("menOdds").textContent = survivors >= 1
    ? `About ${(fraction * 100).toFixed(fraction >= 0.1 ? 0 : 1)} in every 100 single men fit your list.`
    : fraction > 0 ? `Not even one here. Only 1 in ${oneIn.toLocaleString("en-IN")} single men fits.` : "Nobody fits. Not one.";

  const ul = $("menLegend");
  ul.innerHTML = "";
  const addRow = (key, swCls, label, n) => {
    const li = document.createElement("li");
    li.dataset.group = key;
    li.innerHTML = `<span class="sw ${swCls}"></span><span class="lab"></span><span class="n"></span>`;
    li.querySelector(".lab").textContent = label;
    li.querySelector(".n").textContent = n;
    ul.appendChild(li);
  };
  addRow("match", "match", "Match your list", survivors);
  const big = groups.filter((g) => g.n > 0).sort((a, b) => b.n - a.n);
  big.forEach((g) => addRow(g.key, "", g.label, "−" + g.n));
  const minor = groups.filter((g) => g.n === 0);
  if (minor.length) {
    const li = document.createElement("li");
    li.className = "minor";
    li.textContent = `Also filtering (under 1 man each here): ${minor.map((g) => g.label).join(", ")}`;
    ul.appendChild(li);
  }
}

function showTip(text, x, y) {
  tip.innerHTML = text;
  tip.hidden = false;
  const r = tip.getBoundingClientRect();
  tip.style.left = Math.min(x + 14, innerWidth - r.width - 8) + "px";
  tip.style.top = Math.min(y + 14, innerHeight - r.height - 8) + "px";
}
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
menEl.addEventListener("mousemove", (e) => {
  const m = e.target.closest(".man");
  if (!m) return (tip.hidden = true);
  showTip(m.classList.contains("match")
    ? `Man #${m.dataset.idx} · <b>Matches your list ✅</b>`
    : `Man #${m.dataset.idx} · rejected by <b>${esc(m.dataset.reason)}</b>`, e.clientX, e.clientY);
});
menEl.addEventListener("mouseleave", () => (tip.hidden = true));

function focusGroup(key) {
  menEl.classList.toggle("focus", !!key);
  men.forEach((m) => m.classList.toggle("hl", m.dataset.group === key));
}
$("menLegend").addEventListener("mouseover", (e) => { const li = e.target.closest("li[data-group]"); focusGroup(li ? li.dataset.group : null); });
$("menLegend").addEventListener("mouseleave", () => focusGroup(null));

document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach((x) => { const on = x === t; x.classList.toggle("active", on); x.setAttribute("aria-selected", on); $(x.dataset.view).hidden = !on; });
}));

function renderKillers(steps) {
  const ol = $("killers");
  ol.innerHTML = "";
  const cuts = [];
  for (let i = 1; i < steps.length; i++) cuts.push([steps[i][0], 1 - steps[i][1] / steps[i - 1][1]]);
  cuts.sort((a, b) => b[1] - a[1]);
  const top = cuts.filter((c) => c[1] > 0.05).slice(0, 4);
  if (!top.length) { ol.innerHTML = '<li><span class="empty">No dealbreakers. You are refreshingly reasonable. 🙏</span></li>'; return; }
  top.forEach(([label, cut], i) => {
    const li = document.createElement("li");
    li.style.animationDelay = i * 40 + "ms";
    li.innerHTML = `<span class="rank">#${i + 1}</span><span class="name"></span><span class="cut">rejects <b>${(cut * 100).toFixed(cut > 0.99 ? 1 : 0)}%</b> of the men still left</span>`;
    li.querySelector(".name").textContent = label;
    ol.appendChild(li);
  });
}

let currentMeme = null;
function showMeme(key, cls) {
  if (key === currentMeme) return;
  currentMeme = key;
  const m = MEMES[key], fig = $("meme"), img = $("memeImg");
  fig.className = "meme " + MEME_CLASS[cls];
  void fig.offsetWidth; fig.classList.add("pop");
  $("memeArt").textContent = m.art;
  $("memeTop").textContent = m.top;
  $("memeBottom").textContent = m.bottom;
  img.hidden = true; $("memeArt").hidden = false;
  if (!missingMemeImgs.has(key)) {
    img.onload = () => { if (currentMeme === key) { img.hidden = false; $("memeArt").hidden = true; } };
    img.onerror = () => missingMemeImgs.add(key);
    img.src = `memes/${key}.jpg`;
  }
}

let last = null, lastPct = null;
function update() {
  const c = readCriteria();
  const res = calculate(c);
  const pct = res.fraction * 100;
  const [lvl, cls, key] = level(pct);
  const pctText = fmtPct(res.fraction);

  const big = $("pct");
  if (pctText !== lastPct) { big.classList.remove("bump"); void big.offsetWidth; big.classList.add("bump"); }
  big.textContent = pctText;
  lastPct = pctText;
  $("count").textContent = `≈ ${fmtCount(res.fraction * SINGLE_MEN)} men`;
  const lv = $("level");
  lv.textContent = lvl;
  lv.className = "level " + cls;
  $("pin").style.left = (delusionPos(pct) * 100).toFixed(1) + "%";
  showMeme(key, cls);
  renderFunnel(res.steps);
  renderMen(res.steps, res.fraction);
  renderKillers(res.steps);
  last = { c, res, lvl };
}

function biggestFilters(steps) {
  const drops = [];
  for (let i = 1; i < steps.length; i++) drops.push([steps[i][0], +(steps[i][1] / steps[i - 1][1] * 100).toFixed(2) + "% kept"]);
  return drops.sort((a, b) => parseFloat(a[1]) - parseFloat(b[1])).slice(0, 3);
}

// Where the AI verdict comes from. Static hosting (GitHub Pages) has no server to keep the
// Mistral key secret, so there we use the built-in verdict below. To use the real AI on the
// live site, deploy api/verdict.js (e.g. on Vercel) and put its full URL here.
const REMOTE_VERDICT_API = "";
const VERDICT_API = location.hostname.endsWith("github.io") ? REMOTE_VERDICT_API : "api/verdict";

const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];
function localVerdict(c, res, lvl) {
  const pct = fmtPct(res.fraction), count = fmtCount(res.fraction * SINGLE_MEN);
  const cuts = [];
  for (let i = 1; i < res.steps.length; i++) cuts.push([res.steps[i][0], 1 - res.steps[i][1] / res.steps[i - 1][1]]);
  cuts.sort((a, b) => b[1] - a[1]);
  const [k1, k2] = cuts;
  const pctNum = res.fraction * 100;
  const opener = pctNum >= 5
    ? pick(["Arre wah, a sensible list! ", "Shabaash, realistic standards spotted. ", "Aunty is impressed. "])
    : pctNum >= 0.1
      ? pick(["Hmm, beta, interesting list. ", "Okay, thoda filmy, but not fully. ", "Not bad, but the maths is sweating a little. "])
      : pick(["Beta, this is not a husband, this is a Marvel character. ", "Arre, you are not looking for a man, you are looking for a unicorn with a salary slip. ", "Matrimony sites are crying after reading this list. "]);
  const stat = `${pctNum >= 5 ? "" : "Only "}${pct} of India's single men fit, roughly ${count} men in the whole country. `;
  const blame = k1 && k1[1] > 0.05
    ? `The biggest villain is ${k1[0]}, which rejects ${(k1[1] * 100).toFixed(0)}% of the men still standing` +
      (k2 && k2[1] > 0.3 ? `, with ${k2[0]} as its sidekick. ` : ". ")
    : "None of your filters are doing much damage. ";
  const tip = pctNum >= 5
    ? pick(["Go forth, the odds are on your side. 💚", "Now just find one who replies on time. 😄"])
    : k1 ? `Tip: relax ${k1[0]} a little and watch your pool grow. 🙏` : "Tip: relax one filter and the pool grows fast. 🙏";
  return opener + stat + blame + tip;
}

async function getVerdict({ c, res, lvl }) {
  const el = $("verdict"), btn = $("judge");
  if (!VERDICT_API) {
    $("verdictTitle").textContent = "Verdict";
    $("verdictSrc").textContent = "· desi auto-judge";
    el.classList.remove("muted");
    el.textContent = localVerdict(c, res, lvl);
    return;
  }
  el.textContent = ""; el.classList.remove("muted"); el.classList.add("loading");
  btn.disabled = true;
  const readable = {
    age: `${c.ageMin}-${c.ageMax}`, salary: c.salaryLabel, height: c.heightLabel,
    looks: c.looks ? `${c.looks}/10+` : "doesn't matter",
    type: c.types.length ? c.types.map((t) => TYPE_RATES[t][0]) : ["no preference"],
    loyalty: LOYALTY[c.loyalty][0], dressing: DRESSING[c.dressing][0],
    education: EDUCATION[c.education][0], habits: HABITS[c.habits][0],
  };
  try {
    const r = await fetch(VERDICT_API, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ criteria: readable, percent: fmtPct(res.fraction), count: fmtCount(res.fraction * SINGLE_MEN), level: lvl, filters: biggestFilters(res.steps) }),
    });
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || r.statusText);
    el.textContent = j.verdict;
  } catch (e) {
    el.textContent = localVerdict(c, res, lvl) + `\n\n(AI is busy right now: ${e.message})`;
  } finally {
    el.classList.remove("loading");
    btn.disabled = false;
  }
}

// events
ageMin.addEventListener("input", (e) => { syncAge(e); update(); });
ageMax.addEventListener("input", (e) => { syncAge(e); update(); });
looks.addEventListener("input", () => { syncLooks(); update(); });
$("typeAll").addEventListener("change", (e) => typeBoxes.forEach((b) => (b.checked = e.target.checked)));
typeBoxes.forEach((b) => b.addEventListener("change", () => { $("typeAll").checked = typeBoxes.every((x) => x.checked); }));
$("form").addEventListener("change", update);

$("form").addEventListener("submit", (e) => {
  e.preventDefault();
  update();
  if (isNarrow()) $("result").scrollIntoView({ behavior: "smooth", block: "start" });
  getVerdict(last);
});

syncAge();
syncLooks();
update();
