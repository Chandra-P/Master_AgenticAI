from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_evaluation_panel_distinguishes_offline_checks_and_live_quality(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "1")
    monkeypatch.setenv("ENABLE_OPENAI", "0")
    monkeypatch.setenv("CAMPAIGN_RUNTIME", str(tmp_path))
    app = AppTest.from_file(str(Path(__file__).parents[1] / "ui/app.py"), default_timeout=40).run()
    assert not app.exception
    app.button(key="eval-run-offline").click().run()
    assert not app.exception
    from campaign_reporting.evaluation.results import EvaluationStore
    from campaign_reporting.repository import ActorContext

    store = EvaluationStore(tmp_path / "evals/evaluations.sqlite")
    actor = ActorContext("reviewer", "synthetic-cu-001", "review")
    exp = store.experiments(actor)[0]["id"]
    assert {r["case"]["client_id"] for r in store.rows(exp)} == {"synthetic-cu-001"}
    assert any(m.label == "Live AI quality" and m.value == "Not measured" for m in app.metric)
    assert any("unevaluated" in c.value for c in app.caption)
    app.selectbox(key="eval-case").select("edge_mixed_goal_progress").run()
    assert not app.exception
    app.checkbox(key="eval-accepted").check().run()
    app.checkbox(key="eval-attestation").check().run()
    for key in ("factual_support", "completeness", "usefulness", "clarity"):
        app.select_slider(key="eval-score-" + key).set_value(4)
    next(b for b in app.button if b.label == "Save evaluation annotation").click().run()
    assert not app.exception
    assert any(m.label == "Live AI quality" and m.value == "Not measured" for m in app.metric)
