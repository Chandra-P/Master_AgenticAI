# Grounded recommendations and retrieval reliability

## Intent

Make Tagalong's AI evidence visibly useful when groups evaluate and discover options. Retrieved group constraints should materially affect option assessments and rankings, while authoritative current state remains exact and deterministic.

## Goals

- Use Pinecone for semantically retrieving unstructured evidence within the current plan only.
- Fix retrieval chunk extraction, preserve useful ranking metadata internally, and disclose when indexing is behind or retrieval fails.
- Join saved group evidence with public venue results in the recommendation flow; return source-backed matches, conflicts, and unknowns that can change ordering and explain why.
- Keep current plan facts, confirmed preferences, vote counts, consensus, decision status, and workflow rules grounded in PostgreSQL and deterministic application logic.
- Verify evidence IDs and source versions before returning a result; do not write AI assessments into a plan automatically.
- Demonstrate material retrieval value with synthetic ablation tests: the same options evaluated with and without a distinctive saved constraint must produce different supported outcomes.

## Non-goals

- Cross-plan or cross-user retrieval, learned personal profiles, or private benchmark sharing.
- Booking, outbound notifications, external actions, or automated decisions.
- Calling Pinecone for exact votes, current budgets, dates, or other structured facts.
- Claiming research snippets establish live prices, inventory, safety, venue hours, or availability.
- Replacing current summaries or consensus calculations with RAG.

## Approaches considered

1. **PostgreSQL-only selection.** Simple and reliable for current structured state, but cannot reliably find a distinctive older constraint buried in unstructured discussion.
2. **Pinecone for plan memory; PostgreSQL for exact state (chosen).** Retrieval supplies older discussion and Notes to an evidence-aware option evaluator. SQL/application logic remains authoritative for votes, confirmed preferences, budgets, and workflow. This best fits the existing implementation and keeps vector search scoped to work it can improve.
3. **RAG for every AI feature.** Rejected because vote math and current decision state are exact database queries; semantic retrieval there adds noise and weakens correctness.

## Design

### Retrieval and indexing

- Keep the existing plan namespace and source/version validation.
- Return bounded, deduplicated retrieval candidates with similarity scores and correct chunk offsets; do not allow a stale or foreign source to enter model context.
- Correct every chunk consumer to return the complete selected chunk, not a truncated prefix.
- Derive freshness from current source versions and their durable ingestion jobs. Report current, pending, failed, or unavailable state distinctly; current Notes and structured facts remain available during indexing delays.
- Do not expose provider errors or raw credentials. Avoid returning similarity scores as a quality guarantee in the UI.

### Evidence-aware option discovery

- Continue public search and plan-scoped evidence retrieval concurrently.
- Build semantic retrieval queries from the user's search, option category, destination/dates, and confirmed preference labels. Pending proposals must not be represented as group agreement.
- Add a bounded structured model assessment that evaluates each identified public option against relevant saved group evidence plus authoritative plan facts.
- Each option result contains evidence-linked matches, conflicts, unknowns, and a conservative fit state. Use deterministic budget checks where estimates exist. Reorder options using supported fit state; never invent precise scores or unsupported facts.
- Require every evidence-based finding to cite its own public option source and the specific supporting group source (or authoritative plan-facts source), and validate every cited ID against the request's verified evidence. Preserve public source provenance separately from private plan evidence.
- Show a concise explanation and expandable sources on each option card. Keep search results clearly unverified and allow a member to review/propose an option without implying consensus.

### Group Fit and other features

- Retain the existing Group Fit workflow, improve it with the corrected retrieval/chunk handling and explicit index freshness.
- AI summaries may use supplied current context and cite direct sources; describe them as context-grounded summaries, not Pinecone RAG.
- Consensus, voting patterns, confirmed preferences, and plan progress remain SQL/application-derived. Do not vectorize them into recommendations as if semantic similarity were authority.
- Discovered option comparisons use the evidence-aware evaluator; generic AI starter ideas remain proposals and are not described as retrieved recommendations.

## Interfaces and files

- Backend retrieval: `tagalong/backend/tagalong/providers.py`, `group_fit.py`, `app.py` and a focused retrieval/evidence helper if needed.
- Backend research ranking: `tagalong/backend/tagalong/research.py` plus the connected provider's structured assessment method.
- Frontend contracts and cards: `tagalong/src/services/option-research.ts`, `tagalong/src/features/planning/research/research-results.tsx` and scoped styles.
- Tests: backend provider/research/group-fit tests, frontend research-card tests, and shared HTTP/browser coverage where the existing suite supports it.
- Documentation: RAG feature guide, deployment/indexing health instructions, and a demo/evaluation walkthrough.

## Safety and privacy

- Enforce membership, plan isolation, source-version checks, bounded inputs/outputs, request limits, timeouts, and no-store responses.
- Treat user text, public search snippets, and venue pages as untrusted evidence, never tool instructions.
- Use only evidence belonging to the current authorized plan and public sources already returned by the search provider.
- Do not persist model rankings, silently change decisions, or send notifications.

## Acceptance criteria

1. Retrieval of a second chunk returns that entire stored chunk, and source/version authorization still excludes stale, deleted, and foreign records.
2. Research responses include verified, source-cited option assessments, and retrieved group constraints can change the ordering or verdict compared with a no-history ablation.
3. UI shows why an option fits or conflicts and links each claim to the supporting source; unknowns and index freshness are visible.
4. Current structured facts and deterministic vote/consensus logic remain authoritative and unchanged by vector results.
5. Synthetic tests cover retrieval outage, indexing pending/failed, no evidence, malformed citations, changing source versions, over-budget options, and cross-plan isolation.
6. Documentation clearly distinguishes RAG, database-grounded summaries, web search, deterministic workflows, and simulated booking.

## Release constraints

- No new dependency, schema migration, new external account, cross-plan sharing, or production-data mutation.
- Do not publish automatically; keep deployment as a separate explicit action. Hosted indexing may require the existing Render `TAGALONG_EMBEDDED_WORKER=true` setting, which must be verified by the account owner.
