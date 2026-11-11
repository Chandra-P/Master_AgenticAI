"""Analyst UI. DEMO_MODE is explicitly simulated identity, never production authentication."""

import json
import os
from dataclasses import asdict
from pathlib import Path

import streamlit as st

from campaign_reporting.budget import BudgetLedger
from campaign_reporting.contracts import canonical
from campaign_reporting.delivery import publish_report, render_report
from campaign_reporting.narrative import resume_review, start_review
from campaign_reporting.repository import ActorContext, Repository
from campaign_reporting.runs import prepare_run
from campaign_reporting.synthetic import portfolio_configs

st.set_page_config(page_title="Campaign Decision Desk", page_icon=":material/analytics:", layout="wide")
runtime = Path(os.environ.get("CAMPAIGN_RUNTIME", "runtime")).resolve()
runtime.mkdir(parents=True, exist_ok=True)
demo = os.environ.get("DEMO_MODE") == "1"

if demo:
    identity = "local-demo-analyst"
    permitted = {c.client_id for c in portfolio_configs()}
else:
    if not st.user.is_logged_in:
        st.title("Campaign Decision Desk")
        st.info("Sign in with the configured organization identity provider.")
        if st.button("Sign in", key="signin"):
            st.login()
        st.stop()
    identity = st.user.get("email", "")
    grants = json.loads(os.environ.get("AUTH_CLIENTS_JSON", "{}"))
    permitted = set(grants.get(identity, []))
    if not permitted:
        st.error("No client access has been assigned.")
        st.stop()

configs = {c.client_id: c for c in portfolio_configs() if c.client_id in permitted}
if not configs:
    st.error("No configured clients are available.")
    st.stop()
repo = (
    Repository.postgres(os.environ["DATABASE_URL"])
    if os.environ.get("DATABASE_URL")
    else Repository.local(runtime / "runs.sqlite")
)
if not demo and not os.environ.get("DATABASE_URL"):
    st.error("Authenticated deployment requires a scoped Postgres connection.")
    st.stop()

st.title("Campaign Decision Desk")
st.caption("Synthetic Checking campaigns · 50 fictional clients · 2024–2025")
if demo:
    st.warning(
        "Local synthetic demo · simulated analyst identity · offline narrative adapter · no paid calls"
    )
with st.sidebar:
    st.header("Campaign workspace")
    client_id = st.selectbox("Client", list(configs), format_func=lambda k: configs[k].brand, key="client")
    cfg = configs[client_id]
    st.caption(f"{cfg.brand} · {cfg.digital_start.year} · {cfg.campaign_id}")
    st.caption("All records are invented. No real client or customer data.")
    st.metric("OpenAI budget remaining", f"${BudgetLedger(runtime / 'openai-budget.sqlite').remaining():.2f}")
    if not demo and st.button("Sign out", key="signout"):
        st.logout()
actor = ActorContext(identity, client_id, "review")
rows = repo.list_runs(actor)
run = rows[0] if rows else None
st.subheader(cfg.brand)
st.caption(f"Digital {cfg.digital_start}–{cfg.digital_end} · Mailings {cfg.in_home[0]} and {cfg.in_home[1]}")
config_tab, facts_tab, review_tab, report_tab, observe_tab = st.tabs(
    ["1 · Success Plan", "2 · Computed facts", "3 · Analyst review", "4 · Report", "5 · Observability"]
)

with config_tab:
    st.write("Confirm the structured Success Plan before starting a run.")
    source_column, fields_column = st.columns(2)
    with source_column:
        st.markdown("#### Synthetic Success Plan")
        st.markdown(f"**{cfg.brand} · Checking acquisition**")
        st.markdown(
            f"Target **{cfg.checking_goal:,} Checking accounts** and **{cfg.member_goal:,} new members** "
            f"with a **${cfg.cpa_ceiling:,.2f} CPA ceiling**."
        )
        st.markdown(
            f"Campaign budget: **${cfg.budget:,.0f}**. Direct mail: **${cfg.mail_budget:,.0f}** "
            f"across two equal drops; digital: **${cfg.digital_budget:,.0f}**."
        )
        st.markdown(
            f"Mailings reach the same **{cfg.audience_size:,} households**. Digital reaches "
            f"**{cfg.digital_reach:,} households** and supports both drops."
        )
        st.markdown(
            f"Digital flight: **{cfg.digital_start}–{cfg.digital_end}**. "
            f"Mailing in-home dates: **{cfg.in_home[0]}** and **{cfg.in_home[1]}**. "
            f"Final report: **{cfg.final_date}**."
        )
    with fields_column:
        st.markdown("#### Structured campaign fields")
        st.json(json.loads(canonical(asdict(cfg))), expanded=1)
    st.caption("Synthetic configuration fixture. Business-rule changes require a new configuration version.")
    confirmed = st.session_state.get("confirmed:" + client_id, False)
    if st.button("Confirm this Success Plan", key="confirm-config"):
        repo.save_config(actor, cfg)
        st.session_state["confirmed:" + client_id] = True
        st.success("Configuration confirmation recorded.")
        confirmed = True
    correction = st.checkbox("Use corrected synthetic source snapshot", key="correction:" + client_id)
    if st.button("Compute campaign", disabled=not confirmed, key="compute", type="primary"):
        with st.spinner("Validating sources and computing report facts"):
            run = prepare_run(repo, cfg, seed=42 + int(client_id[-3:]) + (10000 if correction else 0))
        st.success("Pinned run computed. No AI or delivery call was made.")
        st.rerun()

