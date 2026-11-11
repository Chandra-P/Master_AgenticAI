# Reporting evaluation design — proposed November 11, 2026

Status: owner confirmed the proposed evaluation approach after clarifying cost and success measures; implementation is proceeding. This is not a claim of measured live AI performance. Execution details are in evals-implementation-plan.md.

## Intent

Evaluate the reporting system's factual grounding, task completion, tool boundaries, operational reliability and analyst usefulness. Keep software tests, offline-adapter checks, live-model quality and human judgments separate. Preserve the $5 total POC OpenAI cap, with no new subscription or paid platform requirement.

Sources consulted: [OpenAI evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices) and [LangSmith evaluation types](https://docs.langchain.com/langsmith/evaluation-types). This is a task-specific application of those practices, not industry certification or official Vericast policy.

## Approach and alternatives

Recommended: maintain datasets, rubrics, graders and release policy in Git; run locally and in CI; optionally export privacy-filtered experiments to the already-approved LangSmith integration. This fits the approved local stack and spending constraint. A hosted-first evaluation platform would provide convenient annotation/comparison UI but add dependency on external access, privacy configuration and usage limits. A tests-only approach cannot establish semantic narrative quality. Do not add either an extra paid platform or a claim that local regex checks prove groundedness.

## Evaluation boundaries

1. Deterministic computation: independent hand-checked fixtures for DM boundaries, duplicate/joint accounts, distinct members, overlap, late arrivals and CPA gating.
2. Narrative task: required evidence, correct direction of comparisons, material caveats, separation of observed/projected results, no unsupported causal inference and no invented facts.
3. Tool execution: authorization, scoped arguments, expected aggregate schema, invocation provenance, retries and failures. Current tools are application-invoked: model tool-selection accuracy is not applicable until a model-directed workflow exists.
4. Review/delivery: exact-draft approval, blocked publication on rejected/stale drafts, audit integrity, correction versioning and recovery.
5. Observability and cost: per-attempt latency/usage, failures/timeouts, persistent reservations and no sensitive payload export.
6. Extraction: register as not implemented, rather than reporting a passing score. Once extraction exists, evaluate exact field accuracy, missing/conflicting-field abstention and verbatim source evidence before enabling it.

## Dataset and leakage prevention

Use the 50 fictional campaign clients as scenarios, not as proof of production representativeness. Five periods per client are correlated. Fix a versioned client-level split: 25 development clients starting in 2024, 10 validation clients from earlier 2025, and 15 locked test clients from later 2025. No client's periods appear in multiple splits. Record exact client IDs, scenario IDs, dataset revision and provenance in a manifest.

Development examples may guide prompt edits. Use validation for candidate selection. Run the frozen final test only after a candidate is selected; do not repeatedly tune against its outputs. New test exposures and changes require an explicit dataset-version record.

Add independently authored edge/adversarial fixtures beyond ordinary campaign periods: CPA unavailable, zero denominators, accounts ahead/members behind, low forecast below goal, correction explanation, unsupported incrementality, omitted limitations, prohibited identifiers, foreign-client access, prompt injection and timeouts. Expected answers come from reviewed fixtures/rubrics, not the same function under evaluation.

Each case stores ID, split, task, tags, allowed aggregate input, reference facts/claims, required caveats, prohibited claims and expected action/abstention. Cases have no real member records. Keep manual annotation status explicit: synthetic labels are proposed until a domain reviewer validates them.

## Rubrics and graders

Hard code-based checks: valid structured output, bounded content, strict allowed fields, referenced metric IDs belonging to the supplied run/period, controlled numeric insertion, canary exclusion, scoped tools, forbidden side effects and approval boundaries.

Semantic criteria: every material claim is supported by the supplied evidence; conclusions distinguish actuals from forecasts; important shortfalls/corrections are described; recommendations do not claim exposure proves incremental lift. Do not equate keyword presence or absence of digits with semantic correctness.

Human rubric: factual support, completeness, actionable interpretation and clarity, each with anchored examples and a small ordinal scale. Human labeling is initially pending. Reviewer notes remain in restricted local artifacts, excluded from external prompts/traces unless explicitly sanitized and approved.

Optional LLM judge: not a default cost dependency. Only enable a bounded evaluation adapter under the same POC budget after human rubric calibration. Store judge model/prompt/rubric versions; treat candidate text as untrusted data; randomize A/B order for blinded pairwise comparisons; measure agreement and inspect disagreements. A model's self-score is never ground truth or sufficient to pass a safety gate.

Test graders themselves with planted good/bad outputs. A useful grader must catch incorrect statements with no digits, generic unhelpful text, fabricated caveats, missing key findings and attempts to influence the judge. Some semantic outcomes must remain needs-human-review if no calibrated semantic evaluator is available.

## Runner and experiment records

Persist a versioned experiment manifest: code revision, dataset/split hashes, model identifier, prompt/rubric/grader versions, sampling settings, seed where supported, execution mode, start/end timestamps and budget reference.

Record each attempt with case/client/period IDs, repetition, input reference/hash, output reference/hash, tool attempt IDs, grading outcomes, latency, usage and reserved/actual cost. Distinguish cache replays from new calls. Missing credentials, budget blocks, provider errors and timeouts are explicit outcomes, not silently removed cases.

Repeated live trials measure variability on a small selected set before expanding. Offline adapters/replays are labeled and excluded from live model accuracy claims. Human-review time is measured separately.

Local results survive restart and are append-only experiment artifacts. Export only an allowlisted synthetic aggregate experiment summary to LangSmith when explicitly enabled; tracing/evaluation never receives raw source records, arbitrary exception messages or secret values. A local dashboard works without external credentials.

## Metrics and proposed release gates

Report coverage and per-dimension metrics rather than one flattering aggregate:
- Scheduled coverage: unique scheduled cases with completed required evaluations / all unique scheduled cases. Report budget-blocked, skipped, errored and unreviewed scheduled cases explicitly; a pre-call budget block must not disappear from coverage.
- Completed-case quality: unique fully evaluated cases satisfying all required criteria / unique fully evaluated cases. Display this together with coverage, never alone. Repetitions do not multiply the unique-case denominator.
- Per-attempt reliability: successful completed invocations / invocations started, with errors/timeouts as failures and retries counted as attempts. Pre-invocation blocks are separately reported. Distinguish invocation success from semantic correctness.
- Factual-support and task-completion scores, critical boundary failures and analyst acceptance.
- Breakdown by task, scenario, client, year and reporting period.
- Repetition stability, latency p50/p95, token usage and cost.
- Candidate-vs-baseline paired outcomes on identical cases.
- Where sample size supports it, uncertainty intervals clustered by client. Do not treat 250 correlated periods as 250 independent clients.

Proposed gates require owner review: no observed critical privacy/access/approval violations; all deterministic oracle cases pass; no new factual regression on the frozen benchmark. A factual regression means that, on the same case and paired repetition protocol, a candidate introduces an unsupported factual assertion or loses a required material finding that the reviewed baseline handled correctly. Unsupported counts, reversed goal comparisons, false funding/date evidence and exposure-to-causality claims are critical; missing required caveats/material shortfalls are important. Style preferences are separate quality ratings.

Predeclare equal repetitions for baseline/candidate (default three where the budget permits), with identical cases and sampling settings. Aggregate repeated semantic judgments at the case level and report per-attempt variation. Any critical violation in any repetition blocks release; report material finding/caveat pass rate per case. Baseline/candidate factual regression labels must be human-reviewed or produced by a human-calibrated grader with disputes adjudicated. Without those labels or complete required repetitions, the regression gate is unevaluated, never pass. Do not excuse a candidate safety failure because the baseline also failed.

Semantic results require reviewed/calibrated labels before promoting a model. Keep review_mode=all; no eval result authorizes autonomous publication or spending. Do not impose an arbitrary universal 95% AI success threshold.

A run with only offline/structural checks must be labeled partial coverage, not live-model success. An unevaluated required semantic criterion cannot yield a passing release gate.

## Execution and budget

Phase 1: local datasets, independent reference cases, rubric, deterministic/mutation tests, offline baseline, results dashboard and no-network CI. No paid calls or account setup required.

Phase 2: securely configure the funded OpenAI adapter, verify current model pricing, then run a small budget-reserved live validation batch. Both generation and any optional judge consume the existing $5 total cap; do not promise the whole benchmark fits before pricing/token estimates. Fail closed on missing pricing/credentials, unknown usage or exhausted reservation budget. Obtain human annotations before asserting a live quality score.

Phase 3: frozen test and baseline comparison, followed by release gating. During the pilot, capture explicit human rejection/correction categories and add sanitized reviewed failures to the development set. Online monitoring is not a substitute for offline release tests.

Fast local/recorded-output checks are intended for each PR after runner/billing confirmation. Initially the workflow is manual-only on an existing self-hosted runner. Dependency setup may download packages; the Python evaluation step prohibits outbound socket connections and external exports. Fresh live-model experiments are explicit/manual and capped rather than charged on every commit. Rerun them before changing a production model/prompt or increasing autonomy. Live production monitoring remains pending until production exists.

## Proposed file changes

All paths are under campaign-reporting/.
- Add docs/evals-design.md and docs/evals-rubric.md.
- Add evals/manifest.json and evals/cases.jsonl for versioned split/case contracts.
- Add src/campaign_reporting/evaluation/{contracts,dataset,graders,runner,results}.py.
- Add scripts/run_evals.py with explicit offline/replay/live modes.
- Add tests/test_evaluation_{dataset,graders,runner,privacy}.py.
- Modify narrative.py and openai_adapter.py only where needed to carry pinned evidence/run/prompt provenance into evaluation.
- Modify ui/app.py to add a results view and local annotation controls.
- Add .github/workflows/campaign-reporting-evals.yml for no-network/local evaluation gates only; use path filters and do not require paid GitHub minutes or provider credentials for ordinary checks.
- Update README.md, VERIFICATION.md and existing local continuity files.

No database migration, production access, new paid service, public hosting or outbound message is included. Local evaluation artifacts live under ignored runtime/evals/ and contain synthetic aggregates only. No secret provisioning through chat.

## Acceptance and risks

Acceptance: reproducible offline experiments, client-disjoint fixed splits, graders demonstrated against planted failures, explicit partial/unreviewed states, truthful denominators, paired comparisons, no privacy canaries in exports, restart-safe results and no implicit live calls. Existing application/browser checks remain green.

Risks: synthetic-only fixtures may not represent actual analyst work; semantic judges can be biased or manipulated; small live samples cannot support broad accuracy claims; the $5 cap may constrain repetitions. Mitigate with explicit coverage labels, human calibration, independent fixtures and staged deployment with all reports reviewed.

The owner is approving this concrete scope before implementation. Existing demo remains available throughout.
