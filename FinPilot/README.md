# FinPilot

**Your autonomous financial intelligence team.**

FinPilot is a local, synthetic personal-finance application that connects transaction analytics, document evidence, structured goals, and deterministic scenario simulation. Its flagship workflow compares a $50,000 car offer against a $25,000 emergency reserve and a house down-payment goal.

All household data is fictional. Educational analysis only, not professional financial advice. FinPilot cannot move money, trade, or apply for credit.

## Architecture

- **Next.js 15 / React 19 / TypeScript**: responsive dashboard, accounts, searchable transactions, subscriptions, goals, documents, scenarios, Tax Planning, Copilot, Evaluation Lab, settings; light/dark themes.
- **FastAPI / Pydantic**: validated API and bounded orchestration. SQL, retrieval, subscription, goal, simulation, critic, and synthesis capabilities have explicit tool events.
- **SQLite**: relational data and local audit/traces, money in integer cents. All projections use Python Decimal. PostgreSQL is not implemented in this release.
- **OpenAI**: optional structured tool-calling intent planner. No model-generated SQL or authoritative monetary arithmetic. User-facing financial synthesis is deterministic to avoid unvalidated model prose.
- **RAG**: local hashing embeddings plus lexical retrieval, section/page citations, explicit supersession, missing/conflicting-term abstention. Optional OpenAI embeddings for newly uploaded documents.
- **LangSmith**: optional redacted root/tool traces. Local traces always persist.

See [architecture](docs/ARCHITECTURE.md), [financial rules](docs/FINANCIAL_RULES.md), and [known limitations](docs/KNOWN_LIMITATIONS.md).

## Prerequisites

Python 3.12+, Node.js 22+, npm, and two terminal windows. Docker Desktop is optional. No bank credentials or paid keys are required. On your laptop: extract the project archive, then **File → Open Folder** in VS Code. This cloud workspace does not sync to your laptop automatically.

## Local setup (macOS / Linux)

From the project folder:

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
cp .env.example backend/.env
cd frontend
npm ci
cd ..
```

Migrate and seed (also performed automatically at API startup):

```bash
cd backend
../.venv/bin/python -m finpilot.db migrate
../.venv/bin/python -m finpilot.db seed
../.venv/bin/uvicorn finpilot.api:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
cd frontend
npm run dev
```

Open **http://localhost:3000**. Enter the demo directly; no login or real bank connection is required. API health: http://127.0.0.1:8000/api/health. API docs: http://127.0.0.1:8000/docs.

### Windows / VS Code PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Copy-Item .env.example backend\.env
cd frontend
npm ci
cd ..\backend
..\.venv\Scripts\python.exe -m finpilot.db seed
..\.venv\Scripts\python.exe -m uvicorn finpilot.api:app --host 127.0.0.1 --port 8000
```

In another terminal, run `cd frontend` then `npm run dev`. Use Windows virtualenv paths for the Python commands below. Docker is the easiest alternative for platform-independent startup.

## OpenAI and LangSmith

Edit **backend/.env** locally; never paste or commit real keys:

```dotenv
MODEL_MODE=openai
OPENAI_API_KEY=your_local_key
OPENAI_MODEL=gpt-4.1-mini
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_local_key
LANGSMITH_PROJECT=finpilot
EMBEDDING_PROVIDER=local
```

Restart the backend. Settings shows configured status without revealing values. The planner calls a strict `select_route` tool. Execution remains bounded and monetary answers remain deterministic. If OpenAI fails, the response explicitly labels the deterministic fallback. No key means the whole synthetic demo still works.

Set `EMBEDDING_PROVIDER=openai` and optionally `OPENAI_EMBEDDING_MODEL=text-embedding-3-small` for new uploads. Synthetic sample documents always use local embeddings so fixture generation is deterministic. Retrieval supports both providers; query embeddings may incur API costs. No automatic bulk migration is performed.

LangSmith receives the route, mode, validation status, latency, and child tool statuses. Questions, document passages, balances, and account identifiers are omitted. OpenAI receives the question when model mode is enabled. Golden evaluations use deterministic planning and isolated fixtures; their metrics do **not** establish live-model quality. Live provider integration was not verified with real keys in this workspace.

### Environment reference

