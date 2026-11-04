---
campaign_id: GLOBAL
campaign_name: Consent recovery launch playbook
campaign_type: Shared campaign operations
client_name: Synthetic course library
description: Original fictional playbook about consent recovery launch playbook; authored
  for chunk-boundary and evidence retrieval exercises.
document_id: GLOBAL-learning-01
document_shape: playbook
document_type: learning_guide
period: ALL
region: ALL
year: 2026
---

# Consent recovery launch playbook

SYNTHETIC COURSE DATA: original fictional teaching scenario; no real institutions or customer records.

## Intake and isolation

A consent recovery launch begins when a delivery partner returns a file whose permission status cannot be reproduced from the campaign register. Stop distribution of that file and copy its checksum, receipt time, row count, and partner batch identifier into the incident ledger. Preserve the received artifact as read only. Create a separate investigation copy so later corrections cannot overwrite the evidence that triggered the stop. Notify the delivery coordinator which batch is paused; a vague instruction to stop all activity would also interrupt unrelated campaigns whose permissions remain valid. This scenario concerns fictional customer permissions, not a statement of applicable law.

## Reconciliation route

Compare the campaign register with the received file using the internal permission key, not a person's displayed name. A renamed household can otherwise appear to be a new prospect. Classify each discrepancy as missing permission, expired permission, mismatched purpose, duplicate delivery, or unreadable evidence. The categories lead to different repairs: a duplicate can be suppressed, while missing permission requires a new authorized record. Keep both the original status and the resolved status. An analyst reviewing the incident later should be able to determine why a row moved, who moved it, and which supporting record justified that movement.

## Recovery gate

Resume only after two independent reviewers reconcile every quarantined row and sign gate CR-217.

Independence means the second reviewer did not prepare the repair file. A manager's availability does not substitute for this separation. Both reviewers compare row counts before and after suppression, inspect a sample of repaired purpose codes, and confirm the partner received the replacement checksum. The signoff records the precise replacement batch, not merely the campaign name. If the delivery partner cannot attest that the old file was removed from its outbound queue, the recovery gate remains closed even when the replacement file is correct. A commercial deadline does not waive that condition.

## Release rehearsal

Before resuming distribution, send a dry run to the internal test route. The route contains invented records with known suppression outcomes: one eligible row, one withdrawn permission, one duplicate, and one conflicting purpose. Confirm that the eligible row alone reaches delivery. A successful file upload is not a successful suppression test. Save the delivery receipt and the suppression summary together so the analyst can connect inputs with outcomes. When a partner's test environment differs from production, record that difference and schedule a limited production verification with internal seed records before the full replacement batch leaves the queue.

## Handoff and follow-up

Give the operations shift a short handoff containing the incident identifier, affected batches, remaining restrictions, owner, and next verification time. Do not paste contact details into the handoff; refer to the restricted ledger. The next shift checks that a delayed receipt did not accidentally reactivate the superseded batch. At the next business review, compare the partner's delivered counts with the approved release counts and investigate any difference. Delivery counts can confirm handling consistency but cannot prove that every individual message was read, understood, or acted upon. Avoid turning an operational reconciliation into an unsupported engagement claim.

## Learning record

Close the incident with a causal narrative supported by timestamps. Distinguish the initial detection, the actual file defect, and the control that failed to detect it earlier. A malformed permission code may have been introduced during export rather than during collection; these require different corrective actions. The learning record assigns one owner to the export validation rule and another to partner receipt verification. Store a small synthetic reproduction with the rule change. Do not retain a second unrestricted copy of the customer file as a convenient training example. A future rehearsal should reproduce the failure using invented rows and demonstrate that gate CR-217 stays closed until the evidence is complete.

## Worked recovery exercise

In the rehearsal incident, a partner reports twelve rejected rows from a replacement batch. Eight have an expired purpose code, three are duplicate routes for otherwise permitted households, and one points to an evidence record that cannot be opened. The preparer initially proposes suppressing all twelve and releasing the rest. The independent reviewer asks whether the same export defect could have affected rows that the partner did not reject. This is a useful distinction: a partner rejection is a symptom, not a complete inventory of the export defect. The team examines the export rule and reconciles the entire quarantined population before describing the repair as complete.

The duplicates can be resolved against stable household keys, while the expired codes require the source owner to establish current authority. The inaccessible evidence record remains unresolved. The team produces a replacement selection that excludes unresolved rows and records the reason for each exclusion. It then reconciles the approved selection with the partner's accepted payload, rather than treating a successful upload as release evidence. The reviewer records why no new permission was inferred from the household match. These decisions become part of the CR-217 record and can be inspected without reading the original customer file.

A training observer asks why two signatures are needed when the automated checks pass. The exercise demonstrates a specific failure mode: the preparer had assumed that the partner's rejection list covered every affected row. An independent review challenged that assumption by checking the rule itself. Automation can validate specified conditions but may not identify a missing condition. The learning objective is therefore to connect signatures to actual review evidence. A form containing two names without the reconciliation and replacement checksum would satisfy the appearance of a control while leaving the original uncertainty unresolved.

As a final challenge, the facilitator inserts a superseded batch receipt into the evidence bundle. The reviewer must reject it because its checksum does not identify the approved replacement. Recognizing the campaign name is insufficient. This tests whether the recovery decision follows the specific artifact that was reconciled, rather than accepting any successful receipt from the same campaign as proof that the quarantined file was safely replaced.