if run:
    st.caption(f"Run {run['run_id']} · version {run['version']} · status {run['status']}")
with facts_tab:
    if not run:
        st.info("Confirm the Success Plan and compute a campaign to inspect results.")
    else:
        period = st.selectbox("Reporting period", ["30", "60", "90", "120", "F"], key="facts-period")
        f = run["facts"][period]
        a, b, c = st.columns(3)
        a.metric("Checking accounts", f["checking_accounts"])
        b.metric("New members", f["new_members"])
        c.metric("Cost per Checking account", "Unavailable" if f["cpa"] is None else f"${f['cpa']}")
        st.caption(f"As of {f['as_of']} · CPA available from day 120 after all components launch")
        st.dataframe([{"channel": k, "accounts": v} for k, v in f["channels"].items()], hide_index=True)
        st.dataframe(f["branches"], hide_index=True)
        st.info(
            "Attribution overlap is not incremental lift. Core-extract inclusion is accepted funding evidence."
        )
with review_tab:
    if not run:
        st.info("Compute a run first.")
    else:
        if st.button("Generate draft for review", key="draft", disabled=run["status"] == "delivered"):
            start_review(repo, actor, run["run_id"], runtime / "checkpoints.sqlite")
            st.rerun()
        if run.get("draft"):
            st.write(run["draft"]["summary"])
            st.code(run["draft_hash"], language=None)
            review_subject = (client_id, run["run_id"], run["draft_hash"], run["revision"])
            if st.session_state.get("review-subject") != review_subject:
                st.session_state["review-attestation"] = False
                st.session_state["review-subject"] = review_subject
            attested = st.checkbox("I reviewed the facts and this exact draft", key="review-attestation")
            left, right = st.columns(2)
            if left.button(
                "Approve this draft", key="approve", disabled=not attested or run["status"] != "review"
            ):
                resume_review(
                    repo, actor, run["run_id"], runtime / "checkpoints.sqlite", run["draft_hash"], True
                )
                st.rerun()
            if right.button("Reject and regenerate", key="reject", disabled=run["status"] != "review"):
                resume_review(
                    repo, actor, run["run_id"], runtime / "checkpoints.sqlite", run["draft_hash"], False
                )
                st.rerun()
        else:
            st.info("Generate an offline draft to start the durable human-review workflow.")
with report_tab:
    if not run or not run.get("draft"):
        st.info("Generate a draft to preview the interactive report.")
    else:
        if run["status"] != "delivered":
            st.caption("Preview · not published")
        st.iframe(render_report(run).decode("utf-8"), height=760)
        if st.button("Publish approved report", key="publish", disabled=run["status"] != "approved"):
            publish_report(repo, actor, run["run_id"], runtime / "reports")
            st.rerun()
        if run.get("artifact"):
            path = Path(run["artifact"]["path"])
            st.success("Approved immutable report is ready.")
            st.download_button(
                "Download approved HTML",
                path.read_bytes(),
                file_name=f"{client_id}-v{run['version']}.html",
                mime="text/html",
                key="download-report",
            )
with observe_tab:
    st.write("Tool attempts, timing and outcomes are recorded without raw inputs or outputs.")
    events = runtime / "telemetry.jsonl"
    if events.exists() and run:
        logs = [json.loads(s) for s in events.read_text(encoding="utf-8").splitlines() if s.strip()]
        scoped = [e for e in logs if e.get("run_id") == run["run_id"]]
        st.dataframe(scoped, hide_index=True)
    else:
        st.info("Generate a draft to see tool timings.")
    st.caption(
        "Offline calls are application-invoked. LangSmith export is opt-in; no model execution is implied."
    )
