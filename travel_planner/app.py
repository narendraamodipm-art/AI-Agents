"""Travel Planner AI Agent.

An AI AGENT (the LLM decides the steps):
    Goal → LLM thinks → picks a tool (web search / weather / budget) → code runs it
         → result goes back to the LLM → repeat until the LLM writes the final plan

LLM:   Mistral ministral-8b-latest (OpenAI-compatible API) with tool calling
Tools: Tavily (web search), OpenWeather (forecast), Python (budget maths)

Run:  streamlit run "AI AGENTS/travel_planner/app.py"
"""

import datetime as dt
import json
import os
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient


# ── Setup ────────────────────────────────────────────────────────────────────
def load_env():
    """Load the nearest .env file above this script (holds the API keys)."""
    for folder in Path(__file__).resolve().parents:
        if (folder / ".env").exists():
            load_dotenv(folder / ".env")
            return


load_env()

MISTRAL_BASE_URL = "https://api.mistral.ai/v1"
MODEL = "ministral-8b-latest"
MAX_STEPS = 12                  # safety limit: the agent can't loop forever
MAX_OUTPUT_TOKENS = 2000        # cap each reply

# Every agent step re-sends the whole conversation, so keep the context small
# (faster, cheaper, and stays clear of free-tier rate limits):
MAX_TOOL_RESULT_CHARS = 2000    # a single tool result sent back to the LLM
KEEP_FULL_RESULTS = 3           # the latest N tool results stay complete …
TRIMMED_RESULT_CHARS = 400      # … older ones are cut to this length

REQUIRED_KEYS = ["MISTRAL_API_KEY", "TAVILY_API_KEY", "OPENWEATHER_API_KEY"]


def call_with_retry(fn, *args, retries=8, **kwargs):
    """Retry on rate limits (HTTP 429), waiting longer each time (or as long as the API says)."""
    delay = 2
    for attempt in range(retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            msg = str(e).lower()
            if ("429" in msg or "rate limit" in msg) and attempt < retries - 1:
                match = re.search(r"try again in (?:(\d+)m)?([\d.]+)s", msg)
                wait = (int(match.group(1) or 0) * 60 + float(match.group(2)) + 0.5) if match else delay
                time.sleep(wait)
                delay *= 2
                continue
            raise


# ═════════════════════════════════════════════════════════════════════════════
#  TOOLS — ordinary Python functions the agent can ask to use
# ═════════════════════════════════════════════════════════════════════════════
def search_web(query: str, max_results: int = 4) -> dict:
    """Tavily web search: attractions, hotels, prices, travel options."""
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    res = client.search(query=query, max_results=min(max_results, 5), include_answer=True)
    return {
        "answer": (res.get("answer") or "")[:400],
        "results": [
            {"title": r.get("title"), "url": r.get("url"), "content": (r.get("content") or "")[:300]}
            for r in res.get("results", [])
        ],
    }


def get_weather_forecast(city: str, country_code: str = "", state: str = "") -> dict:
    """OpenWeather: find the place, then summarise the 5-day forecast per day."""
    key = os.getenv("OPENWEATHER_API_KEY")
    base = "https://api.openweathermap.org"

    # 1. city name → coordinates (geocoding). Returns up to 5 matching places.
    q = ",".join(p for p in [city, country_code] if p)
    places = requests.get(f"{base}/geo/1.0/direct",
                          params={"q": q, "limit": 5, "appid": key}, timeout=20).json()
    if not places:
        return {"error": f"Location '{city}' not found. Try a nearby bigger city."}

    pick = places[0]
    if state:                                   # prefer the match in the requested state
        for p in places:
            if state.lower() in (p.get("state") or "").lower():
                pick = p
                break

    # 2. coordinates → 5-day forecast in 3-hour steps
    fc = requests.get(f"{base}/data/2.5/forecast",
                      params={"lat": pick["lat"], "lon": pick["lon"], "units": "metric", "appid": key},
                      timeout=20).json()

    # 3. group the 3-hour steps into one summary per day
    by_day = defaultdict(list)
    for item in fc.get("list", []):
        by_day[item["dt_txt"][:10]].append(item)

    daily = []
    for date, items in by_day.items():
        temps = [i["main"]["temp"] for i in items]
        condition = Counter(i["weather"][0]["main"] for i in items).most_common(1)[0][0]
        rain_chance = max(i.get("pop", 0) for i in items)        # pop = probability of rain
        daily.append({"date": date, "min_c": round(min(temps)), "max_c": round(max(temps)),
                      "condition": condition, "max_rain_chance": f"{rain_chance * 100:.0f}%"})

    return {
        # the agent must CHECK this is the place the user meant
        "resolved_location": {"name": pick.get("name"), "state": pick.get("state"),
                              "country": pick.get("country")},
        "other_matches": [f"{p.get('name')}, {p.get('state', '')}, {p.get('country')}"
                          for p in places if p is not pick],
        "forecast_days": daily,
        "note": "Forecast covers only the next 5 days. For later dates, use search_web "
                "for the typical weather in that month.",
    }


def calculate_budget(items: list, budget: float, travellers: int = 1) -> dict:
    """Add up trip costs exactly (LLMs are bad at arithmetic, Python isn't)."""
    lines, total = [], 0.0
    for item in items:
        cost = float(item.get("cost", 0)) * float(item.get("quantity", 1))
        total += cost
        lines.append({"name": item.get("name", "item"), "cost": round(cost)})
    return {
        "lines": lines,
        "total": round(total),
        "budget": round(budget),
        "remaining": round(budget - total),
        "over_budget": total > budget,
        "per_person": round(total / max(travellers, 1)),
    }


TOOL_FUNCTIONS = {
    "search_web": search_web,
    "get_weather_forecast": get_weather_forecast,
    "calculate_budget": calculate_budget,
}

# The LLM never sees the Python code — only these descriptions (JSON Schema).
# Clear descriptions = the LLM picks the right tool with the right arguments.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for up-to-date travel information: attractions, "
                           "restaurants, hotels and their prices, transport options, typical weather.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "a focused search query"},
                    "max_results": {"type": "integer", "description": "1-5, default 4"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_forecast",
            "description": "Get the 5-day daily weather forecast for a city. Check "
                           "resolved_location in the result — if it is the wrong place, call again "
                           "with a more specific city name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "city name, e.g. 'Panaji'"},
                    "country_code": {"type": "string", "description": "ISO country code, e.g. 'IN'"},
                    "state": {"type": "string", "description": "state/region to prefer, e.g. 'Goa'"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_budget",
            "description": "Add up trip costs and compare with the budget. Use it for every budget "
                           "check instead of doing maths yourself.",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "cost": {"type": "number", "description": "cost of ONE unit"},
                                "quantity": {"type": "number", "description": "e.g. nights, people"},
                            },
                            "required": ["name", "cost"],
                        },
                    },
                    "budget": {"type": "number"},
                    "travellers": {"type": "integer"},
                },
                "required": ["items", "budget"],
            },
        },
    },
]


