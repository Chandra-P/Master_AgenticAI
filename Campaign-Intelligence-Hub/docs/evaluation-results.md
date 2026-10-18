# Evaluation status

The application writes real run outputs to `data/runs/latest/results.json` and `results.csv`. The dashboard remains empty until those files exist.

The experiment matrix has eight combinations: fixed/semantic chunking, dense/hybrid retrieval, and reranking disabled/enabled. Held-out cases exclude calibration items. `--smoke` uses one held-out question across the matrix; `--full` uses all held-out cases, including report and unsupported requests.

Faithfulness is unavailable unless `--judge` is selected. That option adds a local model entailment judgment with model provenance; it remains an imperfect model assessment rather than independent human verification. Do not interpret retrieval relevance, valid citation IDs, or string-matched completeness as faithfulness. Generated errors are retained in each result row; failed runs are not silently excluded.

## Actual local run: 2026-10-17

Regenerated and reran the corpus after the LangChain/direct-mail/display update. Executed the eight-configuration matrix on 27 held-out cases: **216 result rows, zero execution errors**. All 40 report/configuration cases produced complete reports. These runs used LangChain Ollama embeddings and Chroma search, persistent Chroma collections, real BM25/fusion, and the actual cross-encoder. Question cases used retrieved text instead of LLM-generated answers (`--extractive`); report cases used extractive report generation, deterministic KPI calculations, and channel-specific historical comparisons.

The three calibration cases were excluded. No entailment judge ran in this comparison, so faithfulness values remain null. Unsupported-question abstention was not scored in retrieval-only mode. Completeness is expected-fact string matching, not a measure of overall narrative quality. Report document relevance counts all report sources; question retrieval uses at most five chunks.

| Chunking | Retrieval | Rerank | Mean MRR@5 | Document precision | Document recall |
| --- | --- | --- | ---: | ---: | ---: |
| Fixed | Dense | Off | 0.500 | 0.306 | 1.000 |
| Fixed | Dense | On | 0.500 | 0.298 | 0.989 |
| Fixed | Hybrid | Off | 0.438 | 0.306 | 1.000 |
| Fixed | Hybrid | On | 0.500 | 0.298 | 0.989 |
| Semantic | Dense | Off | 0.481 | 0.370 | 0.955 |
| Semantic | Dense | On | 0.481 | 0.352 | 1.000 |
| Semantic | Hybrid | Off | 0.481 | 0.358 | 1.000 |
| Semantic | Hybrid | On | 0.481 | 0.352 | 1.000 |

These are small synthetic-corpus observations, not universal ranking claims. Reranking improved semantic dense recall but did not uniformly improve other metrics. Latency mixes cold starts, downloads, cache warming, and concurrent local work; inspect raw rows before comparing performance.

Artifacts: [all measured rows](evaluation/held-out-results.json), [configuration means and latency](evaluation/comparison.csv).

Additional live checks: both Chroma collections rebuilt (110 fixed chunks, 450 semantic chunks); live structured LangChain generation and the Historical Comparison UI exercised against real sources. Thirty-three automated checks pass. Direct mail uses 60 days from mail/drop date and display 30 days from exposure. Source-cited reports include ranks and medians; the synthetic default campaign has only one same-product historical peer, so the UI/report explicitly flag the limited cohort. Acquisition-cost comparisons also show their own valid-peer count when zero-conversion peers have undefined costs. No connected browser surface was available for visual screenshot QA.
