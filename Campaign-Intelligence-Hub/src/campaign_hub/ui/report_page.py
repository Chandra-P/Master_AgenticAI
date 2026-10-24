import json
import pandas as pd
import pydeck as pdk
import streamlit as st
from campaign_hub.ui.resources import select_campaign,build_indexes
from campaign_hub.reporting.client_packet import build_client_packet,validate_packet
from campaign_hub.reporting.html_report import export_html


def show(service,options):
    st.header('Campaign performance workspace')
    st.caption('Select a client and campaign. Results and geographic performance update automatically.')
    cid=select_campaign(service,'report')
    meta=service.campaigns[cid]
    left,right=st.columns(2)
    period=left.selectbox('Reporting period',[meta['period']],key=f'period-{cid}')
    channel=right.selectbox('Channel',['All channels','direct_mail','display'],key='map-channel',format_func=lambda x:x.replace('_',' ').title())
    try:
        snap=service.campaign_snapshot(cid,client_name=meta['client_name'],period=period,channel=None if channel=='All channels' else channel)
        packet=build_client_packet(service,cid)
    except (ValueError,KeyError) as error:
        st.error(f'Presentation exports blocked: {error}')
        return
    st.caption(f"{snap['campaign_name']} · {snap['period']} · Data as of {snap['as_of']} · Fictional data")
    a,b,c,d=st.columns(4)
    a.metric('Attributed accounts',f"{snap['actual']:,}",border=True)
    b.metric('Opening balances',f"${snap['balance_cents']/100:,.0f}",border=True)
    c.metric('Attributed spend',f"${snap['spend']:,.0f}",border=True)
    d.metric('Activation goal attainment',f"{snap['actual']/snap['target']:.1%}" if snap['target'] else 'Campaign total only',border=True)
    st.caption(snap['balance_definition'])
    map_col,insight_col=st.columns([3,1])
    with map_col,st.container(border=True):
        st.subheader('Where results originate')
        metric=st.segmented_control('Map measure',['Accounts','Opening balances'],default='Accounts',key='map-measure')
        rows=pd.DataFrame(snap['geography'])
        rows['opening_balances_usd']=rows['balance_cents']/100
        mapped=rows.groupby(['location','latitude','longitude'],as_index=False).agg(accounts=('accounts','sum'),opening_balances_usd=('opening_balances_usd','sum'))
        mapped['radius']=(mapped['accounts'] if metric=='Accounts' else mapped['opening_balances_usd']/3000).pow(.5)*3500
        st.pydeck_chart(pdk.Deck(map_style='https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
            initial_view_state=pdk.ViewState(latitude=float(rows.latitude.mean()),longitude=float(rows.longitude.mean()),zoom=5),
            layers=[pdk.Layer('ScatterplotLayer',mapped,get_position='[longitude, latitude]',get_radius='radius',radius_min_pixels=10,radius_max_pixels=60,get_fill_color=[8,127,128,175],pickable=True)],
            tooltip={'text':'{location}\nAccounts: {accounts}\nOpening balances USD: {opening_balances_usd}'}))
        st.caption('Fictional aggregated results at approximate city centers; no customer addresses. Basemap requires internet.')
        with st.expander('Geographic results table'):
            st.dataframe(rows[['location','channel','accounts','opening_balances_usd','exposures','as_of']],hide_index=True)
    with insight_col,st.container(border=True):
        st.subheader('Measurement')
        st.markdown('**Direct mail**\n\n60 days from mail/drop date.\n\n**Display**\n\n30 days from exposure.')
        if packet['readiness']['ready']:
            st.success('Attribution windows mature')
        else:
            st.error('Attribution incomplete')
        st.caption('Attributed outcomes do not establish causal lift or financial ROI.')
    with st.container(border=True):
        st.subheader('Compared with this client’s history')
        for result in packet['facts']['history']:
            if result['status']=='ok':
                m=result['metrics']['activation_rate']
                st.markdown(f"**{result['channel'].replace('_',' ').title()}** · {m['current']:.2%} activation rate vs {m['peer_median']:.2%} historical median · Rank **{m['rank']} of {m['total']}** including current · {m['peer_count']} comparable prior campaigns")
            else:
                st.info(f"{result['channel'].replace('_',' ').title()}: insufficient comparable same-client history.")
        st.caption('Same client, product and channel; earlier periods; mature, matching attribution and exposure definitions. Small cohorts are descriptive. No verified industry benchmark supplied.')
    st.subheader('Client presentation report')
    st.caption('Full-campaign report; map channel filters do not change campaign-wide goals or report scope.')
    if packet['readiness']['blockers']:
        st.error('Exports blocked: '+'; '.join(packet['readiness']['blockers']))
    if st.button('Generate client-facing report',type='primary',icon=':material/description:',disabled=not packet['readiness']['ready']):
        from campaign_hub.reporting.client_retrieval import retrieve_client_packet
        try:
            with st.spinner('Retrieving campaign evidence from Chroma and validating the report…'):
                st.session_state['client-packet']=retrieve_client_packet(service,cid,options)
        except (ValueError,RuntimeError) as error:
            st.session_state.pop('client-packet',None)
            st.error(str(error))
    saved=st.session_state.get('client-packet')
    if saved and saved['campaign_id']==cid and saved['corpus_hash']==service.corpus_hash and saved.get('evidence_mode')=='rag':
        errors=validate_packet(saved)
        if errors:
            st.error('Exports blocked: '+'; '.join(errors))
        else:
            st.success('Source reconciliation and narrative checks passed. Ready for analyst review.')
            html=export_html(saved)
            st.download_button('Download HTML presentation',html,f'{cid}-client-report.html','text/html',type='primary')
            st.caption('Open the downloaded HTML file in a browser. Comparison charts, insights and source evidence are embedded; no internet connection is needed to view it.')
            st.iframe(html,height=1000,alt='Client campaign performance presentation with comparison charts, insights and source citations')
            with st.expander('Validation and source version'):
                st.download_button('Download factual source packet',json.dumps(saved,indent=2),f'{cid}-source-packet.json','application/json')
                st.json({'corpus_hash':saved['corpus_hash'],'readiness':saved['readiness'],'as_of':saved['facts']['as_of'],
                    'evidence_mode':saved.get('evidence_mode'),'retrieval':saved.get('retrieval',{})})
    with st.expander('Analyst index management'):
        build_indexes(service)
