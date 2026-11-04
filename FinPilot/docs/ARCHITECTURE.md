# Architecture

FinPilot is a local-first, synthetic household application. Next.js presents financial information; a server-only Next.js API gateway forwards to FastAPI; SQLite stores structured facts and audit history. Integer cents and Decimal functions are the only authorities for money. The demo clock is 2026-11-02, independent of the laptop date.

## Responsibilities

| Module | Contract |
|---|---|
| `backend/finpilot/db.py` | Connection, migration, deterministic seed/reset |
| `analytics.py` | Approved parameterized SQL, half-open periods, exclusions, provenance |
| `money.py`, `scenario.py` | Decimal rounding, amortization, composed changes, cash earmarking, constraints |
| `rag.py` | Validated extraction, checksum, section chunks, embeddings, retrieval, offer authority |
| `agents.py` | Intent routing, bounded tool graph, typed facts, validation, deterministic explanation |
| `providers.py` | OpenAI strict route tool; privacy-reduced LangSmith publication |
| `evaluation.py` | Independent golden oracles, isolated fixtures, persisted actual metrics |
| `api.py` | Request validation, demo identity, audit writes, rate-limit hook, health |
| `frontend/components` | Overview, finance areas, Copilot/evidence, Evaluation Lab, settings |
| `frontend/app/api/[...path]/route.ts` | Server-side proxy, optional backend service token, failure translation |

## Sources of truth

Transactions and accounts are relational facts; documents provide cited contract/policy facts; structured memory stores constraints. House savings are an earmark inside cash, not another asset. A document cannot overwrite an emergency reserve. Conflicts are surfaced; explicit user confirmation and revision checking govern memory edits.

## Agent execution

The orchestrator chooses a bounded route. SQL and document retrieval may execute only approved capabilities; scenarios call pure financial functions; the critic checks accounting identities, field/unit provenance, loan amortization, and source-backed summary numbers. The synthesis node uses deterministic templates populated from validated values. UI events report tool executions, not hidden reasoning.

With `MODEL_MODE=openai`, a strict function schema selects one route. The API does not accept arbitrary SQL, Python, model-selected URLs, or financial actions. Document content is never sent as behavioral instructions to the planner. Provider failure explicitly falls back to deterministic routing. Deterministic mode is not presented as live model inference.

## Deployment boundaries

Supported database: SQLite. WAL and request-scoped connections suit a small local demo. PostgreSQL/pgvector migrations, distributed queues, and multi-tenant production auth are not implemented. JSON-stored local vectors avoid adding a service without demonstrated need. OpenAI and LangSmith are optional network dependencies with timeouts and safe local fallback.

Compose runs API and web; only the web loopback port is published. Optional backend service authentication is separate from end-user authentication. Do not expose the single-household demo publicly.

## Architectural critique addressed

- Explicit cash allocation prevents house/emergency double counting.
- The allowed house delay is editable and labeled as a demo assumption until confirmed.
- Offer conflict checks consult the complete current document registry, independent of top-K ranking.
- Numeric facts bind to approved semantic output paths and units; summary monetary/rate/term claims are checked against facts.
- Golden expected values are independently authored, and tests deliberately corrupt values.
- Only executed golden metrics are displayed; deterministic fixture performance is not live-model calibration.


## Texas payroll/tax extension

`payroll.py` validates labeled extraction, human confirmation, current/YTD reconciliation, ownership, correction and audit. `tax_engine.py` applies cached official2026 rules with Decimal, separates payments from liability, and connects net payroll cash effects plus a tax reserve to the existing scenario engine. `tax` is a bounded Copilot route. `tax-planning.tsx` displays reviewed payroll basis, profile confirmation, strategy comparison, statutory sources and exclusions. Payroll embeddings stay local. Existing features and all original47 golden cases remain.
