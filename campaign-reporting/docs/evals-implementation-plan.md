# Reporting Evals Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans task by task in the existing isolated worktree. Do not delegate implementation. A fresh read-only final review is required.

**Goal:** Add a truthful, reproducible local evaluation system and analyst quality review to the existing reporting demo.
**Architecture:** Versioned client-disjoint cases and independent oracle fixtures feed a restart-safe SQLite experiment store. Deterministic graders enforce contracts; explicit human annotations establish semantic quality. Offline/replay/live modes remain distinct, with live calls sharing the existing $5 ledger.
**Tech Stack:** Existing Python 3.12/Pydantic/pytest/Streamlit/OpenAI packages; standard-library SQLite and statistics. No new dependency or database migration.
**Spec:** docs/evals-design.md, accepted through the owner's follow-up confirmation after cost/success-measure clarification.

## Global constraints

- Existing worktree/branch: codex/campaign-reporting. Preserve unrelated projects and existing demo.
- $5 USD total for every POC report, generation, judge, retry and correction; no automatic top-ups.
- No private env file inspection, credential values in output, production access, notifications or deployments.
- Keep all pilot reports human-reviewed. Eval success never authorizes publication.
- Local/offline/replayed performance is not live-model performance.
- Untested, skipped, blocked and human-unreviewed cases cannot silently count as successful.
- Live inference requires explicit mode, secure configuration and current prices. No paid judge until human calibration.
- CI check step makes no provider calls. GitHub workflow manual-only until hosted billing limits are confirmed.

## Review focus

1. Repetitions, skipped cases and pre-call blocks must not inflate coverage or quality.
2. Client-disjoint chronological splits and immutable dataset fingerprints prevent accidental leakage.
3. Replayed/claimed attempts must not cause duplicate provider charges after crash or concurrent runs.
4. Sensitive canaries and unrestricted exception text must not reach stored outputs or exports.
5. Semantic scores require scoped human annotations; code checks alone cannot pass release gates.

## Files and interfaces

- evals/manifest.json, evals/cases.jsonl: versioned cases and split policy.
- src/campaign_reporting/evaluation/contracts.py: strict Case, Check, Annotation contracts.
- dataset.py: load_dataset(path), build_dataset(destination), validate split/evidence boundaries.
- graders.py: grade_output(case, output) -> list[Check], with human-required semantic criteria explicit.
- results.py: EvaluationStore, transactional claims, immutable attempts and append-only scoped annotations.
- runner.py: run_experiment(...), modes offline/replay/live; aggregate_summary(...), compare_experiments(...).
- scripts/build_eval_dataset.py, scripts/run_evals.py: explicit operator commands.
- src/campaign_reporting/evaluation/ui.py: scoped results/annotation UI embedded by ui/app.py.
- docs/evals-rubric.md, README.md, VERIFICATION.md: rubric, instructions and actual evidence.
- .github/workflows/campaign-reporting-evals.yml: manually invoked no-provider-call checks.
- tests/test_evaluation_{dataset,graders,runner,privacy,ui}.py.

## Task 1: Cases, independent references and graders

- [x] Write failing tests for 25/10/15 unique-client splits, chronological separation, all five periods, duplicate IDs, unsafe fields and modified manifest hashes.
- [x] Write graders' planted good/bad output tests: schema, disclosure, invented numbers, disallowed causal claims and unreviewed semantics.
- [x] Run tests and verify expected missing implementation failures.
- [x] Implement strict case/evidence schemas and a deterministic builder from existing synthetic aggregates. Include independent hand-authored oracle/edge/adversarial cases. Mark proposed semantic labels unreviewed.
- [x] Implement contract/risk graders with explicit heuristic limitations. Return human-review-required for grounding/completeness/usefulness/clarity.
- [x] Verify targeted tests pass and rubric defines anchored scores and critical failures.

## Task 2: Persistent experiments, accounting and comparison

- [x] Write failing tests for scheduled/attempted/completed denominators, repeated cases, pre-call budget blocks, errors, resume, duplicate claims, scoped annotation, stale dataset, privacy filtering and cached replay labeling.
- [x] Implement EvaluationStore with immutable experiment/case metadata, per-attempt transactional claims and append-only annotations. Interrupted attempts stay unresolved and are not automatically reissued.
- [x] Implement offline/replay/live runners. Live adapter uses the same POC budget path; unavailable configuration is blocked before a call, never a success.
- [x] Persist provenance/model/prompt/rubric/grader versions, hashes, token/cost/latency metadata and sanitized error categories.
- [x] Implement coverage/quality/reliability summaries, critical/semantic release gates, client/task/period/year slices and paired case/repetition comparisons. Missing labels yield unevaluated. Live quality remains unavailable for offline modes.
- [x] Verify targeted tests and simulate a resume without duplicate attempts.

## Task 3: Analyst dashboard and manual annotations

- [x] Write failing Streamlit tests for a selected client's results, pending semantic review, annotation persistence and denied foreign-client access.
- [x] Add local development benchmark button, experiment/slice view, per-report cost view, score/rubric controls and explicit partial/live labels.
- [x] Keep holdout execution out of casual dashboard controls. Require explicit CLI allow-heldout and selected candidate reference; persist exposure.
- [x] Verify the existing report workflow and new eval panel using AppTest; ensure no provider calls in local UI path.

## Task 4: Checks, documented baseline and handoff

- [x] Add operator scripts and manual-only workflow with provider credentials absent and offline networking prohibited during evaluation tests.
- [x] Run development benchmark, repeated local cases, planted-failure/known-bad grader validation and resume check. Do not run heldout for prompt tuning.
- [x] Run full pytest suite, Ruff, compileall and existing desktop/mobile browser checks. Inspect the live results screen.
- [x] Perform a fresh read-only final review, fix material findings with regressions, record actual outcomes and remaining live/human-validation limitations.
- [x] Commit/push only the new feature to the existing project branch and update local continuity.

## Acceptance

Versioned cases are client-disjoint, local experiments are reproducible and restart-safe, grading mutations are detected, metrics use explicit denominators, human annotations are scoped and do not imply live accuracy, cost is shown per attempt/report with the shared cap, no network calls occur offline, and existing demo/browser tests remain green. Optional live calls/judge and remote experiment exports remain unmeasured until safely configured; this must be visible rather than reported as a passing feature.



Implementation notes: eval UI is colocated with the evaluation package. Human calibration, clustered confidence intervals, live quality and remote LangSmith export remain explicitly deferred; no passing semantic claim is made. Workflow is manual-only on an existing self-hosted runner. Final full suite: 57 passed, 1 skipped. Network-prohibited eval harness: 27 passed; 139 offline cases, 8 passing oracles and 131 unreviewed narratives. Browser smoke and screenshot inspection passed; no fixture approval/publication.
