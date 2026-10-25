"""Offline checks for the viewer's local inference configuration."""
import os
import unittest
from unittest.mock import Mock, patch

import company_kb_viewer as viewer
import langchain_pinecone  # Load SDK type annotations before patching its client.
from langchain_ollama import ChatOllama, OllamaEmbeddings


class LocalViewerTests(unittest.TestCase):
    def tearDown(self):
        viewer.get_embeddings.clear()
        viewer.get_llm.clear()
        viewer.get_vector_store.clear()

    def test_local_models_and_credentials(self):
        with patch.dict(os.environ, {"PINECONE_API_KEY": "test", "PINECONE_LOCAL_INDEX_NAME": "local"}, clear=True):
            self.assertEqual(viewer.missing_env(), [])
            self.assertIsInstance(viewer.get_embeddings(), OllamaEmbeddings)
            self.assertIsInstance(viewer.get_llm(), ChatOllama)

    def test_blank_credentials_are_missing(self):
        with patch.dict(os.environ, {"PINECONE_API_KEY": " ", "PINECONE_LOCAL_INDEX_NAME": " "}, clear=True):
            self.assertEqual(set(viewer.missing_env()), {"PINECONE_API_KEY", "PINECONE_LOCAL_INDEX_NAME"})

    def test_wrong_index_dimension_fails_before_connecting(self):
        pc = Mock()
        pc.describe_index.return_value.dimension = 512
        embeddings = Mock()
        embeddings.embed_query.return_value = [0.0] * 768
        with patch.dict(os.environ, {"PINECONE_API_KEY": "test", "PINECONE_LOCAL_INDEX_NAME": "local"}, clear=True), patch("pinecone.Pinecone", return_value=pc), patch.object(viewer, "get_embeddings", return_value=embeddings):
            with self.assertRaisesRegex(ValueError, "768"):
                viewer.get_vector_store()
        pc.Index.assert_not_called()


if __name__ == "__main__":
    unittest.main()
