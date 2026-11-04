---
campaign_id: GLOBAL
campaign_name: Shared audience suppression policy
campaign_type: Shared campaign operations
client_name: Synthetic course library
description: Original fictional cohesive policy about shared audience suppression
  policy; authored for chunk-boundary and evidence retrieval exercises.
document_id: GLOBAL-learning-06
document_shape: cohesive_policy
document_type: learning_guide
period: ALL
region: ALL
year: 2026
---

# Shared audience suppression policy

SYNTHETIC COURSE DATA: original fictional teaching scenario; no real institutions or customer records.

## Suppression custody

A shared audience service may support several campaigns, each with a different purpose and delivery schedule. This fictional policy separates the identity of an audience record from permission to use that record for a particular purpose. A campaign's previous selection does not establish permanent permission for future selections. The service maintains purpose-specific eligibility and suppression states with effective times and evidence references. A record can be permitted for a service notice while being suppressed for a promotional offer. Collapsing these states into a single global yes-or-no field would either permit unwanted delivery or incorrectly block necessary operational communication.

A withdrawal enters the service through an approved intake route and receives a stable request identifier. The intake operator records the purpose, received time, requested effective time when applicable, and the evidence needed to connect the request to the correct record. Ambiguous identity matches enter a restricted review queue. Do not choose the first similar name from a search result. At the same time, the operator should not require unnecessary personal data when an existing authenticated route already establishes the record. A request's progress is visible through its identifier so service staff can answer status questions without copying private details into unrelated messages.

The suppression service must acknowledge emergency withdrawal SP-809 within four business hours and block queued reuse until reconciliation.

Acknowledgment confirms receipt and the current handling state; it is not a claim that every partner has already removed every queued item. The operations owner identifies active selections, queued files, and scheduled refreshes that could reuse the record. Each downstream system receives an instruction with the suppression identifier and the relevant purpose. The owner records receipts and investigates missing acknowledgments. If a partner cannot remove an individual row safely, the affected batch is paused while a replacement is prepared. An emergency state remains open until the handling of existing queues is known, even if new selections are already blocked.

Recurring refreshes must apply the current suppression state rather than restoring an older audience snapshot. The service tests this by selecting a synthetic record, suppressing it, and running the next refresh from the same upstream source. If the record returns to a deliverable state without new authority, the refresh process has failed. Store the result with the refresh version and schedule. A nightly job that reports a successful execution can still have applied stale suppression data, so the test inspects its actual selected output. Separate execution health from permission correctness in the operational monitor.

Shared suppression requires a clear boundary between a purpose-specific withdrawal and a request affecting every promotional purpose. The intake route records what the person requested, and the review process resolves unclear scope using the approved clarification route. Staff must not narrow a broad request to whichever campaign happens to be open on their screen. Conversely, a narrowly described preference should not automatically become an invented statement about unrelated services. The service preserves both the original request and the interpreted scope, including who approved that interpretation. Later disputes can then be reviewed against the evidence rather than memory.

Reinstatement is a separate authorized event with its own evidence and effective time. Deleting a suppression row is not a valid reinstatement because it removes the history needed to understand earlier handling. A legitimate reinstatement may apply to one purpose while leaving another suppressed. The service creates a new state transition and verifies its downstream interpretation using synthetic records before release. If the same request is received twice, idempotent handling produces one effective transition with multiple receipt references. Duplicate messages should not create alternating suppression and reinstatement states or reset the recorded time of the original request.

Periodic reconciliation compares the current service state with partner acknowledgments and a sample of actual queued outputs. The reviewer records unresolved gaps and assigns an owner to each partner whose handling cannot be verified. Aggregate counts can reveal drift but do not alone establish that the same records were handled correctly; a matching total can conceal different omissions. Use privacy-preserving identifiers where possible to compare membership. This policy is a teaching scenario, not a legal service-level agreement. Its four-business-hour acknowledgment target belongs only to the fictional SP-809 workflow and should not be generalized to real institutions without their own approved requirements.

In the synthetic reconciliation exercise, a person withdraws promotional permission after an audience file is selected but before the partner releases it. New selections immediately exclude the record, yet the already selected file still contains it. The operations owner places that batch on hold and sends a replacement request with the suppression identifier. The partner returns an acknowledgment that the queued predecessor has been removed. The owner compares the replacement checksum and accepted count with the approved selection before releasing the hold. Updating only the master audience table would not have resolved the queue already outside the service.

A later nightly refresh reads an upstream export created before the withdrawal. The synthetic health record must remain suppressed even though the upstream file describes the earlier state. The state transition ledger establishes which evidence is current. If the refresh overwrites it with the old value, the monitor flags a permission regression rather than reporting a routine audience increase. The analyst records the refresh version and the conflicting effective times so the source of the regression can be reproduced. Merely rerunning the job with a newer input would hide the defect without demonstrating that the control was repaired.

The reviewer also submits the same withdrawal twice through different intake routes. Both receipts point to one effective transition. The service should not restart the emergency acknowledgment clock, create two independent reinstatement opportunities, or lose the original evidence. This small exercise connects idempotency with suppression custody: transport duplication must not change the meaning of a person's request. The final ledger shows the original receipt, the second receipt, and a single resolved state with its downstream acknowledgments.
