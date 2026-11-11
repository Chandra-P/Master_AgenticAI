from collections import Counter

import pytest

from campaign_reporting.evaluation.dataset import build_dataset, load_dataset


def test_versioned_client_disjoint_chronological_dataset(tmp_path):
    build_dataset(tmp_path)
    dataset = load_dataset(tmp_path)
    clients = {
        split: {c.client_id for c in dataset.cases if c.split == split and c.task == "narrative"}
        for split in ("development", "validation", "test")
    }
    assert [len(clients[s]) for s in clients] == [25, 10, 15]
    assert not (clients["development"] & clients["validation"] or clients["validation"] & clients["test"])
    ordinary = [c for c in dataset.cases if "portfolio" in c.tags]
    assert len(ordinary) == 250
    assert Counter(c.year for c in ordinary) == {2024: 125, 2025: 125}
    assert {c.period for c in ordinary} == {"30", "60", "90", "120", "F"}
    assert dataset.manifest["dataset_hash"]


def test_tampering_and_duplicate_case_ids_fail_closed(tmp_path):
    build_dataset(tmp_path)
    path = tmp_path / "cases.jsonl"
    path.write_text(path.read_text() + path.read_text().splitlines()[0] + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_dataset(tmp_path)


def test_unknown_sensitive_evidence_field_rejected():
    from campaign_reporting.evaluation.contracts import Evidence

    with pytest.raises(ValueError):
        Evidence(
            checking_accounts=1,
            new_members=1,
            checking_goal=2,
            member_goal=2,
            forecast=2,
            forecast_low=1,
            forecast_high=3,
            cpa=None,
            member_name="PRIVATE",
        )
