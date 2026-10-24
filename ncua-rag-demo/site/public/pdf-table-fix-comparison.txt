# PDF membership table repair: before and after

The same frozen 38 questions were evaluated against the same 29 reports, using identical retrieval settings. The only new evidence is five validated membership-table passages recovered from existing Navy Federal PDFs. Each passage keeps the institution, both year columns, exact counts, units and physical PDF page together.

## Combined retrieval results

Recall@5 measures the fraction of labeled evidence recovered in five passages. MRR measures how early matching evidence appears. Scores exclude the six negative cases.

| Chunker | Rerank | Recall before | Recall after | MRR before | MRR after |
|---|---|---:|---:|---:|---:|
| fixed | False | 0.750 | 0.906 | 0.625 | 0.779 |
| fixed | True | 0.828 | 0.984 | 0.844 | 1.000 |
| semantic | False | 0.750 | 0.906 | 0.635 | 0.773 |
| semantic | True | 0.818 | 0.974 | 0.812 | 0.969 |

## Exact membership questions A01–A05

| Chunker | Rerank | Questions with exact evidence before | After |
|---|---|---:|---:|
| fixed | False | 0/5 | 5/5 |
| fixed | True | 0/5 | 5/5 |
| semantic | False | 0/5 | 5/5 |
| semantic | True | 0/5 | 5/5 |

## Interpretation

The repair addresses lost table context in ingestion. It is shared by both chunkers, so any improvement is not proof that semantic chunking is better. Compare the measured post-repair results directly. This is a regression study motivated by known failures on these questions, not an independent held-out experiment. No question labels or chunking thresholds changed.

The benchmark measures retrieval, not generated-answer accuracy. Missing OCR text in BECU 2023/2024 remains a limitation. No Groq generation calls were used for these scores.

## Paired semantic-minus-fixed results
- Rerank False, recall_at_5: +0.000; exploratory 95% interval [+0.000, +0.000]. Semantic wins/ties/fixed wins: 0/32/0.
- Rerank False, reciprocal_rank: -0.005; exploratory 95% interval [-0.112, +0.094]. Semantic wins/ties/fixed wins: 5/23/4.
- Rerank True, recall_at_5: -0.010; exploratory 95% interval [-0.031, +0.000]. Semantic wins/ties/fixed wins: 0/31/1.
- Rerank True, reciprocal_rank: -0.031; exploratory 95% interval [-0.078, +0.000]. Semantic wins/ties/fixed wins: 0/30/2.

Frozen question SHA-256: b7cd2413d36e7477f29dd6a3722abdde5c771df69a7f0736c3cd5e7e5a109ff9

Rebuilt indexes: 2156 fixed chunks; 1896 semantic chunks.
