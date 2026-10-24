"""Catches misleading retrieval scores and unsafe HTTP inputs."""
import pytest

def test_metrics_rank_and_missing_evidence():
    from pipeline.evaluate import retrieval_metrics
    result=retrieval_metrics(['wrong','right'],['right'])
    assert result['recall_at_5']==1
    assert result['reciprocal_rank']==.5
    assert retrieval_metrics([],['right'])['recall_at_5']==0

def test_invalid_strategy_and_oversized_question_are_rejected():
    from pipeline.server import validate_request
    with pytest.raises(ValueError):validate_request({'question':'assets','strategy':'other'})
    with pytest.raises(ValueError):validate_request({'question':'a'*1201})
    with pytest.raises(ValueError):validate_request({'question':'assets','charter':'../../etc'})

def test_evidence_ids_do_not_allow_path_injection():
    from pipeline.server import validate_request
    request=validate_request({'question':'assets','strategy':'fixed','year':'2025','charter':'5536'})
    assert request['filters']=={'charter':'5536','year_2025':True}

def test_nonobject_payload_is_rejected_cleanly():
    from pipeline.server import validate_request
    for payload in [None,[],12,'hello']:
        with pytest.raises(ValueError):validate_request(payload)
