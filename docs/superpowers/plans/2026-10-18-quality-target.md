# Passage and answer quality target

Goal: measure and improve toward 0.90 passage relevance, answer faithfulness and reference-based factual correctness without relabeling gold or conflating document overlap with model judgments.

Execution: inline under the user's standing instruction to continue without confirmation pauses.

1. Add opt-in query-focused context selection using only question wording, retrieved passages and existing source sections. Keep baseline retrieval unchanged and preserve source-derived citations. Test intent exclusions, lost-evidence fallback and fixed/semantic chunk handling.
2. Extend existing actual RAGAS assessment with FactualCorrectness and explicit per-passage verdict capture. Report plain passage relevance ratio separately from ranked RAGAS precision. Preserve missing/partial judgments as unavailable.
3. Add a target gate requiring complete supported-case assessment, answer coverage and unsupported-case abstention. The existing gold contains 17 held-out questions, five unsupported cases and five reports; limit or missing judgments cannot pass the full question gate. These questions are narrow and have been inspected, so the result is developmental rather than an untouched independent certification.
4. Run a bounded actual local-model smoke assessment and source-grounded retrieval checks; retain exact inputs, contexts, references and model identities. Document actual scores and unmet targets. Broader independently authored questions and a stronger independent judge remain required before claiming production quality.

Constraints: no paid APIs, no fabricated scores, no automatic client evaluation UI, no gold edits to raise scores, no training/tuning from held-out failures. Fix query behavior from calibration examples; hold evaluation labels outside runtime selection.
