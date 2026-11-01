# Public Conversational CONVENE Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline. Steps use checkbox syntax. Independent final review required.

**Goal:** Deliver the approved family-planning journey with working Gmail, private accounts, durable automation and truthful confirmation states.
**Architecture:** React/TypeScript on a FastAPI service; PostgreSQL owns event/approval/outbox state and LangGraph checkpoints. Tool gateway authorizes every side effect. Durable workers process Gmail and scheduled jobs.
**Tech Stack:** Python 3.12+, React/TypeScript, FastAPI, LangGraph, PostgreSQL/pgvector, OpenAI, Keenable, Google OAuth/Gmail/PubSub, Cloud Run/Tasks/Scheduler/Storage, Twilio.
**Spec:** docs/superpowers/specs/2026-11-01-public-planner-design.md

## Global constraints

- San Antonio, Texas; parents; venues, professional decoration, restaurant party trays.
- One adaptive question per turn; tentative answers supported; confirmed brief before research.
- Five suitable options per chosen category when evidence supports them; no invented filler.
- Google sign-in distinct from Gmail authorization. Private multi-event accounts.
- Parent approves initial inquiries, attachments, commitments and material changes.
- Auto-replies only from confirmed facts; 24-hour follow-ups maximum three per inquiry.
- Booking/payment/contract/readiness remain separate and evidence-backed.
- No bookings, contracts, purchases or payments executed by this app.
- No protected .git mutation or commits until intended CONVENE remote is confirmed.
- Preserve local API-key-free synthetic demo; do not expose unauthenticated legacy data/tools publicly.

## Review focus

1. Cross-account event/checkpoint/file/thread access must fail, including valid IDs owned by another parent.
2. Duplicate/replayed jobs and ambiguous Gmail send timeouts must not cause blind duplicate mail.
3. Changed briefs, revoked grants or expired approvals must block old queued actions.
4. A quote, acknowledgement or uncertain deposit must not falsely confirm a booking.
5. Provider failure, insufficient comparable prices or missing portions must remain unknown, not fabricated success.

## Milestones and dependencies

Working Gmail is mandatory in the first end-to-end demonstration, not deferred in
favor of SMS or visual polish. Tasks 1-7 form that integrated path; Task 8 supplies
reliability/notifications; Task 9 deploys and establishes actual release readiness.
November 2 is a target, not a promise of Google approval or unrestricted launch.
Infrastructure selection, OAuth client setup/consent, provider account setup and
an approved test mailbox/recipient are external prerequisites for live evidence.
Code and mocked tests can be prepared without pretending those prerequisites exist.

### Task 1: Domain records, persistence and action policy

Files: create convene/domain.py, repository.py, policy.py, migrations/001_core.sql;
modify requirements.txt/.env.example; test tests/test_domain.py, test_policy.py, test_repository.py.
Interfaces: EventBriefVersion; ProviderOption; EvidenceFact; Approval; Inquiry;
BookingRecord; Job; Repository scoped to principal/event; authorize_action(actor,event,action,payload).

- [ ] Write failing tests: assert invalid transitions fail; payment pending differs from unknown; changed brief invalidates old approval; cross-parent read/update fails.
- [ ] Implement versioned records, PostgreSQL schema, owner checks and explicit scoped tool grants. Keep local SQLite prototype separate, not a silent production fallback.
- [ ] Implement approval payload hashing covering recipients, content, attachments and brief version. Add server-side expiry/revocation and audit events. Define revocable factual-reply, follow-up and reconfirmation capabilities separately.
- [ ] Run tests against an isolated test database; report missing PostgreSQL as an integration gap, not a pass. Update dependency locks using project environment tooling.

### Task 2: One-question intake and confirmation gate

Files: create convene/intake.py, routes/intake.py; tests/test_intake.py.
Interfaces: advance_intake(session,message)->assistant_turn plus proposed brief patch;
confirm_brief(session,expected_version)->confirmed version; no research dispatch before confirmation.

- [ ] Test greetings; birthdays and other family celebrations; one question per turn; unsure/tentative answers; children plus family counts; service subset vs all; priorities before budget compromises.
- [ ] Test event-type-dependent questions and refusal to invent missing details. Date/time, food needs and tentative assumptions must be explicit.
- [ ] Implement structured model extraction with server validation and durable session state. Keep anonymous sessions short-lived and ownership-bound; meter anonymous model usage.
- [ ] Test that research tools are not called during intake or before confirmed brief/account save. Run complete relevant suite.

### Task 2B: Durable six-domain agent integration

Files: create convene/planner_graph.py, checkpoints.py, routes/planner.py;
tests/test_planner_graph.py, test_planner_resume.py.
Interfaces: start_planner(actor,event,brief_version)->run_id;
resume_planner(actor,event,run_id,resume_input,expected_version); authorized
PostgreSQL checkpointer; audited tool gateway backed by authorize_action.

