# Synthetic Campaign Reporting Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task by task. Steps use checkbox syntax for tracking. Do not delegate unless the owner requests it.

**Goal:** Reproduce the supplied report's complete flow for fictional Juniper Valley Credit Union through a local, production-style pipeline using exclusively synthetic records.

**Architecture:** Postgres stores restricted source records, immutable analytical snapshots, approved aggregate facts, and audit records. Airflow orchestrates readiness and deterministic computation; LangGraph drafts narrative from scoped aggregate tools; Streamlit captures configuration and review decisions; a renderer delivers the approved HTML version.

**Tech stack:** Python, Postgres, Docker Compose, Airflow, LangGraph, Streamlit, HTML/CSS/JavaScript. Exact supported dependency versions must be verified from official documentation during implementation before installation. Use SQL/Python for local computation; Spark is unnecessary for the initial data volume.

**Spec:** The architecture approved in conversation on November 11, 2026 and the design contract below. The owner supplied `campaign reporting build spec.md`, `DFCU_Members_checking_Accts.sql`, and `Desert Financial Checking Engine - Day 30 9.html` as references. Attachment paths are inputs for this session, never runtime dependencies.

## Design contract

### Current local-demo milestone — November 11, 2026

Owner subsequently requested 50 fictional clients: 25 campaigns in 2024 and 25 in 2025. The owner approved a Git worktree, dependency installation, startup, builds/tests and browser checks, and chose to keep the project in Master_AgenticAI rather than a separate repository. The runnable local demo is implemented on codex/campaign-reporting; details and actual verification are in README.md and VERIFICATION.md.

Ruling: Docker/Postgres are unavailable on this host, so persistent SQLite is an explicitly labeled local harness; Postgres roles/adapter and Airflow asset DAGs are supplied but not runtime-verified. This does not establish production readiness. The morning-demo milestone does not complete the plan's production-profile integration, real OIDC, live model extraction/evaluation or external tracing setup.

Ruling: Preserve Python/Playwright browser tests alongside pytest rather than introducing a separate TypeScript test runner. All report controls and desktop/mobile rendering are exercised using the same project environment.

Observed: full suite 29 passed, 1 Postgres test skipped; read-only validation reconciled all 50 clients and 250 period snapshots. No real-data access, external notification, model calls or LangSmith export occurred. OpenAI authorization remains $5 total; demo mode makes no paid calls.

- Owner-approved: fictional branding; preserve report experience, navigation, section order, reporting periods, charts, maps, recommendations, executive summary, and appendix.
- Owner-approved: synthetic source records, deterministic metrics, aggregate-only narrative tools, human review, versioned delivery, production-style security boundaries.
- Narrative tools: `get_metrics(run_id)`, `get_rules_context(run_id)`, `get_flag_status(run_id)`, `get_prior_version(run_id)`. Server-resolved client authorization is mandatory; a model-supplied run ID alone grants no access.
- Report order: The Goal; What Is Happening; Early Signals; Where We Land; Recommendation; Executive Summary; Appendix.
- Offline narrative adapter first; external model calls remain disabled. Owner approved LangSmith integration on November 11, 2026 for privacy-filtered observability as described below. Export remains opt-in and requires secure credential provisioning and destination configuration; do not capture raw payloads or incur charges without separate authorization.
- Proposed implementation detail: local authenticated analyst UI and local report storage for the milestone. No public hosting or claim of production readiness.
- Proposed implementation detail: retain immutable audit/fact history; any two-version display limit applies to the report listing, not automatic evidence deletion.
- Proposed implementation detail: matching labels describe observed source matches, never causal lift. Membership counts distinct members; Checking counts distinct accounts. Household counts are separately labeled.

## Global constraints

### Owner-confirmed campaign rules — November 11, 2026

These supersede earlier proposed metric definitions wherever they differ. They are owner-confirmed requirements, not implemented or tested behavior.

