# Tagalong

**Good plans. Great company.**

An AI-assisted group decision-making app that helps people move from an idea to consensus and a finalized plan, with a browser-local demo and authenticated shared workspace. Built with Next.js, FastAPI, Supabase Auth/Postgres/Realtime, LangGraph, OpenAI and Pinecone. The public app is at https://tagalong-web-clbe.onrender.com; verify each new release against both frontend and API rather than assuming a pushed commit is deployed.

The decision-first experience adds action-oriented home cards, versioned decisions/responses, contextual comments, consent progress, owner confirmation/finalization and evidence-backed on-demand AI summaries. Its implementation and compatibility rules are documented in [Decision workflow](docs/DECISION_WORKFLOW.md). A score of 100% requires explicit finalization and never means a booking was made.

## Shared workspace

Sign in at `/account` when Supabase and the API are configured. Create shared plans, add existing signed-in accounts by email, chat, vote, paste text documents, request grounded assistant suggestions, confirm proposed preferences, and revoke membership. Changes use revision checks to avoid overwriting concurrent edits. Sources are restricted to the plan and validated against current document versions. OpenAI suggestions cannot execute reservations or calendar actions.

The demo uses synthetic people and venues and simulated AI. Shared mode uses authenticated accounts, real persistence, and the configured OpenAI model. An unavailable connected service reports an error; it never silently substitutes demo data. Connected Discover supports venue cards and source links through Keenable; live availability and calendar integration are not enabled.

For setup, environment variables, Docker/Render deployment, production email delivery and release verification, see [deployment instructions](docs/DEPLOYMENT.md) and [backend testing](backend/TESTING.md).

## Run locally (Windows, macOS, Linux)

Install Node.js 22 LTS or newer, then open a terminal in this folder:

```bash
npm ci
npm run dev
```

Open http://localhost:3000. The dashboard is at `/`; the product landing page is at `/welcome`.

In VS Code, clone `https://github.com/Chandra-P/Master_AgenticAI.git`, then open its `tagalong` folder. Create feature branches from `main`; unpublished feature work is available only in its named local branch until released.

## Demo features

Reusable themed **Groups** are available in both modes. Signed-in groups are private reusable rosters saved to your account; demo groups remain local to your browser. Both manual plan creation and reviewed AI drafts can select/create a group. Contacts are intended participants, not authenticated members; invite them explicitly using existing plan controls. Shared Groups rollout requires reviewed frontend/API deployment. See [Groups behavior and deployment](docs/GROUPS.md).

- Create an outing or trip with dates and demo participants.
- Open a shared workspace with chat and a local planning board.
- Mention `@Tagalong` to receive a clearly labeled, simulated assistant response.
- Review proposed preferences and explicitly confirm them.
- Create polls, cast a vote, and change that vote.
- Edit working budgets and destinations; manage next-step tasks.
- Browse synthetic suggestions, add them to draft itineraries, and add or remove activities.
- Responsive sidebar and mobile bottom navigation.
- Browser-local persistence for plans and interactions.
- Optional typing suggestions: local in demo mode; connected mode adds OpenAI continuations after a pause. Accepting never sends a message.

In a shared plan, **Demo bookings** demonstrates real MCP calls against a fictional restaurant provider. Explore options, complete group voting and working details, obtain owner approval, then explicitly confirm a simulated reservation. See [the MCP demo guide](docs/DEMO_BOOKING_MCP.md). No real reservation or charge occurs.

**Group fit** checks an option against the current budget, confirmed preferences, saved Notes and plan-scoped retrieved history. Results separate matches, conflicts and missing information, with sources you can inspect. The check does not change the plan or make a reservation. See [the RAG walkthrough](docs/GROUP_FIT_RAG.md).

For the competition narrative, recorded demo, presentation preflight and measured results, see [the Gen Academy demo guide](docs/GEN_ACADEMY_DEMO.md) and [the four-case live evaluation](docs/evaluations/2026-11-06-group-fit-demo.md).

## Demo boundaries

In demo mode, participant, venue, rating, and planning details are synthetic. Photos are illustrative Unsplash images stored locally. Assistant responses are deterministic simulations and demo data stays in one browser. Shared mode persists plan data on the backend; plan members can read their shared plan content. Reusable group contact rosters are private to their owner, and only minimal aliases are copied into plans. Neither mode makes reservations or calendar changes, and adding a member does not send an invitation email.

## Structure

- `src/app`: App Router pages and global styling.
- `src/components`: Shared shell, branding, and UI primitives.
- `src/features/planning`: Interactive feature views and React state provider.
- `src/services`: Typed connected adapters, local demo data, and pure helpers for typing, patches, and itinerary ordering.
- `tests`: Playwright desktop and mobile acceptance scenarios.
- `.env.example`: Public frontend configuration names only; local demo mode needs no provider secrets.

`src/services/connected.ts` provides the authenticated shared-workspace adapter. `backend/tagalong` contains planning services, authorization, LangGraph orchestration and provider adapters; `supabase/migrations` contains the schema. The worker indexes plan sources in isolated Pinecone namespaces. Google Calendar and Google Places remain future integrations; external writes require explicit approval.

## Checks

```bash
npm run lint
npm run typecheck
npm run build
npx playwright install chromium
npm test
npm run test:shared
cd backend
uv run pytest tests -q
```

`VERIFICATION.md` preserves initial-import results. See `docs/CONNECTED_STATUS.md` for current checks and the remaining public-release requirements. The shared browser suite uses the real local API with explicit test-only account/provider adapters; it does not prove production Supabase or email configuration.