- [ ] Write failing tests for all six domains, adaptive branching, persisted
  one-question intake and approval pauses. Research cannot precede confirmed
  brief plus account save.
- [ ] Bind run/thread IDs to owner/event/brief version. Test cross-parent and
  cross-event checkpoint reads/resumes fail, including fabricated run IDs.
- [ ] Implement PostgreSQL checkpointer and node/subworkflow integration for
  Requirements, Budget, Vendor, Schedule, Creative and Review. Wire later tasks
  through explicit tool interfaces rather than bypassing the graph/policy.
- [ ] Test restart/resume across research -> approved inquiry -> provider reply.
  Replay must use recorded outbox results, not repeat sends or model-paid work
  unnecessarily. Stale brief and revoked grants block old resumes.
- [ ] Run graph integration tests with PostgreSQL and report missing live service
  coverage separately from mocks. Task 3 supplies authenticated principal
  resolution; subsequent tasks extend these graph interfaces incrementally.

### Task 3: Google sign-in, account isolation and Gmail authorization

Files: create convene/auth.py, gmail_oauth.py, routes/auth.py; tests/test_auth.py, test_gmail_oauth.py.
Interfaces: current_principal(request); claim_anonymous_event(session,principal);
connect_gmail(principal)->consent flow; stored encrypted per-user refresh token reference.

- [ ] Test state/nonce, issuer/audience/expiry validation, session fixation/CSRF, anonymous-event single-use claim and another user's event denial.
- [ ] Implement Google OIDC and secure sessions, then separate incremental Gmail authorization with offline access. Drafts initially remain in app; send/read scopes only as needed.
- [ ] Test revoked/expired grants stop jobs and ask for reconnect. Tokens never appear in API responses or logs. Test cookie/session security and logout.
- [ ] Document required callback URLs, consent/test-user configuration and public verification dependencies. No live account changes or email sends merely to satisfy mocked tests.

### Task 4: Sourced research, market estimates and RAG

Files: extend convene/venue_research.py; create provider_research.py, market_estimates.py,
evidence_retrieval.py; tests/test_provider_research.py, test_market_estimates.py, test_evidence_retrieval.py.
Interfaces: research_scope(confirmed_brief)->options/evidence/gaps;
estimate_costs(brief,options)->ranges/assumptions/exclusions; retrieve_evidence(actor,event,query).

- [ ] Test venue/decorator/restaurant-tray schemas, servings/units, pickup/delivery, source dates, fewer than five suitable results and partial failures.
- [ ] Implement Keenable and bounded public retrieval/extraction with shared evidence normalization. Existing SSRF/robots safeguards remain.
- [ ] Test incomplete prices never count as zero/full totals. Compare compatible units; no fabricated past-event spending. If evidence insufficient, return needs_quotes.
- [ ] Implement account/event-scoped PostgreSQL retrieval and private document facts; test hostile source instructions and cross-event retrieval rejection.
- [ ] Test confirmed quotes supersede applicable snapshots but stale quotes remain historical when date/headcount/scope changes.

### Task 5: Public frontend, dashboard and uploads

Files: create frontend/ with Vite/React/TypeScript components for intake, brief, options,
chat/plan workspace, provider status, uploads and approvals; backend routes/events.py,
routes/files.py; tests for API ownership and browser interactions.
Interfaces: authenticated event CRUD; signed private uploads/downloads; streamed agent events;
source-linked options and approval-bound inquiry preview.

- [ ] Test anonymous greeting -> single-question conversation -> correction -> confirmed brief -> sign-in -> workspace. Preserve conversation across a safe account claim.
- [ ] Build chat beside mix/match cards and budget, multiple-event dashboard, source evidence and attention items. No synthetic fixtures presented as real providers.
- [ ] Test uploads stay private; per-message attachment approval; invalid types/oversize files; another account's signed-file requests fail.
- [ ] Gate/disable existing unauthenticated /plans and paid-tool routes in public mode. Keep documented local-demo mode explicit.
- [ ] Browser-test desktop/mobile, keyboard operation, streaming errors, stale results and disconnect/reconnect. If browser policy blocks verification, report the exact limit.

### Task 6: Approved Gmail sending and durable outbox

Files: create convene/inquiries.py, gmail_client.py, outbox.py; routes/inquiries.py;
tests/test_inquiries.py, test_outbox.py, test_gmail_client.py.
Interfaces: prepare_inquiry(event,provider)->draft; approve_inquiry(payload_hash,version);
send_approved_inquiry(action_id)->send result or reconciliation-needed.

