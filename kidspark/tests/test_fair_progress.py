import unittest
from kidspark.challenges import CHALLENGES, LEVELS
from kidspark import progress


def scores(name, values):
    return [dict(nickname_key=name.lower(), nickname=name, challenge=challenge, best_score=score)
            for challenge, score in zip(CHALLENGES, values)]


class FairProgressTests(unittest.TestCase):
    def test_overall_requires_all_challenges_and_individual_allows_partial(self):
        rows = scores('Ava', [80, 100, 60]) + scores('Ben', [100]) + scores('Cora', [100, 80, 60])
        rows += scores('Ava', [60])  # Duplicate/lower summaries cannot inflate totals.
        board = progress.challenge_leaderboard(rows)
        self.assertEqual(board.Nickname.tolist(), ['Ava', 'Cora'])
        self.assertEqual(board['Best points'].tolist(), [240, 240])
        self.assertEqual(board.Rank.tolist(), [1, 1])
        self.assertEqual(progress.challenge_leaderboard(rows, CHALLENGES[0]).Nickname.tolist(), ['Ben', 'Cora', 'Ava'])
        self.assertTrue(progress.challenge_leaderboard(scores('New', [100, 100])).empty)

    def test_unknown_challenge_does_not_grant_eligibility(self):
        rows = scores('Ava', [100, 100])
        rows.append(dict(nickname_key='ava', nickname='Ava', challenge='Unknown', best_score=100))
        self.assertTrue(progress.challenge_leaderboard(rows).empty)

    def test_first_latest_best_are_ordered_and_level_scoped(self):
        def attempt(id, score, time, level=LEVELS[0]):
            return dict(attempt_id=id, challenge=CHALLENGES[0], level=level, score=score, completed_at=time)
        history = [attempt('c', 60, '2026-10-11T12:00:00+00:00'),
                   attempt('b', 100, '2026-10-11T12:00:00+00:00'),
                   attempt('a', 80, '2026-10-10T12:00:00+00:00'),
                   attempt('d', 0, '2026-10-12T12:00:00+00:00', LEVELS[1])]
        cards = progress.challenge_progress(history, LEVELS[0])
        self.assertEqual(cards[0], dict(challenge=CHALLENGES[0], rounds=3, first=80, latest=60, best=100, change=-20))
        self.assertEqual(cards[1], dict(challenge=CHALLENGES[1], rounds=0, first=None, latest=None, best=None, change=None))
        high = progress.challenge_progress(history, LEVELS[1])[0]
        self.assertEqual((high['rounds'], high['first'], high['best'], high['change']), (1, 0, 0, None))
        self.assertEqual(len(progress.challenge_progress([], LEVELS[0])), 3)
