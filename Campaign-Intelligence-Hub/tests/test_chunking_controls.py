def test_ui_distinguishes_all_three_chunking_methods():
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_string('from campaign_hub.ui.resources import controls\ncontrols()',default_timeout=30).run()
    assert not app.exception
    assert app.selectbox[0].options==['Section-based','Fixed-size','Embedding-based semantic']
    assert app.selectbox[0].value=='semantic'
    app.selectbox[0].set_value('fixed').run()
    assert app.selectbox[0].value=='fixed' and not app.exception
