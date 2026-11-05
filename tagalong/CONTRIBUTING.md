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
