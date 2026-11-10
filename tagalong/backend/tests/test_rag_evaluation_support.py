from tagalong.core import MemoryRepository
from tagalong.retrieval_status import indexing_status
from types import SimpleNamespace

from tagalong.rag_evaluation import (
    cleanup_synthetic_sources,
    create_synthetic_source,
    compare_ablation_responses,
    mark_synthetic_source_indexed,
    remove_synthetic_source,
    wait_for_pinecone_sources,
)


class FakePinecone:
    def __init__(self, fail_ids=()):
        self.deleted = []
        self.fail_ids = set(fail_ids)

    def delete(self, source):
        self.deleted.append(source['id'])
        if source['id'] in self.fail_ids:
            raise RuntimeError('provider detail must not be returned')


def test_synthetic_source_is_a_plan_message_and_starts_pending():
    repo = MemoryRepository()
    source = create_synthetic_source(
        repo, 'plan-1', 'eval-preference', 'Synthetic preference',
        'The group prefers quiet vegetarian dinner options under $50.',
    )

    assert source == repo.state['sources']['plan-1:eval-preference']
    assert source['kind'] == 'message'
    assert indexing_status(repo.state, 'plan-1')['pending_sources'] == 1


def test_indexed_synthetic_source_is_reported_current():
    repo = MemoryRepository()
    source = create_synthetic_source(
        repo, 'plan-1', 'eval-preference', 'Synthetic preference',
        'The group prefers quiet vegetarian dinner options under $50.',
    )

    mark_synthetic_source_indexed(repo, source)

    assert indexing_status(repo.state, 'plan-1')['status'] == 'current'
    assert indexing_status(repo.state, 'plan-1')['indexed_sources'] == 1


def test_cleanup_attempts_every_synthetic_source_and_reports_failed_ids_only():
    provider = FakePinecone(fail_ids={'eval-b'})
    sources = [{'id': 'eval-a'}, {'id': 'eval-b'}, {'id': 'eval-c'}]

    failures = cleanup_synthetic_sources(provider, sources)

    assert provider.deleted == ['eval-a', 'eval-b', 'eval-c']
    assert failures == ['eval-b']


def test_removing_synthetic_source_clears_only_its_memory_record_and_job():
    repo = MemoryRepository()
    source = create_synthetic_source(
        repo, 'plan-1', 'eval-preference', 'Synthetic preference',
        'The group prefers quiet vegetarian dinner options under $50.',
    )
    remove_synthetic_source(repo, source)

    assert 'plan-1:eval-preference' not in repo.state['sources']
    assert not any(job['source_key'] == 'plan-1:eval-preference' for job in repo.state['jobs'].values())


def test_synthetic_source_rejects_non_evaluation_ids():
    repo = MemoryRepository()

    try:
        create_synthetic_source(repo, 'plan-1', 'real-note', 'Note', 'Do not index this.')
    except ValueError as error:
        assert str(error) == 'Synthetic source IDs must start with eval-'
    else:
        raise AssertionError('non-evaluation source ID was accepted')


def test_live_retrieval_probe_uses_plan_namespace_and_checks_top_k_source_ids():
    calls = []

    class Provider:
        client = SimpleNamespace(with_options=lambda **kwargs: ('client', kwargs))

        def __init__(self):
            self.index = SimpleNamespace(query=self.query)

        def embedding(self, query, client):
            assert query == 'quiet vegetarian dinner'
            assert client == ('client', {'timeout': 8, 'max_retries': 0})
            return [0.1, 0.2]

        def query(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(matches=[SimpleNamespace(
                id='eval-preference:0',
                metadata={'source_id': 'eval-preference'},
                score=0.94,
            )])

    result = wait_for_pinecone_sources(
        Provider(), 'plan-1', 'quiet vegetarian dinner', ['eval-preference'], timeout=0.1,
    )

    assert result['namespace'] == 'tagalong:plan-1'
    assert result['matched_source_ids'] == ['eval-preference']
    assert calls[0]['namespace'] == 'tagalong:plan-1'
    assert calls[0]['top_k'] == 6
    assert calls[0]['include_metadata'] is True


def test_live_retrieval_probe_fails_when_source_never_reaches_top_k():
    class Provider:
        client = SimpleNamespace(with_options=lambda **kwargs: None)
        index = SimpleNamespace(query=lambda **kwargs: SimpleNamespace(matches=[]))
        embedding = lambda self, query, client: [0.1]

    try:
        wait_for_pinecone_sources(Provider(), 'plan-1', 'query', ['eval-missing'], timeout=0)
    except TimeoutError as error:
        assert str(error) == 'Synthetic evidence did not appear in Pinecone top-k results'
    else:
        raise AssertionError('missing Pinecone evidence was accepted')


def test_live_retrieval_probe_can_wait_until_deleted_source_disappears():
    calls = []

    class Provider:
        client = SimpleNamespace(with_options=lambda **kwargs: None)

        def __init__(self):
            self.index = SimpleNamespace(query=self.query)

        def embedding(self, query, client):
            return [0.1]

        def query(self, **kwargs):
            calls.append(kwargs)
            matches = [] if len(calls) > 1 else [SimpleNamespace(
                id='eval-preference:0', metadata={'source_id': 'eval-preference'}, score=0.9,
            )]
            return SimpleNamespace(matches=matches)

    result = wait_for_pinecone_sources(
        Provider(), 'plan-1', 'query', ['eval-preference'], timeout=0.1,
        interval=0.001, present=False,
    )

    assert result['matched_source_ids'] == []
    assert len(calls) == 2


def test_ablation_detects_material_cited_evidence_even_when_safety_verdict_stays_needs_info():
    with_evidence = {
        'verdict': 'needs_info',
        'matches': [{'text': 'All four friends prefer a quiet patio.', 'source_ids': ['saved:eval-pref']}],
        'conflicts': [], 'unknowns': ['Verify allergy safety with the venue.'],
    }
    without_evidence = {
        'verdict': 'needs_info',
        'matches': [{'text': 'Quiet patio details were provided by the user.', 'source_ids': ['option-details']}],
        'conflicts': [], 'unknowns': ['Confirm group preferences.', 'Verify allergy safety with the venue.'],
    }

    result = compare_ablation_responses(with_evidence, without_evidence, 'eval-pref')

    assert result['pinecone_evidence_cited_with_source'] is True
    assert result['response_content_changed'] is True
    assert result['verdict_changed'] is False
    assert result['evidence_materially_changed_response'] is True


def test_ablation_does_not_count_uncited_or_identical_output_as_rag_value():
    response = {'verdict': 'needs_info', 'matches': [], 'conflicts': [], 'unknowns': ['Confirm preferences.']}

    result = compare_ablation_responses(response, response, 'eval-pref')

    assert result['response_content_changed'] is False
    assert result['evidence_materially_changed_response'] is False
