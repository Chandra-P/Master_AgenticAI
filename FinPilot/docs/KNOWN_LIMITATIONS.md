# Known limitations

- Local synthetic demo, not a production financial service. No bank sync, financial actions, production login, or per-user sharing UI.
- SQLite only. PostgreSQL/pgvector and distributed workload support are not implemented.
- Fixed as-of date 2026-11-02; snapshot balances are not reconciled from opening balances and every historical event.
- OpenAI selects bounded routes. Financial synthesis remains deterministic; this is not a free-running multi-agent research system. Live API and LangSmith delivery require local keys and were not verified here.
- Golden metrics cover 47 independently specified synthetic cases. Document-level Recall@5, declared forbidden-tool rate, and provenance-error counts have narrower meanings than broad RAG/hallucination metrics.
- Default rule routing recognizes demonstrated finance intents, not arbitrary natural language. No persistent conversation referent resolution; ask for the specific item rather than “it.”
- Local hashing retrieval is a baseline. New OpenAI embeddings can be enabled; vectors are not automatically reindexed when changing embedding model. Keep a consistent model for previously ingested OpenAI vectors.
- Loan extraction expects labeled price/APR/term fields. No OCR, arbitrary-layout loan parser, or exhaustive contract interpretation. Missing facts cause abstention.
- Exact-price car comparison uses two financed options and postponement. No vehicle ownership-cost quote, tax/fee estimator, trade-in model, changing APR, investment-return forecast, or underwriting decision.
- House timelines count monthly contributions, not a full payday/calendar schedule. The allowed two-month delay and $4,000 allocation cap are demo defaults until explicitly confirmed.
- Annual subscription equivalents may not be immediately refundable. Known schedule evidence does not prove actual usage or guarantee successful cancellation.
- Budget tables exist, but a full budget editor, automatic merchant correction workflow, and goal-creation editor are not implemented.
- UI has loading, errors, accessible names, focus styles and responsive layouts. Browser screenshots/visual review could not be completed because Chromium socket syscalls are denied in this workspace.
- Live port binding and Docker execution were not verified in this workspace. The production build, in-memory API integration, unit tests, and golden evaluations are separate evidence and must not be described as live deployment verification.
- Process-local rate limiting and basic redaction are demo controls. Real financial data needs the hardening listed in SECURITY.md.


Tax planning is implemented for the explicit2026 Texas W-2 scope in TAX_RULES.md. Ages50+, other filing statuses, multiple employers for one worker, itemized/special deductions, self-employment, capital gains/NIIT, AMT, refundable credits and filing are not supported. Labels/manual review are needed for arbitrary paystub layouts; OCR is absent. The annual underpayment screen is not a penalty/timing calculation. HSA payroll FICA savings require explicit cafeteria-plan confirmation. The house timeline assumes a continuing monthly rate even though the tax comparison covers only remaining2026 checks. Actual return tax tables/whole-dollar rules can differ from the bracket-schedule estimate. Texas constitutional HTML was a navigation shell; federal numeric sources were archived and verified.

Tax contributions assume fixed federal income withholding except explicit extra withholding. Actual payroll may automatically recalculate federal withholding; obtain a payroll/IRS estimate for an actual next-paycheck forecast. Confirm the upcoming payday in each paystub review; once it passes, upload/review a current stub.

## Model council

Optional councils provide compact structured reviews, not a full adversarial debate, semantic document audit or proof of suitability. Demo reviews are simulated. Live review quality/cost/latency has not been measured with credentials; existing golden scores do not measure it. Provider timeout is per HTTP phase/inactivity, not an absolute wall-clock deadline. The decoded 4096-character cap applies after SDK buffering; trusted gateway response-byte/deadline controls are needed for hard resource limits. Live mode sends monetary facts/scenario state to the configured provider. Models may share errors even when they agree.
