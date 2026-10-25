def test_collector_uses_live_backend_model_and_reranker(tmp_path,monkeypatch):
    import json
    import requests
    from pipeline.assess_generation import collect
    (tmp_path/'evaluation').mkdir()
    (tmp_path/'evaluation/questions.json').write_text(json.dumps([]))
    (tmp_path/'.env').write_text('OLLAMA_MODEL=outdated-file-value\n')
    class Response:
        def raise_for_status(self): pass
        def json(self):
            return {'ready':True,'generation':True,'generation_provider':'Ollama',
                    'generation_model':'active-local-model','embedding_model':'ollama:embeddinggemma:latest','reranker':None}
    monkeypatch.setattr(requests,'get',lambda *a,**kw:Response())
    result=collect(tmp_path)
    assert result['model']=='active-local-model'
    assert result['provider']=='Ollama'
    assert result['rerank'] is False
