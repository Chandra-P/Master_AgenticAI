import time
import streamlit as st
from campaign_hub.ui.resources import select_campaign


def show(service,options):
    st.header('Retrieval explorer')
    st.caption('Compare the same question and campaign across two retrieval configurations.')
    cid=select_campaign(service,'explorer')
    with st.form('explorer-form'):
        query=st.text_input('Evidence query',value='KPI Results targets actuals')
        other_chunk=st.selectbox('Comparison chunking',['fixed','semantic'])
        other_retrieval=st.selectbox('Comparison retrieval',['dense','hybrid'])
        submitted=st.form_submit_button('Compare retrieved evidence',type='primary')
    if submitted:
        try:
            alternate=options.model_copy(update={'chunking':other_chunk,'retrieval':other_retrieval})
            output=[]
            for config in [options,alternate]:
                started=time.perf_counter()
                hits=service.search(query,cid,config)
                output.append((config,hits,time.perf_counter()-started))
            st.session_state['retrieval-comparison']=output
            st.session_state['retrieval-corpus']=service.corpus_hash
            st.session_state['retrieval-campaign']=cid
        except Exception as error:
            st.error(str(error))
    output=st.session_state.get('retrieval-comparison',[])
    if st.session_state.get('retrieval-corpus')!=service.corpus_hash or st.session_state.get('retrieval-campaign')!=cid:
        output=[]
    for column,(config,hits,seconds) in zip(st.columns(2),output):
        with column:
            st.subheader(f'{config.chunking} · {config.retrieval}')
            st.caption(f'{seconds:.2f}s · reranking {config.reranking}')
            for rank,hit in enumerate(hits,1):
                with st.expander(f"{rank}. {hit.chunk.metadata['document_id']} · {hit.chunk.metadata['section_name']}"):
                    st.code(hit.chunk.text,language='markdown')
                    st.json({**hit.chunk.metadata,'ranking_score':hit.score,'dense_cosine':hit.dense_score,'bm25':hit.bm25_score,'cross_encoder':hit.rerank_score})
