def test_ui_distinguishes_all_three_chunking_methods():
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_string('from campaign_hub.ui.resources import controls\ncontrols()').run()
    assert not app.exception
    assert app.selectbox[0].options==['Section-based','Fixed-size','Embedding-based semantic']
    assert app.selectbox[0].value=='section'
    app.selectbox[0].set_value('semantic').run()
    assert app.selectbox[0].value=='semantic' and not app.exception


def test_evaluation_can_show_bundled_measurements_without_overwriting_local_runs(tmp_path):
    from campaign_hub.config import Settings
    from campaign_hub.ui.evaluation_page import results_path
    settings=Settings(root=tmp_path)
    bundled=tmp_path/'docs/evaluation/three-chunking-results.json'
    bundled.parent.mkdir(parents=True)
    bundled.write_text('[]')
    assert results_path(settings)==bundled
    latest=settings.data/'runs/latest/results.json'
    latest.parent.mkdir(parents=True)
    latest.write_text('[]')
    assert results_path(settings)==latest
