"""One-decision-at-a-time play with feedback and save retry handling."""
from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st
from kidspark.challenges import CHALLENGES, LEVELS, STORIES, TAKEAWAYS
from kidspark.game import normalize_nickname, start_round, submit_answer, advance, completed_result
from kidspark.storage import save_attempt


def _start() -> None:
    try:
        st.session_state['round'] = start_round(st.session_state['nickname'], st.session_state['challenge'], st.session_state['level'])
        st.session_state.pop('answer_error', None)
    except ValueError as exc:
        st.session_state['answer_error'] = str(exc)


def _reset() -> None:
    st.session_state['round'] = None
    st.session_state.pop('answer_error', None)


def _submit(attempt_id: str, question_id: str, widget_key: str) -> None:
    active = st.session_state.get('round')
    try:
        key, _ = normalize_nickname(st.session_state['nickname'])
        if not active or active.attempt_id != attempt_id or active.nickname_key != key:
            return
        question = active.questions[active.cursor]
        selected = st.session_state.get(widget_key)
        if selected not in question.choices:
            raise ValueError('Choose an answer first. Take your time!')
        submit_answer(active, question_id, question.choices.index(selected))
        st.session_state.pop('answer_error', None)
    except ValueError as exc:
        st.session_state['answer_error'] = str(exc)


def _next(attempt_id: str) -> None:
    active = st.session_state.get('round')
    if active and active.attempt_id == attempt_id:
        advance(active)


def _save(active, path: Path) -> None:
    if st.session_state.get('saved_id') == active.attempt_id:
        st.success('Saved! Open My Progress to see this round.')
        return
    retry = False
    if st.session_state.get('save_tried_id') == active.attempt_id:
        st.error('Your round is complete, but it has not been saved yet. Keep this page open and retry when storage is available.')
        retry = st.button('Retry save', key='retry_save')
    if st.session_state.get('save_tried_id') != active.attempt_id or retry:
        st.session_state['save_tried_id'] = active.attempt_id
        try:
            save_attempt(path, completed_result(active))
            st.session_state['saved_id'] = active.attempt_id
            if retry:
                st.rerun()
            st.success('Saved! Open My Progress to see this round.')
        except (OSError, sqlite3.Error, ValueError):
            st.error('We could not save your round. Your result is still here; retry before leaving or changing nickname.')
            if not retry:
                st.button('Retry save', key='retry_save')


def render_play(nickname: str, db_path: Path) -> None:
    active = st.session_state.get('round')
    locked = bool(active and not active.complete)
    level_column, challenge_column = st.columns(2)
    with level_column:
        st.selectbox('School level', LEVELS, key='level', disabled=locked)
    with challenge_column:
        challenge = st.selectbox('Choose your challenge', CHALLENGES, key='challenge', disabled=locked)
    if challenge not in CHALLENGES:
        st.warning('Choose one of the three challenges.')
        return
    if not active:
        icon, title, story = STORIES[challenge]
        with st.container(border=True):
            st.subheader(f'{icon} {title}')
            st.write(story)
            st.write('Five small decisions. Hints are free. A calculator or scratch paper is welcome.')
            st.caption('Practice rounds vary the amounts or pretend messages, with one decision per learning goal. Your first decision is a gentle start; the others can change order.')
            st.caption('Completed rounds are saved. Unfinished rounds reset when you leave or change nickname.')
            if not nickname:
                st.info('Add your nickname above to start your first adventure.')
            st.button('Start round', key='start', type='primary', disabled=not bool(nickname), on_click=_start)
        if st.session_state.get('answer_error'):
            st.warning(st.session_state['answer_error'])
        return
    st.caption(f'{active.challenge} · {active.level} · This round belongs to {active.nickname}')
    st.progress(len(active.answers) / 5)
    st.caption(' '.join('●' if i < len(active.answers) else '○' for i in range(5)) + f'  {len(active.answers)} of 5 decisions answered')
    q = active.questions[active.cursor]
    answered = len(active.answers) > active.cursor
    with st.container(border=True):
        st.subheader(f'Decision {active.cursor + 1} of 5')
        st.text(q.scenario)
        st.markdown(f'**{q.prompt}**')
        answer_key = f'answer_{active.attempt_id}_{q.id}'
        st.radio('What would you choose?', q.choices, index=None, key=answer_key, disabled=answered)
        if not answered:
            if st.checkbox('Show hint', key='hint'):
                st.info(q.hint)
            st.button('Submit answer', key='submit', type='primary', on_click=_submit, args=(active.attempt_id, q.id, answer_key))
            if st.session_state.get('answer_error'):
                st.warning(st.session_state['answer_error'])
        else:
            answer = active.answers[active.cursor]
            if answer['correct']:
                st.success('Nice thinking! You found a helpful choice. +20 points')
            else:
                st.info('Good try! Let’s look at the clue together.')
            st.text(q.explanation)
            st.caption(f'Correct choice: {q.choices[q.correct_index]}')
            if not active.complete:
                st.button('Next decision', key='next', type='primary', on_click=_next, args=(active.attempt_id,))
    if active.complete:
        result = completed_result(active)
        st.subheader('🎉 Adventure complete!')
        st.write(f"You made all five decisions: {result['score']} / 100 points · {result['accuracy']:.0f}% accuracy.")
        st.info(TAKEAWAYS[active.challenge])
        st.caption(f"Completed at {result['completed_at']} (UTC) · {result['elapsed_seconds']:.0f} seconds. Time never affects your score.")
        _save(active, db_path)
        with st.expander('Your round in review'):
            st.dataframe(pd.DataFrame([{'Decision': i + 1, 'Skill': question.skill,
                                        'Your choice': question.choices[answer['selected_index']],
                                        'Result': 'Correct' if answer['correct'] else 'Keep practicing'}
                                       for i, (question, answer) in enumerate(zip(active.questions, active.answers))]), hide_index=True)
        st.button('Play another round', key='another', on_click=_reset, disabled=st.session_state.get('saved_id') != active.attempt_id)
    else:
        st.button('Start over (discard this round)', key='restart', on_click=_reset)
