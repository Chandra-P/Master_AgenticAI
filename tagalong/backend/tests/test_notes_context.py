import pytest
from tagalong.providers import ConnectedAI
from tests.test_workflows import env

@pytest.mark.parametrize('message', ['What should we eat?', 'Remember our dinner?'])
def test_ordinary_requests_use_unindexed_notes_despite_history_failure(env, message):
    c, repo, fake, headers, _, plan = env
    ai = ConnectedAI.__new__(ConnectedAI)
    ai.retrieve = lambda *args: (_ for _ in ()).throw(RuntimeError('offline'))
    captured = {}
    def generate(state):
        captured.update(state)
        return {'output': {'text': 'Use saved food preferences', 'preferences': [], 'source_ids': [x['id'] for x in state['sources']]}}
    ai.generate = generate
    ai.graph = ai.build_graph()
    fake.answer = ai.answer
    url = '/v1/plans/' + plan['id']
    note = c.post(url + '/documents', headers=headers, json={'title': 'Food', 'text': 'Vegetarian dinner only.'}).json()
    response = c.post(url + '/assistant', headers=headers, json={'message': message})
    assert response.status_code == 200
    assert [x['id'] for x in response.json()['sources']] == [note['id']]
    assert captured['sources'][0]['text'] == 'Vegetarian dinner only.'
    assert 'documents' not in captured['plan']


def test_notes_excerpts_are_relevant_bounded_and_transparent():
    from tagalong.notes_context import notes_context
    documents = [{'id': str(i), 'title': 'Notes', 'text': 'x' * 10000 + ' vegetarian dinner ' + 'y' * 10000, 'version': 1} for i in range(9)]
    sources, status = notes_context(documents, 'vegetarian dinner')
    assert len(sources) == 6
    assert sum(len(x['text']) for x in sources) <= 18000
    assert all('vegetarian dinner' in x['text'] for x in sources)
    assert all(x['excerpt_truncated'] for x in sources)
    assert status == {'documents_total': 9, 'documents_included': 6, 'context_truncated': True}

@pytest.mark.parametrize('change', ['delete', 'version'])
def test_changed_notes_reject_even_uncited_generated_response(env, change):
    c, repo, ai, headers, _, plan = env
    url = '/v1/plans/' + plan['id']
    note = c.post(url + '/documents', headers=headers, json={'title': 'Food', 'text': 'Vegetarian.'}).json()
    def answer(plan, message, resolve_sources):
        sources = resolve_sources([])
        assert [x['id'] for x in sources] == [note['id']]
        def mutate(state):
            src = state['sources'][plan['id'] + ':' + note['id']]
            if change == 'delete': src['deleted'] = True
            else: src['version'] += 1
        repo.transact(mutate)
        return {'text': 'Vegetarian', 'preferences': [], 'source_ids': []}, sources
    ai.answer = answer
    assert c.post(url + '/assistant', headers=headers, json={'message': 'Dinner?'}).status_code == 409


def test_resolver_excludes_deleted_other_plan_and_stale_historical_sources(env):
    c, repo, ai, headers, _, plan = env
    url = '/v1/plans/' + plan['id']
    keep = c.post(url + '/documents', headers=headers, json={'title': 'Keep', 'text': 'Current food.'}).json()
    deleted = c.post(url + '/documents', headers=headers, json={'title': 'Deleted', 'text': 'Private.'}).json()
    c.delete(url + '/documents/' + deleted['id'], headers=headers)
    other = c.post('/v1/plans', headers=headers, json={'title': 'Other', 'kind': 'trip', 'start': '2026-12-04', 'end': '2026-12-06'}).json()
    foreign = c.post('/v1/plans/' + other['id'] + '/documents', headers=headers, json={'title': 'Foreign', 'text': 'Private.'}).json()
    def answer(plan, message, resolve_sources):
        sources = resolve_sources([{'id': foreign['id'], 'version': 1}, {'id': deleted['id'], 'version': 1}, {'id': 'missing', 'version': 1}])
        assert [x['id'] for x in sources] == [keep['id']]
        return {'text': 'Grounded', 'preferences': [], 'source_ids': []}, sources
    ai.answer = answer
    response = c.post(url + '/assistant', headers=headers, json={'message': 'Dinner?'})
    assert response.status_code == 200
    assert response.json()['sources'] == []


def test_generation_exposes_excerpt_limits_and_history_outage_to_model():
    import json
    from types import SimpleNamespace
    ai = ConnectedAI.__new__(ConnectedAI)
    ai.model = 'test-model'
    calls = []
    ai.client = SimpleNamespace(responses=SimpleNamespace(create=lambda **kw: calls.append(kw) or SimpleNamespace(output_text='{"text":"Selected excerpts","preferences":[],"source_ids":[]}')))
    def resolver(matches): return []
    resolver.notes_status = {'documents_total': 9, 'documents_included': 6, 'context_truncated': True}
    ai.generate({'plan': {'id': 'plan'}, 'message': 'Dinner?', 'sources': [{'id': 'note', 'title': 'Food', 'text': 'Vegetarian', 'excerpt_truncated': True}], 'resolve_sources': resolver, 'history_unavailable': True})
    payload = json.loads(calls[0]['input'])
    assert payload['plan']['notes_context'] == resolver.notes_status
    assert payload['plan']['historical_retrieval_unavailable'] is True
    assert payload['evidence'][0]['excerpt_truncated'] is True
    assert 'only selected Notes excerpts' in calls[0]['instructions']
    assert calls[0]['text']['format']['schema']['properties']['source_ids']['items']['enum'] == ['note']


@pytest.mark.parametrize('history_count', [0, 1, 2])
def test_six_notes_leave_room_for_verified_historical_chat(env, history_count):
    from tagalong.core import source
    c, repo, ai, headers, _, plan = env
    url = '/v1/plans/' + plan['id']
    for i in range(6):
        assert c.post(url + '/documents', headers=headers, json={'title': 'Note ' + str(i), 'text': 'Current Note.'}).status_code == 200
    def seed(state):
        for i in range(2): source(state, plan['id'], 'chat-' + str(i), 'Chat', 'Earlier dinner decision.')
    repo.transact(seed)
    def answer(plan, message, resolve_sources):
        matches = [{'id': 'chat-' + str(i), 'version': 1} for i in range(history_count)]
        sources = resolve_sources(matches + matches + [{'id': 'missing', 'version': 1}])
        assert len(sources) == 6
        assert len({x['id'] for x in sources}) == 6
        assert {x['id'] for x in sources if x.get('kind') != 'document'} == {'chat-' + str(i) for i in range(history_count)}
        assert resolve_sources.notes_status == {'documents_total': 6, 'documents_included': 6 - history_count, 'context_truncated': bool(history_count)}
        return {'text': 'Grounded in Notes and history', 'preferences': [], 'source_ids': [x['id'] for x in sources]}, sources
    ai.answer = answer
    response = c.post(url + '/assistant', headers=headers, json={'message': 'Remember dinner?'})
    assert response.status_code == 200
