# FinPilot release report — 2026-11-03

## Implemented

All ten UI areas: Overview, Accounts, Transactions, Subscriptions, Goals, Documents, Scenarios, Copilot, Evaluation Lab, Settings. Responsive light/dark styling, charts, transaction filters, uploads, version selection, confirmed goal/constraint edits, scenario comparison, calculation/evidence drawers, and concise tool traces.

Backend: parameterized SQL analytics; integer-cent storage and Decimal scenarios; explicit cash earmarking; independent numeric/goal validation; version-aware hybrid retrieval with injection quarantine and registry-wide offer conflict checks; structured memory and audit; actual golden evaluations; optional OpenAI strict tool-calling planning and privacy-reduced LangSmith tracing; safe deterministic fallback.

## Decisions and modules

Next.js/React/TypeScript and FastAPI/Pydantic with SQLite. No unnecessary vector/database service. Monetary synthesis is deterministic; the model chooses a bounded workflow and never performs authoritative arithmetic. House savings are part of cash. Unknown vehicle costs make loan-only affordability partial evidence.

Main modules: `backend/finpilot/{db,analytics,money,scenario,rag,agents,providers,evaluation,api}.py`; frontend `app`, `components`, `lib`, and tests. Compose, Dockerfiles, environment example, Makefile, verification script, synthetic sample documents, and full design/security/demo documentation are included.

Migration: `backend/migrations/001_initial.sql`, including all required financial/document/scenario/agent/evaluation tables plus memory audit and schema version tracking. Applied successfully through fixtures and demo initialization. PostgreSQL migrations are not provided.

## Executed verification

```bash
bash scripts/verify.sh
.venv/bin/ruff format backend
cd backend
../.venv/bin/pytest -q
../.venv/bin/python -m finpilot.evaluation
```

The verification script executes these exact quality commands from the corresponding directories:

```bash
.venv/bin/ruff check backend
.venv/bin/ruff format --check backend
(cd backend && ../.venv/bin/pytest -q)
(cd backend && ../.venv/bin/python -m finpilot.evaluation) > artifacts/golden.json
(cd frontend && npm run lint && npm run typecheck && npm test && npm run build)
```

Results: Ruff lint/format pass; **46 backend unit/in-memory integration tests pass**; frontend ESLint and TypeScript pass; **5 Vitest tests pass**; optimized Next.js build passes. The final backend-only recheck after remote-trace minimization also passed 46/46. Logs: `artifacts/verification.log`; golden details: `artifacts/golden.json`.

## Actual golden metrics

47/47 passed, 0 failed. SQL exact accuracy 100%; scenario arithmetic 100%; emergency detection 100%; deterministic routing 100%; required tools 100%; document-level Recall@5 100%; declared evidence correctness 100%; forbidden-tool rate 0%; provenance/validation error count 0; both injection cases passed.

These are synthetic deterministic golden-set results, not live OpenAI performance, general semantic recall, calibrated confidence, or a general proof of zero hallucination. See EVALUATION_PLAN.md for denominators and limits.

## Independent review

Three Important findings were reproduced and fixed with regressions: top-K retrieval hiding a competing current offer; fixed emergency-dollar text after edited preferences; accepting unrelated scalar counts as monetary evidence. Subsequent tests additionally reject corrupted house timelines and ensure a real unavailable database still returns a transparent blocked answer even if audit persistence also fails. No financial-action endpoints exist.

## Unverified gates and limitations

The workspace denies socket syscalls and local port binding. Uvicorn completed application initialization but could not bind a port. Chromium launch failed on a denied socket operation; the attempted browser harness log is retained. Therefore live browser journeys, screenshots, visual review, and live network deployment are **not verified**. Docker configuration is provided but was not executed. OpenAI/LangSmith SDK contracts are covered with mocks; no real keys were available for live delivery checks.

This remains a local synthetic demo: SQLite only, single-household identity, no bank sync/actions, no arbitrary-layout PDF/OCR extraction, and limited demonstrated-language routing. Production authentication, hardening, broad semantic evaluation and real vehicle ownership costs remain outside this release. See KNOWN_LIMITATIONS.md and SECURITY.md.

## Launch on a laptop

Extract FinPilot.zip and open its folder in VS Code. With Docker Desktop installed:

```bash
cp .env.example .env
# Optional: set MODEL_MODE=openai and add keys locally; enable LANGSMITH_TRACING.
docker compose up --build
```

Open http://localhost:3000. This command is provided for local execution; Docker verification remains pending.

Without Docker, follow README.md to install Python and Node dependencies, then use two terminals:

```bash
# Terminal 1, project root
cd backend
../.venv/bin/uvicorn finpilot.api:app --host 127.0.0.1 --port 8000
```

```bash
# Terminal 2, project root
cd frontend
npm run dev
```

Open Copilot and ask the car-affordability question, then run Evaluation Lab. Configure OpenAI/LangSmith only in backend/.env; never paste keys into chat or commit them.
