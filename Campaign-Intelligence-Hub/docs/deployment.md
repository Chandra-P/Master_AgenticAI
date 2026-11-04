# Deployment guide

Run the active question-answering application locally with Ollama. Python 3.12 or later, model disk space and sufficient memory for the chosen models are required. From the project directory:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e .
ollama pull llama3.2:3b
ollama pull embeddinggemma
.venv/Scripts/python.exe -m campaign_hub validate
.venv/Scripts/python.exe -m campaign_hub index --chunking all
.venv/Scripts/python.exe -m streamlit run app.py
```

Keep the Ollama service running. The checked-in corpus is ready for validation; `python -m campaign_hub generate` recreates the fictional fixtures when explicitly needed. Index creation requires the configured embedding service. Semantic segmentation also embeds sentence/table units before embedding final chunks.

Configuration lives in environment variables or administrator Streamlit secrets. See [.env.example](../.env.example) and [secrets template](../.streamlit/secrets.example.toml). A `.env` file is not automatically loaded. Defaults are `CIH_GENERATION_PROVIDER=ollama`, `CIH_GENERATION_MODEL=llama3.2:3b`, `CIH_EMBEDDING_PROVIDER=ollama`, `CIH_EMBEDDING_MODEL=embeddinggemma`, and `CIH_OLLAMA_URL=http://localhost:11434`.

OpenAI and Groq are optional answer providers. Set `CIH_GENERATION_PROVIDER`, an account-supported `CIH_GENERATION_MODEL`, and the corresponding `OPENAI_API_KEY` or `GROQ_API_KEY` on the server. Hosted answers send the question and retrieved passages to that provider. Embeddings are configured independently: `sentence_transformers` with `sentence-transformers/all-MiniLM-L6-v2` offers a local CPU alternative. Changing the embedding model requires compatible new indexes; changing answer providers alone does not relabel existing vectors. Optional classification has its own provider/model settings.

For a managed server, persist corpus versions, indexes and model caches, and place Streamlit behind the organization's authenticated HTTPS proxy. `streamlit run app.py --server.address 0.0.0.0 --server.port 8501` binds the server interface. Private-data authentication, authorization and operational hardening require deployment-specific work. The sample is a demonstration framework.

See [cloud quickstart](cloud-quickstart.md) for an optional remote-host checklist. These instructions do not assert that a new cloud deployment has been verified. Local benchmark evidence is recorded separately in [evaluation results](evaluation-results.md).
