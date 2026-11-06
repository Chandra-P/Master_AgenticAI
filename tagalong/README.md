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
- Reusable adult groups with preset/custom themes, suggested editable names, and archive/restore/remove controls.

## Demo groups

Open `/groups` or choose **Groups** in navigation. Alex is the fixed demo owner. Start with Sunday supper, Weekend friends, Family outings, or type a custom theme. Group names are unique within this browser workspace, including archived groups. Each adult needs a distinct preferred name/alias; email and first/last names are optional. Use synthetic adult details only. Do not enter children's names or photos.

Choose **Plan with this group**, or select/create a group in the existing plan dialog. Creating a group within that dialog preserves the plan draft. Saving the group keeps it even if you later cancel the plan. New plans copy aliases and colors only; contact details remain in group storage and are not passed to the simulated assistant. Editing, archiving or removing groups does not alter existing plan participants, messages or votes. Archived groups cannot be selected for new plans. Creating a group sends no invitations.

Groups use `tagalong-groups-v1` in localStorage; plans retain `tagalong-demo-v1`. An empty saved group list stays empty. Unreadable or unavailable group storage produces a visible warning and an in-memory fallback without overwriting malformed data. This is a single-browser demo, not authenticated or synchronized group membership. No credentials, migrations, additional dependencies or files from the root `workspace/` directory are required.

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

The November 6 groups verification is recorded in `../docs/groups-demo-plan.md`. Browser tests use fresh contexts and synthetic data; screenshots are generated under ignored `test-results/`. `npm run build -- --webpack` is an available production build alternative. The current local ESLint dependency/configuration mismatch is recorded separately from feature results; no packages were changed for groups.
