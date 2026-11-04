import json
import os
from datetime import date
import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title='CONVENE', page_icon='🎉', layout='wide')
st.title('CONVENE')
st.caption('Six agents. One event plan. Synthetic estimates — no bookings or payments.')
base = os.getenv('CONVENE_API_URL', 'http://127.0.0.1:8000').rstrip('/')
with st.form('brief'):
    title = st.text_input('Event title', 'AI course celebration')
    city = st.selectbox('City (synthetic vendor catalog)', ['Seattle', 'New York'])
    guests = st.number_input('Guests', min_value=1, max_value=10000, value=40)
    budget = st.number_input('Total budget (USD)', min_value=1.0, value=5000.0)
    event_date = st.date_input('Event date', value=date(2026, 11, 5))
    duration = st.slider('Duration in hours', 1, 12, 4)
    preferences = st.text_area('Preferences', 'Accessible venue, vegetarian food')
    submitted = st.form_submit_button('Create event plan')
if submitted:
    try:
        with st.spinner('The six agents are preparing your plan…'):
            response = httpx.post(base + '/plans', json=dict(title=title, city=city, guests=guests,
                budget=budget, event_date=event_date.isoformat(), duration_hours=duration,
                preferences=preferences), timeout=120)
            response.raise_for_status()
            st.session_state['plan'] = response.json()
    except httpx.HTTPError as error:
        st.error(f'Could not create plan. Check the API and configuration. {error}')
if 'plan' in st.session_state:
    plan = st.session_state['plan']
    st.subheader(plan['brief']['title'])
    st.write(' → '.join(plan['agent_steps']))
    st.metric('Estimated vendor total', f"${plan['estimated_total']:,.2f}")
    st.info(f"Mode: {plan['mode']} · {plan['review']['status']}")
    st.subheader('Vendor suggestions')
    st.dataframe(plan['vendors'])
    st.subheader('Schedule (proposed local time, starts at 10:00)')
    st.table(plan['schedule'])
    st.subheader('Creative ideas')
    st.write(plan['creative'])
    for warning in plan['review']['warnings']:
        st.warning(warning)
    st.download_button('Download plan JSON', json.dumps(plan, indent=2), 'convene-plan.json', 'application/json')
if st.button('Load saved plans'):
    try:
        response = httpx.get(base + '/plans', timeout=10)
        response.raise_for_status()
        st.json(response.json())
    except httpx.HTTPError as error:
        st.error(f'Could not load plans: {error}')
