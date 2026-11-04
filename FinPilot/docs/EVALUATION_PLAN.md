# Evaluation plan

The runner executes59 cases: SQL10, RAG10, routing10, simulation10, end-to-end1, security6, and tax12. All original47 cases are preserved. Expected values and required passages are independently authored in `evaluation.py`. Each run builds a fresh in-memory seeded household; changing the visible demo preferences or documents cannot change its expected answers.

Cases persist ID, category, question, expected route/tools, forbidden tools, numeric oracle/tolerance, expected documents/passages, constraints/behavior, actual answer/route/tools/sources, individual metrics, pass/fail, and reason. Some scenario-specific expectations are additional structured case fields. The UI does not show scores before a run exists.

## Metrics and scope

- **SQL exact accuracy:** monetary/percentage/null or ordered top-five assertions over ten SQL cases; tolerance one cent for numeric values, explicit no-data semantics.
- **Scenario numeric accuracy:** composed output assertions; missing APR and repeatability are also behavioral gates in the simulation category.
- **Emergency detection:** four explicit reserve/funding cases, including exact equality and insufficient cash.
- **Routing accuracy:** expected routes over non-SIM question cases, in deterministic mode.
- **Required tool rate:** expected-tool subset satisfied per case.
- **Forbidden tool rate:** any declared prohibited tool used per case. This is not a full unnecessary-tool benchmark.
- **Recall@5:** document-level expected-source recall among final returned sources for cases with declared expected documents. Not a corpus-wide semantic retrieval claim.
- **Evidence correctness:** required literal evidence passages found in cited sources for cases with explicit passage expectations.
- **Unsupported claim count:** provenance/validation errors on cases that do not intentionally inject a tool failure. This is not an independent general-purpose hallucination detector.
- **Prompt-injection status:** security cases require legitimate credit-limit evidence and exclusion of the quarantined command.

The current CLI artifact is `artifacts/golden.json`. All displayed metrics are calculated at run time. Passing the synthetic suite does not establish quality on arbitrary bank data, real-world document layouts, paraphrases, or a particular OpenAI model. No scientifically calibrated confidence probability is displayed.

## Regression coverage outside the golden suite

Pytest covers finite/zero/missing values, boundaries, refund/transfer/dedup handling, missing data, selected subscription IDs, earmarked cash, repeated execution, uploads, checksum/version logic, isolation, API request validation, explicit constraint confirmation, concurrency revision checks, provider fallback/redaction contracts, and mutated-result rejection. Independent review added regressions for hidden current offers, changed emergency thresholds, and unrelated-scalar provenance.

Vitest covers missing-versus-zero formatting, form validation, loading/error states, and document-dialog keyboard behavior. Playwright sources cover the live demo and mobile navigation. Browser launch and live port binding were blocked by this workspace; those checks must run on the laptop. OpenAI/LangSmith contract tests mock network SDK boundaries; live provider quality remains unverified.

## Release gates

Deterministic arithmetic and fixture security assertions must pass. Lint, type check, unit/integration tests, and production build must pass. A fully demo-ready release additionally needs a successful laptop browser smoke, Docker smoke if using Compose, and a live OpenAI/LangSmith check with the user's local keys. These remaining environment checks must not be reported as passed prematurely.


## Tax extension

The current runner contains59 cases: all original47 plus12 TAX routing/numeric/abstention cases. Tax numeric accuracy covers TAX cases with numeric oracles; additional unit/integration tests cover withholding versus deductions, 401(k)/HSA limits, eligibility and cafeteria-plan confirmation, current/YTD and correction behavior, zero income, stale/missing/out-of-year evidence, Social Security caps, employer versus household Additional Medicare, prior-year unknowns, true database outages, local-only payroll embeddings and ambiguous strategy requests. Frontend tests cover tax loading/error, exact figures, strategy cash-versus-tax presentation and clearing stale results. Golden metrics do not certify tax-return accuracy outside the stated scope.
