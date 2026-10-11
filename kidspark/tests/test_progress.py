import unittest
from kidspark.challenges import CHALLENGES, LEVELS
from kidspark.progress import summarize_attempts, skill_accuracy, suggest_challenge, challenge_leaderboard
from test_storage import result_for


class ProgressTests(unittest.TestCase):
    def test_leaderboard_ranks_and_challenge_filter(self):
        rows = [dict(nickname_key=key, nickname=key.title(), challenge=challenge, best_score=score)
                for key, challenge, score in [('ava', CHALLENGES[0], 80), ('ava', CHALLENGES[1], 60),
                                             ('ben', CHALLENGES[0], 100), ('cora', CHALLENGES[0], 80),
                                             ('cora', CHALLENGES[1], 60),
                                             ('ava', CHALLENGES[2], 40), ('cora', CHALLENGES[2], 40)]]
        board = challenge_leaderboard(rows)
        self.assertEqual(board['Nickname'].tolist(), ['Ava', 'Cora'])
        self.assertEqual(board['Rank'].tolist(), [1, 1])
        self.assertEqual(board['Best points'].tolist(), [180, 180])
        filtered = challenge_leaderboard(rows, CHALLENGES[0])
        self.assertEqual(filtered['Nickname'].tolist(), ['Ben', 'Ava', 'Cora'])
        self.assertEqual(filtered['Rank'].tolist(), [1, 2, 2])
        self.assertTrue(challenge_leaderboard([]).empty)
    def test_empty_progress(self):
        self.assertEqual(summarize_attempts([]), dict(rounds=0, challenges=0, score=0, correct=0, total=0, accuracy=0))
        self.assertEqual(skill_accuracy([]).columns.tolist(), ['skill', 'correct', 'total', 'accuracy'])
        self.assertEqual(suggest_challenge([], LEVELS[0])[0], CHALLENGES[0])

    def test_actual_results_and_weighted_skill_accuracy(self):
        a = result_for(correct=3)
        # Explicit skill fixture: randomized round order must not define this expectation.
        a['answers'] = [dict(skill=s, correct=c) for s, c in
                        [('Unit prices', True), ('Unit prices', True), ('Discounts', True),
                         ('Budgeting', False), ('Budgeting', False)]]
        b = result_for(challenge=CHALLENGES[2], correct=0)
        summary = summarize_attempts([a, b])
        self.assertEqual(summary, dict(rounds=2, challenges=2, score=60, correct=3, total=10, accuracy=30))
        skills = skill_accuracy([a, b]).set_index('skill')
        self.assertEqual(skills.loc['Budgeting', 'total'], 4)
        self.assertEqual(skills.loc['Budgeting', 'accuracy'], 0)
        c = result_for(challenge=CHALLENGES[1], correct=5)
        c['answers'] = [dict(skill='Unit prices', correct=True)]
        a['answers'] = [dict(skill='Unit prices', correct=False)] * 3
        self.assertEqual(skill_accuracy([a, c]).iloc[0].accuracy, 25)

    def test_recommendations_by_level_and_weakest_challenge(self):
        a = result_for(correct=2)
        self.assertEqual(suggest_challenge([a], LEVELS[0])[0], CHALLENGES[1])
        self.assertEqual(suggest_challenge([a], LEVELS[1])[0], CHALLENGES[0])
        results = [result_for(challenge=c, correct=n) for c, n in zip(CHALLENGES, [4, 1, 3])]
        self.assertEqual(suggest_challenge(results, LEVELS[0])[0], CHALLENGES[1])
        tied = [result_for(challenge=c, correct=3) for c in CHALLENGES]
        self.assertEqual(suggest_challenge(tied, LEVELS[0])[0], CHALLENGES[0])
