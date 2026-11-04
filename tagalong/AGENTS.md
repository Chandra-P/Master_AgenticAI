# Tagalong conventions
- Next.js App Router, strict TypeScript, Tailwind CSS. Run commands from this directory.
- Components live in src/components; planning UI/state in src/features/planning; typed mock services in src/services.
- All demo people, venues, votes and conversations are synthetic. AI is explicitly simulated. Never imply live inventory, reservations, or sent invitations.
- No credentials in source. Future settings belong in .env.local; document names only in .env.example.
- Keep state per plan, validate user input, use accessible labels and keyboard focus.
- Before delivery run npm run lint, npm run typecheck, npm run build, npm test.
