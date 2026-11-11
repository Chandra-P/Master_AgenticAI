import json

import pytest

from campaign_reporting.observability import Telemetry


def test_spans_record_timing_status_and_no_arbitrary_payloads(tmp_path):
    path = tmp_path / "events.jsonl"
    tele = Telemetry(path)
    with tele.span(
        "get_metrics",
        "run-1",
        origin="application",
        attributes={
            "input": "SENSITIVE_CANARY",
            "member_id": "SECRET",
            "item_count": 4,
        },
    ):
        pass
    with pytest.raises(RuntimeError), tele.span("get_metrics", "run-1"):
        raise RuntimeError("SECRET_CANARY in database error")
    rows = [json.loads(s) for s in path.read_text().splitlines()]
    assert rows[0]["duration_ms"] >= 0
    assert rows[0]["status"] == "ok"
    assert rows[0]["attributes"] == {"item_count": 4}
    assert rows[1]["status"] == "error"
    assert "CANARY" not in path.read_text() and "SECRET" not in path.read_text()


def test_export_outage_does_not_lose_local_events(tmp_path):
    def broken(event):
        raise RuntimeError("provider sensitive payload")

    path = tmp_path / "events.jsonl"
    with Telemetry(path, exporter=broken).span("compute", "r"):
        pass
    assert json.loads(path.read_text().splitlines()[0])["status"] == "ok"
    assert "provider sensitive" not in path.read_text()
