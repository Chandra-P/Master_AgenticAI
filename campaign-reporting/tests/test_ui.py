from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_demo_ui_selects_clients_and_requires_review_before_delivery(monkeypatch, tmp_path):
    monkeypatch.setenv("DEMO_MODE", "1")
    monkeypatch.setenv("CAMPAIGN_RUNTIME", str(tmp_path))
    app = AppTest.from_file(str(Path(__file__).parents[1] / "ui/app.py"), default_timeout=30).run()
    assert not app.exception
    assert len(app.selectbox(key="client").options) == 50
    app.selectbox(key="client").select("synthetic-cu-026").run()
    assert not app.exception
    assert any("2025" in c.value for c in app.caption)
    app.button(key="confirm-config").click().run()
    app.button(key="compute").click().run()
    assert not app.exception
    app.button(key="draft").click().run()
    assert not app.exception
    app.checkbox(key="review-attestation").check().run()
    app.button(key="reject").click().run()
    assert not app.exception
    assert app.checkbox(key="review-attestation").value is False
    app.checkbox(key="review-attestation").check().run()
    app.button(key="approve").click().run()
    assert not app.exception
    app.button(key="publish").click().run()
    assert not app.exception
    assert list((tmp_path / "reports").glob("*.html"))
