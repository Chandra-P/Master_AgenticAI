"""Offline checks for notebook paths and the local terminal assistant."""
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent


class LocalSetupTests(unittest.TestCase):
    def test_notebook_resolves_project_from_workspace_or_notebook(self):
        notebook = json.loads((ROOT / "Langchain_Fundamentals.ipynb").read_text(encoding="utf-8"))
        for cwd in (ROOT, ROOT.parent.parent):
            with self.subTest(cwd=cwd), patch("pathlib.Path.cwd", return_value=cwd):
                scope = {}
                exec("".join(notebook["cells"][3]["source"]), scope)
                self.assertEqual(scope["project_dir"], ROOT)

    def test_terminal_agent_uses_configured_local_model_without_keys(self):
        import terminal_chatbot
        with patch.dict(os.environ, {"OLLAMA_CHAT_MODEL": "llama3.2:3b", "OLLAMA_BASE_URL": "http://localhost:11434"}, clear=True):
            agent = terminal_chatbot.build_agent()
        self.assertIsNotNone(agent)
        self.assertAlmostEqual(terminal_chatbot.circle_area.invoke({"radius": 3}), 28.274333882308138)


if __name__ == "__main__":
    unittest.main()
