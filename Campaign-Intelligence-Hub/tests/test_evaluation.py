def test_experiment_matrix_and_unknown_metric():
    from campaign_hub.evaluation.runner import configurations, completeness
    configs=configurations()
    assert len(configs)==12
    assert len({(c.chunking,c.retrieval,c.reranking) for c in configs})==12
    assert {c.chunking for c in configs}=={'fixed','section','semantic'}
    assert completeness('120 activations', ['120','funded'])==0.5


def test_ui_exposes_client_workflows_and_analyst_view(tmp_path,monkeypatch):
    from streamlit.testing.v1 import AppTest
    from campaign_hub.config import ROOT
    from campaign_hub.config import Settings
    from campaign_hub.synthetic_data.generator import generate_corpus
    from campaign_hub.reporting.service import CampaignService
    import campaign_hub.ui.resources as resources
    generate_corpus(tmp_path/'data')
    service=CampaignService(Settings(root=tmp_path))
    monkeypatch.setattr(resources,'service_for',lambda model,provider=None:service)
    app=AppTest.from_file(str(ROOT/'app.py'), default_timeout=30).run()
    assert not app.exception
    assert any('Campaign Intelligence Hub' in t.value for t in app.title)
    assert len(app.sidebar.radio)==1
    assert app.sidebar.radio[0].options==['Generate Report','Historical Comparison','Ask Questions','Analyst View']
    for page in ['Historical Comparison','Ask Questions','Analyst View']:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception
