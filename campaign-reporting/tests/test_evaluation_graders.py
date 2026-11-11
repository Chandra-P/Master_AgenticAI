import pytest

from campaign_reporting.evaluation.dataset import edge_cases
from campaign_reporting.evaluation.graders import grade_output


def test_valid_schema_does_not_claim_semantic_or_live_success():
    checks = grade_output(edge_cases()[0], {"summary": "Review the campaign evidence and uncertainty."})
    assert all(c.status == "pass" for c in checks if c.kind == "contract")
    assert any(c.status == "needs_review" and c.kind == "semantic" for c in checks)


@pytest.mark.parametrize(
    "bad",
    [
        {"summary": "There are 99999 members."},
        {"summary": "EVAL_PRIVATE_CANARY"},
        {"summary": "Contact analyst@example.com."},
        {"summary": "<script>publish()</script>"},
        {"summary": "Text", "member_id": "secret"},
    ],
)
def test_planted_unsafe_outputs_are_rejected(bad):
    checks = grade_output(edge_cases()[0], bad)
    assert any(c.status == "fail" and c.severity == "critical" for c in checks)


def test_wrong_nonnumeric_meaning_and_generic_text_cannot_auto_pass():
    for text in (
        "Every goal has been exceeded.",
        "Digital definitely caused the account growth.",
        "Looks fine.",
    ):
        checks = grade_output(edge_cases()[0], {"summary": text})
        assert any(c.kind == "semantic" and c.status == "needs_review" for c in checks)


def test_oracle_is_independent_of_computation_under_test():
    case = next(c for c in edge_cases() if c.task == "oracle" and c.oracle_scenario == "dm_inhome")
    good = grade_output(case, {"checking_accounts": 0, "new_members": 0, "cpa": None})
    bad = grade_output(case, {"checking_accounts": 1, "new_members": 1, "cpa": None})
    assert all(c.status == "pass" for c in good)
    assert any(c.status == "fail" for c in bad)
