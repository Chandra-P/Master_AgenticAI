# Security and privacy

## Threat model

Assets: financial facts, user constraints, uploaded documents, API keys, and audit history. Adversaries can supply questions and uploaded content; a compromised document may contain instructions. Trust boundaries are browser → Next.js gateway → FastAPI → owned database rows, and optional outbound provider APIs.

This release is a **local, single-household synthetic demo**, not a publicly deployable financial service. No endpoint moves money, trades securities, opens accounts, or applies for credit. Recommendations are educational and include limitations.

## Controls

- Browser UI and local API bind to loopback in documented commands; Compose publishes only loopback web access.
- The server selects demo user identity; client-supplied user IDs are never trusted. Transaction queries join account ownership. Retrieval and document lookup filter by owner.
- Optional service token protects the backend boundary and is injected only by the server-side Next.js gateway. This is not per-user login.
- Analytics uses parameterized approved SQL, not generated SQL. The model selects an enum route only.
- Pydantic validates input ranges; money is cents/Decimal. Confirmed memory edits require the current revision and append before/after audit records.
- Upload validation covers extension, size, PDF signature/page count, UTF-8 decoding, extracted-text length, sanitized basename, checksum, and explicit supersession. Contents are not written as executable files.
- React renders source content as escaped text. No raw document HTML or Markdown execution is enabled.
- Retrieved instructions are untrusted; imperative lines matching known patterns are quarantined. More fundamentally, document content has no route to tool authorization, memory updates, or planner instructions.
- Loan authority checks consult the entire current registry rather than only retrieved top-K chunks.
- Numeric validation binds allowed fields and units, with mutated-value and unrelated-count regression tests.
- Rate-limiting hook: 120 requests/minute per API peer, process-local. In a proxied local demo all visitors may share that bucket. No claim of distributed abuse protection is made.
- Next.js gateway limits request bytes; upload reads stop at limit+1. A production reverse proxy must enforce streaming/global limits for direct backend access.
- Response headers include no-sniff/no-store; frontend adds frame denial and same-origin referrer policy.

## Logging and provider privacy

Keys exist only in environment files or runtime variables. Never commit `.env`, databases with real data, or credentials. HTTP logs record method, path, status, and latency; not bodies or headers. Local tool/audit records contain financial facts and source excerpts, with basic API-key/email/long-number redaction. Redaction is not a comprehensive PII detector.

OpenAI mode sends the question to the configured API. Optional OpenAI embeddings send upload passages and retrieval queries to that provider. Users must choose this mode deliberately. LangSmith tracing is opt-in and omits questions, documents, account identifiers, and balances; only route, tool statuses, validation, mode, latency, and local run IDs are sent. Local traces remain available if remote publication fails.

## Known limitations

No production OIDC/session management, multi-user UI, role management, encryption-at-rest integration, distributed rate limiting, malware scanner, secure PDF sandbox/OCR, retention policy, or comprehensive CSRF/CSP deployment configuration. No PostgreSQL RLS. Do not deploy this demo publicly or upload real financial records on a shared host.

PDF parsing can consume resources; size/page/text caps do not prove immunity to all decompression attacks. Heuristic quarantine does not detect every instruction, but instructions cannot execute capabilities. Source contradictions and missing facts trigger conservative abstention rather than inferred terms.

## Production hardening

Add authenticated sessions and server-derived tenant IDs throughout; enforce account/document ownership on every audit/evaluation endpoint; use a transactional production database with migrations and isolation tests; secrets manager and TLS; durable job queues for uploads/evaluations; isolated parser workers and malware scanning; streaming size/timeout limits; content-security policy, CSRF protection, backups and deletion/retention controls; external semantic evaluations and live-provider security tests; legal/privacy review before processing real financial data.


## Payroll extension

Paystub previews force local embeddings, independent of generic document-provider settings; raw payroll files are not sent to OpenAI before review. Only explicitly confirmed structured records enter calculations. Current/YTD fields reconcile to net pay; duplicate confirmations are blocked by a partial unique index; corrections retain prior facts and require the same owned employment and pay date. Tax-profile updates use confirmation and revision checks. Unreviewed drafts never modify balances or tax projections. Local payroll records/audits contain sensitive information if real data is uploaded; the existing single-household/demo and retention limitations still apply. The UI asks users to remove SSNs/bank details, and extraction does not need these fields. No tax filing, W-4 submission, benefit change, or money movement is available.

## Optional model council

`COUNCIL_MODE=openai` explicitly permits sending compact financial facts and deterministic scenario fields to the configured OpenAI-compatible endpoint. Council inputs omit raw questions, uploaded passages, household names and document contents; numeric values remain sensitive. Reviews have no tools or write access. Strict Pydantic/schema validation rejects free-form instructions, unknown properties, inconsistent votes and unknown evidence references; only fixed enum labels reach the UI. Provider exceptions expose only exception categories, not messages. No majority can override deterministic checks. Provider/model collusion, shared training biases and incomplete compact context remain limitations. All council results persist in the existing user-scoped agent audit JSON/tool calls; remote LangSmith exports council status, not review payloads. Existing deployment access and rate-limit boundaries apply; there is no new end-user-controlled switch that can trigger arbitrary model IDs.
