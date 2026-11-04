---
campaign_id: GLOBAL
campaign_name: Delivery receipt troubleshooting FAQ
campaign_type: Shared campaign operations
client_name: Synthetic course library
description: Original fictional troubleshooting about delivery receipt troubleshooting
  faq; authored for chunk-boundary and evidence retrieval exercises.
document_id: GLOBAL-learning-10
document_shape: troubleshooting
document_type: learning_guide
period: ALL
region: ALL
year: 2026
---

# Delivery receipt troubleshooting FAQ

SYNTHETIC COURSE DATA: original fictional teaching scenario; no real institutions or customer records.

## Symptoms and first checks

This fictional FAQ concerns a transport timeout after an audience file has left the sender. A missing receipt does not establish that delivery failed. The remote service may have accepted the batch while the response was lost, or the sender may have stopped before the remote service accepted anything. Record the timeout, original idempotency key, approved payload checksum, and transport attempt identifier. Preserve the request log without exposing audience rows. The first check is the partner's status route for the original business key. Creating a fresh key simply to obtain a clean response can turn an uncertain state into an actual duplicate delivery.

## DR-905 recovery

For DR-905, query the partner using the original idempotency key before retrying; an accepted batch must not be resent.

The following decision table applies to the same original key. An analyst must not substitute a campaign name, because several legitimate batches can belong to one campaign. Save the partner response and time with the incident. A status returned for an unknown key is not evidence about a differently keyed earlier attempt. If the status service itself is unavailable, keep the batch in an uncertain state and contact the designated operations route. A delivery deadline cannot resolve that uncertainty.

| Partner state | Sender action | Required evidence |
|---|---|---|
| accepted | Do not resend | Receipt and matching checksum |
| rejected | Repair before retry | Rejection code and payload revision |
| not found | Retry with original key | Status response and original request |
| unknown | Hold and investigate | Incident owner and next check |

## Exception for a changed payload

Exception DR-906 applies when a rejected batch must be repaired. The replacement payload receives a new revision and checksum, with a reference to the rejected predecessor. Follow the partner's documented revision route instead of reusing the original key with different bytes. Reusing a key for changed content can cause a partner to return the old response without accepting the repair. A new transport attempt for unchanged content is different from a new business revision. The ledger records both concepts so a later reviewer can reconstruct whether the same audience was retried or a corrected audience was released.

## Why do the counts disagree?

Compare the units before searching for missing rows. The sender may count selected contacts while the partner counts accepted households after suppression. A transport log may count attempts and a delivery ledger may count distinct batches. Document the expected transformation at each stage, including suppression and deduplication. A difference is explainable only when the transformation is supported by evidence. Do not add an arbitrary adjustment row to make totals reconcile. If the partner provides only a final count with no suppression explanation, record the gap and request an approved aggregate reconciliation rather than exchanging unrestricted customer files through the incident chat.

## What proves recovery?

Recovery requires a known final state for the original batch and every authorized replacement. The incident owner reconciles accepted payload checksums, delivery receipts, and superseded revisions. The system should demonstrate that retrying the same synthetic request does not create a second business delivery. It should also demonstrate that a repaired rejected request follows the revision route. These are different test cases. A green transport monitor shows that connections work; it does not prove idempotent business handling. Close the incident only when the evidence identifies what the partner accepted and which queued artifacts were removed or replaced.

## Preventing the next ambiguous timeout

Keep business keys stable through retries, record transport attempts separately, and store a durable outbox state before transmitting. The recovery worker should consult that state after a restart instead of treating every unsent receipt as an unsent payload. Monitoring distinguishes accepted-without-local-receipt from confirmed rejection and from unknown status. The on-call handoff states which category is open and when it will be checked again. This fictional FAQ defines a reproducible teaching workflow; it does not assert that every partner implements the same API or retention period. Confirm the actual partner contract before transferring this pattern to a real integration.

## Reproduction trace

The diagnostic harness begins with an approved synthetic payload and a durable original business key. It simulates remote acceptance, then drops the response before the sender stores a receipt. After restart, the sender must query that key and discover the accepted state. The expected ledger contains one accepted batch, the original attempt, the status query, and the recovered receipt. If restart instead creates a fresh business key, the harness records a duplicate-delivery failure even if both HTTP requests received successful responses. This is a business correctness check, not a test of network connectivity alone.

A second trace simulates a rejection caused by a malformed campaign association. The preparer fixes the association in an approved payload revision. The revised checksum differs from the original, so the system follows DR-906 and links the replacement to its rejected predecessor. A retry route that silently reuses the original key with changed bytes fails the trace. The harness also tests a missing partner status response: the correct state is unknown with an assigned incident owner. Treating unknown as rejected would authorize an unsafe resend; treating it as accepted would conceal an undelivered batch.

During review, compare the stored evidence with the decision table row that authorized the action. An operator should be able to explain why a retry was allowed without reconstructing the sequence from informal messages. The trace preserves status timestamps, checksums, keys, and revision links using invented data. It does not require copying audience content into the logs. The FAQ's lexical identifiers help find the specific recovery rule, while the surrounding explanation establishes why a plausible quick retry can produce a duplicate. Both are useful evidence for a grounded answer.
