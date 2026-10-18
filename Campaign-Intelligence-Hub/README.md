# Campaign Intelligence Hub

Transform campaign objectives, success plans, and performance reports into actionable insights and executive-ready narratives.

A Week 2 RAG course project for campaign insights analysts. The main output is a Campaign Performance Report grounded in a fictional banking/credit-union corpus, with inline source citations, KPI comparisons, and an evidence-coverage checklist.

## What is included

- 110 deterministic synthetic Markdown documents for 20 campaigns and shared guidance.
- 30 evaluation cases with expected facts and source/section citations.
- LangChain `OllamaEmbeddings`, `ChatOllama`, prompt/structured-output chains, and the LangChain Chroma integration; no API key or paid API calls by default.
- Persistent ChromaDB, fixed 500-token/50-overlap chunks and business-section chunks.
- Dense retrieval, dense/BM25 reciprocal-rank fusion, and optional real cross-encoder reranking.
- LangGraph report orchestration and explicit insufficient-evidence behavior.
- Streamlit report generation, historical campaign comparison, questions, retrieval exploration, and measured evaluation views.
- Automatic client/campaign map showing attributed accounts and opening balances, with channel filters and a geographic results table.
- A standalone HTML client presentation with embedded SVG comparison charts, findings directly below each chart, and clickable source evidence. The final report retrieves chunks through Chroma, expands validated source documents, and calculates metrics in Python.

See the complete [implementation status report](docs/implementation-status.md): **94 of 102 checklist items implemented (92.2%)**, with eight explicit future-work items and production release boundaries. See the [deployment guide](docs/deployment.md) for local/server/Community Cloud instructions.

## Channels, attribution, and historical standing

Only **direct mail** and **display** are included:

| Channel | Attribution window | Starting event | Activation-rate denominator |
| --- | --- | --- | --- |
| Direct mail | 60 days | Mail/drop date | Mailed households |
| Display | 30 days | Exposure date | Unique exposed users |

Windows include the anchor date through the channel's final elapsed-day boundary; earlier/later conversions are excluded. The synthetic records use date-level cohorts and deduplicated outcomes assigned to one eligible channel. A campaign is mature only when its complete channel window has elapsed.

Use **Historical Comparison** to see activation rate and cost per activation against earlier campaigns of the **same client**, product type, channel, attribution rule, and denominator. An optional cross-client view is labeled **Synthetic peer reference — not an industry benchmark**. The page shows individual peers, peer medians, rank (1 = best), and a performance percentile with tie handling. Lower acquisition cost is better. Rates are compared within channels, not pooled across direct mail and display.

The same source-cited comparison appears in the client report's Progress Toward Goals. This 20-campaign corpus spans eleven product types and five fictional clients; the default campaign has two same-client historical comparators. Some products have no history. Small samples are explicitly flagged; a rank is a descriptive comparison, not a claim that a campaign is universally good. No compatible mature history means no ranking. Verified industry benchmark data has not been supplied.

```powershell
python -m campaign_hub compare --campaign TX-CHK-001
```

## Setup (Windows PowerShell)

