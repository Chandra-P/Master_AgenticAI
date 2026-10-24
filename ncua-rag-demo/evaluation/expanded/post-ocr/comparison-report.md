# Expanded corpus: fixed versus semantic chunking

38 pre-labeled questions: original 15 NCUA cases, 22 annual-report evidence questions and 1 annual-report missing-evidence case. All four configurations use the same 29 documents and frozen questions.

## Combined results (34 evidence questions, 4 negatives)

| Chunker | Rerank | Recall@5 | MRR | Abstention | Retrieval p95 (s) |
|---|---|---:|---:|---:|---:|
| fixed | False | 0.912 | 0.777 | 1.000 | 0.805 |
| fixed | True | 0.985 | 0.985 | 1.000 | 2.644 |
| semantic | False | 0.912 | 0.772 | 1.000 | 1.276 |
| semantic | True | 0.975 | 0.956 | 1.000 | 3648.646 |

## NCUA questions

| Chunker | Rerank | Recall@5 | MRR | Abstention |
|---|---|---:|---:|---:|
| fixed | False | 0.917 | 0.736 | 1.000 |
| fixed | True | 0.958 | 1.000 | 1.000 |
| semantic | False | 0.917 | 0.708 | 1.000 |
| semantic | True | 0.958 | 0.958 | 1.000 |

## ANNUAL questions

| Chunker | Rerank | Recall@5 | MRR | Abstention |
|---|---|---:|---:|---:|
| fixed | False | 0.909 | 0.799 | 1.000 |
| fixed | True | 1.000 | 0.977 | 1.000 |
| semantic | False | 0.909 | 0.807 | 1.000 |
| semantic | True | 0.985 | 0.955 | 1.000 |

## Source-balanced comparison

Each source domain receives 50% weight, rather than allowing the 22 annual evidence questions to outweigh the 12 NCUA evidence questions.

| Chunker | Rerank | Balanced recall | Balanced MRR |
|---|---|---:|---:|
| fixed | False | 0.913 | 0.768 |
| fixed | True | 0.979 | 0.989 |
| semantic | False | 0.913 | 0.758 |
| semantic | True | 0.972 | 0.956 |

## Paired differences (semantic minus fixed)
- Rerank False, recall_at_5: mean +0.000; exploratory 95% bootstrap interval [+0.000, +0.000]; semantic wins/ties/fixed wins: 0/34/0.
- Rerank False, reciprocal_rank: mean -0.005; exploratory 95% bootstrap interval [-0.103, +0.093]; semantic wins/ties/fixed wins: 5/25/4.
- Rerank True, recall_at_5: mean -0.010; exploratory 95% bootstrap interval [-0.029, +0.000]; semantic wins/ties/fixed wins: 0/33/1.
- Rerank True, reciprocal_rank: mean -0.029; exploratory 95% bootstrap interval [-0.074, +0.000]; semantic wins/ties/fixed wins: 0/32/2.

## Coverage and limitations
Exploratory, manually labeled convenience set. Questions share reports and institutions, so question-bootstrap intervals can overstate certainty. Not a held-out general benchmark. All evidence units in a retrieved passage count toward recall; MRR uses first matching passage. nDCG omitted because multi-fact passages require a separately specified gain model. The parser bugfix was motivated by known failures on these same questions; this is a regression evaluation, not an independent held-out test. No chunking hyperparameters changed. Two newly answerable BECU membership cases were relabeled before this run; previous label versions and results remain preserved.

Local warmed retrieval only; randomized configuration order within shuffled questions. No generation, network or UI latency.

Selected BECU 2023/2024 financial tables now have reviewed local OCR. Other image-only pages remain outside OCR coverage. The absent Alliant annual report remains an explicit missing-evidence case. Abstention here means empty retrieval, not a generated-answer faithfulness judgment.

Frozen label SHA-256: f621e6b4f0bb70abbd480f74094eb8a406f61ab532fad83d8a2ae3e2c6ddbd3a

Timing correction: long execution pauses interrupted this run. The p95 column above contains observed wall time only and must not be interpreted as retrieval performance. Latency is excluded from the final OCR comparison.
