# Expanded corpus: fixed versus semantic chunking

38 pre-labeled questions: original 15 NCUA cases, 20 annual-report evidence questions and 3 annual-report missing-evidence cases. All four configurations use the same 29 documents and frozen questions.

## Combined results (32 evidence questions, 6 negatives)

| Chunker | Rerank | Recall@5 | MRR | Abstention | Retrieval p95 (s) |
|---|---|---:|---:|---:|---:|
| fixed | False | 0.750 | 0.625 | 0.833 | 0.607 |
| fixed | True | 0.828 | 0.844 | 0.833 | 3.174 |
| semantic | False | 0.750 | 0.635 | 0.833 | 0.509 |
| semantic | True | 0.818 | 0.812 | 0.833 | 3.279 |

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
| fixed | False | 0.650 | 0.558 | 0.667 |
| fixed | True | 0.750 | 0.750 | 0.667 |
| semantic | False | 0.650 | 0.592 | 0.667 |
| semantic | True | 0.733 | 0.725 | 0.667 |

## Source-balanced comparison

Each source domain receives 50% weight, rather than allowing the 20 annual evidence questions to outweigh the 12 NCUA evidence questions.

| Chunker | Rerank | Balanced recall | Balanced MRR |
|---|---|---:|---:|
| fixed | False | 0.783 | 0.647 |
| fixed | True | 0.854 | 0.875 |
| semantic | False | 0.783 | 0.650 |
| semantic | True | 0.846 | 0.842 |

## Paired differences (semantic minus fixed)
- Rerank False, recall_at_5: mean +0.000; exploratory 95% bootstrap interval [+0.000, +0.000]; semantic wins/ties/fixed wins: 0/32/0.
- Rerank False, reciprocal_rank: mean +0.010; exploratory 95% bootstrap interval [-0.102, +0.115]; semantic wins/ties/fixed wins: 5/23/4.
- Rerank True, recall_at_5: mean -0.010; exploratory 95% bootstrap interval [-0.031, +0.000]; semantic wins/ties/fixed wins: 0/31/1.
- Rerank True, reciprocal_rank: mean -0.031; exploratory 95% bootstrap interval [-0.078, +0.000]; semantic wins/ties/fixed wins: 0/30/2.

## Coverage and limitations
Exploratory, manually labeled convenience set. Questions share reports and institutions, so question-bootstrap intervals can overstate certainty. Not a held-out general benchmark. All evidence units in a retrieved passage count toward recall; MRR uses first matching passage. nDCG omitted because multi-fact passages require a separately specified gain model. No tuning or question selection after results.

Local warmed retrieval only; randomized configuration order within shuffled questions. No generation, network or UI latency.

BECU 2023 is image-only in this extraction; BECU 2024 contains mostly captions. No OCR was added. These and the absent Alliant annual report are explicit missing-evidence cases. Abstention here means empty retrieval, not a generated-answer faithfulness judgment.

Frozen label SHA-256: b7cd2413d36e7477f29dd6a3722abdde5c771df69a7f0736c3cd5e7e5a109ff9

## Interpretation

The new annual reports do not establish an overall semantic advantage. Without reranking, recall ties and semantic has a small MRR advantage. With reranking, fixed achieves 0.828 recall and 0.844 MRR, versus 0.818 and 0.813 for semantic. Weighting NCUA and annual-report questions equally yields the same ordering with reranking. The paired exploratory intervals include zero; shared sources and the small convenience sample limit generalization.

Annual-only evidence recall is 0.750 for fixed with reranking and 0.733 for semantic with reranking. Reranking is the clearer improvement in both strategies on this question set.

Five exact Navy Federal membership-count questions (A01–A05) fail to retrieve the precise table count with either strategy. Retrieved narrative summaries can contain rounded counts instead; those do not satisfy an exact-count question. This points to a PDF table and candidate-retrieval weakness rather than proof that either chunker is inherently superior. Q12 retains incomplete cross-institution evidence. The semantic reranked result also misses one fact in the three-part A15 question.

All configurations return nonempty, unhelpful caption evidence for A22 (BECU 2024 membership count), giving five correct empty-retrieval outcomes out of six negative cases. Empty retrieval is not the same as safe generated-answer abstention. OCR and stronger coverage checks are separate future improvements; neither was added during this experiment.

Evidence labels require a matching original source, an accepted physical page, and a numeric/fact anchor; numeric substrings are boundary checked. Anchor retrieval is a proxy for evidence coverage, not a semantic answer-faithfulness judgment. Full raw passages, labels and paired scores are supplied for audit.
