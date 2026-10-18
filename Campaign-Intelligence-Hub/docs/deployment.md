# Deployment guide

## Local or managed server

The complete application runs locally with free Ollama APIs. Python 3.12+, sufficient RAM for the selected models, and disk for models/indexes are required.

```powershell
cd Campaign-Intelligence-Hub
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e .
ollama pull llama3.2:3b
ollama pull embeddinggemma
.venv/Scripts/python.exe -m campaign_hub generate
.venv/Scripts/python.exe -m campaign_hub validate
.venv/Scripts/python.exe -m campaign_hub index --chunking all
.venv/Scripts/python.exe -m streamlit run app.py
```

The dashboard and map source-table snapshots work without model inference or indexes. Final HTML report generation, Ask Questions, Retrieval Explorer and RAG experiments require the running Ollama embedding service and built collections. Final report prose and chart findings use deterministic source calculations. Downloaded HTML reports contain all charts/styles/source evidence and can be viewed offline. The live geographic basemap uses an external tile service; its table remains available without tiles.

For a server, install dependencies into an isolated environment, run Ollama on the same protected host or a reachable protected service, and persist `data/indexes`, model files and source versions. Start Streamlit with `--server.address 0.0.0.0 --server.port 8501` behind your organization's authenticated HTTPS proxy. Multi-user authentication, authorization, private client ingestion, and durable shared storage are future work; this build is a synthetic local demonstration, not a production client-data service.

Configure `CIH_OLLAMA_URL`, `CIH_GENERATION_MODEL`, and `CIH_EMBEDDING_MODEL` before starting the process. See `.env.example`; this app does not automatically load `.env`. Never commit credentials. Changing embedding models requires fresh indexes.

## Streamlit Community Cloud

The guide is implemented; a live cloud deployment has **not** been performed. Community Cloud runs on a remote host, so its `localhost:11434` cannot reach Ollama on your laptop. This is a hosting constraint, not an API key requirement.

1. Push the project to the intended GitHub branch. Keep the synthetic corpus and manifest in the repository; do not commit local models, caches, indexes or secrets.
2. In Community Cloud, create an app and select the repository, branch and `Campaign-Intelligence-Hub/app.py` as entry point. Use a Python version compatible with `pyproject.toml`.
3. Install dependencies from `Campaign-Intelligence-Hub/requirements.txt`. The app entry point adds its own `src` directory to the import path, so an editable package install is not required for the hosted UI. Confirm dependency-file selection in the cloud build logs.
4. Use the matching project theme. Confirm corpus validation, client/campaign selection and the map table first; those do not need Ollama. The HTML report workflow needs a reachable embedding service and built index before generation; a downloaded report can be viewed offline.
5. Full RAG requires a remotely reachable, protected Ollama endpoint, adequate resources and an index lifecycle. Do not expose an unauthenticated local Ollama service publicly. Provisioning a protected endpoint, cloud index persistence, cold-start/resource testing and full cloud RAG verification are future work. No free hosted model endpoint is promised.
6. Review cloud logs and run the same functional checks after deployment. Never treat missing model/judge results as successful evaluation.

Platform references (checked 2026-10-17): [deployment setup](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [dependency management](https://docs.streamlit.io/deploy/concepts/dependencies), and [secrets configuration](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management). The localhost inference constraint above follows from the app's configured endpoint and the remote-host deployment model.
