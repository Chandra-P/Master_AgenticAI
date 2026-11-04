# Texas tax-planning release report — 2026-11-04

1. **Implemented:** Tax Planning navigation; reviewed paystub extraction and correction; confirmed/revisioned household tax profile; 2026 federal income-tax, Social Security, Medicare, Additional Medicare, withholding and annual underpayment screens; traditional/Roth401(k), eligible payroll HSA and extra withholding scenarios; net-pay/tax-reserve integration with house and emergency goals; Copilot routing and twelve tax golden cases. Existing finance features and all original47 golden cases remain.

2. **Architecture:** cached official rule JSON, Decimal calculations, strict supported scope, user-approved payroll facts, no model arithmetic. Payroll embeddings stay local even when generic Documents use OpenAI. Withholding payments and income-tax liability are separate. Cash effects are explicitly modeled with fixed federal withholding; real payroll may recalculate withholding automatically. A reviewed upcoming payday prevents applying new changes retroactively to already-passed paydays.

3. **Modules:** new `backend/finpilot/payroll.py`, `tax_engine.py`, `rules/us_tx_2026.json`; new `frontend/components/tax-planning.tsx`, `lib/tax-types.ts`, public sample and tax tests/fixtures. Extended API, agent/provider routes, evaluation cases, schema seeding, document chunking, navigation, Docker public assets, browser isolation helper, security/design/demo docs and synthetic samples. Document chunks now preserve monetary tokens rather than cutting amounts in the middle.

4. **Migration:** `002_tax_planning.sql` adds tax_profiles, paystub_uploads, paystubs, tax_audit and tax_runs, including an active employment/pay-date uniqueness constraint. The migration runner applies both migrations idempotently. Existing accounts, ledger and goals are preserved; seed does not overwrite an existing tax profile.

5. **Tests:** 74 backend unit/in-memory ASGI integration tests passed; 10 frontend tests passed; all59 golden cases passed (original47 plus12 tax). Tests cover brackets, dates/YTD, net-pay reconciliation, deductions versus payment timing, caps/eligibility/cafeteria plans, missing facts, corrections/ownership, profile confirmation and revision, zero income/no remaining checks, stale next payday, composed cash-flow changes, corrupted results, local payroll processing and ambiguous Copilot instructions. UI checks cover loading/errors, exact figures, scope and stale-result clearing.

6. **Exact verification commands:**

```bash
bash scripts/verify.sh > artifacts/tax-verification.log 2>&1
```

The script runs:

```bash
.venv/bin/ruff check backend
.venv/bin/ruff format --check backend
(cd backend && ../.venv/bin/pytest -q)
(cd backend && ../.venv/bin/python -m finpilot.evaluation) > artifacts/golden.json
(cd frontend && npm run lint && npm run typecheck && npm test && npm run build)
```

Browser attempt:

```bash
cd frontend
CHROMIUM_PATH=/usr/bin/chromium timeout 45s npm run test:e2e
```

7. **Final outcomes:** Ruff lint/format, ESLint, TypeScript, both unit/integration suites, golden suite and optimized Next.js build passed. Browser execution was blocked before tests ran: Uvicorn completed application initialization but the sandbox denied binding127.0.0.1:8100 (exit3). The socket-permission request was interrupted. This is not reported as a passing browser smoke. Logs: artifacts/tax-verification.log and artifacts/tax-browser-tests.log. Docker and live OpenAI/LangSmith calls remain unverified.

8. **Actual golden metrics:** 59/59 passed; SQL monetary accuracy100%; tax numeric accuracy100%; scenario numeric accuracy100%; emergency detection100%; deterministic routing100%; required-tool rate100%; document-level Recall@5 and declared evidence correctness100%; forbidden-tool rate0%; provenance/validation error count0; injection tests passed. These describe the declared synthetic benchmark, not tax-return certification or general live-model accuracy.

9. **Review and limitations:** Independent review identified three Important issues—pre-review cloud payroll embeddings, stale displayed strategies, and dropping part of combined Copilot instructions. Each was reproduced and fixed with regression tests. Payroll review resets approval after edits and employment defaults follow selected records. Scope is only2026 Texas full-year U.S.-resident W-2 workers ages18–49, single/MFJ, one employer each, standard deduction and explicit assumptions. No filing/W-4 changes, AMT/NIIT, self-employment, capital gains, itemized/special deductions, catch-ups, refundable credits or job/state changes. Annual safe-harbor screening does not compute installment penalties. Actual return tables/whole-dollar conventions may differ. See TAX_RULES.md and KNOWN_LIMITATIONS.md. Federal numeric sources are archived with hashes; the Texas constitutional HTML was a navigation shell, so its URL is a reference rather than an extracted statutory quote.

10. **Launch:** follow README.md dependency setup. From two project-root terminals:

```bash
# Terminal1
cd backend
../.venv/bin/uvicorn finpilot.api:app --host 127.0.0.1 --port 8000
```

```bash
# Terminal2
cd frontend
npm run dev
```

Open http://localhost:3000 and select Tax Planning. Configure OpenAI/LangSmith only in backend/.env if desired; tax calculations and payroll processing work without keys. On a laptop after production build, install a Playwright browser and run `npm run test:e2e` from frontend. Tests use an isolated temporary database and dedicated8100/3100 ports, so they do not mutate the normal demo.
