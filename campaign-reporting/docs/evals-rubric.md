# Reporting evaluation rubric v1

These are proposed application-specific acceptance rules, not an industry certification or live accuracy claim.

## Evidence to review

Read the case's pinned aggregate facts, reporting period, required findings and prohibited claims next to the exact output. Do not infer deposit dates or funding fields absent from the source contract. Account/member goals are separate. Exposure overlap cannot establish causal lift. A correction must be described as corrected evidence. Generic cautious text is not sufficient if it omits a material finding.

## Anchored human scores

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| Factual support | Contradicts evidence or invents material facts | Mostly supported but ambiguous or incompletely qualified | Every material assertion supported and appropriately qualified |
| Completeness | Omits/reverses the key result or correction | Captures main result but misses an important caveat | Covers all required material findings concisely |
| Usefulness | Misleading or unusable action | Useful after some analyst editing | Clear, evidence-based next action within human authority |
| Clarity | Confusing or internally inconsistent | Understandable with minor edits | Concise, well-organized and unambiguous |

Scores 2 and 4 are intermediate. Passing a reviewed narrative requires factual support/completeness >=4, usefulness/clarity >=3, reviewer acceptance and no critical violation. These thresholds implement this rubric only. Critical privacy, unsupported factual/causal claims and approval violations override all aggregate scores. A reviewer must explicitly mark critical violations even if the writing is fluent.

## What code can and cannot establish

Code graders check the summary-only schema, numeric-insertion contract, known canaries/contact/identifier/HTML patterns and independent deterministic oracles. They do not establish semantic grounding or usefulness. A fluent false statement with no digits remains unreviewed until human/calibrated semantic evaluation; it cannot pass the release gate merely because code checks passed.

Independent oracle references are manually specified for in-home exclusion, day-60 inclusion, day-61 exclusion, distinct member/account grain, CPA gating, late arrival and zero activity. Portfolio narrative reference labels are proposed synthetic findings and require domain validation.

## Annotation and calibration

Annotations are append-only and tied to experiment, case, repetition and authenticated/simulated analyst identity. The latest annotation is used for current summaries; previous judgments remain in the local database. Review disagreements before promoting a model. Local-demo identity is simulated and does not establish a real domain expert's approval.

Optional AI judging remains disabled until calibrated against reviewed human labels; no automatic self-grading or paid judge is used by default. Randomize order and hide model labels when performing a manual pairwise review. Do not export free-text notes or source/candidate bodies to hosted tracking.

## Metrics and release

Coverage counts distinct scheduled cases, including cases blocked before a provider call. Fully evaluated narrative quality requires all scheduled repetitions reviewed. Reliability is successful invocation completion among started invocations, not factual correctness. Oracle results are displayed separately from narrative quality. No live accuracy is reported from offline/replay mode.

A critical failure blocks release even when the baseline fails too. Paired promotion requires identical case/split/hash/repetition settings, reviewed baseline/candidate judgments and a frozen test run with at least three repetitions. Eligibility means ready for human release review, never permission to publish reports.
