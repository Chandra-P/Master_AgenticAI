# Campaign Reporting — synthetic POC

A local analyst workflow and interactive campaign report for **50 fictional credit unions**, with 25 Checking campaigns in 2024 and 25 in 2025. Every source record is generated. No original client data, logos, embedded report images or private credentials are included.

## Start the morning demo

From this directory on the prepared Windows machine:

```powershell
.\start-demo.ps1
```

Open **http://127.0.0.1:8510**. This is a local-only synthetic demonstration with visibly simulated analyst identity. The startup script disables OpenAI calls and automatic tracing, so the walkthrough costs $0.

1. Choose any of the 50 clients in the sidebar. Their dates and response patterns differ.
2. Inspect **Success Plan**, confirm it, and use **Compute campaign** if you want to reproduce the seeded run.
3. Inspect period-specific accounts, members, channel categories and branch aggregates under **Computed facts**.
4. In **Analyst review**, generate a draft. The offline adapter and its application-invoked tool calls are explicitly labeled.
5. Review the facts and exact draft, check the attestation, and approve.
6. Under **Report**, publish the approved version and download its standalone HTML. Change reporting period, explore map measures/fair-share, navigate sections and open appendix evidence.
7. Under **Observability**, inspect the tool attempts, timing and outcomes.
8. To demonstrate a correction: confirm the Success Plan, select the corrected-source checkbox and compute again. It creates a new version and requires a fresh review.

Seeded runs are **not pre-approved**. Opening an existing client does not authorize publication. The full-source fixtures are compressed under ignored `runtime/sources/`; portfolio summaries are in `runtime/portfolio.json`. They can be regenerated from a fresh clone.

## Fresh setup

Requires Python 3.12+ and uv. Use a project virtual environment, never global package installation.

```powershell
uv sync --locked
.\.venv\Scripts\python.exe -m campaign_reporting.cli seed --clients 50
.\start-demo.ps1
```

Seeding streams one client at a time and exports 100,000 synthetic households per client, 80,000 digitally reached households, core account records, upstream match results, new-member classifications and synthetic historical curves. Identifiers are scoped by client. Each client sends two drops to the same audience; 5 million household records across the portfolio represent 10 million mail pieces, not 10 million distinct households.

## Business rules

- Checking: distinct qualifying accounts from existing or new members. Multiple accounts per member count independently.
- New members: distinct upstream-matchback-classified new members across any qualifying product. One new member opening Savings and two Checking accounts counts once as a member and twice as Checking.
- Funding: inclusion in the funded active-core extract is accepted evidence. Account-open date is present; there is no invented funding indicator/date.
- Direct mail: response flag 1; in-home date excluded and following 60 days included.
- Digital: TU-style exposure flag 1; TU handles attribution. Support by mailing comes from confirmed campaign configuration.
- Both/DM Only/Digital Only are exclusive categories reconciling to total Checking accounts; they do not establish incremental lift.
- CPA: unavailable until day 120 and every component launched; then full campaign budget / qualifying Checking count.
- Confirmed template: $215,000 total, $150,500 DM split equally, $64,500 digital; 601 Checking goal, 605 member goal and $358.17 CPA ceiling.
- Forecast: observed Checking divided by synthetic historical cohort completion fractions. Range is an empirical scenario range, not a calibrated confidence interval. No current-campaign future records are used to forecast earlier reads.

## What is implemented versus unverified

Implemented and locally testable: synthetic generation, deterministic metrics, persistent run identity, correction versions, aggregate tool interfaces, metadata-only timing, $5 budget ledger, durable LangGraph human review, local analyst UI, approval-bound publication and interactive HTML.

**SQLite is the runnable local harness.** Postgres schema/roles/adapter and development Airflow asset DAGs are supplied, but this host has neither Docker nor PostgreSQL available. Database permission tests and a real Airflow scheduler are therefore unverified. These files are not a production deployment. Airflow requires a separately provisioned metadata database and compatible Linux/container environment; install its package separately with official constraints rather than adding it to this Windows UI environment.

Corporate OIDC and per-client authorization are supported as a deployment path, but are not configured or tested against a real identity provider. Do not expose demo mode remotely. Automatic Success Plan LLM extraction is not wired; the POC confirms structured synthetic configurations. Member forecasts, live notifications, cloud deployment, provider-based quality evaluation and retention automation are not claimed complete.

## OpenAI: optional, never required for the demo

The owner authorized **$5 total** from existing funded OpenAI access. No live calls are made by the demo. The opt-in adapter requires secure environment provisioning of a model, key, verified current input/output prices and pricing-review date. It bounds output tokens, disables automatic SDK retries and persists worst-case reservations; uncertain failures keep reservations. It sends a strict allowlist of aggregate metrics and rejects numeric/HTML/contact-like narrative text. Keys must never be pasted into chat or checked into Git. The offline narrative adapter is not evidence of live-model quality.

## Observability

Local `runtime/telemetry.jsonl` records application-invoked tool names, run IDs, durations and sanitized status. Prompts, source records and reviewer feedback are excluded. LangSmith has an explicit metadata-only exporter; export is not enabled or tested live. Project access/retention/free limits must be checked before enabling it. The audit database is authoritative even if telemetry export fails.

## Verification

```powershell
New-Item -ItemType Directory -Path runtime -Force
.\.venv\Scripts\python.exe -m pytest -q --basetemp=runtime/pytest
.\.venv\Scripts\ruff.exe check src tests ui dags
.\.venv\Scripts\python.exe -m compileall -q src ui dags
```

Browser tests require `python -m playwright install chromium` in the project environment. Tests exercise desktop/mobile navigation, every period, map layers, appendix, no external report requests, HTML escaping, counting boundaries, review/restart, cross-client service checks, duplicate claims and concurrent budget reservations. The optional real-Postgres test skips explicitly unless its scoped test login is provisioned. See `VERIFICATION.md` for actual recorded results.

## Design and provisioning references

- [Design](docs/design.md)
- [Security boundaries](docs/security-boundaries.md)
- [Report inventory](docs/report-inventory.md)
- [Approved plan](docs/implementation-plan.md)
- [Postgres schema](db/001_schema.sql) and [roles](db/002_roles.sql)

Provision LOGIN roles through a trusted operator and map them in `service_bindings`; do not use the database owner in application services. The optional Compose file binds Postgres only to loopback and requires an externally configured password. No runtime component imports `workspace/` or references the owner's attachments.
