import streamlit as st
import sys
from pathlib import Path
# Support Streamlit entry-point deployment without a separate editable-package install.
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from campaign_hub.ui.resources import service_for, controls
from campaign_hub.config import Settings
from campaign_hub.hosting.bootstrap import apply_server_secrets

try:
    apply_server_secrets(st.secrets)
except (FileNotFoundError,st.errors.StreamlitSecretNotFoundError):
    pass
settings=Settings()

st.set_page_config(page_title='Campaign Intelligence Hub',page_icon=':material/insights:',layout='wide')
from campaign_hub.ui.appearance import apply_appearance
apply_appearance()
st.title('Campaign Intelligence Hub')
st.caption('From campaign evidence to executive-ready performance reports.')
st.badge('Synthetic course data',icon=':material/science:')

with st.sidebar:
    st.subheader('Workspace')
    page=st.radio('Navigate',['Generate Report','Historical Comparison','Ask Questions','Analyst View'])
    st.divider()
    with st.expander('Analyst model and retrieval settings'):
        providers=['ollama','openai','groq']
        provider=st.selectbox('Answer provider',providers,index=providers.index(settings.generation_provider))
        default_model=settings.generation_model if provider==settings.generation_provider else {'ollama':'llama3.2:3b','openai':'gpt-4.1-mini','groq':'qwen/qwen3.8-27b'}[provider]
        model=st.text_input('Generation model',value=default_model,key='generation-model-'+provider)
        options=controls()
    st.caption('Local Ollama · ChromaDB · No API key required' if provider=='ollama' else 'Hosted '+provider+' · ChromaDB · Server key required')
    if provider=='openai':
        st.info('OpenAI answers send retrieved passages and your question to OpenAI.')

try:
    service=service_for(model,provider)
except FileNotFoundError:
    st.warning('Source corpus is not generated yet. Run: python -m campaign_hub generate')
    st.stop()
except (ValueError,RuntimeError) as error:
    st.error(f'Knowledge-base startup failed: {error}')
    st.stop()

if page=='Generate Report':
    from campaign_hub.ui.report_page import show
elif page=='Historical Comparison':
    from campaign_hub.ui.history_page import show
elif page=='Ask Questions':
    from campaign_hub.ui.questions_page import show
else:
    from campaign_hub.ui.analyst_page import show
show(service,options)
