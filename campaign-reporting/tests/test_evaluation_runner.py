import socket

import pytest

from campaign_reporting.evaluation.contracts import Annotation
from campaign_reporting.evaluation.dataset import edge_cases
from campaign_reporting.evaluation.results import EvaluationStore
from campaign_reporting.evaluation.runner import compare_experiments, run_experiment, summarize
from campaign_reporting.repository import ActorContext


def nar():
    return edge_cases()[0]


def test_release_requires_matching_complete_independent_oracles(tmp_path):
    store = EvaluationStore(tmp_path / "evals.sqlite")
    case = nar().model_copy(update={"split": "test"})

    class Target:
        def __init__(self):
            self.last_usage = {"cost_usd": 0}

        def __call__(self, case):
            return {"summary": "Review evidence and uncertainty."}

    experiments = []
    for name in ("baseline", "candidate"):
        exp = run_experiment(
            store,
            (case,),
            dataset_hash="fixed",
            mode="live",
            target=Target(),
            repetitions=3,
            split="test",
            allow_heldout=True,
            candidate_id=name,
        )
        for rep in range(3):
            store.annotate(
                ActorContext("reviewer", case.client_id, "review"),
                exp,
                case.case_id,
                rep,
                Annotation(factual_support=5, completeness=5, usefulness=5, clarity=5, accepted=True),
            )
        experiments.append(exp)
    assert compare_experiments(store, *experiments)["release_gate"] == "unevaluated"
    oracle_cases = tuple(c for c in edge_cases() if c.task == "oracle")
    partial = run_experiment(store, oracle_cases[:1], dataset_hash="fixed")
    assert not compare_experiments(store, *experiments, oracle_id=partial)["oracle_gate_passed"]
    complete = run_experiment(store, oracle_cases, dataset_hash="fixed")
    report = compare_experiments(store, *experiments, oracle_id=complete)
    assert report["oracle_gate_passed"]
    assert report["release_gate"] == "eligible_for_human_release_review"


