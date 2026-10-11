"""Application layout and profile-scoped session orchestration."""
import sqlite3
import streamlit as st
from kidspark.config import database_path
from kidspark.game import normalize_nickname
from kidspark.storage import load_attempts
from kidspark.ui.play import render_play
from kidspark.ui.progress import render_progress


def main() -> None:
    st.set_page_config(page_title='KidSpark', page_icon='🌟', layout='wide')
    st.title('🌟 KidSpark')
    st.write('Small choices. Real-life superpowers.')
    st.caption('For middle and high school · Five decisions · Your pace')
    nickname = st.text_input('Your nickname', key='nickname', help='Choose a distinct nickname and use it again to find your saved results.')
    st.caption('Nicknames identify profiles, not private accounts. Pick a nickname without personal information; identical nicknames share results.')
    st.caption('The leaderboard shows nicknames and best challenge scores. Use a nickname you are comfortable sharing.')
    try:
        key, nickname = normalize_nickname(nickname)
    except ValueError as exc:
        key, nickname = None, ''
        if st.session_state['nickname'].strip():
            st.warning(str(exc))
    if st.session_state.get('profile_key') != key:
        st.session_state['round'] = None
        st.session_state['profile_key'] = key
        st.session_state.pop('answer_error', None)
    st.session_state.setdefault('round', None)
    path = database_path()
    play, progress = st.tabs(['Play Challenges', 'My Progress'])
    with play:
        render_play(nickname, path)
    with progress:
        if nickname:
            try:
                attempts = load_attempts(path, nickname)
            except (OSError, sqlite3.Error, ValueError) as exc:
                st.error(f'Your saved progress is unavailable right now. Try again after checking storage: {exc}')
                return
        else:
            attempts = []
        render_progress(nickname, st.session_state.get('level', 'Middle school'), attempts, path)
