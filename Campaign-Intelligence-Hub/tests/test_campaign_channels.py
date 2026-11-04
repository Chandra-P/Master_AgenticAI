import json
from datetime import date
import pytest


def test_channel_attribution_boundaries():
    from campaign_hub.synthetic_data.attribution import attributable
    anchor=date(2026,1,1)
    assert attributable('direct_mail',anchor,date(2026,3,2))
    assert not attributable('direct_mail',anchor,date(2026,3,3))
    assert attributable('display',anchor,date(2026,1,31))
    assert not attributable('display',anchor,date(2026,2,1))
    assert not attributable('display',anchor,date(2025,12,31))
    with pytest.raises(ValueError):
        attributable('email',anchor,anchor)


def test_only_direct_mail_and_display_with_traceable_windows(tmp_path):
    from campaign_hub.synthetic_data.generator import generate_corpus
    manifest=generate_corpus(tmp_path)
    for record in manifest['campaigns']:
        assert set(record['channel_results'])=={'direct_mail','display'}
        assert record['channel_results']['direct_mail']['window_days']==60
        assert record['channel_results']['display']['window_days']==30
        assert record['channel_results']['display']['anchor']=='exposure_date'
        assert sum(s['activations'] for s in record['channel_results'].values())==record['actual']
        assert sum(s['spend'] for s in record['channel_results'].values())==record['spend']
    # The original campaign fixtures retain their two-channel contract. Teaching
    # guides can discuss incident communication (e.g. voicemail) without adding
    # a new measured marketing channel.
    corpus='\n'.join((tmp_path/d['source_path']).read_text() for d in manifest['documents'] if d['document_type']!='learning_guide')
    assert 'paid search' not in corpus.lower()
    assert 'email' not in corpus.lower()
    assert 'last eligible click' not in corpus.lower()
    assert len(manifest['documents'])==130
    cases=json.loads((tmp_path/'evaluation/questions.json').read_text())
    assert len(cases)==58
    assert sum(c['split']=='development' for c in cases)==25
