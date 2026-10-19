# Share the full application with a link

Recommended demonstration setup: **Streamlit Community Cloud + Groq free-tier generation + server-side CPU embeddings and Chroma**. Visitors only need a browser. They do not install Python/Ollama, download models themselves, build indexes, or supply API keys. The hosted version runs independently of the owner's laptop.

The cloud profile is implemented. **A public deployment and a live Groq call have not yet been verified:** an owner account/key must be configured first. Do not present the local app URL or an HTML example as a hosted interactive application.

Local verification on 2026-10-18 built both indexes with the CPU model and generated the default campaign's HTML report with 10 SVG charts, without Ollama or an API key. Embeddings have 384 dimensions. Long chunks are split using the embedding model's own token budget, then pooled and normalized, so the encoder does not silently discard their tails. These checks do not establish cloud memory usage, hosted availability, or live Groq answer quality.

Validation: 59 automated tests passed. A Streamlit AppTest using the hosted configuration confirmed startup, automatic indexes, owner-controlled model selection, and a visible configuration error when the owner key is absent. The live CPU index/report smoke check completed in 61.52 seconds on the development machine; this is not a hosting latency guarantee.

## One-time owner setup

1. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) with access to the GitHub repository.
2. Create an app with these values:

   | Field | Value |
   |---|---|
   | Repository | `Chandra-P/Master_AgenticAI` |
   | Branch | `kidspark-final` |
   | Main file | `Campaign-Intelligence-Hub/app.py` |
   | Python | 3.12 |

3. Create an API key in your own [Groq Console](https://console.groq.com/keys). Keep the account on the free plan for this demo. Never paste the key into chat, commit it to GitHub, or ask visitors to provide one.
4. In Streamlit's **Advanced settings → Secrets**, copy the contents of [.streamlit/secrets.example.toml](../.streamlit/secrets.example.toml), replacing only the placeholder API key with your real key. Confirm the configured model is enabled for your account and available on its free tier. The template currently selects `qwen/qwen3.8-27b`; change `CIH_GENERATION_MODEL` if the provider changes availability.
5. Deploy. First startup downloads a small public embedding model and builds both Chroma indexes. This can take a few minutes. Restarts reuse compatible local indexes when available; an ephemeral-host reset rebuilds them. No action is required from visitors.
6. Verify the acceptance steps below, then share the **actual URL returned by Streamlit**. No URL is reserved or live merely because these instructions exist.

The root-level secret values are loaded only into server configuration. Generation model selection is owner-controlled in the Groq profile. The UI never displays the API key. The real `.streamlit/secrets.toml` file is ignored by Git.

## Acceptance check before sharing

- Open the hosted URL from another browser/device, with the owner's laptop offline.
- Select a client/campaign and confirm the map/KPI totals update.
- Ask “What were the objectives?” and confirm a real answer with source citations. Missing keys, quota errors and unsupported claims must remain visible rather than appearing as successful generation.
- Generate a campaign report. Confirm the HTML preview, 10 default-campaign comparison charts, insights, source links and HTML download.
- Switch fixed/semantic and dense/hybrid retrieval; inspect retrieved chunks. Try reranking and check resource usage.
- Confirm that no visitor-facing setup, model-download or API-key entry is required.

If the cloud host exceeds memory/CPU limits, start with reranking off and inspect its resource logs. Actual Community Cloud memory, cold-start behavior, concurrent users, live Groq generation and reboot persistence still need verification on the deployed service; local tests cannot establish those.

## What changes between local and hosted modes?

| Component | Local default | Hosted profile |
|---|---|---|
| Generation | Ollama / Llama 3.2 | LangChain ChatGroq / owner-selected supported model |
| Embeddings | Ollama / embeddinggemma | CPU SentenceTransformer / all-MiniLM-L6-v2 |
| Retrieval | Chroma + dense/BM25 + optional cross-encoder | Same pipeline; model-isolated Chroma collections |
| Index setup | CLI or analyst button | Automatic startup with compatibility checks |
| Client report | Source-validated HTML | Same source-validated HTML |
| Visitor setup | Required to run a local copy | None after the owner deploys |

The host choice does not add real-document uploads: this remains a synthetic demonstration. Authentication/authorization for private client data is separate future work. Requests and retrieved synthetic excerpts for questions are sent to the configured generation provider; final chart/report arithmetic remains in Python. No automatic paid-plan upgrade is performed. Free API quotas and sleeping hosts limit availability and concurrency; this is a portfolio demo, not an always-on production commitment.

## Platform references checked 2026-10-18

- [Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud): hosted app sharing.
- [Deployment fields](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) and [secrets management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).
- [Streamlit resource limits](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app): limits and hibernation can change.
- [Groq free-plan limits](https://console.groq.com/docs/rate-limits) and [selected model capabilities](https://console.groq.com/docs/model/qwen/qwen3.8-27b).
- [Hugging Face Spaces](https://huggingface.co/docs/hub/spaces-overview): not the default recommendation here because creating Docker/Gradio compute Spaces currently requires a paid plan, despite CPU Basic having no hourly charge. Static Spaces cannot run this Python application.