def run_tool(name: str, arguments_json: str):
    """Run the tool the LLM asked for. Errors go BACK to the LLM so it can adapt."""
    try:
        args = json.loads(arguments_json or "{}")
    except json.JSONDecodeError:
        return {"error": "Arguments were not valid JSON."}
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return {"error": f"Unknown tool '{name}'."}
    try:
        return fn(**args)
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


# ═════════════════════════════════════════════════════════════════════════════
#  THE AGENT LOOP  (Reason → Act → Observe → repeat)
# ═════════════════════════════════════════════════════════════════════════════
SYSTEM_PROMPT = """You are an expert travel-planning AGENT. Today's date is {today}.
You have tools: search_web, get_weather_forecast, calculate_budget. Use them — don't guess
facts you can look up.

How to work:
1. Weather: call get_weather_forecast for the destination. CHECK "resolved_location": if it
   is not the place the user means (wrong state or country), call it again with a more
   specific city (for example, for Goa use "Panaji" with state "Goa"). If the trip dates are
   beyond the forecast range, use search_web for the typical weather in that month.
2. Use search_web to find top attractions that match the user's interests, and places to
   stay with real prices that fit the budget (plus travel from the origin city if given).
3. Use calculate_budget with your cost estimates (stay, food, local transport, activities,
   travel). If over_budget is true, search for cheaper options and recalculate until it
   fits — or explain clearly why it can't. Plan a COMFORTABLE trip that uses a good part
   of the budget (roughly 60-95%); only pick the cheapest options when money is tight.
   The budget table in your answer must match the LAST calculate_budget result exactly —
   if you change any cost, call calculate_budget again.
4. Fit the plan to the weather: outdoor activities on dry days, indoor ones on rainy days.

Rules: never invent prices — use numbers from search results and write "approx." for
estimates. Be efficient: about 4-7 tool calls in total. You may request SEVERAL tools in
one step (e.g. the weather and two searches together) — that saves time.

When you are done, reply WITHOUT calling a tool, in Markdown with real ## headings
(not bold text):
## Trip summary   (destination, dates, travellers, total cost vs budget)
## Weather        (table: date | condition | temperature | rain chance — or typical weather)
## Day-by-day plan (### Day N — date: morning / afternoon / evening, and why it suits the weather)
## Where to stay  (1-2 options with approx. price per night)
## Budget         (table from calculate_budget: item | cost, then total and remaining)
## Tips
## Sources        (the actual URLs from search results you used)"""


