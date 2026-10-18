from dataclasses import replace
import hashlib
import streamlit as st
from campaign_hub.config import Settings
from campaign_hub.models import RetrievalOptions


@st.cache_resource(max_entries=4)
def _cached_service(model,manifest_hash):
    from campaign_hub.reporting.service import CampaignService
    return CampaignService(replace(Settings(),generation_model=model))


def service_for(model):
    manifest_hash=hashlib.sha256((Settings().data/'manifest.json').read_bytes()).hexdigest()
    return _cached_service(model,manifest_hash)


def controls():
    chunking=st.selectbox('Chunking',['semantic','fixed'])
    retrieval=st.selectbox('Retrieval',['hybrid','dense'])
    reranking=st.checkbox('Cross-encoder reranking',value=False)
    return RetrievalOptions(chunking=chunking,retrieval=retrieval,reranking=reranking)


def select_campaign(service,key,label='Campaign'):
    clients=['All clients']+sorted({c['client_name'] for c in service.campaigns.values()})
    client=st.selectbox('Client',clients,key=f'{key}-client')
    campaigns=[cid for cid,c in service.campaigns.items() if client=='All clients' or c['client_name']==client]
    return st.selectbox(label,campaigns,key=f'{key}-campaign',
        format_func=lambda cid:f"{cid} · {service.campaigns[cid]['campaign_name']}")


def source_viewer(service,evidence):
    if not evidence:
        return
    with st.expander('Inspect cited evidence'):
        selected=st.selectbox('Source chunk',list(evidence),key='source-viewer')
        chunk=evidence[selected]
        st.json(chunk.metadata)
        st.code(chunk.text,language='markdown')


def build_indexes(service):
    with st.expander('Knowledge base setup'):
        st.caption('Build once after generating or changing the corpus or embedding model.')
        if st.button('Build both Chroma indexes',icon=':material/database:'):
            try:
                with st.status('Embedding sources locally and building Chroma indexes…',expanded=True) as status:
                    for strategy in ['fixed','semantic']:
                        count=service.index(strategy)
                        st.write(f'{strategy}: {count} chunks indexed')
                    status.update(label='Both indexes ready',state='complete')
            except Exception as error:
                st.error(str(error))
