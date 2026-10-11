import unittest
from kidspark.challenges import CHALLENGES, LEVELS
from kidspark.game import normalize_nickname, start_round, submit_answer, advance, completed_result


class GameTests(unittest.TestCase):
    def test_nickname_identity(self):
        self.assertEqual(normalize_nickname('  Ａva   Star  '), ('ava star', 'Ava Star'))
        for value in ['', '   ', 'x' * 33, 'A\x00B']:
            with self.assertRaises(ValueError):
                normalize_nickname(value)

    def test_unknown_round(self):
        with self.assertRaises(ValueError):
            start_round('Ava', 'Missing', LEVELS[0])

    def test_answer_guards(self):
        r = start_round('Ava', CHALLENGES[0], LEVELS[0])
        q = r.questions[0]
        self.assertFalse(advance(r))
        self.assertFalse(submit_answer(r, r.questions[1].id, 0))
        for value in [None, -1, 3, True, '0']:
            with self.assertRaises(ValueError):
                submit_answer(r, q.id, value)
        self.assertTrue(submit_answer(r, q.id, q.correct_index))
        self.assertFalse(submit_answer(r, q.id, (q.correct_index + 1) % 3))
        self.assertEqual(len(r.answers), 1)
        self.assertTrue(advance(r))
        self.assertFalse(submit_answer(r, q.id, 0))

    def test_mixed_result_and_frozen_completion(self):
        r = start_round('Ava', CHALLENGES[0], LEVELS[0])
        with self.assertRaises(ValueError):
            completed_result(r)
        for i, q in enumerate(r.questions):
            choice = q.correct_index if i < 3 else (q.correct_index + 1) % 3
            submit_answer(r, q.id, choice)
            if i < 4:
                self.assertTrue(advance(r))
        result = completed_result(r)
        self.assertEqual((result['score'], result['accuracy'], result['correct_count']), (60, 60, 3))
        self.assertEqual(len(result['answers']), 5)
        self.assertGreaterEqual(result['elapsed_seconds'], 0)
        self.assertEqual(completed_result(r), result)
        self.assertFalse(advance(r))
        self.assertFalse(submit_answer(r, r.questions[-1].id, 0))
        result['answers'].clear()
        self.assertEqual(len(completed_result(r)['answers']), 5)

    def test_new_round_has_new_id(self):
        a = start_round('Ava', CHALLENGES[0], LEVELS[0])
        b = start_round('Ava', CHALLENGES[0], LEVELS[0])
        self.assertNotEqual(a.attempt_id, b.attempt_id)
