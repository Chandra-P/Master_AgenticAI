# Model council: design and implementation plan

## Decision

Add an optional, bounded post-validation council to the existing workflow. Preserve deterministic calculations, provenance validation and synthesis. Existing authorization asks us to choose reasonable defaults and proceed without repeated design questions.

Approaches considered: replacing synthesis with majority-voted model prose risks unsupported financial claims; independent unbounded agents duplicate tools and expose more private data; bounded structured reviews preserve the verified result and reveal disagreements. Choose structured independent reviews with deterministic reconciliation. The reconciler is code, not a fourth model.

Three reviewers focus on evidence completeness, goal/constraint risks, and assumptions. In live mode each uses an independently configured OpenAI-compatible model. Different models from one provider are not independent institutions, and agreement is not calibrated confidence. No review can update memory, invoke tools, move money, change facts, or change deterministic validation.

Modes: off (default), demo (three explicitly simulated policy reviews), openai (three bounded provider calls). A live failure must remain unavailable, never replaced by a simulated vote. Run only for affordability, goal comparison, subscription scenarios, scenarios and tax; simple SQL/RAG answers skip extra cost. Golden suites using use_model=False remain isolated; council behavior has its own tests.

Provider inputs contain only validated facts with source-tool names, numeric scenario state/constraints, assumption/limitation counts and source counts and allowlisted evidence references. Exclude raw questions, document passages, payroll documents, names and account identifiers. Monetary facts may still be private: live mode is an explicit deployment opt-in. Retrieved/user prose is never included. Structured output is enum verdict/concerns and allowlisted evidence references; never display free-form provider prose. All objections hold a recommendation; missing members make review incomplete; approval requires three approvals, complete evidence, no failed scenario constraints and deterministic validation. Failed alternatives remain visible and trigger caution rather than a misleading blanket endorsement.

Add council result to existing agent-run answer JSON (no migration), local execution events, and redacted LangSmith status metadata. Each call requests at most 250 output tokens, uses an 8-second SDK per-phase/inactivity timeout and no retries, and rejects decoded content over 4096 characters. These are not hard wall-clock or transport-byte limits: the SDK buffers responses before validation. A slow or nonconforming compatible gateway can exceed these soft limits; production needs an upstream absolute deadline and response-byte cap. Three sequential calls cap request count and avoid introducing concurrent DB access. Latency is measured, no fabricated costs or confidence percentages.

## Implementation checklist

- [x] Tests first: off/demo/live contracts, disagreement, unknown evidence, malicious/malformed output, missing key, provider failure, deterministic veto, persisted run integration.
- [x] Implement backend council module and append after deterministic validation and before persistence/tracing. No modifications to authoritative values.
- [x] Render review cards, differences, unavailable states and model/role labels in Copilot; frontend tests.
- [x] Add environment documentation and tracing status; run complete verification and package project.

Known limits: no cross-provider credentials UI, no learned judge, no generated financial recommendations, no scientific calibration, no live-provider guarantee without an executed credentialed test. Review quality needs a dedicated human-labeled evaluation set before claiming improvement. No private chain of thought is requested or exposed.

## Executed verification and presentation

New tests cover off/skipped paths, explicit simulation, deterministic vetoes, complete live approval with mocked SDK, dissent, unknown references, malformed/injected outputs, missing credentials, provider timeout, invalid model configuration, persisted workflow/tool events and isolation from golden runs. Frontend tests cover simulated labels, disagreement, concern/error visibility, and disabled-state rendering. Mocked SDK tests validate the request/response contract; they do not establish live model quality.

Commands: `bash scripts/verify.sh` (output `artifacts/council-verification.log`); `node scripts/generate_ui_preview.cjs` (actual React components rendered against synthetic fixtures). Synthetic end-to-end council result: `artifacts/council-demo.json`; static preview: `artifacts/ui-preview/council.html` and `council-dark.html`. Previews have inactive controls and are not browser screenshots.

No database migration or new dependency was needed. Existing agent_runs.answer JSON and tool_calls retain the council audit. No keys were added to source. Live OpenAI calls, Docker execution and browser E2E remain unverified in this sandbox.

Final local results: Ruff lint/format, ESLint, TypeScript checking, **86 backend tests**, **19 frontend tests**, and Next.js production build passed. The original **59/59 golden cases** passed: SQL/scenario/tax numeric accuracy, emergency detection, routing, RAG Recall@5 and evidence correctness each 100% on those isolated fixtures; forbidden-tool rate 0%, unsupported-claim count 0, injection checks passed. These scores do not evaluate live council quality.