Use Python 3.12 or newer and install [Ollama](https://ollama.com/download).

```powershell
cd Campaign-Intelligence-Hub
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
ollama pull llama3.2:3b
ollama pull embeddinggemma
python -m campaign_hub generate
python -m campaign_hub validate
python -m campaign_hub index --chunking all
python -m streamlit run app.py
```

If activation is blocked, replace `python` with `.\.venv\Scripts\python.exe`. On macOS/Linux activate with `source .venv/bin/activate`. Commands can use absolute file paths; data paths resolve from the project, not the shell working directory. Keep Ollama running. Initial installation and model downloads require internet access; local generation/embedding do not require paid calls.

## Generate a report

Select **Generate Report**, choose a **Client**, then choose one of that client's campaigns. KPI cards, map and same-client historical standing update automatically. Use the channel and map-measure controls to inspect accounts or opening balances. Click **Generate client-facing report** to retrieve evidence and see the HTML presentation preview. Choose **Download HTML presentation**, then open the file in a browser. Client and campaign selectors also appear on Historical Comparison, Ask Questions, and Retrieval Explorer.

The HTML presentation includes client/campaign identity, Executive Summary, Goals, chart-led Progress Toward Goals, Channels, Same-client History, Geography, Learnings, Recommendations, Next Steps, Measurement Notes and Source Citations. Each comparison chart has an adjacent insight and numbered source links. The file is self-contained and needs no CDN or network connection to view. Reconciliation failures, altered narrative, missing required retrieval evidence or immature attribution block exports. Proposed tests are labeled; owner/date/priority remain unassigned when absent from sources. These checks do not guarantee 100% correctness. The source corpus and client names are synthetic.

Open the [example HTML presentation](docs/example-client-report.html). HTML is now the default client output in the UI and CLI; PDF/PowerPoint are no longer generated by that workflow. Legacy export functions remain available for compatibility.

```powershell
python -m campaign_hub client-report --campaign TX-CHK-001
```

The final report uses the selected fixed/semantic, dense/hybrid and reranking settings against the built Chroma index. Retrieved chunk IDs, queries, scores and source hashes are recorded in the frozen JSON packet. Validated parent-document expansion preserves complete source tables for Python calculations; it does not substitute manifest KPI values. The CLI writes HTML, diagnostic Markdown and JSON under `data/reports/`. Report generation needs Ollama embeddings and a compatible index; it does not require Llama prose generation. The landing map remains a fast deterministic source-table snapshot. Map filters do not change the full-campaign report scope. Opening balances mean account balances at opening in USD, not current balances, net new deposits or revenue.

The current input corpus is synthetic Markdown under `data/corpus/`. Real PDF, Word, PowerPoint, Excel/CSV and database ingestion is explicitly future work; the app does not yet ingest real client files.

The separate eleven-section analytical RAG report remains available with:

```powershell
python -m campaign_hub report --campaign TX-CHK-001
```

For a faster deterministic report retaining source wording, without model prose generation:

```powershell
python -m campaign_hub report --campaign TX-CHK-001 --extractive
```

These two analytical modes use real embeddings, Chroma retrieval, and cited evidence. The optional model can suggest concise wording; unsupported paraphrases fall back to verbatim source evidence. KPI variance arithmetic is performed in Python. Analytical outputs are under `data/reports/`: `<campaign>.md`, `<campaign>-technical.md`, and `<campaign>.json`. Outputs are never automatically re-ingested. Use `client-report` for the final presentation packet.

Report sections: Executive Summary, Goal Achievement Analysis, KPI Performance Review, Performance Drivers, Audience Insights, Channel Insights, Recommendations, Lessons Learned, Suggested Next Steps, Presentation Storyline, and Source Citations.

Inputs: campaign brief, success plan, KPI results, historical campaigns, and best practices. Source performance reports contain KPI actuals; they are distinct from newly generated reports. Missing evidence yields a partial report with explicit gaps, not invented findings. Confidence is evidence coverage, not probability of truth.

## Ask, inspect, and evaluate

```powershell
python -m campaign_hub ask --campaign TX-CHK-001 --question "What were the objectives?"
python -m campaign_hub evaluate --smoke --extractive
python -m campaign_hub evaluate --full
python -m pytest -q
```

Reranking downloads `cross-encoder/ms-marco-MiniLM-L-6-v2` on first use. Enable with `--rerank` or the UI toggle; the experiment matrix tests both states. Full evaluation may take considerable time on CPU. Run artifacts under `data/runs/` contain actual results/errors, not example scores. A retrieval-only experiment marks generation as skipped. Add `--judge` for a separate local model support judgment; source/number validation alone does not prove semantic faithfulness, and a model judge is not human verification.

Default model settings use `CIH_OLLAMA_URL`, `CIH_GENERATION_MODEL`, and `CIH_EMBEDDING_MODEL` environment variables. Changing embedding model requires rebuilding indexes. `.env.example` documents names; environment variables must be exported in the shell. Current implementation uses local Ollama providers; the optional OpenAI adapter in the design is not enabled in this build.

## Project layout

```text
app.py                 Streamlit entry point
src/campaign_hub/
  synthetic_data/      Seeded corpus and manifest validation
  ingestion/           Source parsing and path validation
  chunking/            Fixed and business-section chunking
  embeddings/          Local embedding client and cache
  generation/          Local structured generation client
  vectordb/            Persistent Chroma indexes
  retrieval/           Dense/BM25 fusion
  reranking/           Local cross-encoder
  reporting/           KPI calculations, claims, report rendering
  langgraph/           Executable report workflow
  evaluation/          Gold metrics and experiment runner
  ui/                  Streamlit interface
data/corpus/           Synthetic Markdown sources
data/evaluation/       Gold questions
docs/                  Architecture and course methodology
tests/                 Automated tests
```

See [architecture](docs/architecture.md), [methodology](docs/methodology.md), and [evaluation status](docs/evaluation-results.md).
