import unittest
from collections import Counter
from kidspark import challenges
from kidspark.game import start_round


class FairContentTests(unittest.TestCase):
    def test_versioned_banks_and_reading_load(self):
        ids = set()
        for challenge in challenges.CHALLENGES:
            for level in challenges.LEVELS:
                old = challenges.question_bank(challenge, level, '1')
                bank = challenges.question_bank(challenge, level, '2')
                self.assertEqual(len(old), 5)
                self.assertEqual(len(bank), 15)
                self.assertEqual(set(Counter(q.objective for q in bank).values()), {3})
                for q in bank:
                    self.assertNotIn(q.id, ids)
                    ids.add(q.id)
                    self.assertEqual(len(set(q.choices)), 3)
                    self.assertIn(q.correct_index, range(3))
                    self.assertLessEqual(len(q.prompt.split()), 18)
                    self.assertLessEqual(len(q.scenario.split()), 55)
                    self.assertTrue(q.explanation and q.hint)
        self.assertEqual(len(ids), 90)

    def test_reproducible_varied_balanced_selection(self):
        for challenge in challenges.CHALLENGES:
            for level in challenges.LEVELS:
                seen, orders = set(), set()
                for seed in map(str, range(100)):
                    selected = challenges.select_questions(challenge, level, seed)
                    self.assertEqual(selected, challenges.select_questions(challenge, level, seed))
                    self.assertEqual(len({q.objective for q in selected}), 5)
                    self.assertEqual(selected[0].objective, challenges.get_questions(challenge, level)[0].id)
                    seen.update(q.id for q in selected)
                    orders.add(tuple(q.objective for q in selected))
                self.assertEqual(len(seen), 15)
                self.assertGreater(len(orders), 1)

    def test_started_round_uses_current_seeded_bank(self):
        round = start_round('Ava', challenges.CHALLENGES[0], challenges.LEVELS[0])
        self.assertEqual(round.content_version, '2')
        self.assertEqual(round.questions, challenges.select_questions(round.challenge, round.level, round.attempt_id))

    def test_unsupported_bank_version_rejected(self):
        with self.assertRaises(ValueError):
            challenges.question_bank(challenges.CHALLENGES[0], challenges.LEVELS[0], '99')
