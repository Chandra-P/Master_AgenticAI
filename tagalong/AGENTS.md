# Tagalong conventions
- Next.js App Router, strict TypeScript, Tailwind CSS. Run commands from this directory.
- Components live in src/components; planning UI/state in src/features/planning; typed mock services in src/services.
- All demo people, venues, votes and conversations are synthetic. AI is explicitly simulated. Never imply live inventory, reservations, or sent invitations.
- No credentials in source. Future settings belong in .env.local; document names only in .env.example.
- Keep state per plan, validate user input, use accessible labels and keyboard focus.
- Before delivery run npm run lint, npm run typecheck, npm run build, npm test.

<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
