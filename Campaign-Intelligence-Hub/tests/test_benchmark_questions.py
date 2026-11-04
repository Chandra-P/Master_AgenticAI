"""Benchmark coverage and source evidence, independent of retrieval rankings."""
import json
from pathlib import Path

from campaign_hub.synthetic_data.generator import benchmark_questions, generate_corpus

DATA = Path(__file__).resolve().parents[1] / 'data'


def test_benchmark_categories_and_unsupported_controls():
    cases = benchmark_questions()
    assert sum(c['category'] == 'ambiguous' for c in cases) >= 3
    assert sum(c['category'] == 'multi_document' for c in cases) >= 3
    controls = [c for c in cases if c['kind'] == 'unsupported']
    assert len(controls) >= 2
    for case in controls:
        assert case['expected_sources'] == case['expected_facts'] == case['ground_truth_citations'] == []
    assert all(c['split'] == 'held_out' for c in cases)


def test_multi_document_gold_requires_distinct_sources():
    manifest = json.loads((DATA / 'manifest.json').read_text())
    sources = {d['document_id']: (DATA / d['source_path']).read_text(encoding='utf-8')
               for d in manifest['documents']}
    for case in benchmark_questions():
        if case['kind'] == 'unsupported':
            continue
        evidence = case['evidence_facts']
        assert case['expected_sources'] == list(dict.fromkeys(e['source_id'] for e in evidence))
        assert case['ground_truth_citations'] == [e['citation'] for e in evidence]
        assert case['expected_facts'] == [e['fact'] for e in evidence]
        assert case['expected_answer'] == ' '.join(e['fact'] for e in evidence)
        for item in evidence:
            assert item['fact'] in sources[item['source_id']]
            assert item['citation'].split('#')[0] == item['source_id']
        if case['category'] == 'multi_document':
            assert len(case['expected_sources']) >= 2
            # Every gold fact contributes evidence unavailable in every other gold source.
            for item in evidence:
                assert all(item['fact'] not in sources[other]
                           for other in case['expected_sources'] if other != item['source_id'])
            assert not any(all(item['fact'] in text for item in evidence) for text in sources.values())


def test_question_builder_matches_checked_in_cases_without_corpus_changes(tmp_path):
    generate_corpus(tmp_path)
    generated = json.loads((tmp_path / 'evaluation/questions.json').read_text())
    assert generated == json.loads((DATA / 'evaluation/questions.json').read_text())
    assert (tmp_path / 'manifest.json').read_bytes() == (DATA / 'manifest.json').read_bytes()
    for original in (DATA / 'corpus').rglob('*.md'):
        assert (tmp_path / original.relative_to(DATA)).read_bytes() == original.read_bytes()
