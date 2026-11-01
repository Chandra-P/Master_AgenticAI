import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient


def agent_module():
    from convene import party_agent
    return party_agent


def test_catalog_comparison_executes_six_nodes_without_external_calls(monkeypatch):
    agent = agent_module()
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    events = []
    result = agent.run_agent(agent.AgentRequest(mode='catalog'), events.append)
    assert result['steps'] == ['Requirements', 'Budget', 'Vendor', 'Schedule', 'Creative', 'Review']
    assert result['mode'] == 'catalog'
    assert not [event for event in events if event['type'] == 'tool']
    best = result['recommendations'][0]
    assert best['published_subtotal'] == 610
    assert best['headroom_after_reserve'] == 390
    assert best['status'] == 'quotes_needed'
    assert result['date_check']['day'] == 'Sunday'


def test_agent_pushes_back_and_does_not_recommend_impossible_combinations():
    agent = agent_module()
    result = agent.run_agent(agent.AgentRequest(mode='catalog', budget=1000, reserve=800))
    assert not result['recommendations']
    assert result['rejected']
    assert result['status'] == 'needs_changes'
    assert result['warnings']


def test_total_guest_count_controls_capacity_rejection():
    agent = agent_module()
    result = agent.run_agent(agent.AgentRequest(mode='catalog', children=30, family=200))
    assert not result['recommendations']
    assert any('capacity' in row['reason'] for row in result['rejected'])


def test_live_agent_requires_key_without_silent_fallback(monkeypatch):
    agent = agent_module()
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    with pytest.raises(agent.AgentError, match='OPENAI_API_KEY'):
        agent.run_agent(agent.AgentRequest(mode='live'))


def test_live_model_calls_tools_and_rejects_invented_ranking(monkeypatch):
    agent = agent_module()
    monkeypatch.setenv('OPENAI_API_KEY', 'test-only-key')
    responses = [SimpleNamespace(output=[SimpleNamespace(type='function_call', name='search_web',
                  arguments=json.dumps({'query': 'San Antonio Texas civic centers'}), call_id='call1')]),
                 SimpleNamespace(output=[SimpleNamespace(type='function_call', name='read_page',
                  arguments=json.dumps({'url': 'https://www.bexar.org/3665/South-San-Civic-Center'}), call_id='call2')]),
                 SimpleNamespace(output=[])]
    monkeypatch.setattr(agent, '_model_turn', lambda *args, **kwargs: responses.pop(0))
    monkeypatch.setattr(agent, '_search', lambda *args, **kwargs:
                        [{'url': 'https://www.bexar.org/3665/South-San-Civic-Center', 'title': 'South San'}])
    from convene.web_fetch import Page
    monkeypatch.setattr(agent, 'fetch_page', lambda url, **kwargs: Page(url, 'Max Capacity: 160. $235. Security is required.', '2026-10-31T12:00:00Z'))
    monkeypatch.setattr(agent, '_model_review', lambda *args, **kwargs:
                        agent.Judgement(summary='Ask for itemized quotes.', choices=[
                            agent.RankedChoice(pair_id='invented', reason='Made up'),
                            agent.RankedChoice(pair_id='south-san+belle-arch', reason='Lower published base.')]))
    events=[]
    result=agent.run_agent(agent.AgentRequest(mode='live'), events.append)
    assert [event['tool'] for event in events if event['type']=='tool' and event['status']=='started'] == ['search_web','read_page']
    assert result['recommendations'][0]['pair_id']=='south-san+belle-arch'
    assert all(pair['pair_id']!='invented' for pair in result['recommendations'])
    assert result['source_checks'][0]['status']=='read'


def test_agent_api_stream_contains_real_activity_and_final_result(tmp_path):
    from convene.api import create_app
    client=TestClient(create_app(str(tmp_path/'agent.db')))
    response=client.post('/party/agent',json={'mode':'catalog'})
    assert response.status_code==200
    records=[json.loads(line) for line in response.text.splitlines()]
    assert [row['node'] for row in records if row['type']=='node' and row['status']=='started']==[
        'Requirements','Budget','Vendor','Schedule','Creative','Review']
    assert records[-1]['type']=='result'
    assert records[-1]['result']['recommendations'][0]['published_subtotal']==610


def test_failed_live_tools_leave_durable_unverified_warning(monkeypatch):
    agent=agent_module();monkeypatch.setenv('OPENAI_API_KEY','test-only-key')
    responses=[SimpleNamespace(output=[SimpleNamespace(type='function_call',name='read_page',
                 arguments=json.dumps({'url':'https://www.bexar.org/3665/South-San-Civic-Center'}),call_id='fail')]),SimpleNamespace(output=[])]
    monkeypatch.setattr(agent,'_model_turn',lambda *args,**kwargs:responses.pop(0))
    def fail(*args,**kwargs):
        raise agent.FetchError('Robots blocked this page')
    monkeypatch.setattr(agent,'fetch_page',fail)
    monkeypatch.setattr(agent,'_model_review',lambda *args,**kwargs:agent.Judgement(summary='Get quotes.',choices=[]))
    result=agent.run_agent(agent.AgentRequest(mode='live'))
    assert result['research_status']=='unverified'
    assert any('No public source pages' in warning for warning in result['warnings'])
    assert result['source_checks'][0]['status']=='failed'


def test_invalidated_source_price_is_returned_for_browser_reconciliation(monkeypatch):
    agent=agent_module();monkeypatch.setenv('OPENAI_API_KEY','test-only-key')
    responses=[SimpleNamespace(output=[SimpleNamespace(type='function_call',name='read_page',
                 arguments=json.dumps({'url':'https://www.bexar.org/3665/South-San-Civic-Center'}),call_id='changed')]),SimpleNamespace(output=[])]
    monkeypatch.setattr(agent,'_model_turn',lambda *args,**kwargs:responses.pop(0))
    from convene.web_fetch import Page
    monkeypatch.setattr(agent,'fetch_page',lambda url,**kwargs:Page(url,'Prices now require a quote.','2026-10-31T12:00:00Z'))
    monkeypatch.setattr(agent,'_model_review',lambda *args,**kwargs:agent.Judgement(summary='Get quotes.',choices=[]))
    result=agent.run_agent(agent.AgentRequest(mode='live'))
    assert next(update for update in result['option_updates'] if update['id']=='south-san')['price'] is None
