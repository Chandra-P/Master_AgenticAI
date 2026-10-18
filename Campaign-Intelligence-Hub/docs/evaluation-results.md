# Evaluation status

The application writes real run outputs to `data/runs/latest/results.json` and `results.csv`. The dashboard remains empty until those files exist.

The experiment matrix has eight combinations: fixed/semantic chunking, dense/hybrid retrieval, and reranking disabled/enabled. Held-out cases exclude calibration items. `--smoke` uses one held-out question across the matrix; `--full` uses all held-out cases, including report and unsupported requests.

Faithfulness is unavailable unless `--judge` is selected. That option adds a local model entailment judgment with model provenance; it remains an imperfect model assessment rather than independent human verification. Do not interpret retrieval relevance, valid citation IDs, or string-matched completeness as faithfulness. Generated errors are retained in each result row; failed runs are not silently excluded.

## Actual local run: 2026-10-17

Executed the eight-configuration matrix on 27 held-out cases: **216 result rows, zero execution errors**. All 40 report/configuration cases produced complete reports. These runs used real Ollama embeddings, persistent Chroma collections, real BM25/fusion, and the actual cross-encoder. Question cases used retrieved text instead of LLM-generated answers (`--extractive`); report cases used extractive report generation and deterministic KPI calculations.

The three calibration cases were excluded. No entailment judge ran in this comparison, so faithfulness values remain null. Unsupported-question abstention was not scored in retrieval-only mode. Completeness is expected-fact string matching, not a measure of overall narrative quality. Report document relevance counts all report sources; question retrieval uses at most five chunks.

| Chunking | Retrieval | Rerank | Mean MRR@5 | Document precision | Document recall |
| --- | --- | --- | ---: | ---: | ---: |
| Fixed | Dense | Off | 0.500 | 0.269 | 0.943 |
| Fixed | Dense | On | 0.500 | 0.269 | 0.943 |
| Fixed | Hybrid | Off | 0.500 | 0.269 | 0.943 |
| Fixed | Hybrid | On | 0.500 | 0.269 | 0.943 |
| Semantic | Dense | Off | 0.457 | 0.358 | 0.852 |
| Semantic | Dense | On | 0.481 | 0.358 | 0.943 |
| Semantic | Hybrid | Off | 0.500 | 0.383 | 0.943 |
| Semantic | Hybrid | On | 0.481 | 0.358 | 0.943 |

These are small synthetic-corpus observations, not universal ranking claims. Reranking improved semantic dense recall but did not uniformly improve other metrics. Latency mixes cold starts, downloads, cache warming, and concurrent local work; inspect raw rows before comparing performance.

Artifacts: [all measured rows](evaluation/held-out-results.json), [configuration means and latency](evaluation/comparison.csv).

Additional live checks: both Chroma collections built (110 fixed chunks, 430 semantic chunks); source-grounded and optional local-model reports generated; all four UI pages and real report generation exercised with Streamlit AppTest. No connected browser surface was available for visual screenshot QA.
