# Does this option fit our group?

> **For agentic workers:** Use superpowers:subagent-driven-development for backend, frontend and independent review. Use the existing integration checkout; coordinator synchronizes scoped changes and pushes the current deployment branch.

**Goal:** Evaluate an option against current plan constraints and retrieved supporting evidence, visibly citing sources and exposing uncertainty.

**Architecture:** A read-only authenticated FastAPI endpoint always attempts plan-scoped Pinecone retrieval, verifies returned source IDs/versions against current state, and merges bounded current Notes with authoritative plan facts. OpenAI generates structured matches, conflicts and unknowns using only supplied evidence IDs. A deterministic cost/budget check prevents an over-budget option being presented as a fit. Frontend provides a dedicated Group fit form plus a Discover action with prefilled option details. No external URL fetch, automatic itinerary write, reservation, or new provider account.

**Contract:** POST `/v1/plans/{pid}/group-fit` with `expected_revision` and option `{name,details,url?,estimated_cost_per_person?}`. Result `{verdict,summary,matches,conflicts,unknowns,sources,retrieval_status,context_truncated}`. Findings carry `source_ids`; public sources have `id,title,text`. Verdicts: `fits`, `conflicts`, `needs_info`. Missing evidence and unverifiable venue facts remain explicit uncertainty.

**Constraints:** Recheck membership/suspension/revision and evidence versions after generation. No cross-plan evidence or unconfirmed preferences promoted to decisions. Notes work before indexing and when retrieval fails. No draft/model output saved to plan state. Bounded input/context/output, rate limits, and concurrency. Treat option/menu/evidence as untrusted data. Never certify allergens, hours, availability, reservations, or real-time prices from RAG.

## Tasks
- [x] Backend red/green tests, forced retrieval and verified evidence, provider schema, read-only endpoint and bounds.
- [x] Frontend tab/form/Discover action, citations and missing-info states, stale/private-response guards and tests.
- [x] Shared browser scenario using synthetic sources/provider; documentation and demo walkthrough.
- [x] Independent review, required backend/lint/type/build/frontend/shared checks, desktop/mobile visual review.
- [ ] Sync, scan secrets, commit/push and verify public rollout.
