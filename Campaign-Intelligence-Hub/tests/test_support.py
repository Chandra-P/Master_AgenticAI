def test_citation_score_checks_gold_not_just_existence():
    from campaign_hub.evaluation.metrics import citation_accuracy
    assert citation_accuracy(['A#results','B#targets'],['A#results'])==0.5
    assert citation_accuracy([],['A#results']) is None


def test_judge_entailment_aggregation():
    from campaign_hub.evaluation.judge import aggregate_judgments
    assert aggregate_judgments([True,False,True])==2/3
    assert aggregate_judgments([]) is None
