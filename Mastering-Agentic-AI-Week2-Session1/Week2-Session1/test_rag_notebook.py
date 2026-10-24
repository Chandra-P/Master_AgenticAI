"""Offline regression checks for notebook setup and ingestion (no API calls)."""
import ast
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parent
NOTEBOOK = json.loads((ROOT / "1_rag_pipeline.ipynb").read_text(encoding="utf-8"))


def cell(index):
    return "".join(NOTEBOOK["cells"][index]["source"])


class NotebookTests(unittest.TestCase):
    def test_code_compiles(self):
        for index, item in enumerate(NOTEBOOK["cells"]):
            if item["cell_type"] == "code":
                ast.parse(cell(index), filename=f"cell {index}")

    def test_data_loads_from_workspace_and_notebook_directory(self):
        for cwd in (ROOT, ROOT.parent.parent):
            with self.subTest(cwd=cwd), patch("pathlib.Path.cwd", return_value=cwd):
                scope = {"Path": Path, "os": os, "load_dotenv": Mock()}
                exec(cell(1), scope)
                scope.update(json=json, Document=lambda **kw: SimpleNamespace(**kw))
                exec(cell(5), scope)
                self.assertEqual(len(scope["docs"]), 51)
                self.assertEqual(scope["load_dotenv"].call_args.args[0], ROOT / ".env")

    def test_missing_credentials_report_all_names(self):
        with patch.dict(os.environ, {}, clear=True):
            scope = {"os": os}
            with self.assertRaisesRegex(ValueError, "PINECONE_API_KEY.*PINECONE_LOCAL_INDEX_NAME"):
                exec(cell(18), scope)

    def test_local_models_need_no_openai_key(self):
        embeddings = Mock()
        embeddings.embed_query.return_value = [0.0] * 768
        pc = Mock()
        pc.describe_index.return_value = SimpleNamespace(dimension=768)
        scope = {"os": os, "OllamaEmbeddings": Mock(return_value=embeddings),
                 "Pinecone": Mock(return_value=pc), "PineconeVectorStore": Mock()}
        with patch.dict(os.environ, {"PINECONE_API_KEY": "test", "PINECONE_LOCAL_INDEX_NAME": "local"}, clear=True):
            exec(cell(18), scope)
            scope.update(ChatOllama=Mock(), PromptTemplate=SimpleNamespace(from_template=Mock()))
            exec(cell(23), scope)
        self.assertEqual(scope["OllamaEmbeddings"].call_args.kwargs["model"], "nomic-embed-text")
        self.assertEqual(scope["ChatOllama"].call_args.kwargs["model"], "qwen3.5:2b")
        pc.describe_index.return_value = SimpleNamespace(dimension=512)
        with patch.dict(os.environ, {"PINECONE_API_KEY": "test", "PINECONE_LOCAL_INDEX_NAME": "old"}, clear=True):
            with self.assertRaisesRegex(ValueError, "768"):
                exec(cell(18), scope)

    def test_ingestion_upserts_chunks_with_repeatable_ids(self):
        store = Mock()
        store.add_documents.side_effect = lambda **kw: kw["ids"]
        chunks = [SimpleNamespace(page_content="Shipping help", metadata={"title": "Shipping", "start_index": 0})]
        scope = {"vector_store": store, "splits": chunks, "json": json}
        exec(cell(19), scope)
        first_ids = scope["document_ids"]
        exec(cell(19), scope)
        self.assertEqual(scope["document_ids"], first_ids)
        self.assertEqual(len(first_ids), len(chunks))
        self.assertEqual(store.add_documents.call_args.kwargs["documents"], chunks)


if __name__ == "__main__":
    unittest.main()
