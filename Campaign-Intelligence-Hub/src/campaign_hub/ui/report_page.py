import streamlit as st
from campaign_hub.reporting.render import render_report
from campaign_hub.ui.resources import source_viewer,build_indexes


def show(service,options):
    st.header('Generate a campaign performance report')
    st.markdown('Combine campaign goals, KPI results, historical lessons, and best practices into one cited report.')
    with st.container(horizontal=True):
        st.metric('Campaigns',len(service.campaigns),border=True)
        st.metric('Source documents',len(service.manifest['documents']),border=True)
        st.metric('Report sections',11,border=True)
    with st.form('report-form'):
        cid=st.selectbox('Campaign',list(service.campaigns),format_func=lambda c:f"{c} · {service.campaigns[c]['campaign_name']}")
        period=st.text_input('Reporting period (leave blank for campaign period)',value='')
        use_llm=st.checkbox('Use local model for narrative wording',value=False,
            help='Source wording is faster and fully traceable. Unsupported model paraphrases retain the source wording.')
        submitted=st.form_submit_button('Generate report',type='primary',icon=':material/description:')
    if submitted:
        try:
            with st.spinner('Retrieving evidence and assembling eleven report sections…'):
                report=service.generate_report(cid,period or service.campaigns[cid]['period'],options,use_llm=use_llm)
                st.session_state['report']=report
        except Exception as error:
            st.error(str(error))
    report=st.session_state.get('report')
    if report and report.provenance.get('corpus_hash')!=service.corpus_hash:
        st.session_state.pop('report',None)
        report=None
        st.info('Campaign evidence changed. Generate a fresh report using the current corpus.')
    if report:
        st.subheader(f'Report · {report.campaign_id}')
        if report.status=='complete':
            st.success('All required report sections and input categories have evidence.')
        else:
            st.warning('Partial report: some sections or input categories have insufficient evidence.')
        with st.container(horizontal=True):
            st.metric('Evidence coverage',f'{report.confidence:.0%}',border=True)
            st.metric('Cited chunks',len(report.evidence),border=True)
            st.metric('Elapsed',f"{report.timings.get('total_seconds',0):.1f}s",border=True)
        text=render_report(report)
        st.download_button('Download performance report',text,file_name=f'{report.campaign_id}-performance-report.md',mime='text/markdown',icon=':material/download:')
        st.markdown(text)
        source_viewer(service,report.evidence)
        with st.expander('Coverage and provenance'):
            st.json(report.provenance)
    else:
        st.info('Select a campaign and generate a report. Each finding will point to retrieved source evidence.')
    build_indexes(service)
