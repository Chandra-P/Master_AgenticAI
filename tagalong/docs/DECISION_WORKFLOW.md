# Decision-first planning

Tagalong helps groups move from an idea to agreement and a finalized plan. The homepage keeps the existing visual identity and provides an idea composer, **Your next steps** and **Continue planning**. Decisions is the default plan section; Chat, polls, board, discovery, itinerary, documents, Group fit and demo bookings remain available.

## How it works

1. Describe an idea and choose **Start Planning**. Connected plans retain AI draft review and manual fallback. Demo creation is explicitly simulated and reviewed.
2. Working plan details become proposed options. Trips start with destination, dates, budget, lodging and activities; outings use place, date/time, budget and activity/meal. They are not automatically confirmed.
3. Each member responds to the current option version: Support, Can live with, Object or Abstain. Comments belong to the decision and never count as votes.
4. Everyone must respond before the owner confirms. All non-abstaining members must consent to the same option, at least one member must consent, and objections must be resolved. A leading option is not agreement.
5. The owner reviews the outline and explicitly finalizes. Reopening or changing choices, membership or the working outline invalidates obsolete responses and finalization.

All members can review and respond; the owner creates/edits decisions and confirms/finalizes. Required decisions can be made optional through a recorded owner edit. No required decisions means finalization is unavailable. Unresolved objections also block finalization, including in optional decisions.

## Consensus progress

| Score | Label |
| --- | --- |
| 0–30% | Early Discussion |
| 31–70% | Narrowing Options |
| 71–99% | Almost Ready |
| 100% | Finalized |

For each required decision, the contribution is confirmed agreement (1) or the fraction consenting to its leading current option. Abstentions count participation, not agreement; all-abstain contributes zero. The average is rounded and capped at 99 until explicit finalization. Planning completeness remains a different metric in the legacy coordination view. Finalization does not book, charge or send messages.

Homepage blockers and missing participants use actual current-version responses, not model guesses or chat activity. Last activity is recorded rather than invented at render time. The desktop momentum panel becomes an accessible mobile drawer.

## AI and sources

The top summary reuses current revision-matched coordination output. Each connected decision also has an explicit **Summarize decision** action. It uses the existing configured model and returns a timestamped summary with expandable **Evidence used** excerpts and source versions. These are inputs used for the summary, not verbatim attributed model quotations. No per-decision model fanout occurs on page load.

Summaries use current decision facts, vote distribution, missing participants and bounded current-version comments. Text is untrusted data. Model output never sets agreement, permissions, votes or finalization. Stale account/role/plan/version responses are discarded. If AI is unavailable or returns invalid output, recorded responses/comments remain usable and the UI explains the fallback.

The endpoint shares the existing 60-per-hour coordination request budget, throttles changed decision summaries for 15 seconds, and limits concurrent requests. Cached current summaries avoid repeated calls. Tests use fake providers; no new production provider or credential is needed.

## State and code map

- `backend/tagalong/decisions.py`: contracts, defaults, consent, score, comments, owner commands and reconciliation.
- `backend/tagalong/decision_summaries.py`: authorized, versioned, bounded summary generation/cache.
- `backend/tagalong/core.py` and `repository.py`: atomic invalidation in both memory and Postgres transactions.
- `src/services/decisions.ts`: typed transport, response validation and participation helpers.
- `src/services/demo-decisions.ts`: independent local-demo persistence/consent adapter through plan state.
- `src/features/planning/decisions/use-decision-snapshot.ts`: account/role/plan-scoped loading, commands, pagination and summary requests.
- `src/features/planning/decisions/`: rich home cards, structured decision cards/comments, evidence summaries, progress meter and responsive workspace.

Connected data is stored in the existing transactional JSON state as `decision_state`, with versioned source/ingestion records in the existing source model. No SQL schema migration or new dependency is required. Demo data stays in the existing browser-local plan store. Reusable demo-group contacts never become authenticated members or summary context.

## Compatibility and bookings

Existing polls remain legacy/unclassified and keep their original votes. They are not automatically converted into confirmations. Old tab links still work; the default changed from Chat to Decisions. Existing plans can review/confirm the new proposals without losing their chats or polls.

Strict new decision booking gates engage when a plan first mutates its decision workflow. A read-only visit that seeds legacy proposals does not silently invalidate the old booking workflow; its existing poll and owner approval checks remain enforced. This compatibility boundary is intentional. Once engaged, new decision confirmation/finalization checks also apply. Genuine working-outline edits reopen decisions, while server-owned demo booking/cancellation records preserve already reviewed choices. Clients cannot forge or edit those reservation entries through generic plan updates.

Comments are bounded and paginated (50 per request in the UI; snapshot includes recent comments and total counts). Loading older pages preserves that depth across polling/refreshes.

## Release checklist

This change is local and unpublished until the owner requests publication. Deploy the matching API before the frontend, then verify real account collaboration. Both services are required for connected Decisions; an older API produces a recoverable decisions error, not fabricated demo agreement. Existing Render branch settings do not change automatically.

Before release: lint, typecheck, production build, complete frontend/shared/backend tests and responsive visual review. The release evidence in `CONNECTED_STATUS.md` distinguishes local synthetic checks from live authentication, production persistence and provider verification.
