---
campaign_id: GLOBAL
campaign_name: Canary partner receipt troubleshooting protocol
campaign_type: Shared campaign operations
client_name: Synthetic course library
description: 'Fictional CL-640 evidence: canary partner receipt troubleshooting protocol;
  scope and source precedence are explicit.'
document_id: GLOBAL-requirements-06
document_shape: troubleshooting
document_type: learning_guide
effective_date: '2026-10-01'
evidence_pack: requirements-v1
period: ALL
region: ALL
source_status: active
source_version: '1'
year: 2026
---

# Canary partner receipt troubleshooting protocol

SYNTHETIC COURSE DATA: original fictional teaching scenario; no real institutions or customer records.

## Status model
This fictional protocol distinguishes transport attempts from business acceptance for CL-640 batches. A single business batch can have several transport attempts while still representing one intended delivery. The durable identity is the business batch identifier paired with its approved payload checksum. A new transport request identifier does not create a new authorized audience delivery, and a successful connection does not by itself establish acceptance.

## Unknown receipt status
For RP-664, recover the original business batch status after a receipt timeout; do not resend an already accepted batch.
The operator queries the partner status endpoint using the original batch identity and records the response time. If status remains unknown, keep the batch unresolved and escalate through the named delivery owner. The operator must not infer rejection from silence or infer acceptance from a local upload log. Those observations describe different boundaries of the workflow.

## Decision table
| Observed state | Permitted action | Evidence retained |
|---|---|---|
| Accepted, receipt delayed | Recover receipt; no fresh delivery | Acceptance status and batch checksum |
| Explicitly rejected | Correct the stated defect and obtain required review | Rejection reason and replacement identity |
| Unknown after timeout | Query original status; escalate unresolved state | Attempt identifiers and query results |
| Conflicting checksums | Hold and reconcile with custodian | Both payload identities |
The table is a troubleshooting rule, not a record that any real partner experienced these incidents. Apply the relevant row to each batch separately. A new file missing a checksum and a previously accepted batch with a delayed receipt require different actions even if they appear in the same shift note.

## Exception and retry
An Exception is raised when the status response identifies a checksum different from the approved payload. The delivery owner and source custodian reconcile the mismatch before any further transmission. An operator may retry a status query without creating a new delivery, but a payload retransmission is a separate action governed by acceptance state and approval. Keep the retry counter separate from distinct business deliveries so an unstable network does not inflate campaign counts.

## Closing evidence
Close the incident only when the business outcome is known and the handoff identifies any remaining restriction. Preserve the original attempt, status queries, final receipt, and operator decision. A later shift should understand why no resend occurred even when the transport log contains a timeout. The access policy governs any masked sample used during troubleshooting. The release policy governs approvals; this document cannot grant a waiver for an unsigned or changed payload.
