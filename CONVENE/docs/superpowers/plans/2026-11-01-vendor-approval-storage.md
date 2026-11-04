# Vendor approval storage

Approved scope: move the existing directory into PostgreSQL with versioned facts,
source evidence and human approval history, per approved-vendor-design.md and
the user's confirmation. Execute inline; existing protected Git constraints apply.

1. Write failing real-PostgreSQL tests for import persistence/idempotency, draft
   visibility, approval/version binding, stale approval conflict, suspension and
   inability of an ordinary browser principal to write directory records.
2. Add migrations/007_vendor_directory.sql: records, immutable versions and
   immutable approval decisions. Published records reference an approved exact
   version; RLS makes drafts/audit history administrative and published data readable.
3. Implement convene/vendor_directory.py with read-only DirectoryRepository and
   internal DirectoryAdmin operations for import/propose/approve/suspend/history.
   Administrative capability is set only by a local CLI, never a client body or route.
4. Bootstrap only the five previously approved website vendors using an explicit
   scripts/vendor_directory.py import-existing command. Record project-owner
   conversation approval as provenance, not a fabricated Google account identity.
   Re-import must not overwrite or automatically approve later changes.
5. Wire /api/vendors to PostgreSQL. Retain party_catalog.py solely as legacy/demo
   data and one-time import input; remove its generated approval function.
6. Add CLI review/approve/suspend operations, documentation, and UI approval/version
   details. There is no public admin interface until authenticated admin roles exist.
7. Verify full Pytest, frontend build, actual database-backed HTTP directory and
   independent code review. Never expose connection strings or modify parent Git.
