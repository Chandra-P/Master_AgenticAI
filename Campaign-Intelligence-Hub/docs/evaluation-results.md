# Evaluation and verification results

## RAGAS integration verification: 2026-10-18

The context-precision failure was subsequently fixed with a compact, strict-schema prompt while retaining RAGAS's metric calculation and all retrieved passages. A **precision-only** reassessment of the identical saved q05 sample completed at approximately **1.0**, in **55.9 seconds** with a 90-second metric budget. Original failures and the new remeasurement are both preserved in the raw artifact; other metrics were not recomputed or copied into the new execution. Prompt versions are separate dashboard groups. This verifies the execution fix on one case, not full answer quality.

After this fix, the complete regression suite passed **101 tests**, including binary verdict validation, all-passage ranked scoring and prompt-version display. Focused read-only review found no remaining Critical/Important issues in the change.

The earlier integration passed **100 automated tests** with the optional RAGAS stack installed; `pip check` found no broken requirements. Actual RAGAS metric calculations were tested against known positive/negative judge verdicts. Two real CPU smoke cases completed before the JSON-mode correction: q04 abstained (faithfulness unavailable), q05 scored 0.75 faithfulness, and both scored 1.0 context recall. Context precision was unavailable in both original cases due to parsing failure/timeout. These are same-model local Llama measurements, not independent validation or hosted Groq results. A complete live benchmark remains pending. See [RAGAS assessment details](ragas-assessment.md) and the [unmodified measured scores](evaluation/ragas-smoke-results.json).

## Current three-method verification: 2026-10-18

