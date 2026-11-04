# FinPilot Implementation Plan

Goal: deliver a coherent, synthetic, evidence-backed personal finance demo.

Inspection: /workspace contains no application, README, package manifests, schema, tests, or environment examples. No existing functionality to preserve. Python 3.12 and Node 24 are available; no external credentials are configured.

Architecture: Next.js/TypeScript UI; FastAPI API; parameterized SQLite queries with integer cents; Decimal financial engine; local hybrid document retrieval; explicit deterministic orchestration nodes and persisted traces. SQLite is the supported release database. PostgreSQL/pgvector are future extension points. OpenAI strict tool-calling intent planning, optional OpenAI upload embeddings, and redacted LangSmith tracing are implemented; no live keys are configured here.

Assumptions: synthetic household; fixed as-of date 2026-11-02; single demo identity; cash already includes earmarked house savings; house progress uses monthly surplus, not all liquid cash. A substantial house delay means more than two months, editable with confirmed memory updates. No bank or financial-action integrations.

## Tasks
- [x] 1. Foundation: dependencies, migration, deterministic seed, health/reset commands. Tests: table creation, repeatable seed, 6-month coverage.
- [x] 2. Money and analytics: cents/Decimal, date boundaries, exclusion rules, typed approved tools. Tests: baseline 10000/6000/4000, refunds, duplicate/transfer/pending/future exclusion, no-data and savings rate.
- [x] 3. Scenario engine and memory: validated composed inputs, amortization, constraints, goal delay, audited confirmed edits. Tests: SIM-001 through SIM-010, exact boundary, missing APR, zero/negative cash flow.
- [x] 4. Document ingestion: size/type/checksum, sections, hashing embeddings and keyword retrieval, versioning, injection quarantine. Tests: current/old APR, deductible, missing facts, hostile instructions, tenant isolation.
- [x] 5. Agent graph: intent routing, tools, retrieval, scenario comparison, critic, evidence synthesis, persisted trace. Tests: SQL/RAG/memory/affordability/ambiguous/failure routes and numeric provenance.
- [x] 6. Golden evaluation runner: SQL/RAG/AG/SIM/SEC/E2E cases with explicit oracles and actual metrics persisted for UI. Tests: real assertions and failure reporting; do not hard-code answers by question string.
- [ ] 7. Product UI: all ten areas, responsive themes, overview charts, searchable ledger, uploads, scenario form, Copilot evidence and traces, Evaluation Lab, confirmed settings. Tests: formatting/form helpers, loading/error, Playwright critical journey.
- [ ] 8. Release: documentation, Docker config, security review, formatter/linter/type checks/backend and frontend tests/production build/browser smoke. Record exact outcomes in artifacts and limitations.

## Review focus
- Untrusted document instructions cannot change constraints or trigger actions.
- Unknown loan facts and ambiguous purchase references must abstain.
- Cash earmarked for a house cannot be double-counted as spare cash.
- Failed analytics must block an affordability recommendation.
- Uploaded versions and confirmed constraint changes must persist without contaminating golden fixtures.

Execution: inline, as explicitly requested; no approval pauses. Add focused tests before subsystem implementation and run them as work proceeds. No commits or external publishing required.

## Final verification — 2026-11-03

Tasks 1–6 are implemented and tested. Task 7 source and component tests are complete; browser execution is blocked by the execution sandbox. Task 8 documentation, packaging, lint, type checking, production build, backend46/frontend5 tests and golden47 evaluations pass. Live server/browser, Docker, and real-key provider verification remain pending and are not claimed complete.

Independent review found and prompted tested fixes for hidden conflicting offers, hardcoded emergency thresholds, and unrelated-scalar provenance. Additional regressions cover goal timeline mutations, fractional cents, overlapping earmarks, recurrence evidence, keyboard focus restoration, and actual database outages.

Rulings: SQLite is the only supported database in this release; model-assisted planning and deterministic synthesis keep monetary explanations bounded; the single demo identity is not production auth; no real credentials or external financial data were used.