def clean_markdown(text: str) -> str:
    """Fix '**## Heading**' (bold-wrapped headings) that some models produce."""
    return re.sub(r"^\*\*(#{1,6} .*?)\*\*\s*$", r"\1", text or "", flags=re.MULTILINE)


def trim_old_results(messages):
    """Short-term memory management: keep the latest tool results in full and cut
    older ones down. The agent has already used them, and a smaller context keeps
    each step fast and within free-tier limits."""
    tool_msgs = [m for m in messages if m["role"] == "tool"]
    for m in tool_msgs[:-KEEP_FULL_RESULTS]:
        if len(m["content"]) > TRIMMED_RESULT_CHARS:
            m["content"] = m["content"][:TRIMMED_RESULT_CHARS] + " …(older result trimmed)"


def llm_call(client, messages, use_tools=True):
    """One LLM call to Mistral."""
    kwargs = {"model": MODEL, "messages": messages, "temperature": 0.3,
              "max_tokens": MAX_OUTPUT_TOKENS}
    if use_tools:
        kwargs.update(tools=TOOLS, tool_choice="auto")
    return call_with_retry(client.chat.completions.create, **kwargs)


def run_agent(request_text: str, on_step):
    """Run the agent until it answers without a tool call (or hits MAX_STEPS)."""
    client = OpenAI(api_key=os.getenv("MISTRAL_API_KEY"), base_url=MISTRAL_BASE_URL)
    today = dt.date.today().strftime("%A, %d %B %Y")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(today=today)},
        {"role": "user", "content": request_text},
    ]
    steps = []

    for _ in range(MAX_STEPS):
        trim_old_results(messages)
        # REASON: the LLM looks at everything so far and decides what to do next
        response = llm_call(client, messages)
        msg = response.choices[0].message

        # no tool requested → this is the final answer
        if not msg.tool_calls:
            return clean_markdown(msg.content), steps

        # remember the LLM's tool request in the conversation (memory)
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
        })

        for tc in msg.tool_calls:
            # ACT: our code runs the tool the LLM chose
            result = run_tool(tc.function.name, tc.function.arguments)
            # OBSERVE: send the result back to the LLM
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False)[:MAX_TOOL_RESULT_CHARS],
            })
            step = {"n": len(steps) + 1, "tool": tc.function.name,
                    "args": tc.function.arguments, "result": result}
            steps.append(step)
            on_step(step)

    # safety net: step limit reached → ask for the best answer with what we have
    messages.append({"role": "user", "content": "Step limit reached. Write the final plan now "
                                                "using the information you already have."})
    trim_old_results(messages)
    response = llm_call(client, messages, use_tools=False)
    return clean_markdown(response.choices[0].message.content), steps


# ═════════════════════════════════════════════════════════════════════════════
#  UI
# ═════════════════════════════════════════════════════════════════════════════
TOOL_ICONS = {"search_web": "🔍", "get_weather_forecast": "🌦️", "calculate_budget": "🧮"}


def summarise_result(step) -> str:
    """One short line describing a tool result, for the live step log."""
    r = step["result"]
    if "error" in r:
        return f"⚠️ {r['error']}"
    if step["tool"] == "search_web":
        titles = [x["title"] for x in r.get("results", [])][:2]
        return f"{len(r.get('results', []))} results — " + " | ".join(titles)
    if step["tool"] == "get_weather_forecast":
        loc = r["resolved_location"]
        return f"{loc['name']}, {loc.get('state') or ''}, {loc['country']} · {len(r['forecast_days'])} days"
    if step["tool"] == "calculate_budget":
        flag = "❌ over budget" if r["over_budget"] else "✅ within budget"
        return f"total ₹{r['total']:,} of ₹{r['budget']:,} → {flag}"
    return ""


