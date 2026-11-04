# RAG Answer Improvement Implementation Plan

**Goal:** Work toward 80% reference F1 while retaining source validation and correct refusals.
**Architecture:** First isolate generation from retrieval using frozen semantic contexts; promote a prompt only after measured improvement. Ollama remains default. OpenAI is optional, and judge scores remain independent of runtime validation.
**Tech stack:** Existing Python, Ollama, RAGAS and optional OpenAI.

## Design and alternatives
The user authorized work toward the previously proposed improvements. The existing quality plan records standing authorization to execute without confirmation pauses. Keep the current workspace to preserve uncommitted pure-RAG changes.
Compare question-focused generation first; retrieval changes and a stronger generator are separate experiments. Do not change corpus or references to inflate scores. Preserve exact quotation/citation validation. A question may need multiple claims, but unrelated facts must be omitted. Unknown or missing evidence must not be invented.

## Tasks
- [ ] Run frozen-context prompt experiment, saving every answer, exact prompt, model identity and judgments. Retain all 23 supported cases including refusals as zero in primary F1, plus all 7 unsupported controls.
- [ ] If improved, promote the prompt, version its identity in evaluations, and add meaningful source-validation regression checks. Otherwise retain the existing runtime and diagnose results.
- [ ] Verify relevant tests and report actual measured gains, regressions and remaining gaps.

## Constraints and review focus
No secrets in artifacts; no commit or push requested. No default provider change. Do not reuse historical scores as current after changing generation. Inspect multi-part questions, genuine missing evidence, unrelated source facts, invalid citations, and unsupported questions. The reused benchmark is developmental; fresh independently authored held-out evaluation remains required. No claimed 80% result without measured evidence.

## Execution ledger
- Root cause confirmed: broad quoted answers add unrelated facts; multi-part answers omit available breakdowns. Existing context focusing also omitted the numeric Channel Results section.
- Long and short question-focused prompt trials were rejected after single-fact relevance regressions. Runtime answer instructions remain exactly unchanged. The short local-only trial completed three of six planned cases, with one generation error; its partial artifact is explicitly labeled rejected and has no new judged metrics.
- Fixed opt-in context selection to preserve Channel Results, KPI Results and Channel Insights together. Missing-section fallback remains unchanged. Watched the dropped-breakdown regression fail before the fix.
- Added answer prompt + schema SHA-256 to generated evaluation identities and strict current-score loaders. Old generated scores lacking this identity are historical and no longer appear current; no historical data was deleted. Retrieval-only identity compatibility preserved, with regression coverage.
- Fresh static reviewer found a retrieval-only identity regression; corrected it. Follow-up review found no remaining actionable issues.
- Automatic approval review rejected hosted evaluation because it requires explicit approval to transfer benchmark questions, reference answers and retrieved campaign passages to OpenAI. Asked for that specific approval asynchronously; pending. No workaround or further hosted evaluation was attempted. Local Ollama trials load no API keys.
- No score improvement claimed. The 80% goal is outstanding. Next: obtain approval for independent scoring or agree on local/manual scoring, measure focused evidence separately, then compare optional stronger generation as a separate profile. Developmental benchmark reuse must not be described as fresh held-out certification.

- Verification: full non-live suite passed (135 tests, three existing RAGAS deprecation warnings); git diff --check passed. No commit or push.

## Approved evaluation continuation
The user explicitly approved OpenAI evaluation of benchmark questions, references and passages. Focused semantic run uses local Ollama generation, unchanged prompt and all30 original cases. OpenAI generation comparison separately requested, pending.

## Evidence-led citation repair design
Local draft diagnostic shows an exact objective quote rejected because its citation list is empty. Recover only a unique exact retrieved-source match for a nonempty quote when no citation was supplied. Preserve valid explicit citations; reject unknown, wrong or ambiguous citations. Never use reference answers in runtime repair. Keep original claim immutable. Add a grounding contract version to generated evaluation identity so previous results cannot masquerade as repaired runs. Test the unique/duplicate/invented/wrong-ID/blank boundaries before implementation, then measure actual generated answers separately. This recovery identifies provenance and does not claim entailment or relevance.

## Citation recovery verification
- Exact-match recovery regression was watched failing before implementation; unit boundaries then passed. Added an integration assertion that grounded_answer emits the real recovered citation.
- Full non-live suite: 137 passed, three existing RAGAS deprecation warnings. Static follow-up review found no source-validation/security issues.
- Grounding contract version2 is included in the generated identity. Original system prompt remains unchanged. Citation recovery does not repair unknown/wrong explicit citations or ambiguous exact matches.
- OpenAI q11 trace confirmed the reference F1 metric's strict NLI rejects a correct activation total when the terse reference lacks the campaign ID/verified qualifier. The same trace confirms channel breakdown is genuinely absent. Preserve the original metric and references; do not claim a changed evaluator is an answer improvement.

- Focus-only evaluation finished all30 cases, zero execution errors: F1 0.1217 vs baseline0.3348; answered10/23 vs20/23; passage precision0.6986 vs0.3804; faithfulness0.9333 on10 answered; all7 unsupported refused. Rejected as a default. This run predates citation recovery. Four-case recovery smoke: one supported case F1=1, two supported refusals, unsupported control refused. No full-score claim for recovery. Optional OpenAI answer-generation approval remains pending.
