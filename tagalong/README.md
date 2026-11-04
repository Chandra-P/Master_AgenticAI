# Tagalong

**Good plans. Great company.**

A group planning app with a browser-local demo and a separately configured shared workspace. Built with Next.js, FastAPI, Supabase Auth/Postgres/Realtime, LangGraph, OpenAI and Pinecone. Public deployment is pending provisioning and live account/database checks; see [current release evidence](docs/CONNECTED_STATUS.md).

## Shared workspace

Sign in at `/account` when Supabase and the API are configured. Create shared plans, add existing signed-in accounts by email, chat, vote, paste text documents, request grounded assistant suggestions, confirm proposed preferences, and revoke membership. Changes use revision checks to avoid overwriting concurrent edits. Sources are restricted to the plan and validated against current document versions. OpenAI suggestions cannot execute reservations or calendar actions.

The demo uses synthetic people and venues and simulated AI. Shared mode uses authenticated accounts, real persistence, and the configured OpenAI model. An unavailable connected service reports an error; it never silently substitutes demo data. Live venue search and calendar integration are not enabled.

For setup, environment variables, Docker/Render deployment, production email delivery and release verification, see [deployment instructions](docs/DEPLOYMENT.md) and [backend testing](backend/TESTING.md).

## Run locally (Windows, macOS, Linux)

Install Node.js 22 LTS or newer, then open a terminal in this folder:

```bash
npm ci
npm run dev
```

Open http://localhost:3000. The dashboard is at `/`; the product landing page is at `/welcome`.

In VS Code, clone `https://github.com/Chandra-P/Master_AgenticAI.git`, then open its `tagalong` folder. Use the reviewed application branch until its PR is merged.

## Demo features

- Create an outing or trip with dates and demo participants.
- Open a shared workspace with chat and a local planning board.
- Mention `@Tagalong` to receive a clearly labeled, simulated assistant response.
- Review proposed preferences and explicitly confirm them.
- Create polls, cast a vote, and change that vote.
- Edit working budgets and destinations; manage next-step tasks.
- Browse synthetic suggestions, add them to draft itineraries, and add or remove activities.
- Responsive sidebar and mobile bottom navigation.
- Browser-local persistence for plans and interactions.

## Demo boundaries

In demo mode, participant, venue, rating, and planning details are synthetic. Photos are illustrative Unsplash images stored locally. Assistant responses are deterministic simulations and demo data stays in one browser. Shared mode persists group data on the backend; all members can read the group's content. Neither mode makes reservations or calendar changes, and adding a member does not send an invitation email.

## Structure

- `src/app`: App Router pages and global styling.
- `src/components`: Shared shell, branding, and UI primitives.
- `src/features/planning`: Interactive feature views and React state provider.
- `src/services`: TypeScript models, synthetic seed data, and mock service implementations.
- `tests`: Playwright desktop and mobile acceptance scenarios.
- `.env.example`: Future configuration names only; Phase 1 needs no secrets.

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
