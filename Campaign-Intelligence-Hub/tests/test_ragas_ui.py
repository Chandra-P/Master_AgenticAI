import json
from types import SimpleNamespace
from streamlit.testing.v1 import AppTest
from campaign_hub.config import Settings


def test_ragas_saved_scores_are_labeled_and_unavailable_scores_are_not_charted(tmp_path):
    import campaign_hub.ui.ragas_results as view
    settings=Settings(root=tmp_path)
    path=settings.root/'docs/evaluation/ragas-smoke-results.json';path.parent.mkdir(parents=True)
    row={'identity':{'corpus':'corpus','framework':'ragas','assessment_version':1,
        'judge_provider':'ollama','judge_model':'judge','generation_provider':'ollama','generation_model':'generator'},
        'case_id':'q1','chunking':'section','retrieval':'hybrid','reranking':False,
        'ragas_faithfulness':None,'ragas_context_precision':.5,'ragas_context_recall':1.,
        'metric_errors':{'ragas_faithfulness':'unavailable'},'error':None,
        'verification_note':'Earlier judge configuration; not the current deployed model.',
        'sample':{'user_input':'Q','response':'A','retrieved_contexts':['Source'],'reference':'Gold'}}
    path.write_text(json.dumps([row]))
    view._test_service=SimpleNamespace(settings=settings,corpus_hash='corpus')
    try:
        app=AppTest.from_string('from campaign_hub.ui.ragas_results import show_ragas,_test_service\nshow_ragas(_test_service)',default_timeout=30).run()
        assert not app.exception and len(app.dataframe)==1
        headings=[h.value for h in app.subheader]
        assert 'RAGAS context precision' in headings and 'RAGAS faithfulness' not in headings
        assert any('unavailable' in i.value.lower() for i in app.info)
        assert 'judge' in app.dataframe[0].value['judge_profile'][0]
        assert 'precision prompt v1' in app.dataframe[0].value['judge_profile'][0]
        assert any('Earlier judge configuration' in c.value for c in app.caption)
        row['identity']['corpus']='old';path.write_text(json.dumps([row]))
        app.run()
        assert app.warning and not app.dataframe
    finally:
        del view._test_service
