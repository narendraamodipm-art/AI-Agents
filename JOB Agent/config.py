"""Settings for the GCC job agent — edit these to change what it looks for."""

from pathlib import Path

HERE = Path(__file__).resolve().parent
RESUME_PATH = HERE / "Nikhil_Kumar_Resume-2.docx.pdf"
DATA_DIR = HERE / "data"                     # job database + cached resume profile (gitignored)
DB_PATH = DATA_DIR / "jobs.db"

# ── What to look for ─────────────────────────────────────────────────────────
SEARCH_TERMS = ["data engineer", "big data", "etl", "analytics engineer"]   # sent to career-site search
# a job title must contain one of these…
TITLE_KEYWORDS = ["data engineer", "data engineering", "big data", "etl", "analytics engineer",
                  "data platform", "dataops", "data integration", "cloud data", "data pipeline",
                  "snowflake", "bigquery", "gcp data", "data developer"]
# …and none of these (whole words) — roles too senior / junior / different for ~4 years' experience
TITLE_EXCLUDE = ["principal", "director", "vp", "vice president", "head", "intern", "internship",
                 "manager", "distinguished", "fellow", "scientist", "sales", "account executive"]
INDIA_CITIES = ["bengaluru", "bangalore", "hyderabad", "chennai", "pune", "mumbai", "gurugram", "gurgaon",
                "noida", "delhi", "kolkata", "ahmedabad", "kochi", "coimbatore", "mysuru", "trivandrum",
                "thiruvananthapuram", "jaipur", "chandigarh", "karnataka", "telangana", "maharashtra",
                "tamil nadu", "haryana"]
EXCLUDE_COMPANIES = ["Albertsons"]           # e.g. current employer

# ── How much to do per run ───────────────────────────────────────────────────
MAX_AGE_DAYS = 3                 # only jobs posted in the last N days count as "new"
FIRST_RUN_AGE_DAYS = 7           # look further back the very first time
MAX_JOBS_TO_SCORE = 40           # LLM-scored per run; the rest wait for the next run
MIN_FIT_TO_NOTIFY = 50           # interview-chance estimate (0–100) needed to be shortlisted
MAX_NEW_GCC_SEARCHES = 3         # Tavily job searches for newly announced GCCs per run (free tier: 1,000/month;
                                 # salary + company look-ups for shortlisted jobs use ~10 more a day)
MODEL = "ministral-8b-latest"

# ── Auto-fill (apply_bot.py) ─────────────────────────────────────────────────
AUTO_FILL = True                 # replying APPLY also opens Edge and fills the form (you click Submit)
APPLY_MODEL = "ministral-14b-latest"   # matches form fields to your details — a bigger model is worth it here
APPLICANT_PATH = HERE / "applicant.json"
BROWSER_PROFILE = DATA_DIR / "edge-profile"   # the bot's own Edge profile: remembers logins

# ── GCC career sites with public job feeds (verified 30 Oct 2026) ────────────
# (company, host, tenant, site) → https://{host}/wday/cxs/{tenant}/{site}/jobs
WORKDAY = [
    ("Target", "target.wd5.myworkdayjobs.com", "target", "targetcareers"),
    ("Lowe's", "lowes.wd5.myworkdayjobs.com", "lowes", "LWS_External_CS"),
    ("Wells Fargo", "wf.wd1.myworkdayjobs.com", "wf", "WellsFargoJobs"),
    ("Mastercard", "mastercard.wd1.myworkdayjobs.com", "mastercard", "CorporateCareers"),
    ("PayPal", "paypal.wd1.myworkdayjobs.com", "paypal", "jobs"),
    ("Citi", "citi.wd5.myworkdayjobs.com", "citi", "2"),
    ("Fidelity", "fmr.wd1.myworkdayjobs.com", "fmr", "FidelityCareers"),
    ("Morgan Stanley", "ms.wd5.myworkdayjobs.com", "ms", "External"),
    ("Bank of America", "ghr.wd1.myworkdayjobs.com", "ghr", "Lateral-US"),
    ("NVIDIA", "nvidia.wd5.myworkdayjobs.com", "nvidia", "NVIDIAExternalCareerSite"),
    ("Salesforce", "salesforce.wd12.myworkdayjobs.com", "salesforce", "External_Career_Site"),
    ("Adobe", "adobe.wd5.myworkdayjobs.com", "adobe", "external_experienced"),
    ("Intel", "intel.wd1.myworkdayjobs.com", "intel", "External"),
    ("HP", "hp.wd5.myworkdayjobs.com", "hp", "ExternalCareerSite"),
    ("Cisco", "cisco.wd5.myworkdayjobs.com", "cisco", "Cisco_Careers"),
    ("Nike", "nike.wd1.myworkdayjobs.com", "nike", "nke"),
    ("Caterpillar", "cat.wd5.myworkdayjobs.com", "cat", "CaterpillarCareers"),
    ("Chevron", "chevron.wd5.myworkdayjobs.com", "chevron", "jobs"),
    ("Bristol Myers Squibb", "bristolmyerssquibb.wd5.myworkdayjobs.com", "bristolmyerssquibb", "BMS"),
    ("Pfizer", "pfizer.wd1.myworkdayjobs.com", "pfizer", "PfizerCareers"),
    ("Sanofi", "sanofi.wd3.myworkdayjobs.com", "sanofi", "SanofiCareers"),
    ("Thomson Reuters", "thomsonreuters.wd5.myworkdayjobs.com", "thomsonreuters", "External_Career_Site"),
    ("Equinix", "equinix.wd1.myworkdayjobs.com", "equinix", "External"),
    ("Analog Devices", "analogdevices.wd1.myworkdayjobs.com", "analogdevices", "External"),
    ("Autodesk", "autodesk.wd1.myworkdayjobs.com", "autodesk", "Ext"),
    ("Workday", "workday.wd5.myworkdayjobs.com", "workday", "Workday"),
]
# board token → company name  (https://boards-api.greenhouse.io/v1/boards/{token}/jobs)
GREENHOUSE = {"databricks": "Databricks", "stripe": "Stripe", "okta": "Okta", "mongodb": "MongoDB",
              "rubrik": "Rubrik", "twilio": "Twilio", "gitlab": "GitLab", "elastic": "Elastic",
              "coinbase": "Coinbase"}

# ── Tavily: spotting newly announced GCCs in the news ────────────────────────
GCC_NEWS_QUERIES = ["new global capability centre GCC launched India",
                    "company opens GCC in Bengaluru Hyderabad Pune Chennai hiring"]
# a web result counts as a single job posting only if its URL looks like one
JOB_URL_PATTERNS = ["myworkdayjobs.com", "myworkdaysite.com", "greenhouse.io", "lever.co/", "ashbyhq.com",
                    "smartrecruiters.com", "icims.com", "successfactors", "linkedin.com/jobs/view",
                    "naukri.com/job-listings", "/job/", "/jobs/view", "jobdetail"]
