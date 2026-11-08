"""Settings for the Fresher Job Hunt agent. Edit these to change what it looks for."""

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LOCAL_STATE = HERE / "state"                 # used only when Supabase isn't configured (local testing)

# ── Daily post ───────────────────────────────────────────────────────────────
JOBS_PER_POST = 12                           # 10–12 jobs in the daily Telegram / WhatsApp post
MIN_JOBS_PER_POST = 10
MAX_PER_COMPANY = 2                          # variety: at most 2 jobs from one company per post
MAX_AGE_DAYS = 3                             # only jobs posted in the last N days count as new
FIRST_RUN_AGE_DAYS = 7                       # look further back the very first time
SEND_TIME_IST = "10:00"                      # the scheduled run waits until this time before sending
MODEL = "ministral-8b-latest"                # Mistral model for unclear "is this a fresher job?" cases
MAX_LLM_CHECKS = 40                          # LLM checks per run (keeps it inside the free tier)
SITE_URL_DEFAULT = "https://fresher-job-hunt.vercel.app"

# ── Fields (what users pick at signup) ──────────────────────────────────────
# key: (label, emoji, title pattern). Order matters: the first match is the job's main field.
FIELDS = {
    "ai_engineer":       ("AI Engineer",        "🤖", r"\b(ai|artificial intelligence|gen ?ai|llm|nlp|computer vision|agentic|prompt engineer)\b"),
    "ml_engineer":       ("ML Engineer",        "🧠", r"machine learning|\bml\b|mlops|deep learning|data scien"),
    "data_engineer":     ("Data Engineer",      "🛠", r"data engineer|\betl\b|big data|data platform|analytics engineer|data pipeline|data warehouse"),
    "data_analyst":      ("Data Analyst",       "📊", r"data analy|business analy|business intelligence|\bbi\b|analytics|insights analyst|product analyst|reporting analyst|mis analyst"),
    "full_stack":        ("Full Stack",         "🌐", r"full ?stack|front ?end|back ?end|web developer|\breact\b|\bnode\b|\bmern\b|\bmean\b"),
    "software_engineer": ("Software Engineer",  "💻", r"software|\bsde\b|developer|programmer|graduate engineer|engineer trainee|application engineer|cloud engineer|devops|\bqa\b|test engineer"),
}
FIELD_PATTERNS = {k: re.compile(v[2], re.I) for k, v in FIELDS.items()}

# ── Title rules ──────────────────────────────────────────────────────────────
FRESHER_TITLE = re.compile(
    r"\b(intern|internship|trainee|graduate|grad|fresher|freshers|junior|jr\.?|entry[- ]level|new grad|campus|"
    r"early career|early careers|early talent|apprentice|associate software|associate data|associate engineer|"
    r"associate developer|associate analyst|engineer i|analyst i|sde ?1|sde-1|sde i|engineer 1)\b", re.I)
SENIOR_TITLE = re.compile(
    r"\b(senior|sr\.?|staff|principal|lead|manager|mgr|director|head|architect|vp|vice president|ii|iii|iv|"
    r"expert|technical leader|distinguished|fellow|phd)\b", re.I)
NON_TECH = re.compile(
    r"sales|account executive|account manager|recruit|talent acquisition|\bhr\b|human resources|payroll|finance|"
    r"\btax\b|legal|marketing|content|compliance|audit|fraud|customer success|customer experience|customer support|"
    r"operations associate|accounting|procurement|supply chain|brand|design intern|graphic|wells engineer|welding|"
    r"mechanical|civil|chemical|electrical|hardware|microbiology|clinical|nurse|pharma", re.I)

# ── Locations: on-site in India, or remote roles open to India ──────────────
INDIA = re.compile(
    r"\bindia\b|\bind\b|bengaluru|bangalore|hyderabad|chennai|pune|mumbai|gurugram|gurgaon|noida|delhi|kolkata|"
    r"ahmedabad|kochi|coimbatore|mysuru|mysore|trivandrum|thiruvananthapuram|jaipur|chandigarh|indore|"
    r"karnataka|telangana|maharashtra|tamil nadu|haryana|gandhinagar", re.I)   # not "- IN": that's Indiana in US feeds
REMOTE = re.compile(r"remote|work from home|wfh|anywhere", re.I)
REMOTE_OK_REGION = re.compile(r"india|apac|asia|anywhere|worldwide|global", re.I)

# ── Experience in the job description ───────────────────────────────────────
FRESHER_TEXT = re.compile(
    r"\bfreshers?\b|recent graduates?|new grads?|no (prior )?experience (is )?required|0\s*(?:-|–|to)\s*[12]\s*(?:\+\s*)?(?:years|yrs)|"
    r"graduating in 20\d\d|batch of 20\d\d|20\d\d (passout|pass-out|batch|graduates?)", re.I)
