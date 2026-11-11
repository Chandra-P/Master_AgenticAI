# Verification — November 11, 2026

## Evaluation feature — observed final checks

- Full suite: **57 passed, 1 skipped in 66.78 seconds**, using `pytest -q --tb=short --basetemp=runtime/pytest-final-evals`. The skipped real-Postgres check remains unprovisioned. This supersedes the earlier 29-test milestone below.
- Network-prohibited evaluation harness: **27 passed in 34.11 seconds**, followed by 139 development cases. Eight independent calculation oracles passed; 131 narrative attempts remain human-unreviewed. Coverage is 8/139, not a live AI success rate. Release gate: unevaluated. API cost: $0. No validation/final model run, paid judge or remote export occurred.
- Dataset: 264 versioned cases; 25/10/15 client-disjoint chronological development/validation/test split. All five periods stay with their client. Semantic references are proposed and need domain review.
- Regression checks cover malformed/unsafe output redaction, explicit live contract failures, identical production/evaluation goal evidence, foreign-client annotation denial, private-note-free exports, blocked/error denominators, concurrent claims, interrupted resume without reissuing calls, immutable provenance, incomplete paired protocols and mandatory matching oracle evidence before release review eligibility.
- AppTest verifies the Evals panel scopes local execution to the selected client, persists annotations and keeps offline/live quality distinct. No real review annotation was inserted into the demo runtime.
- Ruff and compileall passed after the evaluation implementation. Offline local latency is adapter/harness timing; it is not model latency.
- Fresh read-only review found no Critical issue and three Important findings. Each was fixed with regressions: sanitized live safety failures now block the gate; actual report tools provide confirmed goal facts; paired final release review requires all matching independent oracle checks. Slices and dimension/repetition summaries were added; the manual CI Python step prohibits outbound sockets.
- Remote GitHub workflow execution, calibrated human/model quality, clustered confidence intervals, live-model cost and LangSmith experiment export remain unverified/deferred. The workflow requires an existing self-hosted runner; no hosted spend was initiated.

## Observed in this session

- Full suite after reviewer fixes: **29 passed, 1 skipped in 35.10 seconds**.
- Command: `.venv/Scripts/python.exe -m pytest -q --tb=short --basetemp=runtime/pytest-handoff`.
- Skipped: real-Postgres narrative permissions test, because no Postgres test login/database is provisioned. No claim of tested database-role isolation.
- Streamlit AppTest exercised client selection, Success Plan confirmation, computation, draft generation, rejection/regeneration, fresh attestation, approval and publication.
- Chromium checked desktop 1440×1000 and mobile 390×844: all five periods, section navigation, map measures/keyboard-ready markers, fair-share measures, appendix, CPA gates, no external report requests and no page errors. Screenshots were generated and visually inspected.
- Live demo smoke check: analyst screen and interactive draft iframe loaded at http://127.0.0.1:8510; publication remained disabled without approval. No production/demo fixture report was approved or published by the smoke check.
- Static checks: `ruff check src tests ui dags scripts` passed; `compileall -q src ui dags scripts` passed.
- All-client read-only validation: **50 clients, 250 reporting snapshots, 5,000,000 households, 4,000,000 digitally reached households, 38,000 core account rows and 60,073 attribution matches**. Every snapshot reconciled channel/branch/Checking product counts and direct/Halo/new-member counts. Each pre-120-day CPA was unavailable.
- Sources: 50 compressed synthetic files, approximately 17 MB total; 25 campaign starts in 2024 and 25 in 2025. Runtime/source artifacts are ignored and reproducible.
- OpenAI application calls: **none**. LangSmith exports: **none**. No API budget consumed by the demo.

## Review findings addressed

A fresh read-only reviewer found no Critical issue in the local demo and identified one Important issue: attestation could remain checked after changing the reviewed draft. Regression test first failed, then passed after binding attestation state to client/run/hash/revision. A minor stale-map-detail issue was also reproduced and fixed; changing period now clears previous branch details.

Earlier tests caught a Checking product table that included other products and a narrative repository list returning reviewer feedback. Both were fixed with failing-then-passing regression checks. Audit-write failure rolls back approval; concurrent duplicate triggers claim one run; parallel budget reservations cannot exceed $5.

## Unverified or deferred

Postgres grants/RLS, real Airflow scheduling, corporate OIDC, external LLM extraction, live OpenAI narrative quality, LangSmith export and production infrastructure have not been exercised. SQLite and simulated identity are local demonstration adapters, not verified production security. See README.md and docs/security-boundaries.md.

Initial sandbox runs hit temporary-directory, network and subprocess restrictions. Approved dependencies/browser were installed outside those restrictions; the full UI/browser suite ran successfully with escalation. AppTest emits its documented bare-mode ScriptRunContext warning; no application exception remained.

Observed final browser smoke: running analyst screen, interactive draft and client-scoped Evals tab passed; analyst-evals.png was visually inspected. No report approval/publication or human eval annotation was submitted.
