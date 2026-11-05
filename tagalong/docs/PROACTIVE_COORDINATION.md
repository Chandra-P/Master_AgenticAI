# Proactive coordination demo

Tagalong helps groups move from idea → decision → itinerary → experience. This release extends the existing Next.js/FastAPI/Supabase/LangGraph/OpenAI/Pinecone architecture. It adds no microservice or event-sourcing system.

## Implemented architecture

- **Frontend:** the new homepage contains the requested hero and natural-language input, Continue Planning, AI Recommendations, explicit Group Insights, and the existing plan list. Connected creation dialogs use AI drafts by default with a manual fallback. Each connected workspace has a summary, derived health, open questions and prominent next action.
- **FastAPI:** validates structured drafts, memberships and current account mode. An accepted draft is created transactionally once, even on retry. Initial description, tasks, generic itinerary ideas and reviewed working details are saved together.
- **LangGraph:** dispatches generation to `PlanGeneratorNode`; coordination runs `SummaryNode → RecommendationNode`; chat uses `ExistingAssistantNode`, preserving its existing conditional RAG path. All new model outputs use OpenAI Responses structured JSON and server validation.
- **Postgres:** the existing locked aggregate remains authoritative. New maps hold draft ownership/expiry, plan activity, bounded refresh leases and cached coordination snapshots. `tagalong_coordination` is a backend-only queryable projection, with RLS and direct anon/authenticated access revoked.
- **OpenAI/Pinecone:** OpenAI drafts and summarizes; confirmed preference labels ground generic activity recommendations. Existing plan-scoped embedding/retrieval and source validation remain. Summaries read bounded messages, polls, documents and itinerary directly from Postgres; they do not wait for vector indexing.
- **Keenable:** Discover remains an explicit source-link web search. New activity ideas are generic suggestions, not verified venues or live availability.

## API endpoints

| Endpoint | Behavior |
| --- | --- |
| `POST /v1/plans/generate` | `{prompt, local_date}` → validated `{draft_id, draft, mode, notice}`. Does not create a shared plan. |
| `POST /v1/plans/from-draft` | Owner reviews title/type/location/dates/per-person budget and confirms creation. Stored draft supplies visible suggested tasks/itinerary. |
| `GET /v1/plans/{id}/coordination` | Current derived health/factual snapshot plus cached AI summary and next action; schedules an eligible background refresh. |
| `GET /v1/coordination/overview` | Accessible-plan cards, blockers and confirmed-preference insights; schedules at most three eligible refreshes per request. |

Drafts expire after 30 minutes and belong to their generating account. Generation is limited to 30 attempts/account/hour. Coordination refreshes use a 120-second lease, a 15-second per-plan cooldown and a 60-refresh/account/hour budget. Provider calls run outside database transactions. Results are discarded if the source fingerprint changes or the requesting actor loses access before saving.

## Health and activity rules

Health is a transparent progress indicator, not model confidence. Six equally weighted checks cover dates, resolved voting, location, a positive working budget, a draft itinerary and completed tasks. A stalled plan receives a 20-point deduction, bounded at zero. Existing zero budgets are treated as not yet set.

Statuses are `WAITING_FOR_DATE`, `WAITING_FOR_VOTES`, `WAITING_FOR_LOCATION`, `READY_TO_FINALIZE`, `ACTIVE`, `COMPLETED` and `STALLED`. Inactivity of at least seven days with unresolved work produces STALLED and a Resume Planning action. Completion requires elapsed dates and all tracked checks resolved. ACTIVE means planning is progressing; it does not assert attendance or a booking. A unique vote leader can resolve the voting-progress check after every current member votes, but is never represented as confirmed group consensus.

Human plan edits, messages, votes, membership changes and document changes update activity. AI reads/refreshes do not. Old plans without reliable activity metadata receive a new baseline rather than fabricated historic inactivity.

## Product and privacy boundaries

Unknown dates remain null in the AI draft and must be reviewed before creation. Intended participant counts do not create fake members or send invitations. Budget basis is preserved; a proposed total is not silently stored as a per-person amount. Dates, budgets and itinerary items are working details. Confirmed preferences are distinguished from proposals, and only explicit confirmed labels populate Group Insights. Activity ideas must cite those same labels. Model text cannot publish polls, assign tasks or create bookings.

The context has a hard 40,000-character serialized limit, including derived poll metadata. Every read uses current membership, deletion and Admin/Member restrictions. Homepage cards require matching accessible plan IDs/revisions; insights come from the current accessible plans. Sign-out and mode/account changes invalidate old requests and unmount private views.

## Migration and rollout order

1. Apply `supabase/migrations/202611050001_coordination.sql` using the existing administrative database connection. This is additive and touches no existing plan content. It has been applied to the selected Tagalong project and its RLS/no-direct-read settings verified.
2. Deploy the backend and frontend from the reviewed branch. No new secret or paid service is required. Keep the existing OpenAI and Pinecone configuration.
3. Check the homepage, generate/review a draft, and open its workspace. Confirm current facts immediately and the AI summary after its bounded background refresh.
4. Verify member/admin and revoked-plan isolation. Check provider failures show factual fallbacks rather than synthetic live answers.

Proactivity in this release occurs while people use the app: the homepage and plan cards refresh automatically without an `@Tagalong` mention, and stalled status is derived when read. Free Render services can sleep. This release does not promise offline notifications or an always-on reminder scheduler. Existing external/embedded indexing configuration remains separate.

## Demo in one minute

Describe a weekend for four near Austin with a USD350-per-person budget; generate a draft; review missing dates; create the shared plan; point out the initial planning message, tasks and draft itinerary; show the automatic summary and voting blocker. Confirm a preference to demonstrate explicit Group Insights. Contrast a current factual recommendation with a live AI recommendation using the visible source label.

The model smoke test used synthetic content and passed structured date/budget extraction, summary, recommendation and existing assistant dispatch. Browser tests use explicitly test-only accounts and a deterministic provider; these do not substitute for live Supabase signup verification.
