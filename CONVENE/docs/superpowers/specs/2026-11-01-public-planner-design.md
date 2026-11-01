# CONVENE public family planning app - approved architecture and requirements

Date: November 1, 2026. Status: architecture approved in conversation; implementation planning.
Target: November 2 end-to-end demo, November 5 course deadline. Public launch is
conditional on hosting, Google authorization/verification and operational readiness.
Do not promise unrestricted Gmail access by a calendar date.

## Product and user agreement

Parents plan family celebrations in San Antonio, Texas, including birthdays and
other occasions. The planner greets warmly, asks what they are celebrating and
asks one adaptive question per turn. Uncertain answers remain tentative; the
planner offers help instead of blocking. Do not hardcode the prior birthday as
the user's only event type, theme or date.

Collect occasion, relevant ages/interests, theme, city, date/time or flexibility,
children and accompanying family headcounts, total budget, priorities, and
requested help. Services are venues, professional decoration and restaurant
party trays. Parents choose one, several or the whole scope. Food intake must
identify relevant dietary needs and pickup/delivery preferences before reliable
food comparisons. Never assume a child equals a fractional adult serving without
an explicit explained assumption.

Show a versioned brief separating confirmed, tentative and missing fields; allow
corrections. Require parent confirmation before research. Anonymous chat comes
first; Google sign-in saves the confirmed event before personalized research.
Connect Gmail separately when outreach is needed. Multiple saved celebrations
are private to the account. Keep chat beside options and budget after intake.

Research up to five suitable options per selected category, not five filler
results. Provide official sources, dates, inclusions/exclusions, published
capacity/servings, prices and unknowns. Parents mix and match. Check outside-food
rules, decorator access, venue capacity/layout, restaurant service area, serving
quantities and delivery timing. Unknown rules remain visible as Needs confirmation.

Build spending ranges from comparable published local rates, not invented past
event budgets. State assumptions, sample coverage and missing fees. If a reliable
range cannot be supported, say so. When budget conflicts with headcount or scope,
explain the conflict and ask which priorities to protect before changing the plan.
Do not silently reduce attendance or increase the budget.

Uploads: inspiration photos and provider documents. Keep private unless parent
approves specific attachments to a specific provider email. Explain AI processing;
no cross-parent retrieval or model training using private records.

## Outreach and automation

Shortlisting prepares a venue/decorator/restaurant inquiry automatically. Parent
reviews exact recipients, subject, body and attachments before first send from
their connected Gmail. Registering an email or Google sign-in alone is not Gmail
send/read authorization. No password collection. Sending an actual test inquiry
requires an explicit approved test recipient and content; product requirements
are not permission to send real outreach during development.

Track only event-linked Gmail conversations in application logic. Google scopes
are broader than individual threads; consent copy must not falsely imply a
thread-scoped Google permission. Proposed Gmail scopes: gmail.send and
gmail.readonly, with drafts kept in CONVENE initially. No mailbox deletion scope.

Read replies, extract evidence-backed quotes/rules/availability/questions, and
update the plan. Auto-answer factual questions only from the current confirmed
brief. Missing/ambiguous answers return to the parent. Never automatically accept
prices, contracts, deposits, cancellations or material plan changes. Changed
briefs after outreach generate revised drafts for parent approval.

Initial inquiry approval includes separately visible, revocable delegation for
one follow-up after 24 hours, then at most once daily, maximum three follow-ups
per inquiry. Stop on reply, cancellation or revoked authorization. Counters do
not reset because the model restarts or generates a new response. Recheck thread
state and approval before sending each reminder. Auto-acknowledgements never
count as booking evidence. Ambiguous correspondence remains unresolved.

Background work continues when the website is closed. Dashboard and email alerts
cover needs-attention items; opt-in SMS covers urgent provider-confirmation
issues. Provider cancellations/conflicts alert whenever detected. Store delivery,
opt-out and deduplication records.

## Booking certainty and readiness

Booking, payment, contract and readiness are independent records. Never infer
booked from a shortlist, inquiry, quote or generic acknowledgement. Auto-confirm
only when trusted provider-issued evidence establishes matching provider,
service, approved date/time/location and required securing conditions. No parent
review is required for unambiguous evidence; ambiguous/conflicting evidence
remains Needs confirmation. Validate sender/contact provenance, not just model
confidence or a visible From display name.

Show Payment pending when evidence says payment is outstanding. Show Payment
status needs confirmation when unclear. A provider-confirmed reservation with
required deposit satisfied can coexist with a later balance due. Display due
dates and provider payment links; parent pays directly. No booking, purchase,
contract-signing, deposit or payment execution in this scope.

Keep evidence, message/file IDs, brief version and evaluated conditions behind
each status. A later cancellation or material brief change reopens relevant
confirmation/compatibility checks; do not erase the historical record.

One calendar month before event: readiness check, flag unresolved essential
providers and help research alternatives. One week before: final reconfirmation
for venues, decorators and restaurant orders. Existing bookings are not replaced
or cancelled without approval. For plans created inside the one-month window,
warn about the shorter timeline; do not automatically manufacture an immediate
extra readiness check. Future checks still apply if their dates have not passed.