- Checking campaign only, with two direct-mail drops and digital advertising. Reporting views: 30, 60, 90, 120 days and final.
- Three success measures: Checking accounts, new members, and cost per Checking account.
- The MCIF/core extract includes active, funded accounts by the owner's source contract. It has account-open dates but no funding indicator or deposit-event dates. Inclusion is accepted funding evidence; do not invent a deposit date or require an unavailable funding field.
- Account-open date determines tracking-window eligibility, including for late-arriving extract records. Preserve previously counted eligible accounts even if they subsequently close or disappear from an active-only extract. Snapshot history is therefore required.
- Each direct-mail tracking window excludes the in-home date and includes the following 60 calendar days: `open_date > in_home_date AND open_date <= in_home_date + 60 days`. Mailing 1 eligible dates: March 17 through May 15, 2026 inclusive. Mailing 2: May 19 through July 17, 2026 inclusive.
- Digital has a start date; TU handles attribution. Accept `exposeduserflag = 1` rather than inventing a local digital-duration rule.
- DM matchback eligibility uses `response_flag = 1`; the upstream reporting matchback process enforces the 60-day window.
- Qualifying overlaps count once in campaign totals. Preserve all qualifying mailing/channel matches; channel breakout uses mutually exclusive Both, Digital Only and DM Only categories.
- New members include any product, not just Checking. The upstream reporting matchback process compares member IDs against the pre-campaign file to identify new members.
- One new member opening Savings and two qualifying Checking accounts contributes one new member and two Checking accounts.
- Checking totals include qualifying accounts opened by both existing and new members, including multiple distinct Checking accounts per member. Owner explains that this prospect campaign can contain existing-member responses because of source-file timing and suppressions. Do not exclude those accounts or add a separate audience-quality exception/flag for them. New-member totals still include only members classified new by upstream matchback.
- Forecast follows the reference report's historical Checking campaign response-curve approach, using generated synthetic historical campaigns rather than real campaign data or an unsupported claim of historical validation. Compute projections and ranges deterministically; the exact fitting and range methodology must be documented and tested.
- CPA is unavailable before day 120. At day 120 or later, it becomes available only when both mailings and digital have gone live. If all components launch as planned, use the full $215,000 campaign budget divided by qualifying Checking accounts, not spend-to-date.
- Fictional campaign budget: $215,000; 70% ($150,500) direct mail and 30% ($64,500) digital. Each mailing receives $75,250.
- Success targets: 601 Checking accounts, 605 new members, maximum CPA $358.17. The Checking target was raised from 559 because $215,000 / $358.17 requires at least 601 accounts.
- Mailing 2 targets the same 100,000 households as Mailing 1: 200,000 total mail pieces, not 200,000 distinct households. Digital reaches 80,000 of these households (80% coverage).
- Owner-approved past synthetic dates: digital launch March 9, 2026; Mailing 1 in-home March 16, 2026; Mailing 2 in-home May 18, 2026. These are invented campaign dates, not source observations.
- Reporting-day anchor: digital launch March 9, 2026. Digital end date must come from the analyst-confirmed Success Plan; the fictional plan uses June 30, 2026. Final report date: July 31, 2026, after both DM windows and the digital flight end. TU still determines digital attribution; do not substitute flight dates for TU attribution logic.
- Which mailing(s) digital supports is campaign-specific and must be specified in the analyst-confirmed Success Plan. Forecasting must read that configuration, not hardcode the reference report's DM-only second-mailing assumption. For this fictional campaign, owner approved digital support for both mailings. This planned support is distinct from each account's observed TU/DM matches.

