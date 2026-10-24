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
