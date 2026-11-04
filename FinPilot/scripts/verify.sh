#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/ruff check backend
.venv/bin/ruff format --check backend
(cd backend && ../.venv/bin/pytest -q)
(cd backend && ../.venv/bin/python -m finpilot.evaluation) > artifacts/golden.json
(cd frontend && npm run lint && npm run typecheck && npm test && npm run build)
printf '\nFor live browser checks: cd frontend && npx playwright install chromium && npm run test:e2e\n'