- New work belongs in `campaign-reporting/`; preserve unrelated workspace edits, especially Tagalong.
- Synthetic records are generated from scratch, never masked copies of source customer data.
- No external notifications, deployment, production access, or production migration. Owner subsequently authorized OpenAI API use from existing funded access up to $5 total for this POC, subject to the controls below; this supersedes the earlier blanket prohibition on paid model calls only within that allocation.
- Owner constraint added November 11, 2026: no additional personal out-of-pocket spending for the POC; preserve engineering quality. Prefer existing local hardware and open-source dependencies. No billable usage, automatic overage, trial-based infrastructure or paid upgrades without explicit revised authorization. LangSmith approval is integration approval, not spending approval. Confirm any existing funded model access before enabling live inference; clearly distinguish offline/template or local-model demonstrations from evaluated hosted-model performance.
- Owner reports existing funded OpenAI access/credits and authorizes $5 USD total for this POC, not per run or per month. The cap includes extraction, narrative, evaluation and retry calls. Account balance, expiry, permitted project, credentials and API access have not been verified. No automatic top-up or personal spending beyond the existing allocation is authorized.
- Before any model call, atomically reserve a conservative maximum request cost using verified current model pricing and bounded input/output tokens. Persist reservations and actual token charges across restarts; include parallel requests and retries. Failed/ambiguous requests retain their reservation until reconciled. Block live calls when prices are unknown, the funded allocation is unavailable or the $5 cap cannot cover the next reservation. Offline operation must remain available. Application cap applies to this POC only and cannot control unrelated usage sharing the provider account; prefer a dedicated API project.
- Obtain approval before installations, startup, build, or tests; planned commands below have not run.
- No raw identity/address/account fields in AI payloads, report HTML, logs, traces, or browser responses outside the authorized diagnostic view.
- Source and review files, generated narratives, and tool responses are untrusted inputs.
- Every delivery requires human approval in the pilot. Any regenerated draft invalidates the prior approval.
- Secrets must not be committed, printed, included in examples, or persisted in local memory.
- Local Compose is a learning deployment. Production secret management, TLS termination, identity provider, network policy, backups, and deployment hardening require an environment-specific follow-up.

## Owner-approved observability — November 11, 2026

- Correlate Airflow tasks, model calls, tool attempts, review decisions and report artifacts using an opaque run ID plus trace/span IDs. Preserve parent/child relationships; link resumed review execution to the same durable run without keeping a machine-processing span open during human wait.
- Airflow supplies orchestration status, queue time, task duration, retries and failures. LangSmith supplies agent/model/tool execution traces. OpenTelemetry instruments cross-service spans. The operational database remains the authoritative audit record for approvals and delivery, regardless of trace sampling or retention.
- Record tool name, call origin (model-requested or application-invoked), attempt, sanitized status/error category, authorization outcome, monotonic duration, schema versions and item count. Model spans record provider/model, prompt version and token counts; mark offline narrative adapter executions distinctly and never report them as live model usage.
- Capture model-requested calls and actual execution outcomes separately so rejected/invalid requests are visible without persisting unrestricted arguments. Use opaque references in traces; never expose identity mappings through trace metadata.
- Metrics: p50/p95 latency by stage/tool/model, queue duration, failure/timeout/retry rates, calls per report, token usage, estimated model cost and approval/rejection rates. Separate human-review waiting time from machine execution latency. Avoid run/client IDs as unbounded metric labels; keep those in access-controlled trace/audit records.
- Before export, allowlist attributes, hide all prompt/tool input/output bodies by default, sanitize exception messages and metadata, and test each exporter with planted sensitive canaries. Privacy filtering failure must suppress export rather than leak payloads. Document access permissions and retention for the selected LangSmith project.
- Export is explicitly configurable and disabled until credentials/destination are provisioned safely. Never ask the owner to paste API keys into chat. No LangSmith provisioning, exports, paid calls or leakage tests have run yet.
- Local observability must work without external credentials. Export/network failure must not bypass approval or lose authoritative audit events. Operational audit-write failure blocks approval/publication; telemetry-export failure is recorded locally without sensitive content.

## Review focus

1. Cross-client run IDs must fail at service and database boundaries (Tasks 1, 3, 4).
2. Duplicates, joint holders, multiple products, and repeated snapshots must not inflate distinct counts (Task 2).
3. Restart, concurrent triggers, repeated approval clicks, and delivery retries must preserve one approved artifact per version (Tasks 3, 4).
4. Raw sensitive canaries and malicious narrative HTML must never reach outputs or telemetry (Tasks 4, 5).
5. Period switching must update every dependent chart, table, narrative, and appendix consistently, including missing/zero values (Task 5).

## File map

All paths below are under `campaign-reporting/`.

