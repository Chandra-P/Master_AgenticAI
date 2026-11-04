from pathlib import Path
import importlib


def test_pure_rag_has_no_report_generation_surface():
    root=Path(__file__).parents[1]
    package=root/'src/campaign_hub'
    assert not (package/'reporting').exists()
    assert not (package/'deliverables.py').exists()
    assert not (package/'ui/report_page.py').exists()
    from campaign_hub import models
    assert not hasattr(models,'ReportResult')
    assert importlib.import_module('campaign_hub.synthetic_data.attribution').attributable


def test_generated_benchmark_contains_questions_only(tmp_path):
    import json
    from campaign_hub.synthetic_data.generator import generate_corpus
    generate_corpus(tmp_path)
    cases=json.loads((tmp_path/'evaluation/questions.json').read_text())
    assert all(case['kind'] in ('question','unsupported') for case in cases)
