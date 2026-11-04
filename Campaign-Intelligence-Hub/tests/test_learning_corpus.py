"""Corpus contracts exercise real generated sources, without models or indexes."""
import hashlib
import json
import re
from pathlib import Path

import tiktoken

from campaign_hub.synthetic_data.generator import generate_corpus


def test_original_sources_preserved_and_expansion_deterministic(tmp_path):
    baseline = json.loads((Path(__file__).parents[1] / 'data/manifest.json').read_text())
    generated = generate_corpus(tmp_path)
    original = generated['documents'][:110]
    signature = hashlib.sha256(json.dumps([(d['document_id'], d['content_hash']) for d in original], sort_keys=True).encode()).hexdigest()
    assert signature == 'a87f9de9c3591e30b7be1561272c079ea201701e7f8906fc6639600fdab5db8e'
    for doc in baseline['documents'][:110]:
        assert (tmp_path / doc['source_path']).read_bytes() == (Path(__file__).parents[1] / 'data' / doc['source_path']).read_bytes()
    assert len(generated['campaigns']) == 20
    assert generated['schema_version'] == 4
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    generate_corpus(tmp_path)
    assert before == {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}


def test_long_sources_have_distinct_shapes_and_grounded_development_cases(tmp_path):
    manifest = generate_corpus(tmp_path)
    docs = manifest['documents'][110:122]
    assert len(docs) == 12
    assert {d['document_shape'] for d in docs} == {'playbook', 'cohesive_policy', 'mixed_notes', 'troubleshooting'}
    encoder = tiktoken.get_encoding('cl100k_base')
    by_id = {}
    for doc in docs:
        text = (tmp_path / doc['source_path']).read_text(encoding='utf-8')
        by_id[doc['document_id']] = text
        assert 1200 <= len(encoder.encode(text)) <= 2500, (doc['document_id'], len(encoder.encode(text)))
        assert doc['description'] and doc['campaign_id'] == 'GLOBAL'
        assert 'SYNTHETIC COURSE DATA' in text
        headings = re.findall(r'^## (.+)$', text, re.M)
        if doc['document_shape'] == 'playbook':
            assert len(headings) >= 5
        elif doc['document_shape'] == 'cohesive_policy':
            assert len(headings) == 1
        elif doc['document_shape'] == 'mixed_notes':
            assert not headings
        else:
            assert '|' in text and 'Exception' in text and re.search(r'[A-Z]{2,}-\d{3}', text)
        paragraphs = [p for p in text.split('\n\n') if len(p) > 100]
        assert len(set(paragraphs)) == len(paragraphs)
    cases = json.loads((tmp_path / 'evaluation/questions.json').read_text())
    new_cases = [c for c in cases if re.fullmatch(r'dev-\d{2}',c['id'])]
    assert len(new_cases) == 12
    assert len({c['expected_sources'][0] for c in new_cases}) == 12
    for case in new_cases:
        assert case['split'] == 'development' and case['kind'] == 'question'
        assert case['campaign_id'] is None
        assert case['measurement_provenance']['purpose'] == 'curated development example'
        assert case['measurement_provenance']['held_out'] is False
        assert case['ground_truth_citations']
        text = by_id[case['expected_sources'][0]]
        assert all(fact in text for fact in case['expected_facts'])
        assert case['expected_answer'] in text
        for citation in case['ground_truth_citations']:
            assert citation.split('#')[0] in case['expected_sources']
