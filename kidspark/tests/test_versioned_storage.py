from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from kidspark.challenges import CHALLENGES, LEVELS, get_questions, question_bank
from kidspark.game import start_round, submit_answer, advance, completed_result
from kidspark.storage import save_attempt, load_attempts


def finish_round(round):
    for i, q in enumerate(round.questions):
        submit_answer(round, q.id, q.correct_index)
        if i < 4:
            advance(round)
    return completed_result(round)


class VersionedStorageTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.db = Path(self.folder.name) / 'results.sqlite3'

    def test_current_and_historical_rounds_coexist_and_retry(self):
        fixture = json.loads((Path(__file__).parent / 'fixtures/version1_answers.json').read_text())
        for challenge in CHALLENGES:
            for level in LEVELS:
                old = replace(start_round('Ava', challenge, level),
                              questions=get_questions(challenge, level), content_version='1')
                historical = finish_round(old)
                for answer in historical['answers']:
                    expected = fixture[answer['question_id']]
                    self.assertEqual(answer['selected_index'], expected['correct_index'])
                    self.assertEqual(answer['skill'], expected['skill'])
                self.assertTrue(save_attempt(self.db, historical))
                self.assertFalse(save_attempt(self.db, deepcopy(historical)))
                current = finish_round(start_round('Ava', challenge, level))
                self.assertTrue(save_attempt(self.db, current))
                self.assertFalse(save_attempt(self.db, deepcopy(current)))
        saved = load_attempts(self.db, 'Ava')
        self.assertEqual(len(saved), 12)
        self.assertEqual({r['content_version'] for r in saved}, {'1', '2'})
        self.assertTrue(all(r['score'] == 100 for r in saved))

    def test_duplicate_foreign_and_inconsistent_questions_rejected(self):
        result = finish_round(start_round('Ava', CHALLENGES[0], LEVELS[0]))
        first = result['answers'][0]
        alternate = next(q for q in question_bank(CHALLENGES[0], LEVELS[0], '2')
                         if q.objective == first['question_id'].split('-')[0] and q.id != first['question_id'])
        duplicate_objective = dict(question_id=alternate.id, skill=alternate.skill,
                                   selected_index=alternate.correct_index, correct=True)
        foreign = get_questions(CHALLENGES[0], LEVELS[1])[0]
        for replacement in [first, duplicate_objective,
                            dict(question_id=foreign.id, skill=foreign.skill, selected_index=foreign.correct_index, correct=True),
                            {**first, 'skill': 'Wrong skill'}, {**first, 'correct': False}]:
            changed = deepcopy(result)
            changed['answers'][1] = replacement
            with self.subTest(answer=replacement), self.assertRaises(ValueError):
                save_attempt(self.db, changed)
        changed = deepcopy(result)
        changed['content_version'] = '99'
        with self.assertRaises(ValueError):
            save_attempt(self.db, changed)
        self.assertEqual(load_attempts(self.db, 'Ava'), [])
