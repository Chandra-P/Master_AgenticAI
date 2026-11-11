from campaign_reporting.evaluation.contracts import Annotation
from campaign_reporting.evaluation.dataset import edge_cases
from campaign_reporting.evaluation.results import EvaluationStore
from campaign_reporting.evaluation.runner import public_summary, run_experiment
from campaign_reporting.repository import ActorContext


def test_export_excludes_inputs_outputs_reviewer_notes_and_other_clients(tmp_path):
    store = EvaluationStore(tmp_path / "evals.sqlite")
    case = edge_cases()[0]
    exp = run_experiment(store, (case,), dataset_hash="v1")
    store.annotate(
        ActorContext("reviewer", case.client_id, "review"),
        exp,
        case.case_id,
        0,
        Annotation(
            factual_support=3,
            completeness=2,
            usefulness=3,
            clarity=4,
            accepted=False,
            notes="PRIVATE_REVIEW_NOTE",
        ),
    )
    export = public_summary(store, exp)
    assert "summary" not in export
    assert "output" not in export and "facts" not in export
    assert "EVAL_PRIVATE_CANARY" not in str(export)
    assert "PRIVATE_REVIEW_NOTE" not in str(export)
    assert store.rows(exp, ActorContext("u", "other-client", "review")) == []
