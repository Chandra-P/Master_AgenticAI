# Proactive coordination demo implementation

User supplied the seven-phase redesign brief and explicitly requested implementation with minimal changes to the existing stack. Keep Next.js, FastAPI, Supabase, LangGraph, OpenAI and Pinecone. Do not introduce microservices or event-sourcing.

## Architecture and rollout
1. Add bounded structured PlanGeneratorNode, SummaryNode and RecommendationNode to a coordination LangGraph dispatcher; preserve ExistingAssistantNode and its RAG flow.
2. Add deterministic plan-health/activity calculations and persisted coordination snapshots within the existing aggregate, plus an additive backend-only SQL projection migration. Cache by content fingerprint; refresh summaries in bounded FastAPI background work with a lease and retry cooldown. Derive age/stalled status on reads, without introducing an always-on scheduling dependency for this demo.
3. Add authenticated draft generation/review/create endpoints, plan coordination and dashboard overview endpoints. Validate membership again before storing AI results; discard stale results and never infer group approval from poll leaders. Missing providers expose a factual fallback rather than fake live AI.
4. Replace the homepage with the requested hero, natural-language input, Continue Planning, AI Recommendations and explicit Group Insights. Add plan-summary/health/next-step cards, and use the same generator in connected-mode plan-creation dialogs. Preserve the explicitly synthetic local demo and existing workflows.
5. Test structured outputs, access controls, freshness, status transitions and stale AI writes; verify desktop/mobile generator review and proactive summary flows. Apply only the additive database migration, review, commit/push the existing review branch, and check rollout.

## Product decisions
- AI drafts require confirmation. Natural-language requests with missing dates produce editable drafts; no date is silently invented. Suggested activities are drafts, not verified venues or reservations.
- Health is a transparent rule-based indicator, not an AI confidence metric. STALLED means at least seven days without recorded plan activity while unresolved work remains. Existing records without trustworthy activity timestamps receive an explicit baseline rather than fabricated history.
- Poll vote leaders remain proposed outcomes. Summaries distinguish working details, confirmed preferences, open questions and draft itinerary items. READY_TO_FINALIZE does not claim group consensus or a booking.
- Group Insights aggregate only explicit confirmed preference labels across currently accessible nondeleted plans; Member mode still excludes QA plans.
- Automatic background refresh happens during active app use. Sleeping free hosting cannot deliver out-of-app proactive reminders; external notifications remain outside scope.

## Required verification
Backend tests and repository projection tests; frontend lint/typecheck/build; full Playwright frontend/shared suites, including owner/member/admin isolation, generator confirmation, factual fallback, and stale-refresh protection. Live provider smoke uses synthetic content only.