| Variable | Default / purpose |
|---|---|
| `MODEL_MODE` | `deterministic`; set `openai` for structured planning |
| `OPENAI_API_KEY` | Server-only API key |
| `OPENAI_MODEL` | `gpt-4.1-mini` |
| `OPENAI_BASE_URL` | Optional OpenAI-compatible endpoint |
| `EMBEDDING_PROVIDER` | `local` or `openai` |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` |
| `LANGSMITH_TRACING` | `false`; explicit opt-in |
| `LANGSMITH_API_KEY` | Server-only tracing key |
| `LANGSMITH_PROJECT` | `finpilot` |
| `LANGSMITH_ENDPOINT` | Optional regional/custom LangSmith endpoint |
| `DATABASE_PATH` | `backend/finpilot.db` by default |
| `API_URL` | Next.js server backend URL; default `http://127.0.0.1:8000` |
| `FINPILOT_ACCESS_TOKEN` | Optional shared backend service token; set in both services |

If using `FINPILOT_ACCESS_TOKEN`, also create `frontend/.env.local` with the same variable. The Next.js API gateway injects it server-side. This protects the backend service boundary; it is **not** end-user authentication. Keep the demo local.

## Docker

```bash
cp .env.example .env
# Optional: edit .env for OpenAI / LangSmith.
docker compose up --build
```

Open http://localhost:3000. The backend is private to Compose; the web port binds to laptop loopback. A named volume retains SQLite data. Migration and seed run automatically. Two application services only; no unused database/vector service is added.

To reset Docker demo data (removes the synthetic volume):

```bash
docker compose down -v
docker compose up --build
```

Docker configuration is provided but was not built or run in the restricted workspace.

## Documents and demo data

The fixed demo date is **2026-11-02**. Six complete historical months plus a partial current month include refunds, transfers, aliases, duplicates, pending, reversed, and future-dated entries. September expenses are $5,800; October expenses $6,000; net income $10,000/month; cash $60,000; house savings $20,000 within cash.

Eight synthetic documents are ingested during seed. Files under `sample_documents/` are convenient for presentations. In **Documents**, upload PDF/TXT/Markdown, at most 2 MB. Select an existing document to supersede when uploading a replacement. Current offers must have uniquely evidenced `Vehicle price: $…`, `APR: …%`, and `Term: … months` fields for loan projections. Missing/conflicting terms cause abstention. PDF OCR is not supported.

Local reset, with the API stopped:

```bash
cd backend
../.venv/bin/python -m finpilot.db reset
```

Reset deletes the local synthetic database, including uploads, edited memory, evaluations, and traces. `seed` alone is idempotent and preserves edits.

## Tests, evaluations, and production build

```bash
# From the project root
.venv/bin/ruff check backend
.venv/bin/ruff format --check backend
cd backend
../.venv/bin/pytest -q
../.venv/bin/python -m finpilot.evaluation > ../artifacts/golden.json
cd ../frontend
npm run lint
npm run typecheck
npm test
npm run build
npm run start
```

Or run `bash scripts/verify.sh`. Python tests include in-memory ASGI integration. The test harness runs sync handlers inline because the workspace blocks thread wakeup sockets; concurrent/network behavior is not covered by this adapter.

The Evaluation Lab button runs all **59** cases against fresh in-memory fixtures, persists the actual results, and displays drill-down evidence. Scores are not hard-coded. `artifacts/golden.json` records the most recent CLI run. Exact expected values are independently authored. Scope and denominators are documented in [evaluation plan](docs/EVALUATION_PLAN.md).

Live browser tests on a laptop after building:

```bash
cd frontend
npx playwright install chromium
npm run test:e2e
```

The Playwright config starts an isolated temporary demo database, API on8100 and production frontend on3100 automatically. It never reuses your normal demo servers or database. Install dependencies in the documented virtualenv location first. The alternate Python harness `scripts/browser_smoke.py` requires Python Playwright and `CHROMIUM_PATH`; it tests a production UI with in-memory API interception, not live network deployment.

## Demo sequence

Follow [DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md): dashboard → SQL → current loan APR → car comparison → calculations/citations → agent trace → Evaluation Lab → injection quarantine. No API keys are needed for the deterministic presentation.

## Troubleshooting

- **Service unavailable:** start FastAPI on port 8000; check `API_URL` and health. Next.js proxies `/api/*` server-side, so no browser CORS setup is required.
- **401:** the optional service token must match in both backend and frontend environment files. Restart both services after edits.
- **Missing loan facts:** use explicit price/APR/term labels, supersede the old version, and check the effective date. Future-effective evidence is excluded.
- **Old fixture values:** stop the API and reset the synthetic DB. Seeding never overwrites an existing household.
- **OpenAI fallback:** verify local key/model/network access; errors expose categories rather than credentials. Deterministic mode remains available.
- **LangSmith unavailable:** local traces remain available in Copilot. Remote publishing is best effort.
- **Browser cannot start / socket permission denied:** run browser tests on your laptop. This workspace denied Chromium socket syscalls and local server port binding; browser checks remain unverified here.
- **Fonts unavailable:** the UI uses system fallbacks if Google Fonts cannot load. No financial functionality depends on font connectivity.

