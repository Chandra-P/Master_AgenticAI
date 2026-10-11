import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
import pandas as pd
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from kidspark.challenges import CHALLENGES, LEVELS, get_questions
from kidspark.storage import load_attempts

ROOT = Path(__file__).resolve().parents[1]


class LearningAppTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.db = Path(self.folder.name) / 'test.sqlite3'
        env = patch.dict(os.environ, {'KIDSPARK_DB_PATH': str(self.db)})
        env.start()
        self.addCleanup(env.stop)

    def app(self, nickname='Ava'):
        app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=15).run()
        self.assertFalse(app.exception)
        app.text_input(key='nickname').set_value(nickname).run()
        self.assertFalse(app.exception)
        return app

    def start(self, app, challenge=CHALLENGES[0], level=LEVELS[0]):
        app.selectbox(key='level').select(level).run()
        app.selectbox(key='challenge').select(challenge).run()
        app.button(key='start').click().run()
        self.assertFalse(app.exception)

    def finish(self, app, challenge=CHALLENGES[0], level=LEVELS[0], correct=5):
        self.start(app, challenge, level)
        for i, q in enumerate(app.session_state['round'].questions):
            self.assertIsNone(app.radio[0].value)
            app.radio[0].set_value(q.choices[q.correct_index if i < correct else (q.correct_index + 1) % 3]).run()
            app.button(key='submit').click().run()
            self.assertFalse(app.exception)
            self.assertTrue(any(q.explanation in text.value for text in app.text))
            app.run()
            self.assertEqual(len(app.session_state['round'].answers), i + 1)
            if i < 4:
                app.button(key='next').click().run()
        return app

    def test_empty_state_and_missing_choice(self):
        app = self.app()
        self.assertEqual([m.value for m in app.metric[:4]], ['0', '0 / 3', '0', '0%'])
        self.assertTrue(any('first' in x.value.lower() for x in app.info))
        self.start(app)
        app.button(key='submit').click().run()
        self.assertTrue(app.warning)
        self.assertEqual(len(app.session_state['round'].answers), 0)
        self.assertEqual(load_attempts(self.db, 'Ava'), [])

    def test_all_six_rounds_save_exactly_once(self):
        for challenge in CHALLENGES:
            for level in LEVELS:
                nickname = f'{challenge} {level}'[:32]
                with self.subTest(challenge=challenge, level=level):
                    app = self.finish(self.app(nickname), challenge, level)
                    saved = load_attempts(self.db, nickname)
                    self.assertEqual(len(saved), 1)
                    self.assertEqual((saved[0]['score'], saved[0]['accuracy']), (100, 100))
                    app.run()
                    self.assertEqual(len(load_attempts(self.db, nickname)), 1)
                    self.assertEqual([m.value for m in app.metric[:4]], ['1', '1 / 3', '100', '100%'])

    def test_mixed_round_restart_and_nickname_separation(self):
        app = self.finish(self.app(), correct=3)
        self.assertEqual([m.value for m in app.metric[:4]], ['1', '1 / 3', '60', '60%'])
        history = next(d.value for d in app.dataframe if 'Challenge' in d.value.columns)
        self.assertEqual(history.iloc[0]['Score'], 60)
        self.assertEqual(history.iloc[0]['Accuracy (%)'], 60)
        saved = load_attempts(self.db, 'Ava')[0]
        expected = pd.Timestamp(saved['completed_at']).tz_convert('America/Chicago').tz_localize(None)
        self.assertEqual(history.iloc[0]['Completed (Chicago time)'], expected)
        app.text_input(key='nickname').set_value('Ben').run()
        self.assertEqual([m.value for m in app.metric[:4]], ['0', '0 / 3', '0', '0%'])
        fresh = self.app(' AVA ')
        self.assertEqual([m.value for m in fresh.metric[:4]], ['1', '1 / 3', '60', '60%'])

    def test_hint_no_penalty_and_nickname_switch_abandons_round(self):
        app = self.app()
        self.start(app)
        app.checkbox(key='hint').check().run()
        q = app.session_state['round'].questions[0]
        self.assertTrue(any(q.hint in x.value for x in app.info))
        app.radio[0].set_value(q.choices[q.correct_index]).run()
        app.button(key='submit').click().run()
        self.assertTrue(app.session_state['round'].answers[0]['correct'])
        app.text_input(key='nickname').set_value('Ben').run()
        self.assertIsNone(app.session_state['round'])
        self.assertEqual(load_attempts(self.db, 'Ava'), [])
        self.finish(app)
        self.assertEqual(load_attempts(self.db, 'Ben')[0]['score'], 100)

    def test_start_over_and_new_round_use_fresh_choices(self):
        app = self.app()
        self.start(app)
        first = app.session_state['round'].attempt_id
        app.radio[0].set_value(app.radio[0].options[0]).run()
        app.button(key='restart').click().run()
        self.start(app)
        self.assertNotEqual(first, app.session_state['round'].attempt_id)
        self.assertIsNone(app.radio[0].value)

    def test_save_failure_then_retry_preserves_completion(self):
        with patch('kidspark.ui.play.save_attempt', side_effect=sqlite3.OperationalError('Unavailable')):
            app = self.finish(self.app())
            self.assertTrue(app.error)
            self.assertFalse(app.exception)
            completion = app.session_state['round'].completed_at
            self.assertEqual(load_attempts(self.db, 'Ava'), [])
        app.button(key='retry_save').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(load_attempts(self.db, 'Ava')[0]['completed_at'], completion)
        app.run()
        self.assertEqual(len(load_attempts(self.db, 'Ava')), 1)

    def test_invalid_nickname_cannot_start(self):
        app = self.app(' ')
        self.assertTrue(app.button(key='start').disabled)
        app.text_input(key='nickname').set_value('x' * 33).run()
        self.assertTrue(app.warning)
        self.assertTrue(app.button(key='start').disabled)

    def test_different_challenges_appear_in_leaderboard(self):
        for nickname, challenge, correct in [('Demo Ava', CHALLENGES[0], 4),
                                              ('Demo Ben', CHALLENGES[1], 3),
                                              ('Demo Ava', CHALLENGES[2], 5),
                                              ('Demo Ava', CHALLENGES[1], 5)]:
            self.finish(self.app(nickname), challenge=challenge, correct=correct)
        app = self.app('Demo Ava')
        app.checkbox(key='show_leaderboard').check().run()
        board = next(d.value for d in app.dataframe if 'Rank' in d.value.columns)
        self.assertEqual(board['Nickname'].tolist(), ['Demo Ava'])
        self.assertEqual(board['Best points'].tolist(), [280])
        app.selectbox(key='board_challenge').select(CHALLENGES[1]).run()
        board = next(d.value for d in app.dataframe if 'Rank' in d.value.columns)
        self.assertEqual(board['Nickname'].tolist(), ['Demo Ava', 'Demo Ben'])
        app.selectbox(key='level').select(LEVELS[1]).run()
        self.assertTrue(any('leaderboard' in info.value.lower() for info in app.info))
        self.assertFalse(app.exception)

    def test_rankings_default_hidden_without_query(self):
        with patch('kidspark.ui.progress.load_best_scores', side_effect=AssertionError('Hidden rankings must not query')):
            app = self.app()
            self.assertFalse(app.exception)
            self.assertFalse(app.checkbox(key='show_leaderboard').value)
            self.assertFalse(any('Rank' in d.value.columns for d in app.dataframe))

    def test_negative_change_is_visible_without_erasing_best(self):
        from test_storage import result_for
        from kidspark.storage import save_attempt
        for correct in (4, 5, 3):
            save_attempt(self.db, result_for('Compare', correct=correct))
        app = self.app('Compare')
        self.assertTrue(any('Latest − first: -20 points' in c.value for c in app.caption))
        self.assertTrue(any('Latest: 60' in c.value and 'Best: 100' in c.value for c in app.caption))

    def test_completion_badges_and_personal_comparisons(self):
        app = self.finish(self.app('Explorer'), correct=0)
        self.assertTrue(any('Smart Shopping completed' in s.value for s in app.success))
        app.checkbox(key='show_leaderboard').check().run()
        self.assertTrue(any('2 more' in i.value for i in app.info))
        self.finish(self.app('Explorer'), correct=5)
        app = self.finish(self.app('Explorer'), correct=3)
        self.assertTrue(any('First: 0' in c.value and 'Latest: 60' in c.value and 'Best: 100' in c.value for c in app.caption))
        for challenge in CHALLENGES[1:]:
            self.finish(self.app('Explorer'), challenge=challenge, correct=0)
        fresh = self.app('Explorer')
        self.assertTrue(any('Explorer badge' in s.value for s in fresh.success))
        fresh.selectbox(key='level').select(LEVELS[1]).run()
        self.assertFalse(any('completed' in s.value or 'Explorer badge' in s.value for s in fresh.success))
