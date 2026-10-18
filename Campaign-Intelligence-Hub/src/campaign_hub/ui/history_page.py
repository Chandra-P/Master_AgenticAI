import pandas as pd
import streamlit as st
from campaign_hub.ui.resources import source_viewer,select_campaign


def show(service,options):
    st.header('Historical campaign comparison')
    st.markdown('See where a campaign stands among earlier campaigns of the same product type, measured within the same channel and attribution rules.')
    st.caption('Direct mail: 60 days from mail/drop date. Display: 30 days from exposure. Only fully observed windows qualify.')
    cid=select_campaign(service,'history','Campaign to benchmark')
    scope_label=st.selectbox('Comparison group',['Same-client historical campaigns','Synthetic peer reference — not an industry benchmark'])
    scope='client' if scope_label.startswith('Same-client') else 'peer_reference'
    if scope=='peer_reference':
        st.warning('Fictional cross-client examples only. No verified industry benchmark is available.')
    with st.form('history-form'):
        submitted=st.form_submit_button('Compare with historical campaigns',type='primary')
    if submitted:
        try:
            with st.spinner('Retrieving comparable historical evidence and calculating standing…'):
                st.session_state['historical-comparison']=service.compare_with_history(cid,options,scope=scope)
                st.session_state['historical-scope']=scope
        except Exception as error:
            st.error(str(error))
    comparison=st.session_state.get('historical-comparison')
    if comparison and (comparison['campaign_id']!=cid or st.session_state.get('historical-scope')!=scope):
        comparison=None
    if comparison and comparison.get('corpus_hash')!=service.corpus_hash:
        st.session_state.pop('historical-comparison',None)
        comparison=None
    if not comparison:
        st.info('Choose a campaign to see channel-specific ranks, peer medians, and cited evidence.')
        return
    st.subheader(f"{comparison['campaign_id']} · {comparison['period']}")
    for result in comparison['comparisons']:
        st.subheader('Direct mail' if result['channel']=='direct_mail' else 'Display')
        if result['status']!='ok':
            st.info('No mature compatible historical cohort. This campaign cannot be ranked reliably.')
            continue
        st.caption(result['cohort_rule'])
        st.markdown('**Historical peers:** '+', '.join(result['peer_ids']))
        if result['small_sample']:
            st.warning(f"Only {result['peer_count']} comparable historical campaign(s). Treat this as a descriptive comparison, not a broad benchmark.")
        rows=[]
        for name,m in result['metrics'].items():
            label='Activation rate' if name=='activation_rate' else 'Cost per activation (USD)'
            current=f"{m['current']:.2%}" if name=='activation_rate' else f"${m['current']:.2f}"
            peer=f"{m['peer_median']:.2%}" if name=='activation_rate' else f"${m['peer_median']:.2f}"
            rows.append({'Metric':label,'Current':current,'Peer median':peer,'Rank (1 = best)':f"{m['rank']} of {m['total']}",
                         'Comparable peers':m['peer_count'],'Performance percentile':round(m['percentile'],1),'Position':m['position']})
            if m['small_sample'] and m['peer_count']!=result['peer_count']:
                st.warning(f"{label}: only {m['peer_count']} peers have a defined value. {m['excluded_undefined_cost_peers']} zero-conversion peers were excluded from this cost metric; the cost benchmark has a small sample.")
        st.dataframe(pd.DataFrame(rows),alt='Channel performance compared with compatible historical campaigns')
        for name,m in result['metrics'].items():
            rate=name=='activation_rate'
            st.markdown('**Activation rate (%) — higher is better**' if rate else '**Cost per activation (USD) — lower is better**')
            values={**m['peer_values'],comparison['campaign_id']+' (current)':m['current']}
            chart=pd.DataFrame([{'Campaign':k,'Value':v*100 if rate else v} for k,v in values.items()])
            st.bar_chart(chart,x='Campaign',y='Value',alt='Current campaign within the compatible historical performance distribution')
    st.caption('Percentile = proportion of peers outperformed, with half credit for ties. Lower acquisition cost is better. No cross-channel rate pooling or causal-lift claims.')
    source_viewer(service,comparison['evidence'])
