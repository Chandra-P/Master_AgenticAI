import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


class DashboardTests(unittest.TestCase):
    def test_launch_from_another_directory(self):
        original = Path.cwd()
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ, {'KIDSPARK_DB_PATH': str(Path(folder) / 'test.sqlite3')}):
                try:
                    os.chdir(folder)
                    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=15).run()
                    self.assertFalse(app.exception)
                    self.assertEqual([card.value for card in app.metric], ['0', '0 / 3', '0', '0%'])
                finally:
                    os.chdir(original)


if __name__ == '__main__':
    unittest.main()
