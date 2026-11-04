def test_experiment_matrix_and_unknown_metric():
    from campaign_hub.rag.evaluation import configurations
    configs=configurations(include_reranking=True)
    assert len(configs)==12
    assert len({(c.chunking,c.retrieval,c.reranking) for c in configs})==12
    assert {c.chunking for c in configs}=={'fixed','section','semantic'}


def test_ui_exposes_only_pure_rag_workflows(tmp_path,monkeypatch):
    from streamlit.testing.v1 import AppTest
    from campaign_hub.config import ROOT
    from campaign_hub.config import Settings
    from campaign_hub.synthetic_data.generator import generate_corpus
    from campaign_hub.rag.service import RAGService
    import campaign_hub.ui.resources as resources
    generate_corpus(tmp_path/'data')
    service=RAGService(Settings(root=tmp_path))
    monkeypatch.setattr(resources,'service_for',lambda model,provider=None:service)
    app=AppTest.from_file(str(ROOT/'app.py'), default_timeout=30).run()
    assert not app.exception
    assert any('Campaign Intelligence Hub' in t.value for t in app.title)
    assert len(app.sidebar.radio)==1
    assert app.sidebar.radio[0].options==['Ask Questions','Analyst View','Chunking Lab','Evaluation']
    for page in ['Analyst View','Chunking Lab','Evaluation']:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception
