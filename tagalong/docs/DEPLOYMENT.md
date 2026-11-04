# Deploying Tagalong

The connected app runs as a Next.js web service, a FastAPI web service, and an ingestion worker. Supabase supplies Auth/Postgres/Realtime. OpenAI and Pinecone stay server-side. `render.yaml` describes the three hosting services; it has not been provisioned merely by committing it.

## Local verification

```text
npm ci
cd backend
uv sync --frozen --python 3.12
uv run pytest tests -q
cd ..
npm run lint
npm run typecheck
npm run build
npx playwright install chromium
npm test -- --workers=2
npm run test:shared
```

The browser suites run the production standalone server. Shared tests start the real FastAPI HTTP server with explicitly test-only authentication and in-memory storage; they never claim a live Supabase integration. `backend/TESTING.md` describes the separately gated real SQL/RLS checks.

Shared edits send bounded field patches with an expected revision. The server reconstructs an authorized plan view and applies the same validation as a complete snapshot. This keeps an unrelated vote or task change small even when the plan has a large conversation history. Legacy snapshot PUT remains available directly on the backend.

For local connected development, create `backend/.env` from its example and a frontend `.env.local` from the root example. In PowerShell, backend environment loading can use `uv run --env-file .env uvicorn tagalong.app:app --host 127.0.0.1 --port 8000` and worker `uv run --env-file .env python -m tagalong.worker` from `backend`. Run `npm run dev` in a separate terminal at the Tagalong root.

## Provisioning

1. Create a Supabase project and save its database administrator connection, URL, service-role key, and publishable/anon key in the hosting secret settings. The service-role key and database connection belong only to API and worker. Use a dedicated project or namespace; never apply migrations over another app's tables without review.
2. Apply `supabase/migrations/202611040001_tagalong.sql` to the new project. It creates only `tagalong_*` objects and membership-filtered revision notifications. Administrative writes go through FastAPI. Test migration/RLS on a disposable test project before production.
3. Configure Supabase Site URL and allowed redirects for the actual public frontend origin. Enable email confirmation and configure production SMTP. Supabase's default mail service cannot support unrestricted public signups; verify delivery to two external addresses. Public signup is not verified until this succeeds. See [Supabase SMTP documentation](https://supabase.com/docs/guides/auth/auth-smtp).
4. Reuse the authorized OpenAI and Pinecone account keys through the host's secrets UI. The existing 768-dimensional cosine index can be used with `OPENAI_EMBEDDING_DIMENSIONS=768`; an index with 1536 dimensions needs that value instead. Both API and worker must use the same embedding model and dimension. Each plan uses its own `tagalong:{plan_id}` namespace; other projects' vectors are not queried.
5. Create a Render Blueprint from `Chandra-P/Master_AgenticAI`, selecting `tagalong/render.yaml` and the reviewed application branch. The blueprint requests three paid starter services; review the provider's displayed pricing before creation. Automatic deploys are disabled until tests and live checks pass. Secret prompts are defined on each backend service because Render does not support `sync: false` inside environment groups.
6. Supply the API's HTTPS origin as frontend `FASTAPI_BASE_URL`, plus the public Supabase URL and publishable key. Set `TAGALONG_REQUIRE_CONNECTED=true`. The frontend health route refuses readiness if configuration or API readiness is missing. API `/health` verifies database schema availability; it does not prove provider account quotas or email delivery.
7. Verify both backend services use the same database and provider configuration. The worker performs dimension checks before ingestion. On Supabase poolers, use the connection mode supported by the Psycopg settings; prefer a session-pooler connection if direct IPv6 connectivity is unavailable. Require TLS on external database connections.

The blueprint validates against [Render's official schema](https://render.com/schema/render.yaml.json). Docker builds must also pass CI or a local Docker build before deployment; schema validation alone does not execute containers.

## Public smoke test

Use two real accounts. Verify signup/confirmation/sign-in, plan creation, membership sharing, cross-account isolation, chat persistence after refresh, vote replacement, stale-change conflict reporting, AI preference proposals and explicit confirmation. Add a text document, run ingestion, request its history and inspect source citations. Revoke one member and verify their next API request is denied and private UI clears after refresh. Verify sign-out cannot restore old private data, even during a slow response. Verify the public HTTPS URL on desktop and mobile. Calendar and Places remain unavailable; the app must never report a booking or calendar write.

Set provider spend controls and observe the API's per-account assistant limit. Inspect failed ingestion jobs without recording secret values or raw group conversations in public logs. Back up Postgres and test restoration. The initial repository uses one locked state aggregate with narrowly updated projections: reads avoid writes, but all writes serialize. This is suitable for a small initial rollout; load-test and migrate to row-level transactions before a large launch.

## Release evidence

Record the commit, CI run, migration environment, provider checks, public URL, real-account flow results and remaining limitations in `docs/CONNECTED_STATUS.md`. A successful local build is not evidence that the public deployment exists.
