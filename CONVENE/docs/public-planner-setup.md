# Private planner preview

The new React/FastAPI planner is separate from the legacy synthetic demo. It
supports private browser sessions, versioned briefs, adaptive intake, corrections,
confirmation and persisted history. Google account saving, Gmail and public
deployment are still in progress. The user selected a new Cloud project and no
domain; no cloud resources have been created.

The chat now includes PostgreSQL retrieval of planning guidance, source-backed
answers and persisted source details. See [conversational-rag.md](conversational-rag.md)
for the implemented grounding, evidence isolation and current provider-ingestion limits.

The approved vendor directory also reads PostgreSQL, including version-bound
approval history. [Directory administration](vendor-directory-admin.md) covers
the separate database roles and local review/import commands.

## Run locally

Use the existing Python 3.12 environment and PostgreSQL non-superuser role.
Connection URLs/passwords live only in ignored `.env` and `.dev/` files.

```powershell
# From CONVENE/
.venv/Scripts/python.exe scripts/dev_postgres_start.py
.venv/Scripts/python.exe scripts/init_planner_db.py
Push-Location frontend
npm ci --no-audit --no-fund
npm run build
Pop-Location
.venv/Scripts/python.exe -m uvicorn convene.planner_preview:create_app --factory --host 127.0.0.1 --port 8001
```

If needed, `scripts/dev_postgres_download.py` downloads the official EDB Windows
binaries into `.dev/`, without installing a system service. The start helper
preserves the existing workspace data. The server uses 127.0.0.1:55432 and separate
development/test databases. Never share ignored files or database contents.

Open http://127.0.0.1:8001 on this computer. This is not a mobile public URL.
The preview uses local HTTP cookies: **never expose this preview entrypoint to
the internet**. The private API factory defaults to Secure cookies. The original
synthetic demo remains separate on port 8000, with Streamlit on 8501.

## API

- `POST /api/session`: opaque, expiring, revocable HttpOnly/SameSite browser
  cookie plus CSRF token. All event mutations require `X-CSRF-Token`.
- `POST /api/events`, `GET /api/events`, `GET /api/events/{id}`: create, list,
  retrieve this session's records. Clients cannot supply owner/authentication flags.
- `POST /api/events/{id}/messages`: message, expected_version, UUID request_id.
  Retries reuse saved receipts; stale versions return 409. Proposed facts need
  exact parent-message evidence and full brief validation. Uncertainty remains unknown.
- `POST /api/events/{id}/confirm`: confirms the reviewed version. Anonymous
  confirmation returns `next_action=sign_in`, never research authorization.
- No legacy `/plans`, `/venues/research` or `/party/agent` routes in this app.

PostgreSQL FORCE RLS protects records, histories, receipts and checkpoints. Use a
non-superuser role without BYPASSRLS. Schema/checkpointer setup is explicit and
administrative, never triggered by a public request.

The six-node graph binds every run to owner/event/brief version and checkpoints
each node. Tests inject stub research; completed runs reopen without repeating it.
A crash during remote work still needs tool-result/outbox reconciliation;
checkpoints alone do not guarantee exactly-once remote side effects. No email
tools are wired into this graph yet.

## Cloud prerequisites and cost

Before hosting: Google Cloud account/billing setup, an available project ID,
authenticated Cloud CLI, Cloud SQL/Secret Manager and a deployed HTTPS origin.
Then configure OAuth against actual callback URLs. Start with the hosting URL;
there is no need to buy a domain for the demo.

Google sign-in saves private events across devices. Separate Gmail consent
authorizes approved outreach. Gmail testing needs a consent-screen test user,
mailbox, and explicitly approved recipient/message; do not send test mail merely
to satisfy tests. Broader public Gmail use may require Google verification.

Hosting/database usage can incur ongoing charges. Eligible new users may receive
$300/90-day trial credits without charges unless manually upgrading. OpenAI usage
is billed separately. Review a concrete estimate before paid provisioning.

- [Google trial terms](https://cloud.google.com/signup-faqs)
- [Cloud Run FastAPI setup](https://docs.cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-fastapi-service)
- [Cloud SQL pricing](https://cloud.google.com/sql/pricing)
- [Google OIDC validation](https://developers.google.com/identity/openid-connect/openid-connect)
- [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)

## November 2 priority

Prove greeting -> confirmed brief -> account save -> sourced venue/decorator
research -> approved Gmail inquiry -> linked reply and truthful status. This local
intake milestone does not complete that path. Public hosting, Gmail, general
research/RAG, uploads, food, SMS, mail jobs and reservation evidence remain work.
