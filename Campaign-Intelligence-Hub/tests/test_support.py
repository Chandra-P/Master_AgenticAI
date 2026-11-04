def test_citation_score_checks_gold_not_just_existence():
    from campaign_hub.evaluation.metrics import citation_accuracy
    assert citation_accuracy(['A#results','B#targets'],['A#results'])==0.5
    assert citation_accuracy([],['A#results']) is None
