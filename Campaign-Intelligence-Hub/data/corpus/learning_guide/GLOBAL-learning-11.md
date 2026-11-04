---
campaign_id: GLOBAL
campaign_name: Enrollment feed troubleshooting FAQ
campaign_type: Shared campaign operations
client_name: Synthetic course library
description: Original fictional troubleshooting about enrollment feed troubleshooting
  faq; authored for chunk-boundary and evidence retrieval exercises.
document_id: GLOBAL-learning-11
document_shape: troubleshooting
document_type: learning_guide
period: ALL
region: ALL
year: 2026
---

# Enrollment feed troubleshooting FAQ

SYNTHETIC COURSE DATA: original fictional teaching scenario; no real institutions or customer records.

## Which clock is authoritative?

The fictional enrollment feed records occurrence time and arrival time separately. Occurrence time determines whether an event falls within an attribution window; arrival time describes when the pipeline learned about it. A delayed file can therefore contain eligible events from an earlier day. Before applying the rule, confirm the timestamp offset and the documented anchor. A mail drop anchor is not interchangeable with a display exposure anchor. An analyst who chooses whichever anchor produces the largest count changes the measurement definition. Store the original source timestamp and the normalized comparison timestamp so the boundary decision can be reproduced.

## EF-412 boundary

EF-412 includes a conversion exactly on the documented window endpoint, but excludes a conversion one second after that endpoint.

The endpoint is derived from the approved channel rule and the anchor, not from the file arrival date. The table describes the synthetic diagnostic fixture rather than live campaign outcomes. Its invented event identifiers allow the analyst to inspect exact lexical matches during retrieval. A missing timezone keeps the fixture unresolved until the source owner supplies it; guessing an offset would make the apparent precision misleading.

| Event identifier | Position relative to window | Expected classification |
|---|---|---|
| EVT-410 | One second before anchor | Excluded before anchor |
| EVT-411 | Exactly at anchor | Included |
| EVT-412 | Exactly at endpoint | Included |
| EVT-413 | One second after endpoint | Excluded after endpoint |

## Exception for source corrections

Exception EF-419 handles a source owner correcting an event timestamp. Preserve the original event and create a revision with the correction reason and evidence reference. Recompute eligibility under the same approved rule first. If the rule itself also changes, record that as a separate methodology change. Overwriting the earlier timestamp would hide why an event moved into or out of the accepted set. A correction may change a published count, so notify the consumers of the affected snapshot and identify the revised cutoff. Do not imply that a later analyst had the corrected evidence at the time of an earlier decision.

## Why is the activation total larger than the enrollment total?

Check whether the activation extract contains multiple status transitions for the same enrollment. An application can be started, submitted, verified, and reopened without creating four verified products. The campaign definition identifies the terminal state that qualifies as a verified activation and the stable key used for deduplication. Count unique qualifying products according to that definition, retaining the transition history for investigation. A product's reopened support case should not automatically create another activation. If the stable key is absent, the feed needs a source repair; concatenating a name and a date is an unsafe substitute that can merge different people or split one event.

## Why do early cohorts look stronger?

A cohort received earlier has had more time to convert. Compare observation maturity before interpreting its higher total as better creative or audience quality. The diagnostic view shows anchor, window length, current cutoff, and whether the complete window has elapsed. An immature cohort can still provide operational evidence that the feed is arriving, but it cannot support a final rate comparison with a fully matured cohort without an explicit method. Avoid treating a zero count from an unfinished window as proof of no eventual response. The appropriate result may be unavailable or provisional rather than poor performance.

## Release verification

Run the endpoint fixture, duplicate-transition fixture, corrected-timestamp fixture, and delayed-arrival fixture through the actual normalization route. For each one, retain accepted and rejected identifiers with a reason. A test that checks only the final total can pass when one valid event is lost and one invalid event is included. Identity-level verification catches that cancellation of errors. The review also checks that rejection reasons remain discoverable to an analyst without exposing private event fields. After deployment, inspect the first synthetic health batch and confirm that its trace uses the same rule version approved in the release record.

## Reproduction trace

Build a synthetic cohort with one event before the anchor, one exactly at the anchor, one exactly at the endpoint, and one immediately after it. Send the same events in a different arrival order and then delay the endpoint event until a later file. The accepted membership must remain determined by occurrence time and the approved rule. A pipeline that uses file order or arrival date can produce the correct total on one run and a different total on another. The test therefore compares accepted identifiers, rejection reasons, and normalized timestamps rather than only checking an aggregate activation count.

Next, duplicate the endpoint event with a new transport receipt but the same stable enrollment key. The distinct verified activation count must not increase. Add an unrelated support reopening transition and verify that it does not create another product activation. Finally, submit an authorized timestamp correction that moves the endpoint event outside the window. The accepted set changes under a new revision, while the earlier snapshot remains reproducible. This sequence exercises deduplication, lifecycle state, and correction custody without confusing them with the endpoint rule itself.

The reviewer asks which failures would be visible from a totals-only dashboard. A duplicated valid event and an omitted valid event can cancel numerically. A shifted timestamp can also move one event out while a different invalid event moves in. A stable total therefore does not prove stable membership or correct eligibility. Retaining synthetic event-level evidence makes these failures observable without exposing private customer records. The case supports teaching lexical retrieval around EF-412 and semantic retrieval around observation maturity; it does not claim that one chunk strategy will recover both topics equally well.
