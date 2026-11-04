"""New teaching sources add evidence coverage without changing historical gold."""
import json,re
from pathlib import Path
from campaign_hub.synthetic_data.generator import generate_corpus
from campaign_hub.synthetic_data.validation import validate_corpus

def test_requirements_pack_preserves_existing_sources_and_cases(tmp_path):
    root=Path(__file__).parents[1]/'data'
    old=json.loads((root/'manifest.json').read_text())
    old_docs=[d for d in old['documents'] if not d['document_id'].startswith('GLOBAL-requirements-')]
    old_cases=[c for c in json.loads((root/'evaluation/questions.json').read_text()) if not c['id'].startswith('dev-req-')]
    manifest=generate_corpus(tmp_path)
    assert len(manifest['documents'])==130
    assert validate_corpus(tmp_path)==[]
    for doc in old_docs:
        assert (root/doc['source_path']).read_bytes()==(tmp_path/doc['source_path']).read_bytes()
    cases=json.loads((tmp_path/'evaluation/questions.json').read_text())
    assert [c for c in cases if not c['id'].startswith('dev-req-')]==old_cases
    new=[d for d in manifest['documents'] if d['document_id'].startswith('GLOBAL-requirements-')]
    assert len(new)==8
    assert {d['document_shape'] for d in new}=={'playbook','cohesive_policy','mixed_notes','troubleshooting'}
    assert len({d['description'] for d in new})==8
    for doc in new:
        text=(tmp_path/doc['source_path']).read_text()
        assert 'SYNTHETIC COURSE DATA' in text
        assert doc['evidence_pack']=='requirements-v1'
        assert doc['source_status'] in ('active','superseded')
        assert len(text.split())>=350
        assert 'API_KEY' not in text
    new_cases=[c for c in cases if c['id'].startswith('dev-req-')]
    assert len(new_cases)==13
    assert all(c['split']=='development' and c['measurement_provenance']['held_out'] is False for c in new_cases)
    assert sum(c['kind']=='unsupported' for c in new_cases)==2
    multi=[c for c in new_cases if len(c['expected_sources'])>1]
    assert len(multi)==3
    by_id={d['document_id']:(tmp_path/d['source_path']).read_text() for d in new}
    for case in new_cases:
        if case['kind']=='unsupported':
            assert case['expected_sources']==[]
            continue
        assert case['ground_truth_citations']
        for fact in case['expected_facts']:
            assert any(fact in by_id[s] for s in case['expected_sources'])
        if len(case['expected_sources'])>1:
            assert not any(all(fact in text for fact in case['expected_facts']) for text in by_id.values())
        for citation in case['ground_truth_citations']:
            source,anchor=citation.split('#')
            assert source in case['expected_sources']
            headings=re.findall(r'^## (.+)$',by_id[source],re.M)
            assert anchor=='document' or anchor in [h.lower().replace(' ','-') for h in headings]
            if anchor!='document':
                from campaign_hub.ingestion.markdown import sections
                body=next(body for name,body in sections(by_id[source]) if name.lower().replace(' ','-')==anchor)
                facts=[fact for fact in case['expected_facts'] if fact in by_id[source]]
                assert any(fact in body for fact in facts)
    before={p.relative_to(tmp_path):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    generate_corpus(tmp_path)
    assert before=={p.relative_to(tmp_path):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