def main():
    st.set_page_config(page_title="Travel Planner Agent", page_icon="✈️", layout="wide")
    st.title("✈️ Travel Planner Agent")
    st.caption("An AI agent that searches the web, checks the weather and balances your budget "
               "— deciding each step by itself. Powered by Mistral, Tavily and OpenWeather.")

    with st.sidebar:
        st.header("Settings")
        st.markdown(f"🤖 Model: `{MODEL}` (Mistral)")
        st.divider()
        st.markdown(
            "**How the agent works**\n\n"
            "1. 🧠 The LLM decides the next step\n"
            "2. 🔧 It calls a tool:\n"
            "   - 🔍 web search (Tavily)\n"
            "   - 🌦️ weather (OpenWeather)\n"
            "   - 🧮 budget (Python)\n"
            "3. 👀 It reads the result\n"
            "4. 🔁 Repeats until the plan is ready\n\n"
            f"Safety limit: {MAX_STEPS} steps"
        )
        st.caption("Planning usually takes under a minute; it can take longer if the "
                   "agent has to wait out API rate limits.")

    missing = [k for k in REQUIRED_KEYS if not os.getenv(k)]
    if missing:
        st.error(f"Missing API keys in .env: {', '.join(missing)}")
        st.stop()

    c1, c2, c3 = st.columns(3)
    destination = c1.text_input("Destination", "Goa")
    origin = c1.text_input("Travelling from (optional)", "Bengaluru")
    start = c2.date_input("Start date", dt.date.today() + dt.timedelta(days=1))
    days = c2.number_input("Days", 1, 14, 3)
    travellers = c3.number_input("Travellers", 1, 20, 2)
    budget = c3.number_input("Total budget (₹)", 1000, 10_000_000, 30000, step=1000)
    interests = st.multiselect(
        "Interests",
        ["Beaches", "Food", "Nightlife", "History & culture", "Nature & trekking",
         "Adventure sports", "Shopping", "Relaxation", "Photography"],
        default=["Beaches", "Food"],
    )
    extra = st.text_input("Anything else? (optional)", placeholder="e.g. vegetarian food, no long drives")

    if st.button("🧭 Plan my trip", type="primary", disabled=not destination.strip()):
        request_text = (
            "Plan a trip.\n"
            f"Destination: {destination}\n"
            f"Start date: {start:%A, %d %B %Y}\n"
            f"Number of days: {days}\n"
            f"Travellers: {travellers}\n"
            f"Total budget: ₹{budget:,} (INR) for everyone\n"
            f"Interests: {', '.join(interests) or 'general sightseeing'}\n"
            f"Travelling from: {origin or 'not specified'}\n"
            f"Extra requests: {extra or 'none'}"
        )
        with st.status("🧠 Agent is planning…", expanded=True) as status:
            def show_step(step):
                icon = TOOL_ICONS.get(step["tool"], "🔧")
                st.markdown(f"**Step {step['n']}** · {icon} `{step['tool']}` `{step['args'][:120]}`")
                st.caption(summarise_result(step))

            try:
                plan, steps = run_agent(request_text, show_step)
            except Exception as e:
                status.update(label="Agent error", state="error")
                st.error(f"{type(e).__name__}: {e}\n\nIf this is a rate-limit (429) error, "
                         "wait a minute and try again.")
                st.stop()
            status.update(label=f"✅ Plan ready — {len(steps)} tool calls", state="complete",
                          expanded=False)

        st.session_state.trip = {"plan": plan, "steps": steps, "request": request_text}

    trip = st.session_state.get("trip")
    if not trip:
        return

    tools_used = Counter(s["tool"] for s in trip["steps"])
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tool calls", len(trip["steps"]))
    m2.metric("🔍 Searches", tools_used.get("search_web", 0))
    m3.metric("🌦️ Weather checks", tools_used.get("get_weather_forecast", 0))
    m4.metric("🧮 Budget checks", tools_used.get("calculate_budget", 0))

    tab_plan, tab_steps = st.tabs(["🗺️ Trip plan", "🧭 What the agent did"])
    with tab_plan:
        st.markdown(trip["plan"] or "_The agent returned an empty answer — try again._")

        # real URLs collected by CODE from the search results (small models often
        # cite searches instead of links, so we don't rely on the LLM for this)
        urls = []
        for s in trip["steps"]:
            if s["tool"] == "search_web" and "results" in s["result"]:
                for r in s["result"]["results"]:
                    if r.get("url") and r["url"] not in [u for u, _ in urls]:
                        urls.append((r["url"], r.get("title") or r["url"]))
        if urls:
            with st.expander(f"🔗 Web pages the agent read ({len(urls)})"):
                for url, title in urls:
                    st.markdown(f"- [{title}]({url})")

        st.download_button("⬇️ Download plan (.md)", trip["plan"] or "", file_name="trip_plan.md")
    with tab_steps:
        st.caption("Every decision below was made by the LLM, not hard-coded.")
        for s in trip["steps"]:
            icon = TOOL_ICONS.get(s["tool"], "🔧")
            with st.expander(f"Step {s['n']} · {icon} {s['tool']} — {summarise_result(s)[:90]}"):
                st.markdown("**Arguments the LLM chose**")
                st.code(s["args"], language="json")
                st.markdown("**Tool result sent back to the LLM**")
                st.json(s["result"], expanded=False)


if __name__ == "__main__":
    main()