- **92 automated tests passed** after semantic chunking, configuration isolation, controls, source-span, citation and hosted stale-result fallback regression changes.
- Built real persistent CPU Chroma indexes with LangChain embeddings (`sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions): **130 fixed-size, 490 section-based, 445 embedding-based semantic chunks** from 110 validated documents.
- Each method generated the default campaign's validated HTML report with **10 charts and 9 source documents**. Fixed retrieval used 12 chunks; section and semantic used 38 each. These are functional checks, not a guarantee about all possible real-data inputs.
- Ran **12 configurations × 27 held-out cases = 324 rows**, zero execution errors, using actual dense/hybrid search and a local cross-encoder. Three calibration cases were excluded. Questions used retrieved text; analytical report cases used source-backed extractive claims. No generation API or entailment judge was used.

| Chunking | Retrieval | Rerank | MRR@5 | Document precision | Document recall | Mean seconds |
|---|---|---|---:|---:|---:|---:|
| fixed | dense | Off | 0.4660 | 0.2981 | 0.9886 | 0.4567 |
| fixed | dense | On | 0.5000 | 0.2833 | 0.9659 | 2.3729 |
| fixed | hybrid | Off | 0.4938 | 0.3056 | 1.0000 | 0.4401 |
| fixed | hybrid | On | 0.5000 | 0.2833 | 0.9659 | 1.5761 |
| section | dense | Off | 0.4105 | 0.3457 | 1.0000 | 0.4867 |
| section | dense | On | 0.4815 | 0.3506 | 0.9886 | 2.7427 |
| section | hybrid | Off | 0.4691 | 0.3364 | 1.0000 | 0.4962 |
| section | hybrid | On | 0.4815 | 0.3580 | 1.0000 | 2.7940 |
| semantic | dense | Off | 0.5000 | 0.3537 | 0.9886 | 0.4277 |
| semantic | dense | On | 0.5000 | 0.3432 | 0.9773 | 3.3240 |
| semantic | hybrid | Off | 0.4938 | 0.3457 | 1.0000 | 0.4805 |
| semantic | hybrid | On | 0.5000 | 0.3432 | 0.9773 | 3.1970 |

Analytical report statuses: **36 complete / 24 partial**. Partial reports disclose missing compatible historical cohorts rather than inventing a comparison.

Raw artifacts: [324 measured rows](evaluation/three-chunking-results.json), [configuration means](evaluation/three-chunking-comparison.csv). These are bundled in the dashboard for the matching CPU profile. Existing local `data/runs/latest` takes precedence when its citation-scoring version is current and must match the corpus, embedding and chunker. Older-scoring or unreadable saved runs are preserved while the bundled comparison is shown. Raw identities record the exact configurations; model-generated answer quality is not measured here.

Section citation overlap now resolves exact claim spans in multi-section chunks. Unknown or ambiguous sections make that case's section score unavailable; document citation overlap and section-resolution coverage are separate metrics. Whole-chunk exports list real sections and never invent `#document`. None of these overlap metrics establishes entailment. Faithfulness is **unmeasured (null)**. Source-derived synthetic gold, simple fact matching, small cohorts and uncontrolled development-machine cold starts limit interpretation. These latency values are not hosted benchmarks, and this is not a controlled embedding-model comparison. See the [deliverable audit](deliverable-audit.md) for remaining requirements.

## Historical local verification: 2026-10-18, before three-method migration

The results in this historical section used the old heading-based strategy named `semantic`. That strategy is now called `section`. These measurements do not evaluate the new embedding-based semantic algorithm. Current three-method results are recorded separately above this historical record.

- **51 automated tests passed.** Tests cover corpus construction, chunking, metadata filters, KPI/attribution arithmetic, benchmark eligibility, evidence validation, client selection, report export, source-conflict rejection and unavailable zero-channel CPA.
- Exactly **110 source documents**: 20 briefs, 20 success plans, 20 performance reports, 20 historical deck documents, 10 strategy documents, 10 best-practice guides, 5 KPI dictionaries and 5 methodology documents. There are 20 campaigns, five fictional clients, 200 location/channel rows and 30 evaluation cases.
- Rebuilt actual persistent Chroma collections: **130 fixed chunks and 490 semantic chunks**, using LangChain Ollama embeddings (`embeddinggemma`). Collection compatibility includes the corpus and embedding configuration.
- All **20 source-validated campaign snapshots generated chart-led HTML successfully**. Final UI/CLI generation uses Chroma retrieval and validated parent-document expansion. The default-campaign example retrieved **38 chunks across 9 source documents**, then rendered **10 comparison charts**, each with an adjacent finding and source links.
- The default client output is now [standalone HTML](example-client-report.html). Its inline CSS/SVG and source evidence work without external assets. Desktop/mobile Edge checks at 1440px/430px verified 10 charts, valid citation targets and no document-level horizontal overflow. The complete desktop report was visually inspected. Full accessibility/cross-browser/device-matrix testing remains future work.
- Streamlit AppTest exercised automatic channel filtering, real retrieval-backed generation, the embedded HTML preview and HTML/source-packet download controls. PDF/PowerPoint are no longer offered by the default UI/CLI workflow; legacy export functions retain regression tests.
- Read-only code review found no remaining Critical/Important issues in the targeted source reconciliation, zero-channel CPA, peer isolation, HTML/chart/source attribution or checklist tally.

## Historical eight-configuration retrieval experiment

Executed the eight-configuration matrix on **27 held-out cases: 216 result rows, zero execution errors**, against the current regenerated corpus. Three calibration cases were excluded. The run used actual Chroma search, BM25/fusion, LangChain Ollama embeddings and the downloaded cross-encoder.

Question cases used retrieved text instead of model-generated answers (`--extractive`). Report cases used the eleven-section analytical RAG workflow: **24 complete and 16 partial**. The 16 partial reports correspond to the two evaluated products without compatible same-client historical cohorts across eight configurations; the system preserves an explicit historical-evidence gap instead of inventing standing. This does not prevent a final client packet from disclosing that history is unavailable. All 20 deterministic client packets passed their supported source checks.

| Chunking | Retrieval | Rerank | MRR@5 | Document precision | Document recall | Mean seconds |
|---|---|---|---:|---:|---:|---:|
| Fixed | Dense | Off | 0.4877 | 0.2907 | 0.9773 | 0.2230 |
| Fixed | Dense | On | 0.5000 | 0.2833 | 0.9659 | 4.2568 |
| Fixed | Hybrid | Off | 0.5000 | 0.3056 | 1.0000 | 0.3900 |
| Fixed | Hybrid | On | 0.5000 | 0.2833 | 0.9659 | 1.6558 |
| Semantic | Dense | Off | 0.4352 | 0.3630 | 0.8977 | 0.4406 |
| Semantic | Dense | On | 0.4815 | 0.3432 | 0.9773 | 3.2753 |
| Semantic | Hybrid | Off | 0.4630 | 0.3457 | 1.0000 | 0.3975 |
| Semantic | Hybrid | On | 0.4815 | 0.3506 | 0.9886 | 2.7696 |

Raw artifacts: [all measured rows](evaluation/held-out-results.json), [configuration means](evaluation/comparison.csv). Results under `data/runs/latest/` also drive the dashboard and are rejected if their corpus identity is stale.

These are small synthetic-corpus measurements. Source-derived gold and similar wording can inflate results. Document metrics are not token-level context judgments. Expected-fact completeness is string matching, not overall narrative quality. Citation accuracy is gold source/section overlap; the low aggregate values (about 0.084–0.087) reflect the narrow expected-section gold and additional analytical-report citations and must not be presented as strong semantic citation accuracy. Latency includes cold starts and concurrent local work; it is not a controlled throughput benchmark. Reranking does not uniformly improve retrieval.

**No entailment judge ran in this historical matrix**: all faithfulness values remain null. Faithfulness charts appear only after actual judge measurements. Retrieval-only unsupported-question abstention is unscored. Independent factual evaluation, a controlled matched embedding-model experiment, calibrated confidence, sustained production/cloud testing and separate graph-stage nodes remain future work. Focused hosted/browser checks have since been completed; see the [cloud quickstart](cloud-quickstart.md) and full [implementation status report](implementation-status.md).

## Reproduce

```powershell
python -m pytest -q
python -m campaign_hub generate
python -m campaign_hub validate
python -m campaign_hub index --chunking all
python -m campaign_hub evaluate --full --extractive
python -m campaign_hub client-report --campaign TX-CHK-001
```

Optional `evaluate --full --judge` runs generated answers and an additional local model support judgment; it is slower and remains an imperfect same-model assessment, not independent human validation. No perfect scores are substituted for unavailable measurements.
