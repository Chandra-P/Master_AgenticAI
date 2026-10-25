import streamlit as st
from campaign_hub.ui.resources import select_campaign
from campaign_hub.ui.analyst_page import show as show_analysis


def show(service,options):
    st.header('Ask questions')
    cid=select_campaign(service,'questions')
    show_analysis(service,options,campaign_id=cid,answer=True)
