import streamlit as st
from campaign_hub.models import Chunk
from campaign_hub.ui.resources import source_viewer


def show(service,options):
    st.header('Ask questions')
    example=st.selectbox('Example prompts',['What were the objectives?','How was success defined?','What were the KPI results?','What recommendations were made?'])
    with st.form('ask-form'):
        cid=st.selectbox('Campaign',list(service.campaigns))
        question=st.text_area('Your question',value=example)
        submitted=st.form_submit_button('Find evidence',type='primary')
    if submitted:
        try:
            with st.spinner('Retrieving and validating a grounded answer…'):
                st.session_state['answer']=service.answer_question(question,cid,options)
        except Exception as error:
            st.error(str(error))
    result=st.session_state.get('answer')
    if result:
        st.markdown(result['answer'])
        st.caption('Only verifiable source wording is accepted. No semantic faithfulness score has been assigned.')
        evidence={h['chunk']['chunk_id']:Chunk.model_validate(h['chunk']) for h in result['hits']}
        source_viewer(service,evidence)
