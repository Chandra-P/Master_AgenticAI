from pathlib import Path

import pytest

from campaign_reporting.contracts import CampaignConfig
from campaign_reporting.delivery import publish_report
from campaign_reporting.narrative import resume_review, start_review
from campaign_reporting.repository import ActorContext, Repository
from campaign_reporting.review import record_review_decision, save_draft
from campaign_reporting.runs import prepare_run


def test_config_confirmation_is_persisted(tmp_path):
    repo = Repository.local(tmp_path / "runs.sqlite")
    actor = ActorContext("analyst", "juniper", "review")
    identity = repo.save_config(actor, CampaignConfig())
    assert repo.save_config(actor, CampaignConfig()) == identity


def test_unapproved_delivery_rejected_and_approved_delivery_idempotent(tmp_path):
    repo = Repository.local(tmp_path / "runs.sqlite")
    actor = ActorContext("analyst", "juniper", "review")
    run = prepare_run(repo, CampaignConfig())
    draft = save_draft(repo, actor, run["run_id"], {"summary": "<script>alert(1)</script>"})
    with pytest.raises(ValueError):
        publish_report(repo, actor, run["run_id"], tmp_path / "reports")
    record_review_decision(repo, actor, run["run_id"], draft["draft_hash"], True)
    first = publish_report(repo, actor, run["run_id"], tmp_path / "reports")
    second = publish_report(repo, actor, run["run_id"], tmp_path / "reports")
    assert first == second
    html = Path(first["path"]).read_text(encoding="utf-8")
    assert "<script>alert(1)</script>" not in html
    assert "SYN_MEMBER_" not in html and "Fabricated Fixture Road" not in html
    assert "Desert Financial" not in html and "Vericast" not in html
    assert len(list((tmp_path / "reports").glob("*.html"))) == 1
    assert all(
        section in html
        for section in [
            "The Goal",
            "What Is Happening",
            "Early Signals",
            "Where We Land",
            "Recommendation",
            "Executive Summary",
            "Appendix",
        ]
    )


def test_langgraph_review_resumes_after_recreating_graph(tmp_path):
    repo = Repository.local(tmp_path / "runs.sqlite")
    actor = ActorContext("analyst", "juniper", "review")
    run = prepare_run(repo, CampaignConfig())
    checkpoint = tmp_path / "graph.sqlite"
    start_review(repo, actor, run["run_id"], checkpoint)
    draft = repo.get_run(actor, run["run_id"])
    assert draft["status"] == "review"
    resume_review(repo, actor, run["run_id"], checkpoint, draft["draft_hash"], True)
    assert repo.get_run(actor, run["run_id"])["status"] == "approved"
