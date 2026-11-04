# Answer quality improvement investigation

The initial semantic baseline reference F1 is 0.3348 across all 23 supported questions, counting refusals as zero. The benchmark has seven unsupported controls. This is a model-judged claim-overlap score, not the percentage of questions answered correctly.

## Confirmed failures
- Correct source sentences can be rejected when the local generator omits citation IDs. The saved local diagnostic contains an exact objective quote with an empty citation list.
- Local generation adds unrelated facts and omits requested facts. Both long and short question-focused prompt trials were rejected rather than promoted.
- Context focusing omitted the numeric Channel Results section. The selection now preserves it alongside totals and channel insights.
- FactualCorrectness does not use the question as an input in the installed RAGAS 0.3.9 implementation. The q11 diagnostic explicitly rejected the correct activation total because the terse reference omitted the campaign identifier and verified qualifier. The answer still genuinely omitted both channel counts. Original references and scores have been preserved.

## Implemented repair
Recover a missing citation only when the nonempty exact quote occurs in exactly one retrieved source. Reject unknown/wrong explicit IDs, ambiguous matches and invented text. This establishes source provenance, not relevance or entailment. The generated-evaluation identity includes the prompt, response schema and grounding contract version.

## Verification
The full non-live suite passed: 137 tests, with three existing RAGAS deprecation warnings. Fresh static review found no source-validation issues. Four diagnostic cases with local Ollama generation and approved OpenAI judging produced one supported answer with F1=1.0 and faithfulness=1.0, two supported refusals, and one correct unsupported refusal. This small selected smoke is not an aggregate benchmark improvement or fresh held-out certification.

## Experiments
- Original semantic baseline: unchanged historical comparison.
- Focused semantic evidence: all 30 cases completed with zero execution errors. Predates citation recovery and is a separate intervention. Reference F1 fell from 33.5% to 12.2%; supported answers fell from 20/23 to 10/23. Useful-passage precision rose from 38.0% to 69.9%. Answered-only faithfulness fell from 100% to 93.3%. Both configurations correctly refused all 7 unsupported controls. This focused configuration remains off by default.
- Citation recovery: implemented and boundary-tested; full benchmark gain has not been established.
- Optional OpenAI generation comparison: separate approval requested; Ollama remains default.

## Next decision
Preserve original raw F1 for comparisons. Audit reference completeness and judge claim matching before treating 80% as an absolute quality threshold. Any revised evaluation must be versioned and re-score the baseline, not be presented as an answer improvement. Use a new independently authored held-out set after development decisions are frozen. No production-readiness or 80% achievement is claimed.

Full focused-run records and machine-readable comparison are in `evaluation/focused-evidence-results.json` and `evaluation/focused-evidence-comparison.json`. The optional generation comparison is prepared but has not been executed pending the separate generation approval. No default provider change, commit or push.

Subsequent iteration: [expanded-corpus results](expanded-quality-results.md) reached 87.3% reference F1 using validated factual extraction and eight retrieved chunks. The earlier failures above remain historical diagnostics.
