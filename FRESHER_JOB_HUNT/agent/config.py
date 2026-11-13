"""Settings for the Fresher Job Hunt agent. Edit these to change what it looks for."""

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LOCAL_STATE = HERE / "state"                 # dry-run preview for the local website (gitignored)

# ── Daily post ───────────────────────────────────────────────────────────────
SHARE_URL = "https://t.me/+bfrJNyeNWFhkNjdl"  # free invite link, added at the end of the day's last post
JOBS_PER_POST = 12                          # 10–12 jobs per experience section in the daily post
MIN_JOBS_PER_POST = 10
MAX_PER_COMPANY = 2                          # variety: at most 2 jobs from one company per post
MAX_AGE_DAYS = 3                             # only jobs posted in the last N days count as new
FIRST_RUN_AGE_DAYS = 7                       # look further back the very first time
POOL_DAYS = MAX_AGE_DAYS + 4                 # jobs found but not posted stay eligible for this many days
SEEN_DAYS = 30                               # remember a job's URL this long so it's never posted twice
TEASER_PER_SECTION = 1                       # jobs per section shown free on the website
DB_CLEANUP_BYTES = 450 * 1024 * 1024         # at this database size, each run starts deleting the oldest job records
GRACE_DAYS = 2                              # days after paid_until before a non-renewing member is removed
SEND_TIMES_IST = ["10:00", "18:00"]          # two posts a day; a scheduled run waits for the next of these
HEADS_UP_SECONDS = 60                        # "jobs drop in 1 minute" message goes out this long before the jobs
MODEL = "ministral-8b-latest"                # Mistral model for jobs whose experience level the rules can't tell
MAX_LLM_CHECKS = 60                          # LLM checks per run (one batched call; keeps it inside the free tier)

# ── Experience sections ──────────────────────────────────────────────────────
# key: (label, emoji, heading, min years, max years). A job goes in the section that contains the
# MINIMUM years it asks for, e.g. "2+ years" → 2–4, "5-8 years" → 4–6. 10–12 jobs are posted per section.
EXPERIENCE = {
    "0-2": ("0–2 yrs", "🎓", "Freshers & interns", 0, 1),
    "2-4": ("2–4 yrs", "🚀", "Early career", 2, 3),
    "4-6": ("4–6 yrs", "⭐", "Mid-level", 4, 5),
    "6+":  ("6+ yrs", "🏆", "Senior & lead", 6, 99),
}
SITE_URL_DEFAULT = "https://fresher-job-hunt.vercel.app"

# ── Fields ───────────────────────────────────────────────────────────────────
# key: (label, emoji, title pattern). Order matters: the first match is the job's main field.
FIELDS = {
    "ai_engineer":       ("AI Engineer",        "🤖", r"\b(ai|artificial intelligence|gen ?ai|llm|nlp|computer vision|agentic|prompt engineer)\b"),
    "ml_engineer":       ("ML Engineer",        "🧠", r"machine learning|\bml\b|mlops|deep learning|data scien"),
    "data_engineer":     ("Data Engineer",      "🛠", r"data engineer|\betl\b|big data|data platform|analytics engineer|data pipeline|data warehouse"),
    "cybersecurity":     ("Cybersecurity",      "🔐", r"cyber|security engineer|security analyst|information security|infosec|\bsoc\b|penetration|pen ?test|appsec|vulnerability|ethical hack|network security"),
    "data_analyst":      ("Data Analyst",       "📊", r"data analy|business analy|business intelligence|\bbi\b|analytics|insights analyst|product analyst|reporting analyst|mis analyst"),
    "qa_testing":        ("QA / Testing",       "🧪", r"\bqa\b|quality assurance|quality engineer|test engineer|tester|testing|\bsdet\b|test automation|automation test|selenium"),
    "frontend":          ("Frontend",           "🎨", r"front ?end|\breact\b|angular|\bvue\b|ui developer|ui engineer"),
    "backend":           ("Backend",            "⚙️", r"back ?end|\bnode\b|java developer|python developer|golang|\.net developer|api developer|spring boot"),
    "full_stack":        ("Full Stack",         "🌐", r"full ?stack|web developer|\bmern\b|\bmean\b"),
    "software_engineer": ("Software Engineer",  "💻", r"software|\bsde\b|developer|programmer|graduate engineer|engineer trainee|application engineer|cloud engineer|devops"),
    "hr":                ("HR",                 "👥", r"\bhr\b|human resources?|recruiter|recruitment|talent acquisition|people operations|people partner"),
}
FIELD_PATTERNS = {k: re.compile(v[2], re.I) for k, v in FIELDS.items()}

# ── Title rules ──────────────────────────────────────────────────────────────
FRESHER_TITLE = re.compile(
    r"\b(intern|internship|trainee|graduate|grad|fresher|freshers|junior|jr\.?|entry[- ]level|new grad|campus|"
    r"early career|early careers|early talent|apprentice|associate software|associate data|associate engineer|"
    r"associate developer|associate analyst|engineer i|analyst i|sde ?1|sde-1|sde i|engineer 1)\b", re.I)
