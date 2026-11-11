from tagalong.ragas_eval import (
    _install_ragas_vertexai_compat,
    build_ragas_sample,
    score_ragas_rows,
)


CASE = {
    'id': 'dietary_conflict',
    'option': {
        'name': 'Synthetic steak dinner',
        'details': 'Steak menu for the group.',
        'estimated_cost_per_person': 30,
    },
    'constraints': 'The group agreed to vegetarian food and a $50 per-person limit.',
    'budget': 50,
}
EVIDENCE = [
    {'id': 'plan-facts', 'title': 'Current plan facts', 'text': 'Budget: $50', 'retrieval_origin': 'postgres'},
    {'id': 'option-details', 'title': 'Option details', 'text': 'Steak menu', 'retrieval_origin': 'user_input'},
    {'id': 'saved:eval-dietary', 'title': 'Group preference', 'text': CASE['constraints'], 'retrieval_origin': 'pinecone'},
]
OUTPUT = {
    'verdict': 'conflicts',
    'summary': 'The menu conflicts with the group preference.',
    'matches': [],
    'conflicts': [{'text': 'The group requested vegetarian food.', 'source_ids': ['saved:eval-dietary']}],
    'unknowns': ['Confirm menu availability.'],
}


def run_immediate(coroutine):
    """Drive only the no-I/O fake metric coroutines without opening a socket loop."""
    try:
        coroutine.send(None)
    except StopIteration as complete:
        return complete.value
    raise AssertionError('fake metrics unexpectedly yielded asynchronous work')


def test_build_ragas_sample_separates_pinecone_context_from_all_prompt_evidence():
    sample = build_ragas_sample(CASE, EVIDENCE, OUTPUT)

    assert sample['case_id'] == 'dietary_conflict'
    assert 'Synthetic steak dinner' in sample['user_input']
    assert sample['reference'] == CASE['constraints']
    assert len(sample['prompt_contexts']) == 3
    assert len(sample['pinecone_contexts']) == 1
    assert 'pinecone' in sample['pinecone_contexts'][0]
    assert CASE['constraints'] in sample['pinecone_contexts'][0]
    assert 'source_ids' not in sample['response']
    assert 'The group requested vegetarian food.' in sample['response']


def test_build_ragas_sample_marks_missing_reference_for_retrieval_metrics():
    sample = build_ragas_sample({**CASE, 'constraints': None}, [], OUTPUT)

    assert sample['reference'] is None
    assert sample['pinecone_contexts'] == []


def test_ragas_vertexai_compatibility_is_scoped_to_optional_import():
    import sys

    module_name = 'langchain_community.chat_models.vertexai'
    original = sys.modules.pop(module_name, None)
    try:
        _install_ragas_vertexai_compat()
        shim = sys.modules[module_name]
        assert shim.ChatVertexAI.__name__ == 'ChatVertexAIUnavailable'
    finally:
        sys.modules.pop(module_name, None)
        if original is not None:
            sys.modules[module_name] = original


def test_score_ragas_rows_uses_metric_specific_context_and_preserves_metric_errors():
    class Sample(dict):
        pass

    class Metric:
        def __init__(self, score=None, error=None):
            self.score = score
            self.error = error
            self.samples = []

        async def single_turn_ascore(self, sample):
            self.samples.append(sample)
            if self.error:
                raise self.error
            return self.score

    faithfulness = Metric(score=0.8)
    relevancy = Metric(score=0.9)
    precision = Metric(score=0.75)
    recall = Metric(error=RuntimeError('provider details must not be persisted'))
    rows = [build_ragas_sample(CASE, EVIDENCE, OUTPUT)]

    result = run_immediate(score_ragas_rows(
        rows,
        {
            'faithfulness': faithfulness,
            'answer_relevancy': relevancy,
            'context_precision': precision,
            'context_recall': recall,
        },
        Sample,
    ))

    assert faithfulness.samples[0]['retrieved_contexts'] == rows[0]['prompt_contexts']
    assert relevancy.samples[0]['user_input'] == rows[0]['user_input']
    assert precision.samples[0]['retrieved_contexts'] == rows[0]['pinecone_contexts']
    assert result['cases'][0]['metrics']['faithfulness'] == {'status': 'scored', 'score': 0.8}
    assert result['cases'][0]['metrics']['context_recall'] == {'status': 'error', 'error_type': 'RuntimeError'}
    assert result['aggregate']['faithfulness'] == {'mean': 0.8, 'scored_cases': 1, 'errors': 0}
    assert result['aggregate']['context_recall'] == {'mean': None, 'scored_cases': 0, 'errors': 1}
    assert 'provider details must not be persisted' not in str(result)


def test_score_ragas_rows_skips_reference_metrics_when_synthetic_reference_is_missing():
    class Metric:
        async def single_turn_ascore(self, sample):
            raise AssertionError('reference metrics should be skipped')

    row = build_ragas_sample({**CASE, 'constraints': None}, EVIDENCE[:2], OUTPUT)
    result = run_immediate(score_ragas_rows(
        [row], {'context_precision': Metric(), 'context_recall': Metric()}, dict
    ))

    assert result['cases'][0]['metrics']['context_precision'] == {
        'status': 'skipped', 'reason': 'reference_missing'
    }
