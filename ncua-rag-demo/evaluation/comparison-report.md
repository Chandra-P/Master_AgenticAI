# Chunking and reranking comparison

Measured on the same 15 questions and source corpus. Twelve evidence questions and three expected abstentions.

| Chunking | Rerank | Recall@5 | MRR | nDCG@5 | Abstention | Retrieval p95 (s) |
|---|---|---:|---:|---:|---:|---:|
| fixed | False | 0.917 | 0.736 | 0.783 | 1.000 | 0.328 |
| fixed | True | 0.958 | 1.000 | 0.968 | 1.000 | 1.168 |
| semantic | False | 0.917 | 0.708 | 0.760 | 1.000 | 0.169 |
| semantic | True | 0.958 | 0.958 | 0.937 | 1.000 | 1.410 |

## Measured reranking impact
- fixed: recall@5 delta +0.042; MRR delta +0.264.
- semantic: recall@5 delta +0.042; MRR delta +0.250.

## Failure analysis
- fixed, rerank=False: incomplete or incorrect retrieval on Q12. Inspect raw results for context.
- fixed, rerank=True: incomplete or incorrect retrieval on Q12. Inspect raw results for context.
- semantic, rerank=False: incomplete or incorrect retrieval on Q12. Inspect raw results for context.
- semantic, rerank=True: incomplete or incorrect retrieval on Q12. Inspect raw results for context.

An institution filter makes single-institution questions easier. The cross-document case intentionally has no institution filter; five passages can miss one institution or the required financial row. Similar table labels and repeated institution headers can dominate similarity. Semantic chunks may combine adjacent rows; larger chunks can improve coverage while diluting precision.

## Limits and targets
Recall@5 target: 0.80. Faithfulness target: 0.90. End-to-end warm p95 target: 15 seconds. This experiment measures retrieval only. Generated-answer quality and generation latency are assessed separately in generation-results.json; public load performance is not measured. Retrieval metrics are not answer accuracy. Negative cases use explicit evidence gates; they do not establish general hallucination resistance.

For multi-row chunks, nDCG/MRR use one new relevant row per retrieved chunk; recall follows the ranked chunk relevance mapping. Labels are source rows, not answer text. This small hand-labeled evaluation is a learning demonstration, not a statistically representative benchmark.