| Files | Responsibility |
|---|---|
| `README.md`, `pyproject.toml`, `compose.yaml`, `.env.example`, `.gitignore` | Reproducible local setup and safe configuration |
| `docs/design.md`, `docs/report-inventory.md`, `docs/security-boundaries.md` | Durable approved contract, reference interaction inventory, permission matrix |
| `db/001_schema.sql`, `db/002_roles.sql` | Explicit local provisioning, constraints, roles and client isolation |
| `src/campaign_reporting/contracts.py`, `config.py`, `repository.py` | Typed contracts, configuration, authorized database access |
| `synthetic.py`, `readiness.py`, `compute.py`, `runs.py` | Deterministic generation, validation, calculations and lifecycle |
| `tools.py`, `narrative.py`, `review.py`, `delivery.py` | Aggregate tools, checkpointed draft/review, immutable publication |
| `observability.py`, `tests/test_observability.py` | Privacy-filtered spans, local telemetry, opt-in LangSmith export, latency and leakage checks |
| `dags/campaign_reporting.py`, `ui/app.py` | Orchestration and authenticated analyst workflow |
| `templates/report.html`, `static/report.js`, `static/report.css`, `static/map.svg` | Report layout, interaction and local fictional map |
| `tests/test_*.py`, `tests/browser/report.spec.ts` | Computational, security, lifecycle and browser acceptance |

The Python filenames after `repository.py` also live under `src/campaign_reporting/`.

## Task 1: Restricted synthetic sources and database foundation

**Interfaces:** `generate_sources(seed: int, client_id: str) -> SourceBundle`; `provision_local_database()` is an explicit operator action, never an import side effect. `ActorContext` carries authenticated actor, allowed client, and service role.

- [ ] Write the design/security docs and inventory every reference section, reporting period, control, asset, dynamic field, and external resource; replace real content rather than simply renaming the HTML title.
- [ ] Add failing `tests/test_sources.py` and `tests/test_permissions.py`: identical seeds reproduce records; two clients remain isolated; narrative credentials cannot SELECT source records; synthetic schema contains account/member/household identifiers and account-holder links.
- [ ] After command approval, run the targeted tests and confirm the expected missing implementation failures.
- [ ] Implement source schemas for members, accounts, account holders, exposures, DM responses, mailed recipients, branches, costs, campaign configuration revisions, and rules revisions. Use fixed-point money and explicit dates/time zones. Separate analytical and Airflow metadata databases.
- [ ] Implement database roles for ingestion, computation, narrative aggregates, review, and delivery. Apply client isolation, including ownership/bypass behavior tests. Seed two fictional clients and sensitive canary strings used only by tests.
- [ ] Verify the targeted tests and document local provisioning commands without running production migrations.

## Task 2: Matching, marts, metric contracts and projections

**Interfaces:** `compute_report_facts(snapshot_id: str, config_version: str, rules_version: str) -> ReportFacts`; facts carry metric ID, value, unit, period, methodology, limitations and provenance.

- [ ] Write `tests/test_compute.py` with hand-calculated expectations for digital-only/DM-only/both, repeated exposure rows, joint accounts, multiple accounts per member, exact/ambiguous address matches, zero spend/conversions, late openings and null dates.
- [ ] Specify CPA denominator, cost allocation, funding definition, attribution window, deduplication, projection equation/time units/horizon, and missing-value rules in `docs/design.md`. Treat absent revenue or controls as unavailable ROAS/incrementality, not zero or invented values.
- [ ] Run the targeted tests to confirm failure after approval.
- [ ] Implement snapshot marts with one row per declared grain; use existence checks rather than address-join multiplication. Keep fuzzy candidates in restricted diagnostics and never equate a distance threshold with confirmed identity.
- [ ] Implement deterministic metric and projection calculations. Make forecast assumptions explicit synthetic assumptions, not claims of validated historical performance. Derive direct/any-product/Halo membership through member sets.
- [ ] Verify computed channel totals reconcile, direct members are a subset of all members, Halo equals the set difference, and all periods share consistent definitions.

## Task 3: Readiness, snapshots and orchestration

**Interfaces:** `check_readiness(client_id: str, campaign_id: str) -> ReadinessResult`; `claim_run(snapshot_id: str, config_version: str, rules_version: str) -> Run`; state transitions are persisted and validated.

