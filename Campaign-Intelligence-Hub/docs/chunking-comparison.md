# Three chunking methods

Historical 122-source corpus measurements. The current corpus contains130 sources; these results are preserved for provenance and do not certify the expanded corpus. See [requirements pack](requirements-corpus.md).

All three methods use the same validated source library, embedding interface and retrieval/evaluation pipeline. Section-based is the default. Chunk count alone does not measure answer quality, and no method is assumed to win across every question.

| Method | CLI value | Natural boundary | Default token bound |
|---|---|---|---|
| Fixed-size | `fixed` | Windows across cleaned document text | 500 tokens, 50-token overflow overlap |
| Section-based | `section` | Markdown heading/body groups | 500 tokens, 50-token overflow overlap |
| Embedding-based semantic | `semantic` | Adjacent sentence/unit cosine-distance changes | 500 tokens, 50-token overflow overlap |

The preserved 122-document sample produced 166 fixed, 550 section and 707 semantic chunks in the current local setup. Semantic boundaries depend on the configured embedder, so reproduce them with the recorded embedding identity. See [evaluation results](evaluation-results.md) for the corresponding measured run and its limits.

## Actual implementation and parameter semantics

[chunking/pipeline.py](../src/campaign_hub/chunking/pipeline.py) reconstructs cleaned heading/body text after ingestion. Fixed-size chunking passes that text to token windows. Section-based chunking passes each section body separately; short sections remain separate chunks. A document without headings becomes a single group before token bounding.

[chunking/semantic.py](../src/campaign_hub/chunking/semantic.py) constructs sentence spans using punctuation boundaries and retains each contiguous Markdown table as one unit. It embeds the units, validates count/dimensions/finite nonzero vectors, normalizes them, and computes cosine distance between adjacent units. A boundary occurs when the distance exceeds the document's 65th-percentile threshold by more than the numerical tolerance. Equal distances do not force arbitrary splits. Markdown headings supply context and citation metadata but do not force semantic boundaries.

The API accepts `semantic_percentile` (default 65, range 0â€“100). A higher percentile generally selects fewer distance breaks; it is not a target chunk count or probability of relevance. The current CLI selects a strategy and does not expose a percentile flag. Semantic segmentation requires the configured embedder and does not silently fall back to headings when embeddings fail.

`bounded_spans` defaults to `window=500` and `overlap=50`. It uses the `cl100k_base` tokenizer, selects exact character spans and rechecks each emitted span against the token bound. Overlap is used only when an oversized group needs another window. It is not added between short sections or between natural semantic groups. Tables remain intact when within the bound; oversized tables may split. Source wording and Unicode character boundaries are preserved.

The course tokenizer is a common comparison unit, not a claim to reproduce the generation or embedding model's tokenizer. The CPU embedding adapter independently windows text within its encoder's token limit and pools/normalizes the vectors. Semantic segmentation embeds units before final-chunk embeddings; all methods embed their final chunks for search.

## Compatibility and evaluation

Chunk metadata records source identifiers, section anchors, token counts, hashes and strategy. Semantic chunks additionally retain cleaned-source character offsets, boundary reason, percentile, threshold and segmentation embedder identity. A semantic chunk can intersect several sections, so a whole-chunk citation is not proof of support from a single section.

Collection identities isolate corpus, embedder, strategy and chunker configuration. Historical heading-based `semantic` collections are not current embedding-semantic indexes. Evaluation identities also bind the case set and generation mode. Current comparisons cross three chunkers, dense/hybrid retrieval and reranking off/on: 12 paired configurations. Calibration and report-only fixtures are excluded; the selected active sets contain 30 held-out cases or 25 current development examples (12 in the historical measured development run). Document-level relevance metrics differ from model-judged faithfulness, which stays unavailable without an actual judge run.

## Reproduce

From an installed project environment with the configured embedding service available:

```powershell
python -m campaign_hub index --chunking all
python -m campaign_hub ask --chunking section --question "What are the tracking validation procedures?"
python -m campaign_hub evaluate --full --extractive --include-reranking --split held_out
python -m campaign_hub evaluate --full --extractive --include-reranking --split development
```

Retrieval-only evaluation skips answer generation. Use `--generated` instead of `--extractive` for actual generated-answer measurement and retain its separate identity. See [measured results](evaluation-results.md) rather than treating these commands as proof that a run completed.

The 130-source corpus now indexes 180 fixed, 580 section and 788 semantic chunks. New CL-640 sources demonstrate 1–2 fixed, 2–6 section and 7–12 semantic chunks each. These are observed boundaries, not proof of higher answer quality. See [requirements corpus](requirements-corpus.md).
