from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from decimal import Decimal

import pytest

from campaign_reporting.budget import BudgetLedger
from campaign_reporting.contracts import CampaignConfig
from campaign_reporting.repository import ActorContext, Repository
from campaign_reporting.review import record_review_decision, save_draft
from campaign_reporting.runs import prepare_run
from campaign_reporting.tools import ReportTools


@pytest.fixture
def setup(tmp_path):
    repo = Repository.local(tmp_path / "test.sqlite")
    actor = ActorContext("analyst@example.com", "juniper", "review")
    return repo, actor, CampaignConfig()


def test_unchanged_snapshot_claims_one_run_and_correction_creates_version(setup):
    repo, _actor, cfg = setup
    r = prepare_run(repo, cfg, seed=42)
    assert prepare_run(repo, cfg, seed=42)["run_id"] == r["run_id"]
    corrected = prepare_run(repo, cfg, seed=43)
    assert corrected["run_id"] != r["run_id"]
    assert corrected["correction"] is True


def test_cross_client_tools_and_unauthorized_review_fail(setup):
    repo, actor, cfg = setup
    run = prepare_run(repo, cfg)
    other = replace(actor, client_id="other")
    with pytest.raises(PermissionError):
        ReportTools(repo, other).get_metrics(run["run_id"])
    with pytest.raises(PermissionError):
        record_review_decision(repo, replace(actor, role="narrative"), run["run_id"], "x", True)


def test_approval_binds_hash_and_survives_restart(setup):
    repo, actor, cfg = setup
    run = prepare_run(repo, cfg)
    draft = save_draft(repo, actor, run["run_id"], {"summary": "First reviewed interpretation."})
    record_review_decision(repo, actor, run["run_id"], draft["draft_hash"], True)
    reopened = Repository.local(repo.path)
    assert reopened.get_run(actor, run["run_id"])["status"] == "approved"
    changed = save_draft(reopened, actor, run["run_id"], {"summary": "Revised interpretation."})
    assert changed["status"] == "review"
    with pytest.raises(ValueError, match="stale"):
        record_review_decision(repo, actor, run["run_id"], draft["draft_hash"], True)


def test_snapshot_completeness_blocks_run(tmp_path):
    from campaign_reporting.readiness import check_readiness
    from campaign_reporting.synthetic import generate_sources

    cfg = CampaignConfig()
    src = replace(generate_sources(), complete=False)
    assert check_readiness(src, cfg)["ready"] is False


def test_duplicate_concurrent_triggers_claim_one_run(setup):
    from campaign_reporting.synthetic import generate_sources

    repo, _actor, cfg = setup
    source = generate_sources(42)
    with ThreadPoolExecutor(max_workers=2) as pool:
        runs = list(pool.map(lambda _: prepare_run(repo, cfg, source=source), range(2)))
    assert runs[0]["run_id"] == runs[1]["run_id"]


def test_audit_write_failure_rolls_back_approval(setup):
    repo, actor, cfg = setup
    run = prepare_run(repo, cfg)
    draft = save_draft(repo, actor, run["run_id"], {"summary": "Review this interpretation."})
    with repo.db.transaction() as conn:
        conn.execute(
            "CREATE TRIGGER reject_approval_audit BEFORE INSERT ON audit_events "
            "WHEN NEW.action='approved' BEGIN SELECT RAISE(ABORT,'audit unavailable'); END"
        )
    import sqlite3

    with pytest.raises(sqlite3.IntegrityError, match="audit unavailable"):
        record_review_decision(repo, actor, run["run_id"], draft["draft_hash"], True)
    persisted = repo.get_run(actor, run["run_id"])
    assert persisted["status"] == "review"
    assert persisted["approval"] is None


def test_tools_are_strict_aggregates_and_record_attempts(setup):
    repo, actor, cfg = setup
    run = prepare_run(repo, cfg)
    tools = ReportTools(repo, replace(actor, role="narrative"))
    result = tools.get_metrics(run["run_id"])
    text = str(result)
    assert "SYN_MEMBER" not in text and "Fabricated Fixture" not in text
    assert "checking_accounts" in text
    assert tools.get_rules_context(run["run_id"])["rules_version"] == "checking-v1"
    assert tools.get_prior_version(run["run_id"]) is None


def test_narrative_repository_never_returns_reviewer_feedback(setup):
    repo, actor, cfg = setup
    run = prepare_run(repo, cfg)
    draft = save_draft(repo, actor, run["run_id"], {"summary": "Review this interpretation."})
    record_review_decision(repo, actor, run["run_id"], draft["draft_hash"], True, "PRIVATE_REVIEW_CANARY")
    narrative = replace(actor, role="narrative")
    assert "PRIVATE_REVIEW_CANARY" not in str(repo.get_run(narrative, run["run_id"]))
    assert "PRIVATE_REVIEW_CANARY" not in str(repo.list_runs(narrative))


def test_budget_reservations_cover_parallel_retries_and_restart(tmp_path):
    path = tmp_path / "budget.sqlite"
    ledger = BudgetLedger(path)

    def reserve(_):
        try:
            return ledger.reserve(Decimal("1.50"))
        except ValueError:
            return None

    with ThreadPoolExecutor(max_workers=4) as pool:
        ids = [i for i in pool.map(reserve, range(4)) if i]
    assert len(ids) == 3
    assert BudgetLedger(path).remaining() == Decimal("0.50")
    ledger.settle(ids[0], Decimal("0.25"))
    assert ledger.remaining() == Decimal("1.75")
    with pytest.raises(ValueError):
        ledger.settle(ids[1], Decimal("2.00"))
    with pytest.raises(ValueError):
        ledger.reserve(Decimal(-1))