YEARS = re.compile(r"(\d{1,2})\s*(?:\+|plus)?\s*(?:(?:-|–|to)\s*(\d{1,2})\s*)?\+?\s*(?:years|yrs)", re.I)

# ── Job sources ──────────────────────────────────────────────────────────────
# Public JSON job boards (no API key). Checked 8 Nov 2026: these have India and/or remote roles.
GREENHOUSE = {"stripe": "Stripe", "mongodb": "MongoDB", "rubrik": "Rubrik", "coinbase": "Coinbase",
              "datadog": "Datadog", "hackerrank": "HackerRank", "druva": "Druva", "groww": "Groww",
              "samsara": "Samsara", "zscaler": "Zscaler", "sigmoid": "Sigmoid", "databricks": "Databricks",
              "okta": "Okta", "twilio": "Twilio", "gitlab": "GitLab", "purestorage": "Pure Storage",
              "observeai": "Observe.AI", "dropbox": "Dropbox", "airbnb": "Airbnb", "newrelic": "New Relic"}
LEVER = {"meesho": "Meesho", "cred": "CRED", "zeta": "Zeta", "paytm": "Paytm", "hevodata": "Hevo Data",
         "fampay": "FamPay"}
ASHBY = {"sarvam": "Sarvam AI", "atlan": "Atlan", "notion": "Notion", "openai": "OpenAI", "cohere": "Cohere",
         "ramp": "Ramp", "plaid": "Plaid", "replit": "Replit", "perplexity": "Perplexity", "linear": "Linear"}
# (company, host, tenant, site): big tech centres in India that post intern / graduate roles
WORKDAY = [
    ("Wells Fargo", "wf.wd1.myworkdayjobs.com", "wf", "WellsFargoJobs"),
    ("Mastercard", "mastercard.wd1.myworkdayjobs.com", "mastercard", "CorporateCareers"),
    ("PayPal", "paypal.wd1.myworkdayjobs.com", "paypal", "jobs"),
    ("Citi", "citi.wd5.myworkdayjobs.com", "citi", "2"),
    ("Morgan Stanley", "ms.wd5.myworkdayjobs.com", "ms", "External"),
    ("NVIDIA", "nvidia.wd5.myworkdayjobs.com", "nvidia", "NVIDIAExternalCareerSite"),
    ("Salesforce", "salesforce.wd12.myworkdayjobs.com", "salesforce", "External_Career_Site"),
    ("Adobe", "adobe.wd5.myworkdayjobs.com", "adobe", "external_experienced"),
    ("Intel", "intel.wd1.myworkdayjobs.com", "intel", "External"),
    ("HP", "hp.wd5.myworkdayjobs.com", "hp", "ExternalCareerSite"),
    ("Cisco", "cisco.wd5.myworkdayjobs.com", "cisco", "Cisco_Careers"),
    ("Target", "target.wd5.myworkdayjobs.com", "target", "targetcareers"),
    ("Lowe's", "lowes.wd5.myworkdayjobs.com", "lowes", "LWS_External_CS"),
    ("Sanofi", "sanofi.wd3.myworkdayjobs.com", "sanofi", "SanofiCareers"),
    ("Thomson Reuters", "thomsonreuters.wd5.myworkdayjobs.com", "thomsonreuters", "External_Career_Site"),
    ("Bristol Myers Squibb", "bristolmyerssquibb.wd5.myworkdayjobs.com", "bristolmyerssquibb", "BMS"),
    ("Autodesk", "autodesk.wd1.myworkdayjobs.com", "autodesk", "Ext"),
    ("Workday", "workday.wd5.myworkdayjobs.com", "workday", "Workday"),
]
WORKDAY_TERMS = ["intern", "graduate", "trainee", "fresher", "early career", "associate software engineer",
                 "junior developer", "data analyst"]

# Tavily web search, limited to job-board sites (≈ 6 searches a day = well inside the free tier)
TAVILY_QUERIES = [
    "AI engineer fresher OR intern OR graduate job India",
    "machine learning engineer intern OR fresher India",
    "data engineer fresher OR graduate OR intern India",
    "data analyst fresher OR intern OR entry level India",
    "full stack developer fresher OR intern India",
    "software engineer graduate OR fresher OR SDE 1 India",
]
TAVILY_DOMAINS = ["boards.greenhouse.io", "job-boards.greenhouse.io", "jobs.lever.co", "jobs.ashbyhq.com",
                  "myworkdayjobs.com", "smartrecruiters.com", "wellfound.com", "instahyre.com", "cutshort.io"]

# Optional aggregators: used only if their keys are in .env
ADZUNA_QUERIES = ["fresher", "intern", "graduate trainee", "junior developer", "entry level data"]
JSEARCH_QUERIES = ["fresher software engineer in India", "data analyst fresher in India",
                   "machine learning intern in India", "data engineer fresher in India"]
