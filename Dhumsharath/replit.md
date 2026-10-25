# Workspace

## Overview

pnpm workspace monorepo using TypeScript. Each package manages its own dependencies.

## Stack

- **Monorepo tool**: pnpm workspaces
- **Node.js version**: 24
- **Package manager**: pnpm
- **TypeScript version**: 5.9
- **API framework**: Express 5
- **Database**: PostgreSQL + Drizzle ORM
- **Validation**: Zod (`zod/v4`), `drizzle-zod`
- **API codegen**: Orval (from OpenAPI spec)
- **Build**: esbuild (CJS bundle)

## Key Commands

- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- `pnpm --filter @workspace/api-server run dev` — run API server locally

See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details.

## Local setup

Use Node.js 24 and Corepack with the pinned pnpm 12.15.0. From the workspace root:

```text
corepack pnpm install
corepack pnpm run build
corepack pnpm --filter @workspace/dhumsharath run dev
```

The app runs at `http://localhost:5173/`. To run the API in a separate terminal:

```text
corepack pnpm --filter @workspace/api-server run dev
```

The development API defaults to port `3001`; the mockup sandbox defaults to `5174`.
Explicit `PORT` and `BASE_PATH` environment variables override frontend defaults;
the default frontend base path is `/`.

Authenticated gameplay requires an existing Clerk application. Set its
`VITE_CLERK_PUBLISHABLE_KEY` in `artifacts/dhumsharath/.env.local` before starting
the frontend, and configure Clerk for the local origin. Players must sign in
before playing. Keep backend Clerk secrets in the API environment when using
authenticated API routes. This project requires no OpenAI API keys or AI runtime.

## Artifacts

### Indian Dumb Charades (Dhumsharath)
- **Path**: `artifacts/dhumsharath/`
- **Type**: React + Vite (frontend-only, no backend)
- **Preview path**: `/`
- **Description**: A party game app for Indian Dumb Charades with Telugu movies

### Features
- 60+ Telugu movies spanning multiple decades and genres (easy/medium/hard)
- Movies displayed with Telugu script titles
- Team setup (2-6 teams with custom names)
- Configurable rounds per team (1-5) and time per round (30-120s)
- Difficulty selection (easy/medium/hard mix)
- Real-time countdown timer with color changes
- Point tracking system per team
- Hint system for difficult movies
- Round history and scoreboard
- Final podium with winner announcement
- Smooth animations throughout (framer-motion)