## Target stack and boundaries

Public React + TypeScript website, FastAPI backend, LangGraph with durable
PostgreSQL checkpoints, OpenAI Responses tools/structured extraction, Keenable
search, PostgreSQL/pgvector retrieval, private Cloud Storage uploads, Cloud Run
API/workers, Cloud Tasks + Cloud Scheduler jobs, Gmail API/OAuth + Pub/Sub,
transactional email and Twilio SMS, Secret Manager and encrypted token storage.
Use hosted public deployment, not localhost as the final multi-user product.
Retain the six graph domains Requirements, Budget, Vendor, Schedule, Creative,
Review, with event-dependent loops/subworkflows rather than one rigid pass.

An authenticated tool gateway enforces event ownership, action scope, required
approvals, limits and audit records. Model tool proposals do not grant permission.
Application arithmetic and state rules determine budgets/confirmation gates.
Untrusted email, websites and uploads cannot change system rules or permissions.
All private rows/files/checkpoints belong to user_id and event_id. Server checks
ownership on every endpoint and tool call, including SSE/NDJSON subscriptions.
Anonymous intake uses a short-lived opaque server session, not public event IDs.

Use durable job/outbox records, unique action IDs and transactional claims. Queue
redelivery is expected. For uncertain Gmail send outcomes, reconcile the outgoing
Message-ID/thread before retry; never promise exactly-once delivery or blindly
send again. Verify Gmail Pub/Sub caller identity, keep per-mailbox history cursors,
renew watches daily, reconcile missed notifications and handle revoked tokens.
Calendar checkpoints live in the database; enqueue work when due rather than
holding in-memory sleeps or browser timers for weeks.

No credentials or private evidence in frontend bundles, prompts, logs or Git.
Private uploads use authorized short-lived access. OAuth tokens encrypted at
rest; application secrets in Secret Manager. Restrict retrieved context to the
current parent's event. Revoke/disconnect stops related jobs and token use.
Tracing off by default; any future tracing requires explicit privacy design.

Public Gmail verification/security assessment and SMS sender registration/consent
are launch dependencies, not features a code change can grant. Public site and
invited OAuth test access may be released separately with clear actual status.

## Existing prototype and gap

Existing local code provides a source-backed venue fetcher, Keenable adapter,
photo-led static comparison page, deterministic synthetic /plans workflow,
six-node party research graph and tests. It does not yet provide public-account
authorization, general conversational intake, restaurant research, durable agent
checkpoints, Gmail OAuth/send/watch, background jobs, uploads or SMS. Current
unauthenticated legacy routes must be gated or disabled before public deployment;
retaining an endpoint does not authorize exposing private plans or paid tools.

## Success contract

End-to-end: anonymous greeting -> adaptive intake -> confirmed brief -> Google
account save -> scoped research and estimates -> mix/match -> draft -> Gmail
connect -> parent approves -> send to approved test provider -> reply ingested ->
evidence-backed budget/status update -> permitted factual response or parent
question -> follow-up/reconfirmation scheduler -> dashboard/email/SMS delivery
status. Test happy and failure paths, including duplicate jobs, revoked Gmail,
unavailable providers, misleading confirmations and cross-account requests.
No success claim for real Gmail, notification delivery or public launch without
actual integration evidence; mocked tests are identified as mocked.

## Builder-check decisions - authorization and graph ownership

A parent's initial inquiry review must explicitly display separate revocable
capabilities: factual replies from the confirmed brief; daily follow-ups capped
at three; and one reconfirmation request at each future month/week checkpoint
for an existing recorded reservation/order. These are the concrete delegation
mechanisms for the automatic behavior approved in conversation, not implicit
permissions hidden in a model prompt. Each grant binds user, event, inquiry,
provider, Gmail account, brief version and capability. Initial inquiry send still
requires exact payload approval. Commitments remain outside automatic grants.

Revocation/disconnect stops all related automation. A material brief change
invalidates queued actions bound to that version; revised inquiry and delegation
must be reviewed before sending updates. Factual auto-replies must recheck both
the grant and current confirmed facts at execution time.

Readiness checks can create dashboard findings without email permission. Sending
reconfirmation requires its explicit grant; otherwise prepare a draft for review.
Only recorded existing reservations/orders qualify for automated reconfirmation.
Unanswered, unbooked inquiries do not get an extra reminder by pretending it is a
reconfirmation, nor a reset of their three-reminder counter. Checkpoint requests
are once per provider/checkpoint/brief version and never execute overdue past
checks automatically for late-start plans.

The six graph domains use PostgreSQL checkpoints keyed by an opaque run/thread
ID, bound to owner, event and brief version. An approval pause and later worker
resume must reauthorize that binding. Process restart resumes existing state;
it must not re-send previously recorded side effects. Transactional outbox work
is separated from replayable model/node execution. No shared checkpoint context
across parents or events.
