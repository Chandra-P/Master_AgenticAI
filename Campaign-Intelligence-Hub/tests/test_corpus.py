import json
from collections import Counter


def test_corpus_counts_and_consistency(tmp_path):
    from campaign_hub.synthetic_data.generator import generate_corpus
    from campaign_hub.synthetic_data.validation import validate_corpus
    manifest = generate_corpus(tmp_path)
    assert len(manifest["documents"]) == 110
    assert Counter(d["document_type"] for d in manifest["documents"]) == {
        "brief": 20, "success_plan": 20, "performance_report": 20,
        "historical_deck": 20, "strategy": 10, "best_practice": 10,
        "kpi_dictionary": 5, "methodology": 5,
    }
    assert len(manifest["campaigns"]) == 20
    assert manifest["campaigns"][0]["campaign_id"] == "TX-CHK-001"
    assert validate_corpus(tmp_path) == []
    cases = json.loads((tmp_path / "evaluation/questions.json").read_text())
    assert len(cases) == 30
    before = (tmp_path / "manifest.json").read_bytes()
    generate_corpus(tmp_path)
    assert before == (tmp_path / "manifest.json").read_bytes()


def test_tampered_document_is_rejected(tmp_path):
    from campaign_hub.synthetic_data.generator import generate_corpus
    from campaign_hub.synthetic_data.validation import validate_corpus
    manifest = generate_corpus(tmp_path)
    (tmp_path / manifest["documents"][0]["source_path"]).write_text("tampered")
    assert validate_corpus(tmp_path)
