from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from kidspark.challenges import CHALLENGES, LEVELS
from kidspark.game import start_round, submit_answer, advance, completed_result
from kidspark.storage import save_attempt, load_attempts, load_best_scores


def result_for(nickname='Ava', challenge=CHALLENGES[0], level=LEVELS[0], correct=5):
    r = start_round(nickname, challenge, level)
    for i, q in enumerate(r.questions):
        submit_answer(r, q.id, q.correct_index if i < correct else (q.correct_index + 1) % 3)
        if i < 4:
            advance(r)
    return completed_result(r)


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'attempts.sqlite3'

    def test_idempotent_save_and_reopen(self):
        result = result_for(correct=3)
        self.assertTrue(save_attempt(self.path, result))
        self.assertFalse(save_attempt(self.path, deepcopy(result)))
        self.assertEqual(load_attempts(self.path, ' AVA '), [result])

    def test_nicknames_separate_and_sql_is_literal(self):
        for nickname in ['Ava', 'Ben', "x'; DROP TABLE attempts;--"]:
            result = result_for(nickname)
            save_attempt(self.path, result)
            self.assertEqual(load_attempts(self.path, nickname), [result])
        self.assertEqual(load_attempts(self.path, 'New student'), [])

    def test_conflicting_id_cannot_overwrite(self):
        result = result_for()
        save_attempt(self.path, result)
        changed = result_for('Ben')
        changed['attempt_id'] = result['attempt_id']
        with self.assertRaises(ValueError):
            save_attempt(self.path, changed)
        self.assertEqual(load_attempts(self.path, 'Ava'), [result])
        self.assertEqual(load_attempts(self.path, 'Ben'), [])

    def test_inconsistent_or_incomplete_results_rejected(self):
        result = result_for()
        for field, value in [('answers', result['answers'][:4]), ('score', 99),
                             ('accuracy', 10), ('elapsed_seconds', -1),
                             ('nickname_key', 'ben'), ('completed_at', 'not a date')]:
            changed = deepcopy(result)
            changed[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                save_attempt(self.path, changed)
        self.assertEqual(load_attempts(self.path, 'Ava'), [])

    def test_invalid_database_error_is_visible_to_caller(self):
        self.path.write_text('not a database')
        with self.assertRaises(Exception):
            save_attempt(self.path, result_for())

    def test_leaderboard_uses_best_scores_and_separate_levels(self):
        save_attempt(self.path, result_for('Ava', correct=2))
        save_attempt(self.path, result_for(' AVA ', correct=4))
        save_attempt(self.path, result_for('Ava', level=LEVELS[1], correct=5))
        save_attempt(self.path, result_for('Ben', challenge=CHALLENGES[1], correct=3))
        rows = load_best_scores(self.path, LEVELS[0])
        ava = next(row for row in rows if row['nickname_key'] == 'ava')
        self.assertEqual(ava['best_score'], 80)
        self.assertEqual(len(rows), 2)
        self.assertNotIn('answers', ava)
        self.assertEqual(load_best_scores(self.path, LEVELS[1])[0]['best_score'], 100)
