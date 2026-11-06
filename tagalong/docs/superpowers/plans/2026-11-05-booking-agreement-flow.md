# Group agreement before reservations

> **For agentic workers:** Use superpowers:subagent-driven-development for backend, frontend, and independent review. Work in the integration checkout; coordinator synchronizes scoped source and publishes the existing deployment branch.

**Goal:** Members understand where they are in planning and cannot confirm a reservation before the group agrees.

**Architecture:** Preserve exploration and quotes. Derive a server-authoritative readiness checklist from current polls, members, dates, location and budget. The owner explicitly approves the current decision fingerprint. Confirmation rechecks this gate before and after MCP work. Cancellation and idempotent retries remain available. Frontend shows stages and links blockers to existing editing screens.

**Global constraints:** Fictional reservations only, explicit confirmation, existing authentication/membership rules, no new credentials/services. No poll is silently decided by AI. All current members must vote and a unique winner is required. A winning request for different dates is unresolved. Changes to decisions or membership invalidate approval; unrelated chat does not. Owner transfer invalidates approval. Existing reservations remain visible and cancellable.

## Tasks
- [x] Backend: write failing gate tests; implement readiness and owner approval; recheck confirmation atomically; preserve idempotency/cancellation; update demo documentation.
- [x] Frontend: display Explore → Group agreement → Owner review → Reservation; blocker links; owner action; disable confirmation until server ready; test blocked/ready states.
- [x] Shared browser journey: start blocked, complete each member vote and working details, owner review, confirm, duplicate retry, shared visibility, cancel.
- [x] Independent review of decision fingerprint, auth, stale responses and user guidance.
- [x] Required backend/frontend/build/shared checks, desktop/mobile visual review, and secret scan: 154 backend passed (1 gated skip), 66 frontend passed, 18 shared passed; lint/typecheck/build passed.
- [ ] Commit/push and verify public deployment.

## Verification
Run backend pytest, npm run lint, npm run typecheck, npm run build, npm test, npm run test:shared. Inspect desktop/mobile captures. Publish only after successful checks; report public rollout separately from source completion.
