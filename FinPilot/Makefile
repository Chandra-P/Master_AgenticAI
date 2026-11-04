.PHONY: setup seed reset test eval build dev-api dev-web
setup:
	python3 -m venv .venv
	.venv/bin/pip install -r backend/requirements.txt
	cd frontend && npm ci
seed:
	cd backend && ../.venv/bin/python -m finpilot.db seed
reset:
	cd backend && ../.venv/bin/python -m finpilot.db reset
test:
	.venv/bin/ruff check backend
	.venv/bin/ruff format --check backend
	cd backend && ../.venv/bin/pytest -q
	cd frontend && npm run lint && npm run typecheck && npm test
eval:
	cd backend && ../.venv/bin/python -m finpilot.evaluation
build:
	cd frontend && npm run build
dev-api:
	cd backend && ../.venv/bin/uvicorn finpilot.api:app --host 127.0.0.1 --port 8000
dev-web:
	cd frontend && npm run dev