- [ ] Add `tests/test_runs.py` for incomplete sources, valid zero activity, duplicate/concurrent triggers, same-size corrections, failed runs and retry after restart.
- [ ] Run the tests to confirm failure after approval.
- [ ] Implement versioned source manifests/content fingerprints, campaign-specific completeness rules, atomic run claiming, immutable run snapshots and uniqueness constraints. Polling only detects readiness; a scoped readiness event triggers reporting.
- [ ] Implement an Airflow DAG using the version-appropriate data-aware scheduling API after checking official docs. Event payloads contain identifiers only; payloads and worker credentials enforce client scope.
- [ ] Treat every changed valid snapshot as reviewable in the pilot. Record refresh materiality as a configurable deterministic policy; do not discard corrections based solely on row count or timestamp.
- [ ] Verify retries reuse the claimed run and all downstream reads remain pinned to its source/config/rules versions.

## Task 4: Aggregate narrative tools and durable human approval

**Interfaces:** Each of the four approved tools consumes `ActorContext` plus `run_id` and returns a strict aggregate schema. `record_review_decision(actor, run_id, draft_hash, decision, feedback)` uses authenticated identity. `publish_report(run_id, approved_hash) -> Artifact` is application-controlled.

- [ ] Add `tests/test_tools.py`, `tests/test_review.py`, and `tests/test_leakage.py`: unauthorized run access fails; extra sensitive fields fail closed; canaries never enter prompts/checkpoints/logs; restart resumes review; stale/repeated approvals cannot publish a different draft.
- [ ] Run the tests to confirm failure after approval.
- [ ] Implement an offline narrative adapter and LangGraph durable checkpoint/interrupt flow with bounded regeneration. Tools select pinned aggregate facts only. Use trusted authenticated context rather than accepting client identity from model arguments.
- [ ] Validate structured narrative references against allowed metric IDs; inject numeric values through deterministic formatting. Treat commentary as draft interpretation, with no unsupported causal or historical claims.
- [ ] Implement authenticated Streamlit configuration/review and persisted draft hashes, reviewer IDs, decisions and timestamps. Do not expose raw diagnostics through aggregate tools or report pages.
- [ ] Verify approval invalidation, rejection/regeneration, client isolation, restart recovery and fail-closed validation. Keep external model adapters disabled; gate approved tracing export on secure configuration and leakage checks.
- [ ] Implement approved observability with one local event contract shared by tool/model wrappers and pipeline stages. Add tests for successful/failed/retried/unauthorized attempts, offline adapter labeling, duration measurement, correlation, body/metadata/exception canary exclusion, filtering failure, exporter outage and audit-write failure. LangSmith export may be configured under the owner's approval after secure setup; live model calls remain disabled.

## Task 5: Full report flow and versioned delivery

**Interfaces:** `render_report(facts: ReportFacts, approved_narrative: Narrative) -> bytes`; rendering embeds allowlisted aggregates only. Delivery stores content hash, version, run ID and approval reference with the immutable artifact.

- [ ] Add `tests/test_delivery.py` for deterministic rendering, escaping, missing metrics, canary exclusion, immutable version creation and idempotent retry.
- [ ] Run the tests to confirm failure after approval.
- [ ] Implement the reference inventory using fictional branding, assets, source narratives and all period views. Use a local fictional map with equivalent layer controls; no external map tiles, CDN scripts, telemetry or tracking pixels.
- [ ] Implement atomic artifact creation and version manifests. Make local review/download authorization explicit; document that a downloaded HTML file can be copied and cannot enforce later revocation.
- [ ] Add browser tests exercising every period/section, navigation, accordion, map layer, chart control, responsive layout, keyboard interaction and missing values; verify no external requests and no raw embedded records. Capture screenshots for comparison with the reference flow.
- [ ] After approval, run targeted integration/browser checks and visually inspect generated report views. Document actual output and limitations without claiming unrun checks passed.

## Milestone acceptance

- A fresh setup generates synthetic sources, detects readiness, computes a pinned run, drafts narrative, pauses for human review, and delivers approved HTML.
- A synthetic source correction creates a second reviewed version; an unchanged retry creates no duplicate delivery.
- The complete reference flow is present with fictional content; totals reconcile across all views.
- Negative security tests demonstrate isolation and absence of sensitive fields in model inputs, logs and artifacts.
- No runtime dependency on attachments or `workspace/`; no external model calls, notifications or deployment.

## Execution approval and verification status

Historical planning status: architecture/tool boundaries were approved before implementation. Current evidence and disclosed deployment gaps are recorded in VERIFICATION.md and the local-demo milestone above; unchecked tasks must not be interpreted as completed production integrations.
