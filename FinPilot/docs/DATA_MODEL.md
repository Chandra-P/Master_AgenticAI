# Data model

Migration: `backend/migrations/001_initial.sql`; version tracked in `schema_migrations`. Startup applies the idempotent migration, then seeds only if the demo user is absent. Reset deletes the synthetic database; it is not a production migration strategy.

All monetary columns are **integer USD cents**, not SQLite REAL. API monetary values are decimal strings. Currency is USD for this release. Embedding floats and chart rendering floats are not authoritative money.

| Tables | Purpose |
|---|---|
| users, accounts | Household identity; active account balance snapshot and cash eligibility |
| transactions, transaction_categories | Signed posted ledger, dates, merchant/category, diagnostic flags |
| merchant_aliases | Explicit merchant variant → canonical name |
| recurring_transactions | Active billing schedules and recurrence evidence |
| budgets, budget_categories | Budget schema foundation; no full budgeting editor in this release |
| financial_goals | Target/current earmarked amounts, date, priority, status |
| user_preferences, memory_audit | Emergency minimum, risk, currency, exclusions, rules, revision; confirmed before/after audit |
| documents, document_versions, document_chunks | Ownership, checksum, family, effective date, supersession, version history, page/section, provider, vector, quarantine |
| scenario_runs, scenario_inputs, scenario_results | User, timestamp, inputs and deterministic outputs |
| agent_runs, tool_calls, citations | Route, sequence, validation, outputs, latency/errors and source references |
| evaluation_cases, evaluation_runs, evaluation_results | Golden definitions, measured metrics, per-case actual assertions |

Foreign keys are enabled on every connection. Account ownership scopes transaction analytics; document ownership scopes retrieval. API actor is the server-selected demo identity, never a submitted user ID. UUIDs identify uploaded documents and audit runs.

`duplicate_group_id` marks an excluded duplicate copy and references the original ID by convention. The original has a null group field and is counted once. Pending, internal transfer, reversed, and future-dated entries stay in the visible ledger but are excluded from analytics.

Balances are an explicit 2026-11-02 snapshot: checking $12,000, savings $48,000, investments $95,000. Cash is $60,000. The $20,000 house earmark is included in savings. Transaction history is deliberately not a complete bank reconciliation; no opening balances or investment history are inferred.

Document uniqueness is `(user_id, checksum)`. Replacement is explicit; matching filenames do not silently supersede. Chunk vectors record the embedding provider. Current retrieval excludes superseded/future-effective records. Authority checks inspect all eligible offer identities before loan simulation.


Migration002 adds tax_profiles (confirmed versioned household JSON), paystub_uploads (owned inactive extraction), paystubs (confirmed/superseded structured facts, explicit correction links), tax_audit (before/after confirmation history), and tax_runs (scenario inputs/results). Money in payroll JSON is validated Decimal strings with two fractional digits rather than SQLite REAL. Only the latest confirmed pay date per employment is used; a unique active employment/pay-date index prevents duplicates.