def test_offline_is_network_free_and_semantics_are_unreviewed(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("network attempted")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    store = EvaluationStore(tmp_path / "evals.sqlite")
    exp = run_experiment(store, (nar(),), dataset_hash="fixed", mode="offline")
    summary = summarize(store, exp)
    assert summary["scheduled_cases"] == 1
    assert summary["completed_case_quality"] is None
    assert summary["coverage"] == 0
    assert summary["live_quality_rate"] is None
    assert summary["release_gate"] == "unevaluated"
    assert summary["actual_cost_usd"] == 0


def test_repetition_does_not_inflate_coverage_and_resume_is_idempotent(tmp_path):
    store = EvaluationStore(tmp_path / "evals.sqlite")
    case = nar()
    calls = []

    def target(c):
        calls.append(c.case_id)
        return {"summary": "Review material findings and attribution limitations."}

    exp = run_experiment(store, (case,), dataset_hash="fixed", mode="replay", target=target, repetitions=3)
    run_experiment(
        store, (case,), dataset_hash="fixed", mode="replay", target=target, repetitions=3, experiment_id=exp
    )
    assert len(calls) == 3
    actor = ActorContext("reviewer", case.client_id, "review")
    store.annotate(
        actor,
        exp,
        case.case_id,
        0,
        Annotation(factual_support=4, completeness=4, usefulness=4, clarity=4, accepted=True),
    )
    assert summarize(store, exp)["coverage"] == 0
    for repetition in (1, 2):
        store.annotate(
            actor,
            exp,
            case.case_id,
            repetition,
            Annotation(factual_support=4, completeness=4, usefulness=4, clarity=4, accepted=True),
        )
    report = summarize(store, exp)
    assert report["coverage"] == 1
    assert report["completed_case_quality"] == 1
    assert report["attempts_started"] == 3
    assert report["release_gate"] == "unevaluated"


def test_pre_call_blocks_and_errors_stay_in_scheduled_coverage(tmp_path):
    from campaign_reporting.evaluation.runner import EvaluationBlocked

    store = EvaluationStore(tmp_path / "evals.sqlite")
    cases = edge_cases()[:2]

    def target(case):
        if case.case_id == cases[0].case_id:
            raise EvaluationBlocked("budget")
        raise TimeoutError("PRIVATE_ERROR_CANARY")

    exp = run_experiment(store, cases, dataset_hash="fixed", mode="replay", target=target)
    report = summarize(store, exp)
    assert report["scheduled_cases"] == 2
    assert report["blocked_attempts"] == 1
    assert report["error_attempts"] == 1
    assert report["attempts_started"] == 1
    assert report["reliability"] == 0
    assert report["coverage"] == 0
    assert "PRIVATE_ERROR_CANARY" not in str(store.rows(exp))


def test_cross_client_annotations_are_denied_and_critical_failures_block_release(tmp_path):
    store = EvaluationStore(tmp_path / "evals.sqlite")
    case = nar()
    exp = run_experiment(
        store,
        (case,),
        dataset_hash="fixed",
        mode="replay",
        target=lambda c: {"summary": "EVAL_PRIVATE_CANARY"},
    )
    with pytest.raises(PermissionError):
        store.annotate(
            ActorContext("wrong", "other-client", "review"),
            exp,
            case.case_id,
            0,
            Annotation(factual_support=5, completeness=5, usefulness=5, clarity=5, accepted=True),
        )
    assert summarize(store, exp)["release_gate"] == "blocked"
    # Canary definitions are allowed in synthetic reference cases, never persisted model outputs.
    assert "EVAL_PRIVATE_CANARY" not in str([r["result"] for r in store.rows(exp)])


def test_dataset_change_cannot_resume_existing_experiment(tmp_path):
    store = EvaluationStore(tmp_path / "evals.sqlite")
    exp = run_experiment(store, (nar(),), dataset_hash="v1")
    with pytest.raises(ValueError, match="provenance"):
        run_experiment(store, (nar(),), dataset_hash="v2", experiment_id=exp)


def test_oracle_failures_are_not_hidden_by_narrative_passes(tmp_path):
    store = EvaluationStore(tmp_path / "evals.sqlite")
    oracle = next(c for c in edge_cases() if c.task == "oracle")
    exp = run_experiment(store, (oracle,), dataset_hash="v1")
    report = summarize(store, exp)
    assert report["coverage"] == 1
    assert report["by_task"]["oracle"]["passed_cases"] == 1
    assert report["live_quality_rate"] is None


def test_bad_candidate_is_not_eligible_just_because_baseline_also_failed(tmp_path):
    store = EvaluationStore(tmp_path / "evals.sqlite")
    case = nar().model_copy(update={"split": "test"})
    actor = ActorContext("reviewer", case.client_id, "review")
    experiments = []
    for name in ("baseline", "candidate"):
        exp = run_experiment(
            store,
            (case,),
            dataset_hash="fixed",
            mode="live",
            model="test-fixture",
            target=lambda c: {"summary": "Every goal has been exceeded."},
            repetitions=3,
            split="test",
            allow_heldout=True,
            candidate_id=name,
        )
        for repetition in range(3):
            store.annotate(
                actor,
                exp,
                case.case_id,
                repetition,
                Annotation(factual_support=1, completeness=2, usefulness=2, clarity=4, accepted=False),
            )
        experiments.append(exp)
    assert compare_experiments(store, *experiments)["release_gate"] == "blocked"


def test_live_mode_without_secure_configuration_is_explicitly_blocked(tmp_path, monkeypatch):
    from campaign_reporting.evaluation.live import LiveTarget

    monkeypatch.setenv("ENABLE_OPENAI", "0")
    store = EvaluationStore(tmp_path / "evals.sqlite")
    exp = run_experiment(store, (nar(),), dataset_hash="fixed", mode="live", target=LiveTarget(tmp_path))
    report = summarize(store, exp)
    assert report["blocked_attempts"] == 1
    assert report["attempts_started"] == 0
    assert report["live_quality_rate"] is None
    assert report["actual_cost_usd"] == 0


def test_paired_gate_does_not_pass_two_equally_incomplete_protocols(tmp_path):
    store = EvaluationStore(tmp_path / "evals.sqlite")
    case = nar().model_copy(update={"split": "test"})
    full = run_experiment(
        store,
        (case,),
        dataset_hash="fixed",
        mode="live",
        model="test-fixture",
        target=lambda c: {"summary": "Review the evidence and uncertainty."},
        repetitions=3,
        split="test",
        allow_heldout=True,
        candidate_id="reference",
    )
    one_result = store.rows(full)[0]["result"]
    actor = ActorContext("reviewer", case.client_id, "review")
    partials = []
    for name in ("baseline", "candidate"):
        meta = {**store.metadata(full), "candidate_id": name}
        exp = store.create(meta, (case,))
        store.claim(exp, case.case_id, 0)
        store.finish(exp, case.case_id, 0, one_result)
        store.annotate(
            actor,
            exp,
            case.case_id,
            0,
            Annotation(factual_support=5, completeness=5, usefulness=5, clarity=5, accepted=True),
        )
        partials.append(exp)
    comparison = compare_experiments(store, *partials)
    assert comparison["paired_labels_complete"] is False
    assert comparison["release_gate"] == "unevaluated"


def test_concurrent_workers_do_not_issue_duplicate_attempts(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    store = EvaluationStore(tmp_path / "evals.sqlite")
    calls = []

    def target(case):
        calls.append(case.case_id)
        return {"summary": "Review evidence and uncertainty."}

    def worker(_):
        return run_experiment(
            store,
            (nar(),),
            dataset_hash="fixed",
            mode="replay",
            target=target,
            experiment_id="concurrent-experiment",
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert len(set(pool.map(worker, range(2)))) == 1
    assert len(calls) == 1


def test_interrupted_attempt_is_unresolved_not_successful_and_not_reissued(tmp_path):
    store = EvaluationStore(tmp_path / "evals.sqlite")
    calls = []

    def interrupted(case):
        calls.append(case.case_id)
        raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        run_experiment(
            store,
            (nar(),),
            dataset_hash="fixed",
            mode="replay",
            target=interrupted,
            experiment_id="interrupted-run",
        )
    report = summarize(store, "interrupted-run")
    assert report["unresolved_attempts"] == 1
    assert report["reliability"] == 0
    run_experiment(
        store,
        (nar(),),
        dataset_hash="fixed",
        mode="replay",
        target=interrupted,
        experiment_id="interrupted-run",
    )
    assert len(calls) == 1
