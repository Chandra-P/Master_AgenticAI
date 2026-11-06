import copy
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from tagalong.app import create_app
from tagalong.core import Actor, MemoryRepository


def setup():
    repo = MemoryRepository()
    app = create_app(repo, lambda token: Actor(token, token+'@example.test', token))
    client = TestClient(app)
    headers = {'Authorization': 'Bearer alice'}
    plan = client.post('/v1/plans', headers=headers, json={'title':'Weekend', 'kind':'trip', 'start':'2027-05-14','end':'2027-05-16'}).json()
    calls = []
    def complete(draft, context):
        calls.append((draft, context))
        return ' meet at noon'
    app.state.typing_provider = SimpleNamespace(complete=complete)
    return repo, app, client, headers, plan, calls


def request(client, headers, plan, **extra):
    return client.post('/v1/plans/'+plan['id']+'/typing-suggestion', headers=headers, json={'draft':'We could', 'expected_revision':plan['revision'], **extra})


def test_suggestion_is_authorized_and_never_saved():
    repo, app, client, headers, plan, calls = setup()
    before = copy.deepcopy(repo.state)
    response = request(client, headers, plan)
    assert response.status_code == 200, response.text
    assert response.json() == {'suggestion':' meet at noon','source':'model'}
    assert repo.state == before
    assert len(calls) == 1
    assert request(client, {}, plan).status_code == 401
    assert request(client, {'Authorization':'Bearer bob'}, plan).status_code == 404


@pytest.mark.parametrize('change', ['revision','revoked','suspended'])
def test_access_and_revision_rechecked_after_completion(change):
    repo, app, client, headers, plan, calls = setup()
    def complete(draft, context):
        if change == 'revision': repo.state['plans'][plan['id']]['revision'] += 1
        elif change == 'revoked': repo.state['members'][plan['id']] = []
        else: repo.state['suspended_users'] = {'alice':True}
        return ' together'
    app.state.typing_provider.complete = complete
    assert request(client, headers, plan).status_code in (403,404,409)
    assert repo.state['plans'][plan['id']]['messages'] == []


def test_stale_or_invalid_input_does_not_call_provider():
    repo, app, client, headers, plan, calls = setup()
    assert request(client, headers, plan, expected_revision=0).status_code in (409,422)
    assert request(client, headers, plan, draft='x'*1801).status_code == 422
    assert request(client, headers, plan, draft='hello\nthere').status_code == 422
    assert request(client, headers, plan, draft='   ').status_code == 422
    assert calls == []


@pytest.mark.parametrize('output', ['hello\nthere','x'*81,'We could meet soon','one two three four five six seven eight nine','\x00secret'])
def test_invalid_model_suffix_is_not_displayed(output):
    repo, app, client, headers, plan, calls = setup()
    app.state.typing_provider.complete = lambda draft, context: output
    response = request(client, headers, plan)
    assert response.status_code == 200
    assert response.json()['suggestion'] == ''


def test_rate_limit_and_unavailable_provider():
    repo, app, client, headers, plan, calls = setup()
    for _ in range(20): assert request(client, headers, plan).status_code == 200
    assert request(client, headers, plan).status_code == 429
    repo, app, client, headers, plan, calls = setup()
    app.state.typing_provider = None
    assert request(client, headers, plan).status_code == 503


def test_context_is_bounded_to_current_plan_human_messages():
    repo, app, client, headers, plan, calls = setup()
    p = repo.state['plans'][plan['id']]
    p['messages'] = [{'text':'human'+str(i)+'x'*500,'assistant':False} for i in range(8)] + [{'text':'PRIVATE ASSISTANT','assistant':True}]
    assert request(client, headers, plan).status_code == 200
    context = calls[0][1]
    assert set(context) == {'title','location','start','end','budget','messages'}
    assert len(context['messages']) == 4
    assert all(len(text) <= 200 for text in context['messages'])
    assert 'PRIVATE ASSISTANT' not in str(context)


def test_openai_provider_uses_bounded_ephemeral_request():
    from tagalong.typing_suggestions import TypingProvider
    calls = []
    class Responses:
        def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(output_text=' together')
    provider = TypingProvider(client=SimpleNamespace(responses=Responses()), model='test-model')
    assert provider.complete('We could', {'title':'Weekend'}) == ' together'
    call = calls[0]
    assert call['model'] == 'test-model' and call['store'] is False
    assert call['max_output_tokens'] == 64
    assert call['timeout'] == 5
    assert 'tools' not in call


def test_concurrency_is_bounded_and_slots_release_after_errors():
    from concurrent.futures import ThreadPoolExecutor
    import threading
    repo, app, client, headers, plan, calls = setup()
    entered = threading.Barrier(3)
    release = threading.Event()
    def complete(draft, context):
        entered.wait(timeout=5)
        assert release.wait(timeout=5)
        return ' together'
    app.state.typing_provider.complete = complete
    with ThreadPoolExecutor(max_workers=2) as workers:
        futures = [workers.submit(request, client, headers, plan) for _ in range(2)]
        try:
            entered.wait(timeout=5)
            assert request(client, headers, plan).status_code == 429
        finally:
            release.set()
        assert all(future.result().status_code == 200 for future in futures)
    def broken(draft, context):
        raise RuntimeError('secret provider detail')
    app.state.typing_provider.complete = broken
    response = request(client, headers, plan)
    assert response.status_code == 503 and 'secret provider detail' not in response.text
    app.state.typing_provider.complete = lambda draft, context: ' together'
    assert request(client, headers, plan).status_code == 200
