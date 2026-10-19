# Share the full application with a link

Recommended demonstration setup: **Streamlit Community Cloud + Groq free-tier generation + server-side CPU embeddings and Chroma**. Visitors only need a browser. They do not install Python/Ollama, download models themselves, build indexes, or supply API keys. The hosted version runs independently of the owner's laptop.

Live demo: [Campaign Intelligence Hub](https://9swrtwtm4lvrbw2zrh2pyg.streamlit.app/). Hosted acceptance checks on 2026-10-18 verified automatic CPU embeddings/Chroma startup, campaign KPI totals, the geographic map, attribution rules, and historical comparisons. Report generation passed source reconciliation and narrative checks, offered the HTML download, and rendered comparison charts with insights and source citations. A separate incognito browser session opened the app without owner login or visitor API-key setup and received cited Groq answers for the campaign objectives and the USD 540,000 opening-balance goal.

Local verification on 2026-10-18 built both indexes with the CPU model and generated the default campaign's HTML report with 10 SVG charts, without Ollama or an API key. Embeddings have 384 dimensions. Long chunks are split using the embedding model's own token budget, then pooled and normalized, so the encoder does not silently discard their tails. These checks do not establish cloud memory usage, hosted availability, or live Groq answer quality.

Validation: 71 automated tests passed after hosted acceptance fixes, including cached-module compatibility, source-code cache invalidation, credential-safe model errors, verbatim question grounding, and document scoping for generic objectives versus metric goals and achievement questions. A Streamlit AppTest using the hosted configuration confirmed startup, automatic indexes, owner-controlled model selection, and a visible configuration error when the owner key is absent. The local CPU index/report smoke check completed in 61.52 seconds on the development machine; this is not a hosting latency guarantee.

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

If the cloud host exceeds memory/CPU limits, start with reranking off and inspect its resource logs. The live checks above cover a small functional sample. Sustained Community Cloud memory usage, concurrent-user capacity, repeated cold starts, broad model-answer quality, and persistence across host resets remain unmeasured.

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
