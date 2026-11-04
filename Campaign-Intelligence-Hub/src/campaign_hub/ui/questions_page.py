import streamlit as st
from campaign_hub.ui.resources import select_campaign
from campaign_hub.ui.analyst_page import show as show_analysis


def show(service,options):
    st.header('Ask questions')
    scope=st.radio('Search scope',['Entire knowledge base','Selected campaign'],key='question-scope',horizontal=True)
    cid=select_campaign(service,'questions') if scope=='Selected campaign' else None
    show_analysis(service,options,campaign_id=cid,answer=True)
