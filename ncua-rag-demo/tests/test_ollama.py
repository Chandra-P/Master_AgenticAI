import pytest


def test_embeddings_preserve_order_in_bounded_batches(monkeypatch):
    from pipeline.index import LocalEmbeddings
    import requests
    sizes = []
    class Response:
        def __init__(self, texts): self.texts = texts
        def raise_for_status(self): pass
        def json(self): return {'embeddings': [[float(text), 1.] for text in self.texts]}
    def post(url, **kwargs):
        texts = kwargs['json']['input']
        sizes.append(len(texts))
        return Response(texts)
    monkeypatch.setattr(requests, 'post', post)
    vectors = LocalEmbeddings().embed_documents([str(i) for i in range(65)])
    assert [v[0] for v in vectors] == list(range(65))
    assert sizes == [32, 32, 1]

def test_default_model_is_local_and_needs_no_api_key(monkeypatch):
    from pipeline.graph import local_model
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    import requests
    captured = {}
    class Response:
        def raise_for_status(self): pass
        def json(self): return {'message': {'content': 'Supported answer [E1].'}}
    def post(url, **kwargs):
        captured.update(url=url, **kwargs)
        return Response()
    monkeypatch.setattr(requests, 'post', post)
    from langchain_core.prompts import ChatPromptTemplate
    result = (ChatPromptTemplate.from_messages([('human', '{question}')]) | local_model()).invoke({'question': 'assets?'})
    assert result.content == 'Supported answer [E1].'
    assert captured['url'] == 'http://localhost:11434/api/chat'
    assert captured['json']['model'] == 'llama3.2:3b'
    assert captured['json']['stream'] is False

def test_default_embeddings_are_ollama_and_validate_response(monkeypatch):
    from pipeline.index import LocalEmbeddings
    import requests
    class Response:
        def raise_for_status(self): pass
        def json(self): return {'embeddings': [[1., 0.], [0., 1.]]}
    monkeypatch.setattr(requests, 'post', lambda *a, **kw: Response())
    embedder = LocalEmbeddings()
    assert embedder.identity == 'ollama:embeddinggemma:latest'
    assert embedder.embed_documents(['a', 'b']) == [[1., 0.], [0., 1.]]
    with pytest.raises(ValueError, match='embedding'):
        embedder.embed_documents(['a'])
