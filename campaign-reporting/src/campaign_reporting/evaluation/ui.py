import json

import streamlit as st

from .contracts import SEMANTIC_DIMENSIONS, Annotation
from .dataset import load_dataset
from .results import EvaluationStore
from .runner import public_summary, run_experiment, summarize


def render_evals_panel(runtime, actor, dataset_path):
    st.subheader("Evaluation evidence")
    st.caption("Results are scoped to this client. Offline checks do not measure live AI accuracy.")
    dataset = load_dataset(dataset_path)
    store = EvaluationStore(runtime / "evals/evaluations.sqlite")
    scoped_cases = tuple(c for c in dataset.select("development") if c.client_id == actor.client_id)
    if st.button(
        "Run local development benchmark · $0 API", key="eval-run-offline", disabled=not scoped_cases
    ):
        run_experiment(store, scoped_cases, dataset_hash=dataset.manifest["dataset_hash"])
        st.rerun()
    experiments = store.experiments(actor)
    if not experiments:
        st.info(
            "No results for this client. Development uses 2024 clients; validation and final test stay separate."
        )
        return
    identity = st.selectbox("Experiment", [e["id"] for e in experiments], key="eval-experiment")
    report = summarize(store, identity, actor)
    a, b, c, d = st.columns(4)
    a.metric("Scheduled cases", report["scheduled_cases"])
    b.metric("Fully evaluated cases", report["fully_evaluated_cases"])
    c.metric(
        "Live AI quality",
        "Not measured" if report["live_quality_rate"] is None else f"{report['live_quality_rate']:.1%}",
    )
    d.metric("Known evaluation API cost", f"${report['actual_cost_usd']:.6f}")
    st.caption(f"Mode: {report['mode']} · split: {report['split']} · release gate: {report['release_gate']}")
    st.info(
        f"Coverage {report['coverage']:.1%}. {report['unreviewed_attempts']} attempts need human review; "
        f"critical failures {report['critical_failures']}; blocked {report['blocked_attempts']}; "
        f"errors {report['error_attempts']}; unknown costs {report['unknown_cost_attempts']}."
    )
    st.dataframe([{"task": k, **v} for k, v in report["by_task"].items()], hide_index=True)
    with st.expander("Quality slices and repetition stability"):
        dimension = st.selectbox("Slice", list(report["slices"]), key="eval-slice")
        st.dataframe([{"slice": k, **v} for k, v in report["slices"][dimension].items()], hide_index=True)
        st.dataframe([{"dimension": k, **v} for k, v in report["dimension_scores"].items()], hide_index=True)
        st.write(report["repetition_stability"])
    rows = store.rows(identity, actor)
    st.dataframe(
        [
            {
                "case": r["case"]["case_id"],
                "period": r["case"]["period"],
                "repetition": r["repetition"],
                "status": r["status"],
                "duration_ms": r["result"].get("duration_ms"),
                "cost_usd": r["result"].get("cost_usd"),
                "reviewed": bool(r["annotation"]),
            }
            for r in rows
        ],
        hide_index=True,
    )
    st.caption("Cost per case/report view is evaluation generation cost, not a production report quote.")
    st.download_button(
        "Download privacy-filtered eval summary",
        json.dumps(public_summary(store, identity, actor), indent=2),
        file_name=f"evaluation-{identity}.json",
        mime="application/json",
        key="eval-download",
    )
    reviewable = [r for r in rows if r["case"]["task"] == "narrative" and r["status"] == "completed"]
    if not reviewable:
        return
    st.markdown("#### Review against the pinned evidence")
    selected = st.selectbox(
        "Evaluation case", list(dict.fromkeys(r["case"]["case_id"] for r in reviewable)), key="eval-case"
    )
    options = [r for r in reviewable if r["case"]["case_id"] == selected]
    rep = st.selectbox("Repetition", [r["repetition"] for r in options], key="eval-repetition")
    row = next(r for r in options if r["repetition"] == rep)
    left, right = st.columns(2)
    with left:
        st.json(row["case"]["facts"])
        st.write("Required findings:", row["case"]["required_findings"])
    with right:
        output = row["result"].get("output")
        st.text(output["summary"] if output else "Unsafe output redacted before storage.")
        st.dataframe(row["result"].get("checks", []), hide_index=True)
    subject = (identity, selected, rep)
    if st.session_state.get("eval-review-subject") != subject:
        for key in ("eval-attestation", "eval-accepted", "eval-critical"):
            st.session_state[key] = False
        st.session_state["eval-review-subject"] = subject
        st.session_state["eval-notes"] = ""
        for name in SEMANTIC_DIMENSIONS:
            st.session_state["eval-score-" + name] = 3
    st.caption("Support/completeness need >=4; usefulness/clarity >=3. Critical violations override scores.")
    with st.form("eval-annotation"):
        scores = {
            name: st.select_slider(
                name.replace("_", " ").capitalize(), [1, 2, 3, 4, 5], value=3, key="eval-score-" + name
            )
            for name in SEMANTIC_DIMENSIONS
        }
        accepted = st.checkbox("Accept without material correction", key="eval-accepted")
        critical = st.checkbox("Critical violation", key="eval-critical")
        notes = st.text_area("Local notes · excluded from exports/prompts", key="eval-notes", max_chars=1500)
        attested = st.checkbox("I reviewed this exact output and evidence", key="eval-attestation")
        save = st.form_submit_button("Save evaluation annotation")
    if save:
        if not attested:
            st.error("Review the exact output and evidence first.")
        else:
            store.annotate(
                actor,
                identity,
                selected,
                rep,
                Annotation(**scores, accepted=accepted, critical_violation=critical, notes=notes),
            )
            st.rerun()