# Title hints for the other sections (used only when the description doesn't state the years).
# Checked in this order: 6+, 4–6, 2–4, then FRESHER_TITLE for 0–2.
TITLE_6_PLUS = re.compile(r"\b(staff|principal|lead|manager|mgr|architect|technical leader|expert|iv)\b", re.I)
TITLE_4_6 = re.compile(r"\b(senior|sr|iii|engineer 3|sde ?3|sde-3|sde iii)\b", re.I)
TITLE_2_4 = re.compile(r"\b(ii|engineer 2|sde ?2|sde-2|mid[- ]level|intermediate)\b", re.I)
# Executive roles are skipped in every section.
EXEC_TITLE = re.compile(r"\b(director|vp|vice president|head|chief|cto|cio|president|distinguished|fellow)\b", re.I)
NON_TECH = re.compile(
    r"sales|account executive|account manager|payroll|finance|"
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
    # Mass recruiters for freshers (checked 13 Nov 2026)
    ("Accenture", "accenture.wd103.myworkdayjobs.com", "accenture", "AccentureCareers"),
    ("PwC", "pwc.wd3.myworkdayjobs.com", "pwc", "Global_Experienced_Careers"),
]

# Mass recruiters without a public job API: Tavily search limited to each company's official careers site.
# (TCS, Infosys, Tech Mahindra and LTIMindtree were tested on 13 Nov 2026 and returned no usable job pages.)
OFFICIAL_SITES = {
    "Wipro": ["careers.wipro.com"],
    "Cognizant": ["careers.cognizant.com"],
    "Capgemini": ["careers.capgemini.com"],
    "HCLTech": ["careers.hcltech.com"],
    "IBM": ["careers.ibm.com"],
}
# Companies that hire freshers in large numbers. Their jobs get a "🏭 Mass recruiter" badge.
MASS_RECRUITER = re.compile(
    r"\b(tcs|tata consultancy|infosys|wipro|cognizant|accenture|capgemini|hcl\s?tech|hcl technologies|tech mahindra|"
    r"ltimindtree|lti mindtree|ibm|pwc|pricewaterhouse|deloitte|kpmg|ernst\s*&\s*young|genpact|mphasis|hexaware)\b", re.I)


def is_mass_recruiter(company) -> bool:
    return bool(MASS_RECRUITER.search(company or ""))


OFFICIAL_JOB_URL = re.compile(r"/job/|/jobs/\d|JobDetail", re.I)     # a single job's page, not a search or blog page
WORKDAY_TERMS = ["intern", "graduate", "trainee", "fresher", "early career", "associate software engineer",
                 "junior developer", "data analyst", "qa engineer", "security analyst", "hr intern",
                 # experienced sections
                 "software engineer", "data engineer", "machine learning engineer", "senior software engineer",
                 "lead engineer"]
WORKDAY_MAX_DETAILS = 30                     # job pages fetched per Workday company per run

# Tavily web search, limited to job-board sites (≈ 6 searches a day = well inside the free tier)
TAVILY_QUERIES = [
    "AI engineer fresher OR intern OR graduate job India",
    "machine learning engineer intern OR fresher India",
    "data engineer fresher OR graduate OR intern India",
    "data analyst fresher OR intern OR entry level India",
    "full stack developer fresher OR intern India",
    "software engineer graduate OR fresher OR SDE 1 India",
    "frontend OR backend developer fresher OR intern India",
    "cybersecurity OR QA tester OR automation tester fresher India",
    "HR intern OR HR executive OR recruiter fresher India",
    # experienced sections
    "software engineer 2-4 years experience India",
    "senior data engineer OR senior ML engineer India",
    "lead OR staff software engineer India",
]
TAVILY_DOMAINS = ["boards.greenhouse.io", "job-boards.greenhouse.io", "jobs.lever.co", "jobs.ashbyhq.com",
                  "myworkdayjobs.com", "smartrecruiters.com", "wellfound.com", "instahyre.com", "cutshort.io"]

# Optional aggregators: used only if their keys are in .env
ADZUNA_QUERIES = ["fresher", "intern", "graduate trainee", "junior developer", "entry level data",
                  "software engineer", "senior engineer", "lead engineer"]
# (query, JSearch experience filter)
JSEARCH_QUERIES = [("fresher software engineer in India", "under_3_years_experience,no_experience"),
                   ("data analyst fresher in India", "under_3_years_experience,no_experience"),
                   ("machine learning intern in India", "under_3_years_experience,no_experience"),
                   ("data engineer fresher in India", "under_3_years_experience,no_experience"),
                   ("software engineer in India", "more_than_3_years_experience"),
                   ("data engineer in India", "more_than_3_years_experience")]
