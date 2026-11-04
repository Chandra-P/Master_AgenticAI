---
campaign_id: GLOBAL
campaign_name: Attribution correction retention policy
campaign_type: Shared campaign operations
client_name: Synthetic course library
description: Original fictional cohesive policy about attribution correction retention
  policy; authored for chunk-boundary and evidence retrieval exercises.
document_id: GLOBAL-learning-04
document_shape: cohesive_policy
document_type: learning_guide
period: ALL
region: ALL
year: 2026
---

# Attribution correction retention policy

SYNTHETIC COURSE DATA: original fictional teaching scenario; no real institutions or customer records.

## Correction custody

This fictional policy governs the custody of attribution corrections for campaign learning records. A source event is an observation with a stable identifier, event time, collection route, and recorded campaign association. A signed snapshot is the set of observations accepted at a stated cutoff, accompanied by the rules used to include them. Neither an event's arrival time nor the analyst's review time replaces its occurrence time. The custodian stores these times separately because delayed delivery and an actually late conversion have different implications. A late-arriving observation can still fall within a previously defined attribution window; an observation occurring outside that window cannot be pulled inside merely because its file arrived with eligible events.

When a team discovers a correction, the requester identifies the original event, proposed replacement value, reason, and supporting evidence. The request is attached to a revision ledger with an owner and a review state. A correction may concern a duplicate, an incorrect anchor date, an invalid campaign association, or an incorrectly applied rule. These are recorded as distinct reasons because a duplicate removal does not imply that a channel's entire measurement window was wrong. If the request lacks enough evidence to establish which event changed, it remains unresolved and the published learning record notes the uncertainty. An urgent presentation deadline does not convert an unverified request into an accepted correction.

A late correction receives a new revision linked to the original snapshot; it never overwrites the signed snapshot under policy AC-318.

The revised artifact includes a machine-readable parent snapshot identifier and a human-readable change note. The note explains which counts changed and why, without exposing customer details. An analyst comparing revisions should be able to reproduce both the original and revised values using the corresponding source events and rule versions. A file with the same name and a different modification time is insufficient lineage. Each revision has a new checksum and a declared cutoff, even if only one event changed. Where a revision affects several campaigns, list them explicitly rather than implying that every campaign in the same period changed.

Reviewers distinguish a data correction from a methodology change. Correcting a mistyped anchor date applies an existing rule to better evidence. Replacing a thirty-day window with a different window changes the rule and therefore the meaning of the count. A methodology change needs a separate comparison note and cannot be presented as a routine data cleanup. If both occur together, calculate their effects separately when the data permits. If their effects cannot be separated, state that limitation. A single combined difference should not be attributed entirely to delivery performance when part of it comes from a changed definition.

Downstream consumers receive a revision notice identifying superseded artifacts and the scope of the change. A cached chart, extracted table, or presentation image may continue to show the old values after the source file is corrected. The owner checks the consumers listed in the dependency register and marks each as updated, intentionally frozen, or awaiting action. Intentionally frozen materials retain their original cutoff and carry a notice that a later revision exists. Do not change historical exports in place without preserving their identity; doing so would make a past decision appear to have used evidence that did not yet exist at the time.

Access to the raw correction evidence follows the same restrictions as access to the original source events. The revision note may be broadly readable while supporting records remain restricted. The custodian removes unnecessary personal fields from the analyst's working copy and refers to stable internal identifiers. An access request for aggregate learning does not automatically justify access to individual records. Reviewers can often validate a checksum, event count, or rule application using an approved aggregate extract. When individual evidence is essential, the request explains the specific uncertainty that cannot be resolved from aggregate material.

Closure requires the requester and an independent reviewer to agree that the accepted change matches its evidence and that affected consumers have been notified. The ledger preserves rejected requests as decisions with reasons, because repeated rejected requests can reveal a confusing definition. Retention follows the fictional library schedule attached to the snapshot; this document does not prescribe a real legal retention period. If a deletion request conflicts with a pending investigation, the designated records owner resolves it and documents the basis. The analyst must not improvise a retention deadline from this teaching example or infer that keeping every working copy forever improves traceability.

A worked custody example begins with a signed snapshot containing an event assigned to the wrong campaign. The source owner supplies the event's original delivery reference and a corrected association. The requester opens a revision against the signed snapshot, records the old and proposed campaign identifiers, and attaches the evidence reference. One campaign loses an accepted event and another gains one, so a library-wide total might remain unchanged. A total-only check would miss the correction. The reviewer verifies the membership change and its effect on both campaign records before approving the revision.

The downstream register lists a saved answer, a chart extract, and an exported presentation. The answer and chart can be recomputed under the new revision. The presentation is a frozen record of an earlier decision, so its owner retains the original file and adds a notice linking to the later correction. This preserves what the decision makers actually saw. The notice does not imply misconduct or poor analysis; it simply identifies that new evidence became available. If the original event cannot be reconstructed from the retained source, the record states that reproducibility limitation rather than claiming full auditability from a checksum alone.

In a second request, a manager asks to apply a longer window because the corrected result appears disappointing. That request is routed as a methodology proposal and does not enter the data-correction queue. Its business rationale may be discussed, but it cannot alter the meaning of the signed measurement retroactively without disclosure. The policy's custody controls preserve both the evidence and the distinction between repairing a source fact and changing the question being measured.
