from dataclasses import replace
import pytest


def test_cloud_configuration_is_runtime_selected(monkeypatch):
    from campaign_hub.config import Settings
    monkeypatch.setenv('CIH_EMBEDDING_PROVIDER','sentence_transformers')
    monkeypatch.setenv('CIH_GENERATION_PROVIDER','groq')
    monkeypatch.setenv('CIH_AUTO_INDEX','true')
    settings=Settings()
    assert settings.embedding_provider=='sentence_transformers'
    assert settings.embedding_model=='sentence-transformers/all-MiniLM-L6-v2'
    assert settings.generation_provider=='groq'
    assert settings.auto_index


def test_embedding_factory_keeps_local_default_and_rejects_unknown(tmp_path):
    from campaign_hub.config import Settings
    from campaign_hub.embeddings.providers import create_embedder,OllamaEmbedder
    assert isinstance(create_embedder(Settings(root=tmp_path)),OllamaEmbedder)
    with pytest.raises(ValueError,match='embedding provider'):
        create_embedder(replace(Settings(root=tmp_path),embedding_provider='unknown'))


def test_hosted_embeddings_are_normalized_cached_and_model_isolated(tmp_path,monkeypatch):
    from campaign_hub.config import Settings
    import campaign_hub.embeddings.providers as providers
    import numpy as np
    calls=[]
    class Encoder:
        def encode(self,texts,**kwargs):
            calls.append((texts,kwargs))
            return np.array([[.6,.8] for _ in texts])
    monkeypatch.setattr(providers,'_sentence_model',lambda name:Encoder())
    monkeypatch.setattr(providers,'_token_windows',lambda model,text:[(text,1)])
    settings=replace(Settings(root=tmp_path),embedding_provider='sentence_transformers',embedding_model='model-a')
    embedder=providers.create_embedder(settings)
    assert embedder.embed_documents(['evidence'])==[[.6,.8]]
    assert embedder.embed_query('evidence')==[.6,.8]
    assert len(calls)==1 and calls[0][1]['normalize_embeddings'] is True
    other=providers.create_embedder(replace(settings,embedding_model='model-b'))
    other.embed_query('evidence')
    assert len(calls)==2
    assert embedder.identity!=other.identity


def test_cpu_embeddings_include_chunk_tails_within_model_token_budget(tmp_path,monkeypatch):
    from campaign_hub.config import Settings
    import campaign_hub.embeddings.providers as providers
    import numpy as np,re
    class Tokenizer:
        def num_special_tokens_to_add(self,pair=False):return 2
        def __call__(self,text,**kwargs):
            matches=list(re.finditer(r'\S+',text))
            return {'input_ids':list(range(len(matches))),'offset_mapping':[(m.start(),m.end()) for m in matches]}
    class Encoder:
        tokenizer=Tokenizer();max_seq_length=6
        def __init__(self):self.seen=[]
        def encode(self,texts,**kwargs):
            self.seen+=texts
            assert all(len(t.split())<=4 for t in texts)
            return np.array([[0.,1.] if 'tail' in t.split() else [1.,0.] for t in texts])
    model=Encoder();monkeypatch.setattr(providers,'_sentence_model',lambda name:model)
    settings=replace(Settings(root=tmp_path),embedding_provider='sentence_transformers',embedding_model='test')
    vector=providers.create_embedder(settings).embed_query('a b c d e f g h i j k tail')
    assert any('tail' in t.split() for t in model.seen)
    assert vector[1]>0
    assert np.linalg.norm(vector)==pytest.approx(1)


def test_groq_key_is_server_owned_and_not_required_for_reports(monkeypatch):
    from campaign_hub.config import Settings
    from campaign_hub.generation.providers import create_generator
    monkeypatch.delenv('GROQ_API_KEY',raising=False)
    with pytest.raises(RuntimeError,match='server.*GROQ_API_KEY'):
        create_generator(replace(Settings(),generation_provider='groq'))


def test_bootstrap_builds_only_missing_indexes(tmp_path,monkeypatch):
    from campaign_hub.hosting.bootstrap import prepare_indexes
    class Service:
        corpus_hash='version-a'
        def __init__(self):self.built=[];self.available={'fixed'}
        def store(self,strategy):
            if strategy not in self.available:raise ValueError('Index missing')
            return object()
        def index(self,strategy):self.built.append(strategy);self.available.add(strategy)
    service=Service()
    prepare_indexes(service)
    prepare_indexes(service)
    assert service.built==['section','semantic']


def test_experiment_identity_separates_providers_with_same_model_names(tmp_path):
    from campaign_hub.evaluation.runner import experiment_identity
    from campaign_hub.models import RetrievalOptions
    from campaign_hub.config import Settings
    class Service:
        corpus_hash='version'
        settings=Settings(root=tmp_path)
    service=Service();first=experiment_identity(service,RetrievalOptions(),{'id':'q1'},False,False)
    service.settings=replace(service.settings,embedding_provider='sentence_transformers',generation_provider='groq')
    second=experiment_identity(service,RetrievalOptions(),{'id':'q1'},False,False)
    assert first!=second
    assert first['embedding']==second['embedding']
    assert first['embedding_config']!=second['embedding_config']
    assert 'chunking_config' in second


def test_server_secrets_are_whitelisted(monkeypatch):
    from campaign_hub.hosting.bootstrap import apply_server_secrets
    import os
    monkeypatch.delenv('NOT_AN_APP_SETTING',raising=False)
    monkeypatch.delenv('CIH_AUTO_INDEX',raising=False)
    apply_server_secrets({'CIH_AUTO_INDEX':'true','NOT_AN_APP_SETTING':'ignore'})
    assert os.getenv('CIH_AUTO_INDEX')=='true'
    assert 'NOT_AN_APP_SETTING' not in os.environ
