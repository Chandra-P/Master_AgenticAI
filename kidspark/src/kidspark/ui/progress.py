"""Personal dashboard using saved attempts, never fictional import scores."""
import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path
import sqlite3
from kidspark.challenges import CHALLENGES, STORIES
from kidspark.game import normalize_nickname
from kidspark.storage import load_best_scores
from kidspark.progress import summarize_attempts, skill_accuracy, suggest_challenge, challenge_leaderboard, challenge_progress


def render_progress(nickname: str, level: str, attempts: list[dict], db_path: Path) -> None:
    st.subheader('🌱 My Progress')
    st.write('See what you have tried, what you are learning, and where to go next.')
    if nickname:
        st.text(f'Profile: {nickname}')
    summary = summarize_attempts(attempts)
    values = [('🎮 Rounds finished', str(summary['rounds'])),
              ('🧭 Adventures explored', f"{summary['challenges']} / 3"),
              ('⭐ Points earned', str(summary['score'])),
              ('🎯 Answers correct', f"{summary['accuracy']:.0f}%")]
    for column, (label, value) in zip(st.columns(4), values):
        with column, st.container(border=True):
            st.metric(label, value)
    st.caption('Your personal totals include both school levels. Every finished round counts here.')
    st.subheader('Your adventure collection')
    cards = challenge_progress(attempts, level)
    completed = sum(bool(card['rounds']) for card in cards)
    st.caption(f'{level} collection: {completed} of 3 completion badges. Finishing earns a badge at any score.')
    if completed == 3:
        st.success(f'🧭 Explorer badge: you completed all three {level.lower()} adventures!')
    for column, card in zip(st.columns(3), cards):
        name = card['challenge']
        icon, title, _ = STORIES[name]
        with column, st.container(border=True):
            st.markdown(f'### {icon} {name}')
            st.caption(title)
            if card['rounds']:
                best = card['best']
                st.success(f'🏅 {name} completed')
                st.write(f'Best round: **{best} / 100**')
                st.progress(best / 100)
                st.caption(f"First: {card['first']} / 100 · Latest: {card['latest']} / 100 · Best: {best} / 100")
                st.caption(f"{card['rounds']} rounds finished · {level}")
                change = card['change']
                if change is not None:
                    st.caption(f'Latest − first: {change:+d} points')
                if change is None:
                    st.caption('Try another round to compare with your first score.')
                elif change > 0:
                    st.caption(f'Your latest score is {change} points above your first. Keep practicing!')
                elif change < 0:
                    st.caption('Scores can vary with practice. Your best result is still here; hints are always free.')
                else:
                    st.caption('Your latest score matches your first. Try explaining your choices as you practice.')
            else:
                st.write('Ready to explore!')
                st.progress(0)
                st.caption(f'Your first {level.lower()} round is waiting.')
    challenge, reason = suggest_challenge(attempts, level)
    with st.container(border=True):
        st.subheader(f'✨ Try next: {challenge}')
        st.write(reason)
        st.caption('Choose this adventure in Play Challenges. Take your time—hints are free.')
    if not attempts:
        st.info('Your first adventure starts in Play Challenges. Finish five decisions and your saved result will appear here!')
    else:
        skills = skill_accuracy(attempts)
        history = pd.DataFrame([{'Challenge': a['challenge'], 'School level': a['level'],
                                 'Score': a['score'], 'Accuracy (%)': a['accuracy'],
                                 'Completed (Chicago time)': pd.to_datetime(a['completed_at'], utc=True).tz_convert('America/Chicago').tz_localize(None),
                                 'Duration (seconds)': round(a['elapsed_seconds'], 1)} for a in attempts])
        left, right = st.columns(2)
        with left, st.container(border=True):
            st.subheader('🧠 Skills I am building')
            st.caption('Each bar shows how many of your answers were correct. All your saved rounds are included.')
            chart = px.bar(skills, x='accuracy', y='skill', orientation='h',
                           text=skills.accuracy.map(lambda x: f'{x:.0f}%'),
                           custom_data=['correct', 'total'], color='skill',
                           color_discrete_sequence=['#7c3aed', '#059669', '#2563eb', '#db2777', '#b45309', '#0891b2', '#6d28d9'],
                           labels={'accuracy': 'Correct decisions (%)', 'skill': 'Skill'})
            chart.update_layout(xaxis_range=[0, 110], showlegend=False, height=340, template='plotly_white',
                                yaxis_title=None, margin=dict(l=0, r=15, t=10, b=0))
            chart.update_traces(hovertemplate='%{y}: %{customdata[0]} of %{customdata[1]} correct<extra></extra>')
            st.plotly_chart(chart, config={'displayModeBar': False})
        with right, st.container(border=True):
            st.subheader('📈 My scores over time')
            st.caption('Each dot is a finished round. Trying again is part of learning.')
            chart = px.line(history, x='Completed (Chicago time)', y='Score', markers=True,
                            hover_data=['Challenge', 'School level', 'Accuracy (%)'], color_discrete_sequence=['#059669'])
            chart.update_traces(line=dict(width=3), marker=dict(size=11))
            chart.update_layout(yaxis_range=[-5, 105], height=340, template='plotly_white',
                                yaxis_title='Points out of 100', margin=dict(l=0, r=15, t=10, b=0))
            chart.update_xaxes(title='Day and time (Chicago)', tickformat='%b %d<br>%I:%M %p', hoverformat='%b %d, %Y %I:%M %p')
            st.plotly_chart(chart, config={'displayModeBar': False})
            st.caption('Hover over a dot for the challenge and school level. Dates use Chicago time, including daylight saving changes.')
        with st.expander('📚 My saved rounds', expanded=False):
            st.dataframe(history, hide_index=True)
            st.caption(f"You answered {summary['correct']} of {summary['total']} decisions correctly. Each decision counts equally.")
    st.caption('Learning comes first. Rankings are optional to view. Saved nicknames and best scores remain eligible for the shared leaderboard even when you hide it.')
    if st.checkbox('Show leaderboard', key='show_leaderboard', value=False):
        render_leaderboard(nickname, level, db_path, completed)


