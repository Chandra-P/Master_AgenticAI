# BECU OCR: retrieval evaluation

Local Tesseract.js 7.0.0 OCR processed 19 selected pages from BECU 2023/2024 annual reports. Nine financial-table pages were visually checked and normalized into 119 row passages, each carrying table context, years and units. Raw OCR, source hashes and correction audit are retained. Other image-only pages remain outside reviewed OCR coverage.

## Fair comparison

Same 38 question texts and filters. Before running retrieval, A21/A22 were changed from missing-evidence negatives to verified membership evidence: 2023 = 1,457,207 (physical page 69); 2024 = 1,514,773 (page 100). Version 3 therefore has 34 evidence questions and four negatives. Pre-OCR saved passages were rescored against these same labels below; original results are preserved. No chunking or ranking settings were tuned.

| Chunker | Rerank | Recall before OCR | Recall after OCR | MRR before | MRR after |
|---|---|---:|---:|---:|---:|
| fixed | False | 0.853 | 0.912 | 0.733 | 0.777 |
| fixed | True | 0.926 | 0.985 | 0.941 | 0.985 |
| semantic | False | 0.853 | 0.912 | 0.728 | 0.772 |
| semantic | True | 0.917 | 0.975 | 0.912 | 0.956 |

## Newly recovered membership questions

| Chunker | Rerank | A21 recall | A22 recall |
|---|---|---:|---:|
| fixed | False | 1.000 | 1.000 |
| fixed | True | 1.000 | 1.000 |
| semantic | False | 1.000 | 1.000 |
| semantic | True | 1.000 | 1.000 |

## Interpretation and limits

OCR and table normalization improve document coverage shared by both chunkers. This convenience sample and repair of known failures do not establish universal superiority of either method. Scores measure retrieval only, not generated-answer accuracy. Annual questions concern membership/member services; new loan and balance-sheet rows are ingested but not exhaustively benchmarked. No external OCR service or Groq calls were used for this retrieval run. Latency is excluded because long execution pauses interrupted the run. Raw wall-clock measurements remain in the audit artifacts and are not inference performance estimates.

## Paired semantic-minus-fixed results
- Rerank False, recall_at_5: +0.000; exploratory 95% interval [+0.000, +0.000]; wins/ties/losses 0/34/0.
- Rerank False, reciprocal_rank: -0.005; exploratory 95% interval [-0.103, +0.093]; wins/ties/losses 5/25/4.
- Rerank True, recall_at_5: -0.010; exploratory 95% interval [-0.029, +0.000]; wins/ties/losses 0/33/1.
- Rerank True, reciprocal_rank: -0.029; exploratory 95% interval [-0.074, +0.000]; wins/ties/losses 0/32/2.

Frozen v3 labels SHA-256: f621e6b4f0bb70abbd480f74094eb8a406f61ab532fad83d8a2ae3e2c6ddbd3a

Index counts: 2275 fixed, 1936 semantic.
