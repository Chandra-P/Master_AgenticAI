# Course methodology and limits

Corpus generation is seeded Python rendering, not an API-generated dataset. Four linked documents describe each of 20 fictional campaigns; 30 shared guides complete the 110-document corpus. Canonical values determine both source documents and gold facts. Generation never uses actual customer data.

Fixed chunks use the documented cl100k_base tokenizer, 500-token maximum and 50-token overlap. Business-section chunking follows Markdown headings, with the same bounds for oversized sections. This is structure-aware chunking, not learned semantic breakpoint detection. The tokenizer is a consistent course comparison unit, not a claim to reproduce every provider's internal tokenizer.

Dense and BM25 searches apply identical metadata filters. Hybrid ranking combines document ranks with reciprocal rank fusion, constant 60. Cross-encoder scores and dense/fusion scores have different scales and must not be displayed as calibrated confidence probabilities.

The default report method retains source wording to prevent unsupported narrative claims; optional LLM rewrites are accepted conservatively. Numeric KPI comparisons are deterministic. Citation ID and numeric consistency checks are necessary but insufficient for entailment; no system can promise zero hallucinations from generative models. Source facts can also be wrong outside this synthetic course setting.

Report coverage is not correctness probability. No support for an audience/channel breakdown means an explicit limitation, not an inferred breakdown. Attribution is observational; do not claim causal lift or ROI without the required evidence and denominators.

Gold evaluation includes calibration and held-out records. MRR/nDCG/precision/recall operate on deduplicated source document IDs. Expected-fact string matching is a completeness proxy, not semantic grading. Independent model-judged faithfulness is nullable; unavailable scores are never substituted with one or zero. Experiments disclose failed configurations and generation-skipped modes.