See [SECURITY.md](docs/SECURITY.md) before sharing any deployment. This is not a production financial service.


## Texas paystub and federal tax planning

Open **Tax Planning** for the 2026 Texas W-2 extension. It adds a confirmed household tax profile, paystub extraction/review, federal withholding and annual safe-harbor screens, and traditional/Roth 401(k), payroll HSA, and withholding comparisons connected to the existing goals engine. No tax return or W-4 is filed.

The synthetic two-worker fixture reconciles to the existing $10,000 monthly take-home income. The initial projected federal balance is $2,137.60. Review the next pay date as well as remaining checks; once that payday has passed, a current stub is required. Sample paystubs are in `sample_documents/` and a downloadable example is available from the page. Uploads remain inactive until explicit review; duplicates need an explicit correction relationship. Payroll previews always use local embeddings, even when generic Documents uploads use OpenAI.

Migration `002_tax_planning.sql` runs automatically with existing migrations. It adds `tax_profiles`, `paystub_uploads`, `paystubs`, `tax_audit`, and `tax_runs`. Existing account/transaction/goal data is preserved. Seeding adds the synthetic tax profile only when absent and never overwrites confirmed edits.

Supported scope: 2026, Texas, full-year U.S. residents, single or married filing jointly, ages18–49, one employer per worker, standard deduction and explicit eligibility assumptions. See [TAX_RULES.md](docs/TAX_RULES.md) for official sources, exact formulas, worked examples and exclusions. Additional HSA payroll-tax benefits require confirmation of a pre-tax cafeteria plan. Missing facts, stale stubs, unsupported years, and ambiguous combined Copilot changes abstain.

Try: “Am I withholding enough federal tax?” or “What if Alex increases traditional 401(k) by $250 per paycheck?” Use the Tax Planning form for combined changes. The 59-case Evaluation Lab preserves all original47 cases and adds12 TAX cases; metrics remain actual deterministic runs rather than live-model performance guarantees.

Latest extension status and exact checks: [TAX_RELEASE_REPORT.md](docs/TAX_RELEASE_REPORT.md). Browser and Docker checks are not claimed passed in this workspace.

## Modern React interface preview

The interface includes responsive navy navigation, teal financial cards, light/dark themes and keyboard page/question search (Ctrl/Cmd+K). All existing financial and Texas tax workflows remain available.

Open `artifacts/ui-preview/index.html` for a static preview generated from the actual React dashboard and synthetic API fixtures; `dark.html` shows the dark theme. Preview controls are deliberately inactive. Start the application using the commands above for interactive workflows. Regenerate after installing frontend dependencies with `node scripts/generate_ui_preview.cjs`. See [UI refresh report](docs/UI_RELEASE_REPORT.md) for validation and limitations.

## Optional model council

FinPilot can add three independent structured reviews after deterministic validation. Set these in `backend/.env`, then restart the API:

```dotenv
# Offline demonstration; clearly labeled simulated reviews.
COUNCIL_MODE=demo
```

For actual model calls, use:

```dotenv
COUNCIL_MODE=openai
OPENAI_API_KEY=your-local-key
COUNCIL_MODELS=gpt-4.1-mini,gpt-4.1,gpt-4o
```

Use three model IDs available to your account that support Chat Completions JSON-schema structured output. `MODEL_MODE` controls the intent planner separately; the council works with the deterministic planner. Docker reads the same settings from the root `.env`.

Ask the car-affordability question in Copilot, then inspect the Model council panel and agent/tool trace. Any objection holds the recommendation; missing reviews show an incomplete result. Simple SQL/document questions skip council calls. To disable it, set `COUNCIL_MODE=off` (default). Live mode sends compact monetary facts and scenario state to the configured OpenAI-compatible provider, adds three calls, and may add latency/cost. Raw questions, document passages, names and payroll documents are omitted. Keys remain server-side. Council agreement is not proof of accuracy or professional financial advice.

Design, limits and test scope: [Model council](docs/MODEL_COUNCIL.md). Golden evaluations remain deterministic and do not measure live council quality.
