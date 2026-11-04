from streamlit.testing.v1 import AppTest


def lab_app():
    import streamlit as st
    from campaign_hub.ui.chunking_page import show
    from campaign_hub.models import RetrievalOptions
    from types import SimpleNamespace
    if 'stub' not in st.session_state:
        class Service:
            corpus_hash='corpus1'
            manifest={'documents':[{'document_id':'a','region':'TX'},{'document_id':'b','region':'CA'}]}
            settings=SimpleNamespace()
            calls=[]
            def search(self, query, campaign_id, options, **kwargs):
                self.calls.append((query,campaign_id,options.chunking,kwargs))
                return [{'chunk':{'chunk_id':'hit','text':'Retrieved proof','metadata':{}},'score':.3}]
        st.session_state.stub=Service()
    show(st.session_state.stub,RetrievalOptions())


def test_comparison_is_explicit_same_filters_and_hides_stale_results():
    at=AppTest.from_function(lab_app).run()
    assert not at.exception
    assert not at.session_state.stub.calls
    at.text_area[0].set_value('Find proof').run()
    next(x for x in at.multiselect if x.label=='Region').select('TX').run()
    assert not at.session_state.stub.calls
    at.button(key='lab-compare').click().run()
    assert not at.exception
    assert [c[2] for c in at.session_state.stub.calls]==['fixed','section','semantic']
    assert all(c[3]['filters']=={'region':['TX']} for c in at.session_state.stub.calls)
    assert any(x.value=='Retrieved proof' for x in at.code)
    at.selectbox(key='lab-source').select('b').run()
    assert not any(x.value=='Retrieved proof' for x in at.code)
    assert len(at.session_state.stub.calls)==3


def test_query_filters_and_corpus_edits_hide_evidence_without_searching():
    at=AppTest.from_function(lab_app).run()
    at.text_area[0].set_value('proof').run()
    at.button(key='lab-compare').click().run()
    assert any(x.value=='Retrieved proof' for x in at.code)
    at.text_area[0].set_value('changed').run()
    assert not any(x.value=='Retrieved proof' for x in at.code)
    assert len(at.session_state.stub.calls)==3
    at.button(key='lab-compare').click().run()
    next(x for x in at.multiselect if x.label=='Region').select('CA').run()
    assert not any(x.value=='Retrieved proof' for x in at.code)
    assert len(at.session_state.stub.calls)==6
    at.button(key='lab-compare').click().run()
    at.session_state.stub.corpus_hash='corpus2'
    at.run()
    assert not any(x.value=='Retrieved proof' for x in at.code)
    assert len(at.session_state.stub.calls)==9

