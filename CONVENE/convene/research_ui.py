"""Streamlit venue research, kept separate from synthetic plan estimates."""
import json

import httpx
import streamlit as st
from convene.venue_research import RESEARCH_CITY


def render_venue_research(base: str):
    # The city is fixed, including sessions opened before the geographic scope changed.
    st.session_state['research_city'] = RESEARCH_CITY
    previous = st.session_state.get('venue_research')
    if previous and previous.get('query', {}).get('city') != RESEARCH_CITY:
        st.session_state.pop('venue_research', None)
    st.divider()
    st.header('Research San Antonio venues')
    st.caption('Discover venues or paste their public website URLs. Search and AI extraction use paid API services. '
               'Only city and guest count go to search; fetched page text goes to OpenAI. '
               'These results are separate from synthetic demo estimates.')
    with st.form('venue_research_form'):
        city = st.text_input('City for venue research', key='research_city', disabled=True)
        st.caption('San Antonio, Texas only. Candidates need a published local address; nearby cities are excluded.')
        guests = st.number_input('Guests for venue research', min_value=1, max_value=10000,
                                 value=40, key='research_guests')
        discover = st.checkbox('Discover venues automatically', value=True, key='research_discover')
        urls_text = st.text_area('Venue website URLs (optional, one per line, maximum five)', key='research_urls',
                                help='Turn off automatic discovery to research only the URLs you supply.')
        submitted = st.form_submit_button('Research venues', key='research_submit')
    if submitted:
        # Do not leave an older result displayed as if it matched the new request.
        st.session_state.pop('venue_research', None)
        urls = [line.strip() for line in urls_text.splitlines() if line.strip()]
        if not city.strip():
            st.error('Enter a city for venue research.')
        elif len(urls) > 5:
            st.error('Supply at most five venue URLs.')
        elif not discover and not urls:
            st.error('Supply venue URLs or enable automatic discovery.')
        else:
            try:
                with st.spinner('Reading public venue pages and checking supporting evidence...'):
                    response = httpx.post(base + '/venues/research', json={
                        'city': city, 'guests': guests, 'urls': urls, 'discover': discover}, timeout=240)
                    response.raise_for_status()
                    st.session_state['venue_research'] = response.json()
            except httpx.HTTPStatusError as error:
                detail = error.response.json().get('detail', 'Venue research failed.')
                st.error(f'Venue research: {detail}')
            except httpx.HTTPError:
                st.error('Could not reach venue research. Check that the FastAPI service is running.')
    result = st.session_state.get('venue_research')
    if result is None:
        return
    query = result['query']
    st.caption(f"Research request: {query['city']}, {query['guests']} guests")
    st.info(result['disclaimer'])
    for error in result['errors']:
        st.warning(f"{error.get('url') or 'Discovery'}: {error['error']}")
    if not result['candidates']:
        st.info('No venue details extracted. Try a public venue event-space page.')
    for venue in result['candidates']:
        details = venue['details']
        st.subheader(details['name']['value'])
        st.link_button('View source website', venue['source_url'])
        st.caption(f"Retrieved: {venue['retrieved_at']} | Availability: unconfirmed | Budget fit: unknown")
        for field, label in [('address', 'Address'), ('capacity', 'Capacity / room layout'),
                             ('contact', 'Business contact'), ('pricing', 'Published pricing')]:
            fact = details[field]
            missing = 'Quote required' if field == 'pricing' else 'Not published / not extracted'
            st.text(f"{label}: {fact['value'] if fact else missing}")
        st.text('Amenities: ' + ('; '.join(fact['value'] for fact in details['amenities']) or 'Not published / not extracted'))
        with st.expander('Supporting page excerpts'):
            for field in ('name', 'address', 'capacity', 'contact', 'pricing'):
                if details[field]:
                    st.text(f"{field.capitalize()}: {details[field]['evidence']}")
            for fact in details['amenities']:
                st.text(f"Amenity: {fact['evidence']}")
        for warning in venue['warnings']:
            st.warning(warning)
    st.download_button('Download venue research JSON', json.dumps(result, indent=2),
                       'convene-venue-research.json', 'application/json', key='research_download')
