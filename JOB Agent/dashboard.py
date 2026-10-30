"""Dashboard for the GCC Job Agent: browse matches, approve jobs, read cover letters.

Run:  streamlit run "JOB Agent/dashboard.py"
"""

import html
import json
import os

import streamlit as st

import agent          # also loads .env
import config
import matching
import store
import telegram_bot

STATUS_LABELS = {"shortlisted": "🎯 Shortlisted", "approved": "✅ Approved (kit ready)", "applied": "🎉 Applied",
                 "skipped": "🗑 Skipped", "low_fit": "⬇️ Low fit", "pending": "⏳ Not scored yet"}


def chips(items, color):
    if not items:
        return "<i>none</i>"
    return " ".join(
        f"<span style='background:{color};color:white;padding:3px 10px;border-radius:12px;"
        f"margin:2px;display:inline-block;font-size:0.85rem'>{html.escape(s)}</span>"
        for s in items
    )


def jobs_table(rows) -> str:
    """Plain HTML table — st.dataframe needs pandas, whose DLLs Windows Application Control blocks here."""
    def fit_cell(fit):
        if fit is None:
            return "–"
        color = "#16a34a" if fit >= 75 else "#ca8a04" if fit >= 50 else "#dc2626"
        return f"<b style='color:{color}'>{fit}</b>"

    body = "".join(
        f"<tr><td>#{j['no']}</td><td>{fit_cell(j['fit'])}</td><td>{html.escape(j['title'])}</td>"
        f"<td>{html.escape(j['company'])}</td><td>{html.escape(j['location'])}</td><td>{j['posted']}</td>"
        f"<td>{STATUS_LABELS.get(j['status'], j['status'])}</td>"
        f"<td><a href='{html.escape(j['url'], quote=True)}' target='_blank'>open</a></td></tr>"
        for j in rows
    )
    head = "".join(f"<th>{h}</th>" for h in ["#", "Fit", "Role", "Company", "Location", "Posted", "Status", "Link"])
    return f"<table style='width:100%;font-size:0.9rem'><tr>{head}</tr>{body}</table>"


def sidebar(con):
    with st.sidebar:
        st.header("Agent")
        checks = {
            "Resume": config.RESUME_PATH.exists(),
            "Mistral key": bool(os.getenv("MISTRAL_API_KEY")),
            "Tavily key": bool(os.getenv("TAVILY_API_KEY")),
            "Telegram bot": telegram_bot.configured(),
        }
        for name, ok in checks.items():
            st.write(f"{'✅' if ok else '❌'} {name}")

        notify = st.toggle("Send Telegram message after run", value=telegram_bot.configured(),
                           disabled=not telegram_bot.configured())
        if st.button("🔎 Run agent now", type="primary", width="stretch"):
            with st.status("Running…", expanded=True) as status:
                agent.run(log=st.write, notify=notify)
                status.update(label="Done", state="complete", expanded=False)
        if st.button("💬 Check Telegram replies", width="stretch",
                     disabled=not telegram_bot.configured()):
            with st.status("Reading replies…", expanded=True) as status:
                agent.handle_replies(log=st.write)
                status.update(label="Done", state="complete", expanded=False)
        st.divider()
        st.caption(f"Looks for: {', '.join(config.SEARCH_TERMS)}\n\n"
                   f"{len(config.WORKDAY) + len(config.GREENHOUSE)} GCC career sites + new GCCs from the news.\n\n"
                   f"Shortlists jobs with fit ≥ {config.MIN_FIT_TO_NOTIFY}/100. Edit JOB Agent/config.py to change.")


