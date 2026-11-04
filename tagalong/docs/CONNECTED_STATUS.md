# Connected application work in progress

Snapshot requested by the user on 2026-11-04. This is not a public release.

Implemented: Supabase sign-in/account UI; server-side FastAPI proxy; shared plan adapter with revision conflicts; member sharing; assistant responses and evidence UI; proposal confirmation; authenticated FastAPI services; Postgres migration; OpenAI/LangGraph/Pinecone adapters; durable source ingestion worker. The browser demo remains available separately.

Verification in this session: frontend lint, TypeScript and production build passed. Backend suite: 14 tests passed. Connected-mode browser tests for configuration isolation and authentication/service failures passed on desktop. Existing demo browser tests are failing and remain under investigation. The full browser suite is not passing. Real Supabase/Postgres, OpenAI/Pinecone calls and public deployment have not been verified.

Pending: finish browser regression fixes; run real two-account integration tests; configure Supabase database/auth and hosted frontend/API/worker; verify external provider access, ingestion, RLS and public URL; finish deployment configuration and operational documentation. Places and Calendar are disabled. No live reservation or calendar action is available. Do not present this snapshot as production ready.

Secrets remain excluded. Existing project keys may be reused only through local/server environment configuration. Never place server credentials in NEXT_PUBLIC_ variables.
