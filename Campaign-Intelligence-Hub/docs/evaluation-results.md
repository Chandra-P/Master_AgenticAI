# Current RAG evaluation and failure analysis

Historical 122-source corpus measurements. The current corpus contains130 sources; these results are preserved for provenance and do not certify the expanded corpus. See [requirements pack](requirements-corpus.md).

Measured locally on 25 October 2026 against the 122-document corpus. This is retrieval-only evaluation: no generated-answer faithfulness score is implied. All numbers below are actual executions, not values copied from the financial reference kit.

The subsequent [generated-answer comparison](chunking-answer-quality-comparison.md)
evaluates all three chunkers with Ollama answers and an OpenAI judge. Semantic
also had the highest observed reference F1 across the complete supported set;
that outcome is separate from the document-overlap diagnostics below.

The complete current held_out matrix contains 360 rows: 30 cases across 12 configurations, including 23 supported and seven unsupported cases per configuration. The legacy split name includes newly authored ambiguous and multi-document examples; it is not independent blind validation. The 72 development baseline rows were measured earlier on the identical corpus, case set and embedding/chunker profiles and are retained separately.

Execution errors in the held_out matrix: 0. Every expected case/configuration pair is present.

## Identical query comparison

Document precision/recall and MRR below use deduplicated document IDs at five, not passage judgments. Unsupported cases have no gold relevant sources and are excluded from these means, not scored as zero. Multiple chunks from one source count once.

| Chunker | Retriever | Rerank | Document precision | Document recall | MRR | Mean retrieval execution seconds |
|---|---|---|---:|---:|---:|---:|
| fixed | dense | False | 0.330 | 1.000 | 0.616 | 0.095 |
| fixed | dense | True | 0.326 | 1.000 | 0.609 | 2.670 |
| fixed | hybrid | False | 0.341 | 1.000 | 0.630 | 0.269 |
| fixed | hybrid | True | 0.319 | 1.000 | 0.609 | 5.053 |
| section | dense | False | 0.449 | 0.913 | 0.554 | 0.391 |
| section | dense | True | 0.431 | 1.000 | 0.609 | 7.711 |
| section | hybrid | False | 0.417 | 1.000 | 0.587 | 0.509 |
| section | hybrid | True | 0.431 | 1.000 | 0.609 | 9.719 |
| semantic | dense | False | 0.424 | 1.000 | 0.630 | 0.323 |
| semantic | dense | True | 0.413 | 1.000 | 0.630 | 10.979 |
| semantic | hybrid | False | 0.460 | 1.000 | 0.630 | 1.504 |
| semantic | hybrid | True | 0.417 | 1.000 | 0.630 | 12.647 |

## Paired reranking impact

Each delta compares the same query and scope before and after cross-encoder reranking. Candidate k is 20, returned chunk k is five. The model is cross-encoder/ms-marco-MiniLM-L-6-v2. A positive delta is an observed gain, not a universal guarantee.

Configurations ran sequentially while machine load and cache state varied. Timing deltas are descriptive observations, not a controlled causal estimate of reranker overhead. Reranking improved section-based dense recall from 0.913 to 1.000, but lowered document precision for fixed and semantic configurations; it therefore remains optional and off by default.

| Chunker | Retriever | Paired successful cases | Precision delta | Recall delta | MRR delta | Added seconds |
|---|---|---:|---:|---:|---:|---:|
| fixed | dense | 30 | -0.004 | 0.000 | -0.007 | 2.575 |
| fixed | hybrid | 30 | -0.022 | 0.000 | -0.022 | 4.784 |
| section | dense | 30 | -0.018 | 0.087 | 0.054 | 7.320 |
| section | hybrid | 30 | 0.014 | 0.000 | 0.022 | 9.210 |
| semantic | dense | 30 | -0.011 | 0.000 | 0.000 | 10.656 |
| semantic | hybrid | 30 | -0.043 | 0.000 | 0.000 | 11.143 |

## Failure analysis and limits

- Section/dense retrieval without reranking missed the expected briefing documents for q05 (NY-CMP-005) and q07 (CA-CMP-007), returning plans, historical decks or results instead. Both expected documents appeared after reranking. All 36 multi-document and all 36 ambiguous case/configuration rows retrieved their gold documents; that does not establish complete or relevant generated answers.
- This comparison calls the base retrieval path with the case's campaign scope. Selected-campaign question answering additionally routes objective-only questions to briefing evidence. These retrieval diagnostics are not a claim that the two corresponding generated answers failed.
- Inspect rag-multi-01 through rag-multi-03 for missing cross-document evidence; rag-ambiguous-01 through rag-ambiguous-03 have explicit reference interpretations. A narrow gold source list can penalize other reasonable interpretations.
- Small semantic units can separate qualifications or tables from the relevant sentence. More chunks and higher document precision do not establish better answers.
- The earlier local llama3.2:3b relevance judge failed three negative calibration controls; see current-judge-controls.json. This retrieval-only comparison did not use a cloud judge. A subsequent owner-authorized [OpenAI-judged answer evaluation](openai-quality-results.md) now provides generated-answer scores separately.
- Live UI checks are separate: one consent question abstained despite related evidence; dev-01 returned the expected CR-217 sentence plus two other source-backed sentences. Those extras expose relevance risk despite valid citations.
- The cited dev-01 answer took 67.53 seconds, including 0.60 seconds retrieval/filtering. This exceeds the proposed 60-second sample ceiling; two checks cannot establish warm p95. CPU load, cold initialization and memory pressure affected this machine.
- The table measures retrieval execution, including reranking/model startup where encountered, not answer generation. Reranking adds material latency and remains optional/off by default.
- The synthetic corpus and source-derived references are teaching examples, not customer or production validation. Precision, recall and faithfulness targets have not been certified.

## Evidence and reproduction

Full identity-bearing rows: [pure-rag-retrieval-results.json](evaluation/pure-rag-retrieval-results.json). Flat rows: [comparison CSV](evaluation/pure-rag-retrieval-comparison.csv). Paired deltas: [reranking-impact.json](evaluation/reranking-impact.json). Live checks: [live-question-checks.json](evaluation/live-question-checks.json).

Run `python -m campaign_hub evaluate --full --include-reranking` for the complete current held_out retrieval matrix. Use `--generated` for generated-answer execution (which does not itself measure faithfulness), or the opt-in calibrated `--ragas` workflow for actual RAGAS judgments. Changing corpus, questions, embeddings or chunkers invalidates incompatible saved scores.
