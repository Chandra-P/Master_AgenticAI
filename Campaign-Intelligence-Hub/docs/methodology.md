# Course methodology and limits

Corpus generation is seeded Python rendering, not an API-generated dataset. Four linked documents describe each of 20 fictional campaigns; 30 shared guides complete the 110-document corpus. Canonical values determine both source documents and gold facts. Generation never uses actual customer data.

Fixed chunks use the documented cl100k_base tokenizer, 500-token maximum and 50-token overlap. Business-section chunking follows Markdown headings, with the same bounds for oversized sections. This is structure-aware chunking, not learned semantic breakpoint detection. The tokenizer is a consistent course comparison unit, not a claim to reproduce every provider's internal tokenizer.

Dense and BM25 searches apply identical metadata filters. Hybrid ranking combines document ranks with reciprocal rank fusion, constant 60. Cross-encoder scores and dense/fusion scores have different scales and must not be displayed as calibrated confidence probabilities.

The default report method retains source wording to prevent unsupported narrative claims; optional LLM rewrites are accepted conservatively. Numeric KPI comparisons are deterministic. Citation ID and numeric consistency checks are necessary but insufficient for entailment; no system can promise zero hallucinations from generative models. Source facts can also be wrong outside this synthetic course setting.

Report coverage is not correctness probability. No support for an audience/channel breakdown means an explicit limitation, not an inferred breakdown. Attribution is observational; do not claim causal lift or ROI without the required evidence and denominators.

Channels are limited to direct mail and display. Direct mail receives a 60-day attribution window anchored to mail/drop date; display receives 30 days from exposure. Attribution rejects conversions before the anchor and beyond the applicable window. Source tables preserve anchor dates, as-of dates, window lengths, exposure units, spend, activations, and maturity. Results are deduplicated at campaign level; synthetic channel totals are mutually exclusive and sum to campaign actuals.

Historical standing is computed in Python from retrieved Channel Results tables, not from generated narrative or manifest KPI values. Peers must have an earlier reporting period, matching product type and channel, matching window/anchor/denominator, and a fully observed window. Rankings and percentiles account for directionality: higher activation rate and lower acquisition cost are better. Performance percentile is the proportion of historical peers outperformed plus half of tied peers. Rank includes the current campaign and uses competition ranking for ties. Peer medians exclude the current campaign. Zero-conversion peers remain in rate benchmarks; their undefined acquisition costs are excluded only from the cost comparison. Small cohorts are descriptive, not statistically representative; future and incompatible campaigns never supply benchmark values.

LangChain provides the embedding contract, Ollama clients, chat prompt/structured-output runnable chain, and Chroma similarity-search wrapper. LangGraph continues to orchestrate report assembly. Existing index compatibility and evidence validation remain application responsibilities.

Gold evaluation includes calibration and held-out records. MRR/nDCG/precision/recall operate on deduplicated source document IDs. Expected-fact string matching is a completeness proxy, not semantic grading. Independent model-judged faithfulness is nullable; unavailable scores are never substituted with one or zero. Experiments disclose failed configurations and generation-skipped modes.
