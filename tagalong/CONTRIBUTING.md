# Contributing to Tagalong

Repository: https://github.com/Chandra-P/Master_AgenticAI

The current development and Render deployment branch is `checkpoint/all-projects-2026-11-04`. Use it as the base until the reviewed changes are merged into `main`. Tagalong lives in `tagalong/` within the repository. Ask the repository owner for collaborator access to push your own feature branch; otherwise use a fork and pull request.

## First checkout

Install Git, Node.js compatible with `package.json`/CI, Python 3.12 and uv. Then:

```sh
git clone https://github.com/Chandra-P/Master_AgenticAI.git
cd Master_AgenticAI
git switch checkpoint/all-projects-2026-11-04
git pull --ff-only origin checkpoint/all-projects-2026-11-04
git switch -c feat/your-name-your-change
cd tagalong
npm ci
uv sync --project backend --frozen --python 3.12
npm run dev
```

The frontend can run in local demo mode without live provider credentials. For connected development, copy `.env.example` to `.env.local` and `backend/.env.example` to `backend/.env`; obtain development credentials from the owner through a secure channel. Keep real environment files out of commits. In a second terminal run `uv run --env-file .env uvicorn tagalong.app:app --port 8000` from `tagalong/backend`. Follow `docs/DEPLOYMENT.md` for indexing and provider configuration.

## Pull teammates' changes

Commit or stash your work first. From the repository root, bring the development branch into your own branch:

```sh
git fetch origin
git merge origin/checkpoint/all-projects-2026-11-04
```

If you are only updating the shared base branch, switch to it and use `git pull --ff-only origin checkpoint/all-projects-2026-11-04`. Create a feature branch before editing; do not push directly to the deployment branch.

## Where to make feature changes

- `src/features/planning/workspace.tsx`: workspace tabs, invitations and plan-level actions.
- `src/features/planning/chat.tsx`: group conversation and message composer.
- `src/features/planning/use-typing-suggestions.ts`: debounce, cancellation, current-draft guards and model/local fallback.
- `src/features/planning/typing-suggestions.tsx` and its CSS: suggestion controls and presentation.
- `src/services/typing-suggestions.ts`: pure on-device matching for demo and immediate fallback. Connected model continuations use the authenticated typing endpoint; preserve its bounds and avoid logging or persisting drafts.
- `backend/tagalong/typing_suggestions.py`: OpenAI continuation provider, authorization, input/output bounds and usage limits.
- `src/features/planning/group-fit.tsx` and `src/services/group-fit.ts`: option review, source presentation and typed API client.
- `backend/tagalong/group_fit.py`: read-only RAG evidence assembly, source verification and group-fit result validation.
- `src/features/planning/demo-bookings.tsx` and `backend/tagalong/demo_bookings.py`: reservation review UI and authoritative agreement/confirmation rules.
- `tests`: browser and pure-helper regressions; `backend/tests`: service and authorization tests.

Keep feature behavior in its module rather than growing the workspace component. Remove imports and helpers only after confirming they have no remaining callers. Preserve historical design/release notes as records; update current guides when behavior changes. Demo-only feature development needs no infrastructure dashboard access or production keys.

## Verify and submit

From `tagalong/`:

```sh
npm run lint
npm run typecheck
npm run build
npx playwright install chromium
npm test -- --workers=2
npm run test:shared
uv run --project backend pytest backend/tests -q
```

After reviewing `git diff` and `git status`, stage only your changed source, tests and documentation. For example, from the repository root:

```sh
git add tagalong/src/path-you-changed.tsx tagalong/tests/your-test.spec.ts
git commit -m "Describe the change"
git push -u origin feat/your-name-your-change
```

On GitHub choose **Compare & pull request**, with base `checkpoint/all-projects-2026-11-04` and compare your feature branch. Describe the user-visible change and checks run. Ask the owner to review and merge; a merge into the deployment branch can trigger Render. Read `AGENTS.md` and preserve plan membership, Admin/Member isolation, source validation, and explicit draft/booking distinctions.