def render_leaderboard(nickname: str, level: str, db_path: Path, completed: int = 0) -> None:
    st.subheader('🏆 Challenge leaderboard')
    st.caption(f'{level} only · Your best round per challenge counts. Repeat play can improve a score, but cannot add extra points.')
    selected = st.selectbox('Leaderboard challenge', ('All challenges', *CHALLENGES), key='board_challenge')
    if selected == 'All challenges':
        st.caption('Overall rankings compare students who finished all three adventures at this school level. Equal totals share a rank.')
        if nickname and completed < 3:
            st.info(f'Finish {3 - completed} more adventure(s) at {level.lower()} level to join the overall leaderboard. You can view your individual challenge ranking now.')
    try:
        board = challenge_leaderboard(load_best_scores(db_path, level), None if selected == 'All challenges' else selected)
    except (OSError, sqlite3.Error, ValueError):
        st.info('The leaderboard is unavailable right now. Your personal progress is shown above.')
        return
    if board.empty:
        st.info('The overall leaderboard is waiting for someone to finish all three adventures at this school level!' if selected == 'All challenges' else 'The leaderboard is ready for its first finished challenge at this school level!')
        return
    maximum = 300 if selected == 'All challenges' else 100
    for column, (_, row) in zip(st.columns(3), board.head(3).iterrows()):
        with column, st.container(border=True):
            medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(row['Rank'], '⭐')
            st.markdown(f"### {medal} Rank {row['Rank']}")
            st.text(row['Nickname'])
            st.write(f"**{row['Best points']} / {maximum} points**")
    if nickname:
        key, _ = normalize_nickname(nickname)
        mine = board[board.Nickname.map(lambda name: normalize_nickname(name)[0] == key)]
        if not mine.empty:
            st.caption(f"Your place: {mine.iloc[0]['Rank']} · Best points: {mine.iloc[0]['Best points']}")
    st.dataframe(board, hide_index=True, column_config={
        'Best points': st.column_config.ProgressColumn('Best points', min_value=0, max_value=maximum, format='%d'),
    })
    st.caption('All-challenge points add your best score in each of the three adventures. Equal points and challenge counts share a rank. Nicknames and best scores are visible here; individual answer histories stay in My Progress.')
