import streamlit as st
import sys
from pathlib import Path
# Support Streamlit entry-point deployment without a separate editable-package install.
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from campaign_hub.ui.resources import service_for, controls

st.set_page_config(page_title='Campaign Intelligence Hub',page_icon=':material/insights:',layout='wide')
st.title('Campaign Intelligence Hub')
st.caption('From campaign evidence to executive-ready performance reports.')
st.badge('Synthetic course data',icon=':material/science:')

with st.sidebar:
    st.subheader('Workspace')
    page=st.radio('Navigate',['Generate Report','Historical Comparison','Ask Questions','Retrieval Explorer','Evaluation Dashboard'])
    st.divider()
    with st.expander('Analyst model and retrieval settings'):
        model=st.text_input('Local generation model',value='llama3.2:3b')
        options=controls()
    st.caption('Local Ollama · ChromaDB · No API key required')

try:
    service=service_for(model)
except FileNotFoundError:
    st.warning('Source corpus is not generated yet. Run: python -m campaign_hub generate')
    st.stop()

if page=='Generate Report':
    from campaign_hub.ui.report_page import show
elif page=='Historical Comparison':
    from campaign_hub.ui.history_page import show
elif page=='Ask Questions':
    from campaign_hub.ui.questions_page import show
elif page=='Retrieval Explorer':
    from campaign_hub.ui.explorer_page import show
else:
    from campaign_hub.ui.evaluation_page import show
show(service,options)
