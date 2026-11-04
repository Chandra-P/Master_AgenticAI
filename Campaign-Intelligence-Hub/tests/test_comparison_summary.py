from campaign_hub.rag.comparison import paired_reranking


def test_pairing_uses_identical_cases_and_keeps_failure_counts():
    def row(case, rerank, precision, error=None):
        return dict(case_id=case, split='held_out', chunking='fixed', retrieval='hybrid',
                    reranking=rerank, context_precision=precision, context_recall=1,
                    mrr=1, latency_seconds=2 if rerank else 1, error=error)
    rows = [row('a', False, .2), row('a', True, .4), row('b', False, .5),
            row('b', True, None, 'unavailable'), row('c', True, 1)]
    group = paired_reranking(rows)[0]
    assert group['paired_successes'] == 1
    assert group['before_failures'] == 0 and group['after_failures'] == 1
    assert group['unpaired_cases'] == 1
    assert abs(group['precision_delta'] - .2) < 1e-8
    assert group['latency_delta_seconds'] == 1
