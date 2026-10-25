import json
from dataclasses import replace
import pytest
from campaign_hub.config import Settings


def test_classifier_defaults_to_ollama_even_with_hosted_answers(monkeypatch):
    import campaign_hub.retrieval.classification as module
    captured = {}
    class Generator:
        def __init__(self, settings): captured['settings'] = settings
        def generate_json(self, system, prompt, schema):
            captured['prompt'] = json.loads(prompt)
            return schema(filters=[{'field':'region','values':['TX'],'source_text':'Texas'},
                                   {'field':'year','values':[2026],'source_text':'2026'}])
    monkeypatch.setattr(module, 'create_generator', Generator)
    settings = replace(Settings(), generation_provider='groq', generation_model='hosted')
    result = module.classify_filters('Texas results in 2026', {'region': ['TX'], 'year': [2026]}, settings)
    assert result == {'region': ['TX'], 'year': [2026]}
    assert captured['settings'].generation_provider == 'ollama'
    assert captured['settings'].generation_model == 'llama3.2:3b'
    assert captured['prompt']['allowed_values']['region'] == ['TX']


def test_classifier_rejects_invented_value(monkeypatch):
    import campaign_hub.retrieval.classification as module
    class Generator:
        def generate_json(self, system, prompt, schema):
            return schema(filters=[{'field':'region','values':['ZZ'],'source_text':'Texas'}])
    monkeypatch.setattr(module, 'create_generator', lambda settings: Generator())
    with pytest.raises(ValueError): module.classify_filters('Texas', {'region': ['TX']}, Settings())


def test_classifier_rejects_constraints_without_question_evidence(monkeypatch):
    import campaign_hub.retrieval.classification as module
    class Generator:
        def generate_json(self, system, prompt, schema):
            return schema(filters=[{'field':'year','values':[2026],'source_text':'2025'}])
    monkeypatch.setattr(module, 'create_generator', lambda settings: Generator())
    with pytest.raises(ValueError, match='supporting words'):
        module.classify_filters('Reports in 2026', {'year': [2026]}, Settings())


def test_generic_question_never_invents_filters_or_calls_model(monkeypatch):
    import campaign_hub.retrieval.classification as module
    def forbidden(*a, **kw): raise AssertionError('No metadata terms need classification')
    monkeypatch.setattr(module, 'create_generator', forbidden)
    assert module.classify_filters('What were the objectives?',
        {'region': ['TX', 'ALL'], 'campaign_id': ['TX-CHK-001', 'GLOBAL'], 'period': ['ALL', '2026-Q2']}, Settings()) == {}


def test_classifier_cannot_infer_campaign_ids_or_quarters_from_region_and_year(monkeypatch):
    import campaign_hub.retrieval.classification as module
    captured = {}
    class Generator:
        def generate_json(self, system, prompt, schema):
            captured.update(json.loads(prompt))
            return schema(filters=[])
    monkeypatch.setattr(module, 'create_generator', lambda settings: Generator())
    module.classify_filters('Texas reports in 2026', {'region': ['TX'], 'year': [2026],
        'campaign_id': ['TX-CHK-001'], 'period': ['2026-Q2']}, Settings())
    assert 'campaign_id' not in captured['allowed_values']
    assert 'period' not in captured['allowed_values']


def test_campaign_id_does_not_imply_a_region_filter():
    from campaign_hub.retrieval.classification import mentioned_values
    catalog={'campaign_id':['TX-CHK-001'],'region':['TX'],'year':[2026],
             'client_name':['Fictional Meridian Credit Union']}
    assert mentioned_values('Show TX-CHK-001',catalog)=={'campaign_id':['TX-CHK-001']}
    assert mentioned_values('Show TX-CHK-001 in Texas',catalog)['region']==['TX']


def test_openai_is_explicit_and_errors_do_not_expose_credentials(monkeypatch):
    from campaign_hub.generation.providers import create_generator
    from pydantic import BaseModel
    class Output(BaseModel): value: str
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    with pytest.raises(RuntimeError, match='OPENAI_API_KEY'):
        create_generator(replace(Settings(), generation_provider='openai'))
    monkeypatch.setenv('OPENAI_API_KEY', 'private-test-value')
    import httpx
    seen = {}
    def post(url, **kwargs):
        seen.update(url=url, **kwargs)
        return httpx.Response(200, json={'choices': [{'finish_reason': 'stop', 'message': {'content': '{"value":"ok"}'}}]}, request=httpx.Request('POST', url))
    monkeypatch.setattr(httpx, 'post', post)
    generator = create_generator(replace(Settings(), generation_provider='openai', generation_model='configured-model'))
    assert generator.generate_json('system', 'question', Output).value == 'ok'
    assert seen['json']['response_format']['json_schema']['strict'] is True
    assert seen['json']['model'] == 'configured-model'
    def fail(*a, **kw): raise RuntimeError('private-test-value')
    monkeypatch.setattr(httpx, 'post', fail)
    with pytest.raises(RuntimeError) as error: generator.generate_json('system', 'question', Output)
    assert 'private-test-value' not in str(error.value)


@pytest.mark.parametrize('choice', [
    {'finish_reason': 'length', 'message': {'content': '{"value":"partial"}'}},
    {'finish_reason': 'stop', 'message': {'refusal': 'Cannot comply', 'content': None}},
    {'finish_reason': 'stop', 'message': {'content': '{"wrong":"schema"}'}},
])
def test_openai_refusal_truncation_and_bad_schema_fail_closed(monkeypatch, choice):
    import httpx
    from pydantic import BaseModel
    from campaign_hub.generation.providers import create_generator
    class Output(BaseModel): value: str
    monkeypatch.setenv('OPENAI_API_KEY', 'test-placeholder-only')
    monkeypatch.setattr(httpx, 'post', lambda url, **kwargs: httpx.Response(200,
        json={'choices': [choice]}, request=httpx.Request('POST', url)))
    with pytest.raises(RuntimeError, match='OpenAI generation failed'):
        create_generator(replace(Settings(), generation_provider='openai')).generate_json('s', 'q', Output)


def test_provider_defaults_and_server_secret_whitelist(monkeypatch):
    from campaign_hub.hosting.bootstrap import apply_server_secrets
    for name in ('CIH_CLASSIFICATION_PROVIDER', 'CIH_CLASSIFICATION_MODEL', 'CIH_GENERATION_PROVIDER', 'CIH_GENERATION_MODEL'):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    assert Settings().generation_provider == Settings().classification_provider == 'ollama'
    monkeypatch.setenv('CIH_GENERATION_PROVIDER', 'openai')
    assert Settings().generation_model == 'gpt-4.1-mini'
    assert Settings().classification_provider == 'ollama'
    apply_server_secrets({'OPENAI_API_KEY': 'test-placeholder-only'})
    import os
    assert os.environ['OPENAI_API_KEY'] == 'test-placeholder-only'