def job_detail(con, j):
    st.subheader(f"#{j['no']} {j['title']} · {j['company']}")
    st.caption(f"{j['location']} · posted {j['posted']} · via {j['source']} · {STATUS_LABELS.get(j['status'], j['status'])}")

    if j["fit"] is not None:
        c1, c2 = st.columns(2)
        c1.metric("Interview chance (estimate)", f"{j['fit']} / 100")
        c2.metric("Overall match", f"{j['match']}%")
        st.info(j["summary"])
        gap = json.loads(j["gap"])
        st.markdown("**✅ Matched required**  " + chips(gap["matched_required"], "#16a34a"), unsafe_allow_html=True)
        st.markdown("**❌ Missing required**  " + chips(gap["missing_required"], "#dc2626"), unsafe_allow_html=True)
        st.markdown("**👍 Matched nice-to-have**  " + chips(gap["matched_nice_to_have"], "#2563eb"), unsafe_allow_html=True)

    b1, b2, b3, b4 = st.columns(4)
    b1.link_button("🔗 Open apply page", j["url"], width="stretch")
    if b2.button("✅ Approve + write kit", disabled=j["fit"] is None, width="stretch"):
        with st.spinner("Writing cover letter and resume tips…"):
            agent.approve(con, j["no"])
        st.rerun()
    if b3.button("🎉 Mark applied", width="stretch"):
        store.update_job(con, j["no"], status="applied")
        st.rerun()
    if b4.button("🗑 Skip", width="stretch"):
        store.update_job(con, j["no"], status="skipped")
        st.rerun()

    if j["letter"]:
        tab_letter, tab_tips = st.tabs(["💌 Cover letter", "✍️ Resume tips"])
        with tab_letter:
            warnings = json.loads(j["warnings"] or "[]")
            if warnings:
                st.warning("⚠️ These numbers are not in your resume or the job description — "
                           f"check or remove them before sending: {', '.join(warnings)}")
            st.text_area("Cover letter", j["letter"], height=380)
            st.download_button("⬇️ Download (.txt)", j["letter"],
                               file_name=f"cover_letter_{j['company']}_{j['no']}.txt".replace(" ", "_"))
        with tab_tips:
            tips = matching.ResumeSuggestions.model_validate_json(j["tips"])
            if tips.skills_to_highlight:
                st.markdown("**Put front and centre:** " + ", ".join(tips.skills_to_highlight))
            for b in tips.rewrites:
                st.markdown(f"**Before:** {b.original}")
                st.success(f"**After:** {b.improved}")
                st.caption(f"Why: {b.reason}")
            for tip in tips.tips:
                st.markdown(f"- {tip}")

    with st.expander("Job description"):
        st.text(j["description"])


def main():
    st.set_page_config(page_title="GCC Job Agent", page_icon="🧭", layout="wide")
    st.title("🧭 GCC Job Agent")
    st.caption("New data-engineering jobs at Global Capability Centres in India, scored against your resume.")

    con = store.connect()
    sidebar(con)

    all_jobs = store.jobs(con)
    count = lambda s: sum(j["status"] == s for j in all_jobs)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Shortlisted", count("shortlisted"))
    m2.metric("Approved (kit ready)", count("approved"))
    m3.metric("Applied", count("applied"))
    m4.metric("Jobs tracked", len(all_jobs))

    tab_jobs, tab_gccs = st.tabs(["🎯 Jobs", "🆕 New GCCs"])

    with tab_jobs:
        f1, f2 = st.columns([3, 1])
        statuses = f1.multiselect("Status", list(STATUS_LABELS), default=["shortlisted", "approved"],
                                  format_func=STATUS_LABELS.get)
        min_fit = f2.slider("Min fit", 0, 100, 0, step=5)
        rows = [j for j in all_jobs if j["status"] in statuses and (j["fit"] or 0) >= min_fit]
        if not rows:
            st.info("No jobs here yet — click **Run agent now** in the sidebar.")
        else:
            st.markdown(jobs_table(rows), unsafe_allow_html=True)
            by_no = {j["no"]: j for j in rows}
            pick = st.selectbox("Open a job", list(by_no),
                                format_func=lambda n: f"#{n} {by_no[n]['title']} · {by_no[n]['company']}")
            st.divider()
            job_detail(con, by_no[pick])

    with tab_gccs:
        gccs = store.gccs(con)
        if not gccs:
            st.info("No new GCCs found yet.")
        for g in gccs:
            st.markdown(f"**{g['company']}** · {g['city']} · found {g['found_on']}  \n{g['summary']}"
                        + (f"  \n[source]({g['url']})" if g["url"] else ""))


main()
