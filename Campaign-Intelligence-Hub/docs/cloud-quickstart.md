# Optional cloud setup

The default supported development path is [local Ollama setup](deployment.md). A remote Streamlit host needs its own reachable inference service: its `localhost:11434` addresses that host, not the owner's laptop. A CPU embedding provider plus an administrator-configured OpenAI or Groq answer provider is an optional alternative.

1. Deploy the intended repository revision with `Campaign-Intelligence-Hub/app.py` as the entry point and its dependency files available to the host. Use a Python version supported by `pyproject.toml`.
2. Keep the 122 synthetic sources and manifest available. Keep credentials, local model files and local indexes out of source control.
3. Configure private server secrets using the [administrator template](../.streamlit/secrets.example.toml). For CPU embeddings, select `CIH_EMBEDDING_PROVIDER=sentence_transformers` and the intended embedding model. Select the answer provider/model and corresponding server-side key. The template's model names are examples; confirm access with the provider account.
4. Set `CIH_AUTO_INDEX=true` if startup should prepare compatible collections. First startup may download the embedding model and build all three chunk strategies. Ephemeral storage can require rebuilding after a host reset.
5. Inspect startup logs, then verify source validation, index compatibility and a cited answer. Share the actual URL issued by the host after acceptance checks.

Before sharing, open the deployed app in a separate browser session. Check Ask Questions, Analyst View, Chunking Lab and Evaluation. Ask a supported source question, an unsupported question and a scoped campaign question. Inspect returned evidence and citations; verify that missing credentials, quota failures and unavailable scores remain visible. Confirm that visitors cannot see administrator secrets. Check all three chunkers and dense/hybrid settings, with reranking enabled only if the host has adequate resources.

No new cloud deployment or visitor-access check is claimed by this document. Memory, concurrency, cold-start behavior, persistence and provider quotas must be measured on the selected host. Local paired retrieval results do not establish hosted generation quality or availability. Current experiment evidence belongs in [evaluation results](evaluation-results.md).
