(function () {
  'use strict';

  const REPO = 'https://github.com/narendraamodipm-art/AI-Agents';
  const tree = (p) => REPO + '/tree/main/' + encodeURI(p);

  /* ---------------- Data ---------------- */
  const SKILLS = [
    // Languages
    ['SQL', 'lang'], ['Python', 'lang'], ['C++', 'lang'],
    // AI
    ['LLMs', 'ai'], ['RAG', 'ai'], ['AI Agents', 'ai'], ['LangChain', 'ai'], ['LangGraph', 'ai'], ['Mistral AI', 'ai'], ['Pinecone', 'ai'],
    // Warehouses & DBs
    ['Snowflake', 'warehouse'], ['Google BigQuery', 'warehouse'], ['Amazon Redshift', 'warehouse'], ['MySQL', 'warehouse'], ['MongoDB', 'warehouse'],
    // ETL
    ['Apache Airflow', 'etl'], ['Informatica IICS', 'etl'], ['AWS Glue', 'etl'], ['Azure Data Factory', 'etl'], ['AWS Step Functions', 'etl'], ['Snowpark', 'etl'],
    // Big data & streaming
    ['Apache Spark', 'stream'], ['Hadoop', 'stream'], ['Databricks', 'stream'], ['Confluent Kafka', 'stream'], ['Google Pub/Sub', 'stream'], ['Amazon Kinesis', 'stream'],
    // Cloud
    ['GCS', 'cloud'], ['Cloud Functions', 'cloud'], ['Dataproc', 'cloud'], ['Cloud Composer', 'cloud'],
    ['S3', 'cloud'], ['Lambda', 'cloud'], ['DynamoDB', 'cloud'], ['Athena', 'cloud'], ['SNS', 'cloud'],
    ['Azure Logic Apps', 'cloud'], ['Azure Blob Storage', 'cloud'], ['Azure DevOps', 'cloud'],
    // Tools
    ['Streamlit', 'tools'], ['Git', 'tools'], ['Bitbucket', 'tools'], ['Jira', 'tools'], ['Confluence', 'tools'], ['Linux', 'tools'],
  ];
  const SKILL_COLORS = {
    lang: '#f59e0b', ai: '#a78bfa', warehouse: '#38bdf8', etl: '#2dd4bf',
    stream: '#f472b6', cloud: '#818cf8', tools: '#94a3b8',
  };

  const PROJECTS = [
    {
      id: 'job-agent', icon: '🎯', type: 'agent', label: 'Agent',
      title: 'GCC Job Agent',
      short: 'Each morning it finds new data engineering jobs at India GCCs, scores them against my resume and sends a Telegram shortlist. Reply "APPLY 8" to get a tailored cover letter.',
      tags: ['Python', 'Mistral', 'Tavily', 'Telegram', 'SQLite', 'Streamlit'],
      steps: [
        'Pull jobs from 26 Workday and 9 Greenhouse GCC career feeds, filtered by title, India location and the last 3 days',
        'Search news with Tavily; Mistral picks out newly announced GCCs, then Tavily finds jobs there',
        'Store new jobs in SQLite and skip duplicates',
        'Score each job: Mistral extracts JD skills and finds gaps, embeddings measure similarity, Python computes the fit score',
        'Fit ≥ 50 → send a Telegram shortlist with fit scores',
        'Reply APPLY / SKIP / APPLIED / LIST; APPLY writes a cover letter and resume tips and sends the apply link',
      ],
      highlights: [
        'Runs on its own through Windows Task Scheduler: a daily 9:00 run plus a reply check every 15 minutes',
        'Human in the loop: nothing is ever submitted without my review',
        'Auto-fill bot opens Edge, fills Workday and Greenhouse forms, and stops before Submit',
        'Streamlit dashboard to browse matches, read cover letters and mark jobs applied',
      ],
      link: tree('JOB Agent'),
    },
    {
      id: 'resume-matcher', icon: '📄', type: 'workflow', label: 'Workflow',
      title: 'Resume Matcher + Cover Letter Writer',
      short: 'An 8-step AI workflow that scores how well a resume fits a job description, shows the skill gaps, rewrites bullets and writes a cover letter. A guardrail flags any invented numbers.',
      tags: ['Python', 'LangChain', 'Mistral', 'Pydantic', 'Embeddings', 'Streamlit'],
      steps: [
        'Read the resume (PDF or text) with pypdf',
        'Structured output → ResumeProfile (skills, years, experience)',
        'Structured output → JobProfile (required and nice-to-have skills, minimum years)',
        'Mistral embeddings + cosine similarity → semantic match',
        'Skill-gap analysis that understands equivalents (PostgreSQL ≈ SQL)',
        'Plain Python scoring: overall match % and interview chance out of 100',
        'Suggested resume bullet rewrites (before / after / why)',
        'Tailored cover letter, checked by the invented_numbers() guardrail',
      ],
      highlights: [
        'Score = 0.5 × required + 0.2 × nice-to-have + 0.3 × semantic, a heuristic that is easy to explain',
        'Hard caps stop inflated scores when key skills or experience are missing',
        'Exponential backoff retries on rate limits (2s → 32s)',
        'About 23 seconds per full analysis',
      ],
      link: tree('AI WORKFLOW/resume_matcher'),
    },
    {
      id: 'yt-notes', icon: '🎬', type: 'workflow', label: 'Workflow',
      title: 'YouTube → Study Notes',
      short: 'Paste a YouTube link and get timestamped study notes, Anki-ready flashcards and an interactive quiz, all built with map-reduce summarisation.',
      tags: ['Python', 'LangChain', 'Mistral', 'Pydantic', 'Streamlit'],
      steps: [
        'Extract the video ID from any YouTube URL format',
        'Fetch the timestamped transcript (cached)',
        'Split it into ~12k-character chunks tagged with [mm:ss]',
        'MAP: one Mistral call per chunk produces bullet notes',
        'REDUCE: merge them into one structured notes document',
        'Structured output → flashcards and a multiple-choice quiz, validated by a guardrail',
      ],
      highlights: [
        'An 18-minute video takes about 45 seconds end to end',
        'Notes in English, Hindi or the video\'s own language',
        'Flashcards export to CSV for Anki',
      ],
      link: tree('AI WORKFLOW/youtube_notes'),
    },
    {
      id: 'docchat', icon: '📚', type: 'rag', label: 'RAG',
      title: 'DocChat AI: RAG Pipeline',
      short: 'Chat with any PDF or web page. Answers are grounded in the most relevant chunks retrieved from Pinecone, which reduces hallucination.',
      tags: ['Python', 'LangChain', 'Mistral', 'Pinecone', 'Streamlit'],
      steps: [
        'Ingest a PDF upload or a web URL',
        'Chunk the text with RecursiveCharacterTextSplitter',
        'Embed with llama-text-embed-v2 through the Pinecone inference API',
        'Upsert into a Pinecone namespace',
        'A custom LangChain retriever fetches the top-4 relevant chunks',
        'Mistral answers using only the retrieved context',
      ],
      highlights: [
        'Answers are grounded in source content to reduce hallucination',
        'Deployable on Streamlit Community Cloud, with secrets kept out of Git',
      ],
      link: tree('RAG'),
    },
    {
      id: 'travel', icon: '✈️', type: 'agent', label: 'Agent',
      title: 'Travel Planner AI Agent',
      short: 'An autonomous ReAct agent that picks its own tools (web search, weather forecasts, a budget calculator) to build day-by-day itineraries that fit the weather and the budget.',
      tags: ['Python', 'Groq', 'Tavily', 'OpenWeather', 'Streamlit'],
      steps: [
        'User gives a destination, dates and a budget',
        'The LLM reasons about what it needs next (ReAct loop)',
        'It picks a tool: Tavily web search, OpenWeather forecast or a Python budget calculator',
        'It observes the result and repeats, up to 12 reasoning steps',
        'It produces a weather-adjusted, day-by-day plan within budget',
      ],
      highlights: [
        'Context trimming keeps long runs within the token limit',
        'Exponential backoff retry for flaky APIs',
        'A step-limit cap prevents runaway loops',
      ],
      link: null,
    },
    {
      id: 'graphify', icon: '🕸️', type: 'web', label: 'Web app',
      title: 'GRAPHIFY: Code → Knowledge Graph',
      short: 'Paste code in Python, JS/TS, Java, HTML or Rust and get an interactive knowledge graph of its classes, functions and imports, plus AI analysis.',
      tags: ['Next.js 14', 'React', 'React Flow', 'Tailwind', 'Claude API'],
      steps: [
        'Paste code or upload a file',
        'Detect the language automatically (or pick it)',
        'A language-specific parser extracts classes, functions, methods and imports',
        'Generate graph nodes and edges',
        'Render with React Flow: zoom, pan and drag',
        'Show statistics and export the graph as JSON',
      ],
      highlights: [
        'Supports six languages, each with its own parser',
        'Nodes are colour-coded by entity type',
        'Has an API route for AI-powered code analysis',
      ],
      link: tree('GRAPHIFY'),
    },
    {
      id: 'hahabot', icon: '😄', type: 'rag', label: 'Chatbot',
      title: 'HahaBot',
      short: 'A friendly conversational chatbot built on Mistral AI with a Streamlit chat UI, deployable on Streamlit Community Cloud.',
      tags: ['Python', 'Mistral', 'Streamlit'],
      steps: [
        'The user sends a message in the Streamlit chat UI',
        'Conversation history is kept in session state',
        'The Mistral chat model generates a reply',
        'The reply is shown in the chat thread',
      ],
      highlights: [
        'API keys are read from Streamlit secrets or .env and never committed',
        'One-file app that deploys straight from the repo',
      ],
      link: tree('CHATBOT'),
    },
  ];

  /* ---------------- Helpers ---------------- */
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  function toast(msg) {
    const t = $('#toast');
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(toast._t);
    toast._t = setTimeout(() => t.classList.remove('show'), 2200);
  }

  /* ---------------- Theme ---------------- */
  function currentTheme() {
    const attr = document.documentElement.getAttribute('data-theme');
    if (attr) return attr;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  $('#themeToggle').addEventListener('click', () => {
    const next = currentTheme() === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('theme', next); } catch (e) { /* storage unavailable */ }
  });

  /* ---------------- Mobile menu ---------------- */
  const menuBtn = $('#menuBtn');
  const navLinks = $('#navLinks');
  menuBtn.addEventListener('click', () => {
    const open = navLinks.classList.toggle('open');
    menuBtn.setAttribute('aria-expanded', String(open));
  });
  $$('a', navLinks).forEach((a) => a.addEventListener('click', () => {
    navLinks.classList.remove('open');
    menuBtn.setAttribute('aria-expanded', 'false');
  }));

  /* ---------------- Typing effect ---------------- */
  const roles = ['Data Engineer', 'Cloud Engineer', 'AI Agent Builder', 'Pipeline Architect', 'SQL Enthusiast'];
  const typedEl = $('#typed');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!reduceMotion) {
    let r = 0, i = roles[0].length, deleting = true;
    setTimeout(function tick() {
      if (deleting) {
        i--;
        if (i <= 0) { deleting = false; r = (r + 1) % roles.length; }
      } else {
        i++;
        if (i >= roles[r].length) { deleting = true; typedEl.textContent = roles[r]; return setTimeout(tick, 1800); }
      }
      typedEl.textContent = roles[r].slice(0, Math.max(i, 0));
      setTimeout(tick, deleting ? 45 : 85);
    }, 2000);
  }

  /* ---------------- Pipeline tooltips ---------------- */
  const tip = $('#pipeTip');
  const defaultTip = tip.textContent;
  $$('.pipeline .node').forEach((n) => {
    const show = () => { tip.textContent = n.dataset.tip; tip.classList.add('on'); };
    const hide = () => { tip.textContent = defaultTip; tip.classList.remove('on'); };
    n.addEventListener('mouseenter', show);
    n.addEventListener('mouseleave', hide);
    n.addEventListener('click', show);
  });
  // Auto-cycle highlights on the pipeline so it feels alive
  const nodes = $$('.pipeline .node');
  let ni = 0;
  setInterval(() => {
    nodes.forEach((n) => n.classList.remove('lit'));
    nodes[ni % nodes.length].classList.add('lit');
    ni++;
  }, 1400);

  /* ---------------- Counters ---------------- */
  function countUp(el) {
    const target = +el.dataset.count;
    const start = performance.now();
    const dur = 1200;
    (function step(now) {
      const p = Math.min((now - start) / dur, 1);
      el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(step);
    })(start);
  }

  /* ---------------- Skills ---------------- */
  const cloud = $('#skillCloud');
  function renderSkills(filter) {
    cloud.innerHTML = '';
    SKILLS.filter(([, c]) => filter === 'all' || c === filter).forEach(([name, cat], idx) => {
      const s = document.createElement('span');
      s.className = 'skill';
      s.textContent = name;
      s.style.setProperty('--dot', SKILL_COLORS[cat]);
      s.style.animationDelay = (idx * 18) + 'ms';
      cloud.appendChild(s);
    });
  }
  $$('[data-skill-filter]').forEach((b) => b.addEventListener('click', () => {
    $$('[data-skill-filter]').forEach((x) => x.classList.remove('active'));
    b.classList.add('active');
    renderSkills(b.dataset.skillFilter);
  }));
  renderSkills('all');

  /* ---------------- Projects ---------------- */
  const grid = $('#projectGrid');
  function renderProjects(filter) {
    grid.innerHTML = '';
    PROJECTS.filter((p) => filter === 'all' || p.type === filter).forEach((p, idx) => {
      const card = document.createElement('button');
      card.type = 'button';
      card.className = 'pcard';
      card.style.animationDelay = (idx * 60) + 'ms';
      card.setAttribute('aria-haspopup', 'dialog');
      card.innerHTML =
        '<div class="pcard-top"><span class="pcard-ico">' + p.icon + '</span><span class="pcard-type">' + esc(p.label) + '</span></div>' +
        '<h3>' + esc(p.title) + '</h3>' +
        '<p>' + esc(p.short) + '</p>' +
        '<div class="tags">' + p.tags.map((t) => '<span class="tag">' + esc(t) + '</span>').join('') + '</div>' +
        '<span class="pcard-more">How it works</span>';
      card.addEventListener('mousemove', (e) => {
        const r = card.getBoundingClientRect();
        card.style.setProperty('--mx', (e.clientX - r.left) + 'px');
        card.style.setProperty('--my', (e.clientY - r.top) + 'px');
      });
      card.addEventListener('click', () => openProject(p));
      grid.appendChild(card);
    });
  }
  $$('[data-proj-filter]').forEach((b) => b.addEventListener('click', () => {
    $$('[data-proj-filter]').forEach((x) => x.classList.remove('active'));
    b.classList.add('active');
    renderProjects(b.dataset.projFilter);
  }));
  renderProjects('all');

  const modal = $('#projModal');
  function openProject(p) {
    $('#modalContent').innerHTML =
      '<span class="pcard-type">' + esc(p.label) + '</span>' +
      '<h3 id="mTitle">' + p.icon + ' ' + esc(p.title) + '</h3>' +
      '<p class="m-desc">' + esc(p.short) + '</p>' +
      '<div class="tags">' + p.tags.map((t) => '<span class="tag">' + esc(t) + '</span>').join('') + '</div>' +
      '<h4>How it works</h4>' +
      '<ol class="steps">' + p.steps.map((s, i) => '<li style="animation-delay:' + (i * 70) + 'ms">' + esc(s) + '</li>').join('') + '</ol>' +
      '<h4>Highlights</h4>' +
      '<ul class="hl">' + p.highlights.map((h) => '<li>' + esc(h) + '</li>').join('') + '</ul>' +
      '<div class="modal-actions">' +
        (p.link ? '<a class="btn primary" href="' + p.link + '" target="_blank" rel="noopener">View code on GitHub</a>' : '<span class="tag">Code available on request</span>') +
      '</div>';
    if (typeof modal.showModal === 'function') modal.showModal();
    else modal.setAttribute('open', '');
  }
  $('#modalClose').addEventListener('click', () => modal.close());
  modal.addEventListener('click', (e) => { if (e.target === modal) modal.close(); });

  /* ---------------- Terminal ---------------- */
  const termBody = $('#termBody');
  const termIn = $('#termIn');
  const history = [];
  let hIdx = -1;

  const COMMANDS = {
    help: () => [
      'Available commands:',
      '  <b>whoami</b>       who is Nikhil?',
      '  <b>skills</b>       tech stack by category',
      '  <b>projects</b>     list AI projects',
      '  <b>open</b> &lt;n&gt;     open project n (e.g. open 1)',
      '  <b>experience</b>   work history',
      '  <b>education</b>    degree',
      '  <b>contact</b>      how to reach me',
      '  <b>sql</b>          run a query 😉',
      '  <b>theme</b>        toggle light/dark',
      '  <b>clear</b>        clear the screen',
    ],
    whoami: () => [
      '<b>Nikhil Kumar</b>: Data Engineer and Cloud Engineer in Bengaluru, India.',
      'About 4 years building scalable pipelines on Snowflake, GCP and AWS.',
      'Currently: Advance Data Engineer at Albertsons.',
      'Side quest: building AI agents with LangChain and Mistral.',
    ],
    skills: () => {
      const names = { lang: 'Languages', ai: 'AI / LLM', warehouse: 'Warehouses', etl: 'ETL', stream: 'Streaming', cloud: 'Cloud', tools: 'Tools' };
      return Object.keys(names).map((k) =>
        '<b>' + names[k].padEnd(11, ' ') + '</b> ' + SKILLS.filter(([, c]) => c === k).map(([n]) => n).join(', '));
    },
    projects: () => PROJECTS.map((p, i) => '  <b>' + (i + 1) + '.</b> ' + esc(p.title)).concat(['', 'Type <b>open 1</b> to see details.']),
    experience: () => [
      '<b>2026 → now</b>  Advance Data Engineer @ Albertsons',
      '              Kafka → BigQuery, SCD Type 2, YAML-driven deployments',
      '<b>2022 → 2025</b> Data Engineer @ MathCo',
      '              Marketing Data Lake (Airflow, GCS, Snowflake)',
      '              MDL Redesign (IICS): 🏆 appreciation award',
      '              Data Quality Framework (Streamlit + Snowflake)',
    ],
    education: () => ['B.E. Electronics &amp; Communication: Siddaganga Institute of Technology (2018–2022), CGPA 7.4'],
    contact: () => [
      'email   → <a href="mailto:Nikhil.nk0101@gmail.com">Nikhil.nk0101@gmail.com</a>',
      'github  → <a href="' + REPO + '" target="_blank" rel="noopener">narendraamodipm-art/AI-Agents</a>',
      'where   → Bengaluru, India',
    ],
    sql: () => [
      '<span class="muted">SELECT name, role, open_to_work FROM engineers WHERE passion = \'data\';</span>',
      '+--------------+---------------+--------------+',
      '| name         | role          | open_to_work |',
      '+--------------+---------------+--------------+',
      '| Nikhil Kumar | Data Engineer | TRUE         |',
      '+--------------+---------------+--------------+',
      '1 row returned in 0.004s ⚡',
    ],
    theme: () => { $('#themeToggle').click(); return ['Theme switched to <b>' + currentTheme() + '</b>.']; },
    sudo: () => ['<span class="err">Nice try. Permission denied. 🔒</span>'],
    ls: () => ['about/  skills/  experience/  projects/  contact/'],
  };

  function print(lines, cls) {
    lines.forEach((l) => {
      const p = document.createElement('p');
      if (cls) p.className = cls;
      p.innerHTML = l;
      termBody.appendChild(p);
    });
    termBody.scrollTop = termBody.scrollHeight;
  }

  function run(raw) {
    const input = raw.trim();
    if (!input) return;
    history.unshift(input);
    hIdx = -1;
    print([esc(input)], 'cmd');
    const [cmd, ...args] = input.toLowerCase().split(/\s+/);
    if (cmd === 'clear') { termBody.innerHTML = ''; return; }
    if (cmd === 'open') {
      const n = parseInt(args[0], 10);
      const p = PROJECTS[n - 1];
      if (p) { print(['Opening <b>' + esc(p.title) + '</b>…']); openProject(p); }
      else print(['Usage: open &lt;1-' + PROJECTS.length + '&gt;'], 'err');
      return;
    }
    const fn = COMMANDS[cmd];
    if (fn) print(fn());
    else print(['command not found: ' + esc(cmd) + '. Type <b>help</b>.'], 'err');
  }

  $('#termForm').addEventListener('submit', (e) => {
    e.preventDefault();
    run(termIn.value);
    termIn.value = '';
  });
  termIn.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowUp' && history.length) {
      hIdx = Math.min(hIdx + 1, history.length - 1);
      termIn.value = history[hIdx];
      e.preventDefault();
    } else if (e.key === 'ArrowDown') {
      hIdx = Math.max(hIdx - 1, -1);
      termIn.value = hIdx >= 0 ? history[hIdx] : '';
      e.preventDefault();
    } else if (e.key === 'Tab') {
      const v = termIn.value.trim().toLowerCase();
      const m = Object.keys(COMMANDS).concat(['clear', 'open']).filter((c) => c.startsWith(v));
      if (v && m.length === 1) { termIn.value = m[0]; e.preventDefault(); }
    }
  });
  $('#term').addEventListener('click', (e) => { if (!e.target.closest('a')) termIn.focus({ preventScroll: true }); });
  $$('[data-cmd]').forEach((b) => b.addEventListener('click', () => run(b.dataset.cmd)));

  /* ---------------- Copy email ---------------- */
  $('#copyEmail').addEventListener('click', async () => {
    const email = 'Nikhil.nk0101@gmail.com';
    try {
      await navigator.clipboard.writeText(email);
      toast('Email copied ✓');
    } catch (e) {
      toast(email);
    }
  });

  /* ---------------- Scroll: progress, reveal, active nav ---------------- */
  const progress = $('.scroll-progress');
  window.addEventListener('scroll', () => {
    const h = document.documentElement;
    progress.style.width = (h.scrollTop / (h.scrollHeight - h.clientHeight) * 100) + '%';
  }, { passive: true });

  const revealObs = new IntersectionObserver((entries) => {
    entries.forEach((en) => {
      if (en.isIntersecting) { en.target.classList.add('in'); revealObs.unobserve(en.target); }
    });
  }, { threshold: 0.12 });
  $$('.reveal').forEach((el) => revealObs.observe(el));

  const countObs = new IntersectionObserver((entries) => {
    entries.forEach((en) => {
      if (en.isIntersecting) { countUp(en.target); countObs.unobserve(en.target); }
    });
  });
  $$('[data-count]').forEach((el) => countObs.observe(el));

  const links = $$('.nav-links a');
  const navObs = new IntersectionObserver((entries) => {
    entries.forEach((en) => {
      if (en.isIntersecting) {
        links.forEach((a) => a.classList.toggle('active', a.getAttribute('href') === '#' + en.target.id));
      }
    });
  }, { rootMargin: '-45% 0px -50% 0px' });
  $$('main section[id]').forEach((s) => navObs.observe(s));

  $('#year').textContent = new Date().getFullYear();
})();
