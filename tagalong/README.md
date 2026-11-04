# Tagalong

**Good plans. Great company.**

A Phase 1 interactive frontend prototype for planning group outings and trips. Built with Next.js App Router, TypeScript, Tailwind CSS, Radix-based shadcn-style UI components, and lucide-react.

## Run locally (Windows, macOS, Linux)

Install Node.js 22 LTS or newer, then open a terminal in this folder:

```bash
npm ci
npm run dev
```

Open http://localhost:3000. The dashboard is at `/`; the product landing page is at `/welcome`.

In VS Code, use **Git: Clone** with `https://github.com/Chandra-P/tagalong.git`, then open the cloned folder. Pull changes from GitHub to bring remote changes into your local checkout.

## Prototype features

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

All participant, venue, rating, and planning details are synthetic. Photos are illustrative Unsplash images stored locally. Assistant responses are deterministic simulations. No live inventory, real invitations, reservations, calendar changes, or production integrations are used. Data is stored only in this browser, not synchronized across users or devices.

## Structure

- `src/app`: App Router pages and global styling.
- `src/components`: Shared shell, branding, and UI primitives.
- `src/features/planning`: Interactive feature views and React state provider.
- `src/services`: TypeScript models, synthetic seed data, and mock service implementations.
- `tests`: Playwright desktop and mobile acceptance scenarios.
- `.env.example`: Future configuration names only; Phase 1 needs no secrets.

`PlanningService` and `AssistantService` are replacement boundaries for future Supabase and FastAPI services. Supabase Auth/Postgres/Realtime, OpenAI Responses API with LangGraph, Google Calendar, and Google Places are future work. Booking and calendar writes must require human approval in future phases.

## Checks

```bash
npm run lint
npm run typecheck
npm run build
npx playwright install chromium
npm test
```

The initial upload remains a prototype under verification. See `VERIFICATION.md` for the results from the upload session. Production integration work has not started.
