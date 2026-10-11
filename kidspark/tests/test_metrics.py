import io
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from kidspark.metrics import load_missions, summarize, category_progress, leaderboard

HEADER = 'learner,mission_id,mission,category,completed,stars\n'
ROWS = ('Ava,1,Read,Reading,true,5\nAva,2,Draw,Art,true,5\n'
        'Ava,3,Paint,Art,false,99\nBen,1,Read,Reading,true,10\n'
        'Cora,1,Read,Reading,true,10\nDrew,1,Read,Reading,true,5\n')


class MetricsTests(unittest.TestCase):
    def load(self, content):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'missions.csv'
            path.write_text(content)
            return load_missions(path)

    def test_pending_rewards_and_category_progress(self):
        df = self.load(HEADER + ROWS)
        ava = df[df.learner == 'Ava']
        result = summarize(ava)
        self.assertEqual((result['completed'], result['total'], result['stars']), (2, 3, 10))
        self.assertAlmostEqual(result['progress'], 200 / 3)
        art = category_progress(ava).set_index('category').loc['Art']
        self.assertEqual((art.completed, art.total, art.progress, art.stars), (1, 2, 50, 5))
        self.assertFalse(df.iloc[2].completed)

    def test_leaderboard_tiebreakers_and_shared_ranks(self):
        board = leaderboard(self.load(HEADER + ROWS))
        self.assertEqual(board.learner.tolist(), ['Ava', 'Ben', 'Cora', 'Drew'])
        self.assertEqual(board['rank'].tolist(), [1, 2, 2, 4])
        self.assertEqual(board.stars.tolist(), [10, 10, 10, 5])

    def test_empty_data(self):
        df = self.load(HEADER)
        self.assertEqual(summarize(df), dict(completed=0, total=0, stars=0, progress=0))
        self.assertTrue(category_progress(df).empty)
        self.assertEqual(leaderboard(df).columns.tolist(), ['rank', 'learner', 'stars', 'completed'])

    def test_invalid_data(self):
        bad_rows = ['Ava,1,Read,Reading,maybe,5', 'Ava,1,Read,Reading,true,-1',
                    'Ava,1,Read,Reading,true,1.5', 'Ava,1,Read,Reading,true,abc',
                    'Ava,1,Read,Reading,true,inf', ',1,Read,Reading,true,5',
                    'Ava,,Read,Reading,true,5', 'Ava,1,,Reading,true,5',
                    'Ava,1,Read,,true,5']
        for row in bad_rows:
            with self.subTest(row=row), self.assertRaises(ValueError):
                self.load(HEADER + row + '\n')
        for content in ['learner,stars\nAva,5\n', HEADER + ROWS + ROWS]:
            with self.subTest(content=content), self.assertRaises(ValueError):
                self.load(content)

    def test_whitespace_and_boolean_case(self):
        df = self.load(HEADER + ' Ava ,1, Read , Reading , TRUE ,5\n')
        self.assertEqual(df.iloc[0].learner, 'Ava')
        self.assertEqual(summarize(df)['stars'], 5)

    def test_rejects_extra_csv_fields(self):
        with self.assertRaises(ValueError):
            self.load(HEADER + 'extra,Ava,1,Read,Reading,true,5\n')

    def test_large_stars_remain_exact(self):
        large = 2 ** 64 + 1
        df = self.load(HEADER + f'Ava,1,Read,Reading,true,{large}\n'
                       + f'Ben,1,Draw,Art,true,{large + 1}\n'
                       + 'Ava,2,Draw,Art,true,1\n')
        self.assertEqual(df.iloc[0].stars, large)
        self.assertEqual(summarize(df[df.learner == 'Ava'])['stars'], large + 1)
        self.assertEqual(category_progress(df[df.learner == 'Ava']).stars.sum(), large + 1)
        self.assertEqual(leaderboard(df)['rank'].tolist(), [1, 2])

    def test_quoted_csv_fields(self):
        df = self.load(HEADER + 'Ava,1,"Read, then draw",Reading,true,5\n')
        self.assertEqual(df.iloc[0].mission, 'Read, then draw')


if __name__ == '__main__':
    unittest.main()
