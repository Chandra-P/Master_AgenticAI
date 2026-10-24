# Expanded corpus: fixed versus semantic chunking

38 pre-labeled questions: original 15 NCUA cases, 20 annual-report evidence questions and 3 annual-report missing-evidence cases. All four configurations use the same 29 documents and frozen questions.

## Combined results (32 evidence questions, 6 negatives)

| Chunker | Rerank | Recall@5 | MRR | Abstention | Retrieval p95 (s) |
|---|---|---:|---:|---:|---:|
| fixed | False | 0.906 | 0.779 | 0.833 | 0.367 |
| fixed | True | 0.984 | 1.000 | 0.833 | 1.672 |
| semantic | False | 0.906 | 0.773 | 0.833 | 0.275 |
| semantic | True | 0.974 | 0.969 | 0.833 | 1.507 |

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
| fixed | False | 0.900 | 0.804 | 0.667 |
| fixed | True | 1.000 | 1.000 | 0.667 |
| semantic | False | 0.900 | 0.812 | 0.667 |
| semantic | True | 0.983 | 0.975 | 0.667 |

## Source-balanced comparison

Each source domain receives 50% weight, rather than allowing the 20 annual evidence questions to outweigh the 12 NCUA evidence questions.

| Chunker | Rerank | Balanced recall | Balanced MRR |
|---|---|---:|---:|
| fixed | False | 0.908 | 0.770 |
| fixed | True | 0.979 | 1.000 |
| semantic | False | 0.908 | 0.760 |
| semantic | True | 0.971 | 0.967 |

## Paired differences (semantic minus fixed)
- Rerank False, recall_at_5: mean +0.000; exploratory 95% bootstrap interval [+0.000, +0.000]; semantic wins/ties/fixed wins: 0/32/0.
- Rerank False, reciprocal_rank: mean -0.005; exploratory 95% bootstrap interval [-0.112, +0.094]; semantic wins/ties/fixed wins: 5/23/4.
- Rerank True, recall_at_5: mean -0.010; exploratory 95% bootstrap interval [-0.031, +0.000]; semantic wins/ties/fixed wins: 0/31/1.
- Rerank True, reciprocal_rank: mean -0.031; exploratory 95% bootstrap interval [-0.078, +0.000]; semantic wins/ties/fixed wins: 0/30/2.

## Coverage and limitations
Exploratory, manually labeled convenience set. Questions share reports and institutions, so question-bootstrap intervals can overstate certainty. Not a held-out general benchmark. All evidence units in a retrieved passage count toward recall; MRR uses first matching passage. nDCG omitted because multi-fact passages require a separately specified gain model. The parser bugfix was motivated by known failures on these same questions; this is a regression evaluation, not an independent held-out test. No chunking hyperparameters or question labels were changed.

Local warmed retrieval only; randomized configuration order within shuffled questions. No generation, network or UI latency.

BECU 2023 is image-only in this extraction; BECU 2024 contains mostly captions. No OCR was added. These and the absent Alliant annual report are explicit missing-evidence cases. Abstention here means empty retrieval, not a generated-answer faithfulness judgment.

Frozen label SHA-256: b7cd2413d36e7477f29dd6a3722abdde5c771df69a7f0736c3cd5e7e5a109ff9