- [ ] Test shortlist prepares appropriate venue/decorator/restaurant draft but never sends; changed recipient/body/attachments/brief invalidates approval.
- [ ] Implement verified contact/source addressing, scoped Gmail send and stored RFC Message-ID/thread mapping, encrypted credential use and audit.
- [ ] Test visible factual-reply/follow-up/reconfirmation grants and per-inquiry/provider/version binding. Test job replay, concurrent claims, uncertain HTTP send outcomes, reconciliation before retry and revoked permission. No claimed exactly-once Gmail guarantee.
- [ ] Run a real send only to an explicitly approved test recipient with reviewed content. Verify actual Sent message/thread and report exact result.

### Task 7: Reply ingestion, factual responses and confirmation evidence

Files: create convene/mail_ingest.py, confirmation.py; routes/webhooks.py;
tests/test_mail_ingest.py, test_confirmation.py.
Interfaces: ingest_mailbox_change(mailbox,history_id); extract_reply_evidence(thread,event);
evaluate_confirmation(event,provider,evidence); prepare_safe_response(question,confirmed_brief).

- [ ] Test Pub/Sub auth, duplicate history events, unrelated mail exclusion, allowed thread mapping, provider provenance and attachment ownership.
- [ ] Implement watch/history sync, daily renewal and recovery of missed notifications. Auto-answer only known facts under an explicit active factual-reply grant bound to the current confirmed brief; test revoke/change while a reply is queued.
- [ ] Test acknowledgement/quote is not booked; required deposit unknown vs payment pending; secured reservation plus later balance due; wrong date/time/service and conflicting sender evidence remain unresolved.
- [ ] Test commitment, price acceptance, cancellation or changed plan pauses for parent approval. Brief changes reopen affected checks.
- [ ] Verify an actual approved test reply updates only the intended event, with supporting message evidence.

### Task 8: Durable follow-ups, readiness and notifications

Files: create convene/jobs.py, notifications.py, readiness.py; routes/internal_jobs.py;
tests/test_jobs.py, test_notifications.py, test_readiness.py.
Interfaces: dispatch_due_jobs(now); execute_job(job_id); notify_parent(event,issue,channels).

- [ ] Test first follow-up after24h, at most one/day, max3 per inquiry; no reset on restarts; stop on reply/cancel/revocation and recheck before send.
- [ ] Implement database job ledger/outbox, Cloud Tasks dispatch and authenticated worker endpoints; retries/backoff and terminal failures visible.
- [ ] Test one-calendar-month and one-week checks in event timezone; late-start warning without immediate extra check; cancelled/changed events invalidate stale jobs. Reconfirmation sends require a visible scoped grant and recorded existing reservation/order; otherwise draft only. Test once per checkpoint and no three-follow-up-limit bypass for unbooked inquiries.
- [ ] Add dashboard/transactional email and opt-in SMS notifications with delivery logs, deduplication and unsubscribe controls. Never imply delivery when provider rejected it.
- [ ] Test a real approved Gmail follow-up, read-back and notification only with configured accounts and consent; do not send unsolicited development mail/SMS.

### Task 9: Deployment, release gates and end-to-end proof

Files: Dockerfile, .dockerignore, infra/ deployment templates, CI, README.md,
docs/verification.md, operations runbooks and privacy/retention configuration.
Interfaces: Cloud Run API/worker plus PostgreSQL, storage, secrets, Pub/Sub,
Scheduler/Tasks, verified OAuth callbacks and notification senders.

- [ ] Inventory configuration without printing secrets. Choose intended Google Cloud project, domain, database and approved test account/recipient before applying resources.
- [ ] Prepare reviewable deployment configuration. Never copy local secrets into image/build context; server-side per-user tokens only.
- [ ] Run migrations, backup/restore checks, ownership/access tests, webhook auth, rate limits and action audit checks in staging.
- [ ] Prove end-to-end user journey with approved Gmail exchange. Capture actual status, not mock-only success, for each external service.
- [ ] Public release requires Google/sender approval status and privacy readiness; do not confuse public website accessibility with unrestricted Gmail readiness.
- [ ] Run full Python/frontend suites and independent final review. Document known gaps; no commit/push until intended remote verified.

## Setup inputs required before live deployment

Google Cloud project and billing authorization; owned public domain/HTTPS callback;
Google OAuth application ownership and consent configuration; PostgreSQL/storage;
OpenAI/Keenable server credentials as applicable; approved test Gmail users and a
safe provider-test recipient; transactional email sender; opt-in SMS number and
sender registration. Never request passwords or paste secrets into chat.

## Current-state ruling

Existing prototype remains unchanged by this planning step. Architecture approval
is not a claim that Google OAuth, Gmail, cloud hosting or SMS are configured. Use
existing known source/research utilities, not a rewrite of all working modules.
