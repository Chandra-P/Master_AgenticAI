import unittest

from kidspark.challenges import CHALLENGES, LEVELS, get_questions


class ChallengeTests(unittest.TestCase):
    def test_all_rounds_have_five_valid_questions(self):
        self.assertEqual(len(CHALLENGES) * len(LEVELS), 6)
        ids = set()
        for challenge in CHALLENGES:
            for level in LEVELS:
                questions = get_questions(challenge, level)
                self.assertEqual(len(questions), 5)
                for q in questions:
                    self.assertNotIn(q.id, ids)
                    ids.add(q.id)
                    self.assertEqual(len(set(q.choices)), 3)
                    self.assertIn(q.correct_index, range(3))
                    self.assertTrue(all([q.prompt, q.skill, q.hint, q.explanation]))
                    self.assertTrue(q.scenario)
                    self.assertLessEqual(len(q.prompt.split()), 18)
                    self.assertLessEqual(len(q.scenario.split()), 55)
        self.assertEqual(len(ids), 30)

    def test_unknown_round_rejected(self):
        for challenge, level in [('Unknown', LEVELS[0]), (CHALLENGES[0], 'College')]:
            with self.assertRaises(ValueError):
                get_questions(challenge, level)
