"""Original authored synthetic sources for observing chunk boundary tradeoffs.

These are teaching scenarios, not banking advice or observed campaign results.
Content is authored once rather than lengthened by repeating a template.
"""
import textwrap


# title, shape, evidence heading, question, exact answer, body
SOURCES = [
    (
        'Consent recovery launch playbook', 'playbook', 'Recovery gate',
        'When can a quarantined consent file resume in the consent recovery playbook?',
        'Resume only after two independent reviewers reconcile every quarantined row and sign gate CR-217.',
        """
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
        """,
    ),
    (
        'Branch opening readiness playbook', 'playbook', 'Accessible rehearsal',
        'What does the branch opening playbook require for an accessible rehearsal?',
        'Run the accessible rehearsal with a keyboard-only journey and a staffed telephone alternative before gate BR-406.',
        """
        ## Location evidence

        The fictional branch opening team starts with an address record approved by the facilities owner. An address in a creative mockup is not sufficient: a map pin can identify the shopping center while directing visitors to a loading entrance. Record the public entrance, parking access, transit description, opening hours, and the date each detail was checked. A local coordinator walks the route that an invited visitor would take. If construction blocks the advertised entrance, the campaign should describe the temporary route and who will help a visitor who cannot use it. Treat opening day logistics as source evidence rather than decorative copy.

        ## Invitation sequence

        Separate the announcement, reminder, and appointment confirmation. The announcement explains the purpose and location; the reminder repeats practical information without implying that attendance establishes product eligibility. An appointment confirmation must identify whether the visitor has reserved a time with a specialist or only registered interest. The two statuses are not interchangeable. The coordinator tests cancellation and rescheduling links using invented registrations. If a rescheduled appointment retains the original time in a reminder queue, pause that reminder sequence and reconcile its state before adding further invitations. A low unsubscribe rate does not demonstrate that the sequence is accurate.

        ## Accessible rehearsal

        Run the accessible rehearsal with a keyboard-only journey and a staffed telephone alternative before gate BR-406.

        The rehearsal follows the complete registration journey, including error messages, time selection, cancellation, and confirmation. A page that can be opened by keyboard may still trap focus inside a calendar control. Ask the reviewer to document the point where assistance was needed rather than simply marking the screen as passed. The telephone alternative must be staffed during the advertised registration hours and capable of changing the same appointment register. A voicemail box checked the following week is not an equivalent route for a next-day event. Record rehearsal observations with synthetic names and appointments.

        ## Capacity and waiting

        Build capacity from available staff time and service duration, allowing time for breaks and complex questions. A room with twenty chairs does not automatically provide twenty simultaneous consultation slots. Keep drop-in attendance separate from booked consultations. On the event day, explain expected waiting time at arrival and provide a way to leave and receive an update without losing the queue position. Avoid broadcasting names or financial interests across the waiting area. If staff shortages reduce capacity, the event owner decides which sessions can move and sends clear instructions using the approved contact route.

        ## Observation ledger

        Count invitations, completed registrations, confirmed appointments, arrivals, and completed consultations as separate events. Record the point at which each count becomes final. A person who cancels and later registers again should not inflate the count of distinct visitors, although both actions can remain in the operational event log. Do not infer account openings from consultation attendance. Product enrollment belongs to a separate verification process with its own timing and attribution rules. The branch opening ledger provides evidence about event handling; it does not establish incremental deposit growth or financial return from the event.

        ## Weather contingency

        The contingency owner checks conditions and building access on the morning before the event and again before staff travel. If the location closes, update the registration page, telephone script, and outgoing reminder queue from one approved notice. The notice distinguishes a postponed event from a canceled appointment and states when a replacement decision will be announced. Retain a timestamped copy so staff can identify people who received an earlier instruction. After reopening, review whether accessible routes, staffing, and appointment capacity still match the invitation. Passing the original rehearsal does not cover a changed entrance or a replacement registration service.
        """,
    ),
    (
        'Controlled creative experiment playbook', 'playbook', 'Stop rule',
        'What is the stop rule for the fictional creative experiment?',
        'Pause experiment EX-552 when either variant has a broken eligibility link; do not declare a winner from the partial run.',
        """
        ## Hypothesis and assignment

        A creative experiment asks whether one explanation helps eligible prospects complete a verified enrollment more often than another. State the proposed mechanism before launch: for example, a shorter explanation may reduce confusion about the next step. Define the eligible population and random assignment unit. If households can receive several messages, assigning each message independently could expose the same household to both variants and weaken interpretation. The experiment register records the assignment key, allocation ratio, treatment versions, and planned analysis date. Keep a frozen copy of each variant so an unnoticed copy edit does not become an unrecorded third treatment.

        ## Delivery parity

        Hold the offer, eligibility rules, delivery schedule, and measurement window constant when the intended comparison concerns wording. Different send times can change which recipients see a message before a deadline. Check delivery failures for each assigned group and retain both assignment and exposure counts. The assigned population supports an intention-to-treat view; exposed recipients answer a different question that may be affected by delivery selection. Do not silently switch denominators because the exposed-recipient result is more attractive. Record any exclusions in a rule that can be applied consistently to both variants without looking at their outcomes.

        ## Stop rule

        Pause experiment EX-552 when either variant has a broken eligibility link; do not declare a winner from the partial run.

        A link failure changes access to the product rather than simply changing persuasive language. Save the failure time, repair time, affected variant, and evidence from the monitoring route. Determine whether the full interval is known or whether a gap in monitoring leaves uncertainty. The experiment owner decides whether a fresh randomized run is needed after repair. Removing only the low-performing hours from one variant would compromise the comparison. A repaired link can restore operations, but it does not retrospectively restore comparability to the interrupted experiment.

        ## Maturity and stopping

        Choose an observation horizon that allows the relevant conversion window to close for the final assigned recipient. An early recipient may have had weeks to act while a late recipient has had only a day. This difference can distort an apparent treatment effect if assignment volumes vary by date. The analyst can inspect operational health during the run, but repeated unplanned significance checks should not become a reason to stop at the first favorable result. Record the planned sample size rationale and the intended analysis method. If delivery falls short, describe the resulting uncertainty instead of inventing precision from additional decimal places.

        ## Interpretation route

        Compare groups using the predefined primary outcome and report the counts needed to reconstruct the rate. Explain uncertainty using an interval or another prespecified method appropriate to the design. An observed difference does not establish why the creative worked; a comprehension survey might test that mechanism separately. Keep secondary outcomes, such as link clicks or appointments, clearly labeled. A variant can attract more clicks while producing fewer verified enrollments. The business decision should consider the primary outcome, service burden, and evidence limitations together, rather than treating every movement in the dashboard as independent confirmation.

        ## Reuse and transfer

        A result from one offer, channel, or eligible population may not transfer unchanged to another. The reuse note identifies the population actually studied, the exact versions, the exposure period, and any interruption. A future team can choose a replication rather than treating the prior result as a universal wording rule. Preserve the assignment specification and synthetic validation records so analysts can test the pipeline without accessing recipient details. Close the register with a decision and its evidence, including a decision to continue learning. A neutral or inconclusive result is a legitimate outcome and must remain discoverable alongside successful experiments.
        """,
    ),
    (
        'Attribution correction retention policy', 'cohesive_policy', 'Correction custody',
        'How are late attribution corrections handled under the custody policy?',
        'A late correction receives a new revision linked to the original snapshot; it never overwrites the signed snapshot under policy AC-318.',
        """
        ## Correction custody

        This fictional policy governs the custody of attribution corrections for campaign learning records. A source event is an observation with a stable identifier, event time, collection route, and recorded campaign association. A signed snapshot is the set of observations accepted at a stated cutoff, accompanied by the rules used to include them. Neither an event's arrival time nor the analyst's review time replaces its occurrence time. The custodian stores these times separately because delayed delivery and an actually late conversion have different implications. A late-arriving observation can still fall within a previously defined attribution window; an observation occurring outside that window cannot be pulled inside merely because its file arrived with eligible events.

        When a team discovers a correction, the requester identifies the original event, proposed replacement value, reason, and supporting evidence. The request is attached to a revision ledger with an owner and a review state. A correction may concern a duplicate, an incorrect anchor date, an invalid campaign association, or an incorrectly applied rule. These are recorded as distinct reasons because a duplicate removal does not imply that a channel's entire measurement window was wrong. If the request lacks enough evidence to establish which event changed, it remains unresolved and the published learning record notes the uncertainty. An urgent presentation deadline does not convert an unverified request into an accepted correction.

        A late correction receives a new revision linked to the original snapshot; it never overwrites the signed snapshot under policy AC-318.

        The revised artifact includes a machine-readable parent snapshot identifier and a human-readable change note. The note explains which counts changed and why, without exposing customer details. An analyst comparing revisions should be able to reproduce both the original and revised values using the corresponding source events and rule versions. A file with the same name and a different modification time is insufficient lineage. Each revision has a new checksum and a declared cutoff, even if only one event changed. Where a revision affects several campaigns, list them explicitly rather than implying that every campaign in the same period changed.

        Reviewers distinguish a data correction from a methodology change. Correcting a mistyped anchor date applies an existing rule to better evidence. Replacing a thirty-day window with a different window changes the rule and therefore the meaning of the count. A methodology change needs a separate comparison note and cannot be presented as a routine data cleanup. If both occur together, calculate their effects separately when the data permits. If their effects cannot be separated, state that limitation. A single combined difference should not be attributed entirely to delivery performance when part of it comes from a changed definition.

        Downstream consumers receive a revision notice identifying superseded artifacts and the scope of the change. A cached chart, extracted table, or presentation image may continue to show the old values after the source file is corrected. The owner checks the consumers listed in the dependency register and marks each as updated, intentionally frozen, or awaiting action. Intentionally frozen materials retain their original cutoff and carry a notice that a later revision exists. Do not change historical exports in place without preserving their identity; doing so would make a past decision appear to have used evidence that did not yet exist at the time.

        Access to the raw correction evidence follows the same restrictions as access to the original source events. The revision note may be broadly readable while supporting records remain restricted. The custodian removes unnecessary personal fields from the analyst's working copy and refers to stable internal identifiers. An access request for aggregate learning does not automatically justify access to individual records. Reviewers can often validate a checksum, event count, or rule application using an approved aggregate extract. When individual evidence is essential, the request explains the specific uncertainty that cannot be resolved from aggregate material.

        Closure requires the requester and an independent reviewer to agree that the accepted change matches its evidence and that affected consumers have been notified. The ledger preserves rejected requests as decisions with reasons, because repeated rejected requests can reveal a confusing definition. Retention follows the fictional library schedule attached to the snapshot; this document does not prescribe a real legal retention period. If a deletion request conflicts with a pending investigation, the designated records owner resolves it and documents the basis. The analyst must not improvise a retention deadline from this teaching example or infer that keeping every working copy forever improves traceability.
        """,
    ),
    (
        'Offer eligibility exception policy', 'cohesive_policy', 'Exception control',
        'What is required before using an offer eligibility exception?',
        'Exception OE-624 requires a named approver, an expiration date, and a recorded customer-facing explanation before delivery.',
        """
        ## Exception control

        This fictional policy treats an offer as a promise whose practical conditions must be understandable at the point where a person decides to respond. Eligibility is not established merely because a record entered an audience file. The product owner maintains the eligibility specification, including applicable product status, permitted geography, enrollment timing, and evidence needed at fulfillment. The campaign owner translates that specification into a delivery rule and a customer-facing explanation. Both versions must refer to the same approved offer revision. If the data needed to determine eligibility is missing, the audience process records an unknown state instead of quietly treating missing values as eligible.

        An exception changes one specified condition for one defined scope. It is not general permission to ignore the offer specification. The requester describes the affected population, the condition being changed, the reason, and the proposed end date. A change to the benefit amount is a different exception from a change to enrollment timing, even when they concern the same campaign. The reviewer considers whether recipients can understand the resulting promise and whether fulfillment can apply it consistently. If the operational system cannot distinguish the exception population from standard recipients, the exception remains blocked until that distinction can be represented and tested.

        Exception OE-624 requires a named approver, an expiration date, and a recorded customer-facing explanation before delivery.

        The approver is accountable for the defined exception and cannot be represented only by a shared inbox. The expiration date governs the authority to make new deliveries under the exception; it does not retroactively erase promises already made to eligible recipients. The explanation states the condition being changed in plain language and avoids implying that every product requirement has been waived. Save the exact explanation with the offer revision and delivery selection. A reviewer who sees the record later should be able to determine which promise a particular delivery carried without reconstructing the campaign from informal conversations.

        Test the exception using synthetic records that exercise the boundary and unknown states. A record on the final permitted date is different from a record one day after it. A known eligible product state is different from an absent state field. Include a record that meets the exception condition but fails an unchanged condition, because an implementation can accidentally treat the exception as an unconditional pass. Document the expected outcome before running the test. If the actual result differs, repair the rule or revise the approved specification through review; do not edit the expected outcome merely to make the validation sheet appear successful.

        Delivery partners receive the minimum fields needed to apply the approved selection and explanation. They do not receive authority to invent additional exceptions in response to complaints or delayed files. Route a disputed eligibility decision to the product owner with the offer revision, delivery timestamp, and evidence status. Customer service can explain the documented rule, but an uncertain case should remain uncertain until the required evidence is available. A promise to investigate is preferable to an unsupported assurance that a benefit will be paid. Keep investigation notes separate from the approved offer text so an internal hypothesis is not later mistaken for a promise.

        When an exception expires, the operations owner removes it from new audience selections and checks queued deliveries. A file selected before expiration may still be waiting at a partner, so the owner must apply the approved queue rule rather than assuming selection time settles every case. Record the disposition of each queued batch. Existing recipients retain the terms that applied to their delivery unless the approved terms themselves state otherwise. A revised offer should have a new identifier and a clear transition rule. Reusing the same identifier for incompatible terms makes both fulfillment and later learning unreliable.

        The closing review compares the approved exception scope with actual deliveries and fulfillment decisions. Report the count of recipients whose eligibility remained unknown separately from confirmed eligible and confirmed ineligible records. Do not describe the exception as successful solely because it increased response volume; responses from people who cannot receive the promised benefit can create service burden and misunderstanding. The learning note identifies operational failures, unresolved disputes, and any additional evidence needed for future changes. It remains a synthetic teaching record and cannot be used as a statement of real banking eligibility requirements or legal obligations.
        """,
    ),
    (
        'Shared audience suppression policy', 'cohesive_policy', 'Suppression custody',
        'How quickly must the fictional suppression service acknowledge an emergency withdrawal?',
        'The suppression service must acknowledge emergency withdrawal SP-809 within four business hours and block queued reuse until reconciliation.',
        """
        ## Suppression custody

        A shared audience service may support several campaigns, each with a different purpose and delivery schedule. This fictional policy separates the identity of an audience record from permission to use that record for a particular purpose. A campaign's previous selection does not establish permanent permission for future selections. The service maintains purpose-specific eligibility and suppression states with effective times and evidence references. A record can be permitted for a service notice while being suppressed for a promotional offer. Collapsing these states into a single global yes-or-no field would either permit unwanted delivery or incorrectly block necessary operational communication.

        A withdrawal enters the service through an approved intake route and receives a stable request identifier. The intake operator records the purpose, received time, requested effective time when applicable, and the evidence needed to connect the request to the correct record. Ambiguous identity matches enter a restricted review queue. Do not choose the first similar name from a search result. At the same time, the operator should not require unnecessary personal data when an existing authenticated route already establishes the record. A request's progress is visible through its identifier so service staff can answer status questions without copying private details into unrelated messages.

        The suppression service must acknowledge emergency withdrawal SP-809 within four business hours and block queued reuse until reconciliation.

        Acknowledgment confirms receipt and the current handling state; it is not a claim that every partner has already removed every queued item. The operations owner identifies active selections, queued files, and scheduled refreshes that could reuse the record. Each downstream system receives an instruction with the suppression identifier and the relevant purpose. The owner records receipts and investigates missing acknowledgments. If a partner cannot remove an individual row safely, the affected batch is paused while a replacement is prepared. An emergency state remains open until the handling of existing queues is known, even if new selections are already blocked.

        Recurring refreshes must apply the current suppression state rather than restoring an older audience snapshot. The service tests this by selecting a synthetic record, suppressing it, and running the next refresh from the same upstream source. If the record returns to a deliverable state without new authority, the refresh process has failed. Store the result with the refresh version and schedule. A nightly job that reports a successful execution can still have applied stale suppression data, so the test inspects its actual selected output. Separate execution health from permission correctness in the operational monitor.

        Shared suppression requires a clear boundary between a purpose-specific withdrawal and a request affecting every promotional purpose. The intake route records what the person requested, and the review process resolves unclear scope using the approved clarification route. Staff must not narrow a broad request to whichever campaign happens to be open on their screen. Conversely, a narrowly described preference should not automatically become an invented statement about unrelated services. The service preserves both the original request and the interpreted scope, including who approved that interpretation. Later disputes can then be reviewed against the evidence rather than memory.

        Reinstatement is a separate authorized event with its own evidence and effective time. Deleting a suppression row is not a valid reinstatement because it removes the history needed to understand earlier handling. A legitimate reinstatement may apply to one purpose while leaving another suppressed. The service creates a new state transition and verifies its downstream interpretation using synthetic records before release. If the same request is received twice, idempotent handling produces one effective transition with multiple receipt references. Duplicate messages should not create alternating suppression and reinstatement states or reset the recorded time of the original request.

        Periodic reconciliation compares the current service state with partner acknowledgments and a sample of actual queued outputs. The reviewer records unresolved gaps and assigns an owner to each partner whose handling cannot be verified. Aggregate counts can reveal drift but do not alone establish that the same records were handled correctly; a matching total can conceal different omissions. Use privacy-preserving identifiers where possible to compare membership. This policy is a teaching scenario, not a legal service-level agreement. Its four-business-hour acknowledgment target belongs only to the fictional SP-809 workflow and should not be generalized to real institutions without their own approved requirements.
        """,
    ),
    (
        'Operations handoff notebook north', 'mixed_notes', 'Document',
        'In the north handoff notebook, what happens to a partner file without a checksum?',
        'A partner file without a checksum stays in intake hold NH-143 and cannot become a delivery batch.',
        """
        The morning shift inherited two similar file names from different partners. One contained the final audience selection and the other a rehearsal set. Their names differed only by an added date, which was not enough for a safe handoff. The coordinator compared the approved manifest with the received receipt and asked the partner to identify the production checksum. A partner file without a checksum stays in intake hold NH-143 and cannot become a delivery batch. The shift notes preserve that rule alongside the incident so a late operator cannot mistake a familiar filename for evidence of approval. The test set remains available for pipeline rehearsal using invented records.

        Later, the service desk noticed that a reminder message still described an appointment as confirmed after the visitor had canceled it. The appointment register was correct; the reminder queue had been built before the cancellation and had no refresh route. Operations removed the affected reminders and changed the queue builder to check current appointment status immediately before delivery. A successful queue build would not have caught this problem because the state changed afterward. The handoff asks the next shift to verify a synthetic cancellation through the complete sequence, including its receipt, instead of inspecting only the registration screen.

        The warehouse team then examined a display exposure feed whose dates appeared one day earlier than the partner's dashboard. The feed used coordinated universal time while the dashboard displayed a local date. No conversion had actually moved in time. The analyst stored the timestamp with its offset and derived the campaign reporting date explicitly. Comparing date strings without this conversion had created an apparent discrepancy. For future checks, the notebook asks analysts to compare exact timestamps first, then apply the documented reporting zone. It also warns that a timestamp with no offset is missing evidence, not automatically local time.

        At midday, a creative reviewer found that a shortened offer explanation removed a condition that remained in the fulfillment system. The design was visually cleaner but described a different promise. The team restored the condition and asked service staff to review the wording using a fictional customer question. The reviewer recorded what the text meant rather than counting lines of legal copy. Copy length is an implementation detail; comprehension of the condition is the intended result. The notebook keeps both versions so future reviewers can see why the shorter version was rejected instead of reintroducing the same omission under a new design request.

        The branch event coordinator supplied a new entrance description because construction had closed the previously advertised walkway. The audience and offer were unchanged, but appointment confirmations still contained the old route. Staff updated the confirmation template and contacted registered visitors through the approved route. A local coordinator walked the replacement route and checked whether it could be used by visitors with mobility needs. The handoff notes that a map pin did not change when the entrance changed, so a map-only review would have missed the access problem. Future checks must inspect the complete arrival instructions and the actual path to the public entrance.

        A separate analyst asked whether rising direct mail response proved that the new design outperformed display. The notebook records why the question could not be settled from the available counts: the channels used different exposure units and observation windows, and the audiences were not randomly assigned. The team could compare each channel with a compatible prior cohort, but that would still be observational. The proposed next step was a controlled experiment within a clearly defined population. No one should turn the handoff's scheduling recommendation into a claim that causal lift was measured during this shift.

        Before leaving, the shift lead reconciled open incidents against the release board. The checksum hold, reminder repair, timestamp investigation, copy revision, and entrance update had separate owners and evidence routes. They were not combined into one generic campaign problem. The next shift receives a status and a concrete verification action for each item. Closed items retain their evidence references; unresolved items retain the reason they remain blocked. The notebook intentionally mixes these topics without formal section headings so a retrieval exercise can observe whether topic transitions remain discoverable when the source author did not supply a ready-made outline.
        """,
    ),
    (
        'Operations handoff notebook west', 'mixed_notes', 'Document',
        'What is the west notebook rule for a mismatched product code?',
        'Route product-code mismatch WH-268 to the product owner; never map it to the nearest familiar product label.',
        """
        The west operations team received a fulfillment extract with a product code that did not appear in the campaign dictionary. Its display name resembled a savings product, but the source system could also use that prefix for a closed legacy account. Route product-code mismatch WH-268 to the product owner; never map it to the nearest familiar product label. The analyst retained the unknown code and excluded it from product-specific conclusions while the owner investigated. This preserves uncertainty in the evidence instead of converting an attractive label into a false enrollment. A later mapping must identify its effective dates because product codes can be reused.

        A delivery specialist reviewed duplicate receipts from a partner whose retries used new transport identifiers. Counting receipts would have counted the same payload twice. The specialist matched the approved payload checksum and the original business batch identifier, then recorded both transport attempts under one delivery event. The retry log still matters for operational reliability, but it is a different measure from distinct delivered batches. The next shift will test a synthetic timeout followed by a successful retry. The intended outcome is one business delivery with two transport attempts and a traceable final acknowledgment, not two deliveries with mysteriously identical audience members.

        During the same shift, the survey team changed an answer option from unsure to not applicable. The new wording seemed minor but changed the meaning of the response. An unsure respondent may lack information, whereas a not-applicable respondent may understand the question and fall outside its scope. The analyst kept the versions separate and declined to combine their counts into a trend. The questionnaire register now records option text, order, and the date of change. A survey export with identical column names can conceal a changed instrument, so schema matching alone does not establish measurement compatibility across waves.

        In the afternoon, a branch manager asked for extra invitations because several appointments remained open. The event owner checked staffing first and discovered that a specialist would be absent for part of the day. Empty slots in the calendar did not represent usable capacity for that service. The owner adjusted the appointment type and routed general questions to another staffed session. The handoff records the staffing interval and the revised public description. It avoids recording a customer's financial circumstances in the shared event notes; staff who need those details use the restricted appointment system with the appropriate access.

        The media coordinator then asked whether an unspent display allocation could move directly into a mail drop. Operations explained that mail production had a different lead time, address validation step, and observation window. A budget transfer alone would not produce comparable evidence or immediate delivery. The team prepared a schedule showing the earliest feasible drop and the date at which its conversion window would mature. The notebook records those dependencies so the following shift does not mistake an approved allocation for a released audience file. Approval, production readiness, delivery, and measurement maturity remain distinct states with their own evidence.

        Near closing, an analyst noticed that a dashboard labeled opening account balances as new deposits. The source field described the balance recorded at account opening and did not establish how much represented transfers from existing accounts. The analyst corrected the label and retained the field definition beside the extract. No new measurement was invented to fill the gap. If a future project needs net new deposits, it must define transfer treatment and obtain the necessary evidence. A familiar financial phrase should not be substituted for a narrower source measure simply because it fits better in a chart title.

        The shift lead ended with a practical audit of pending handoffs. Every open item needed an owner, a source identifier, the current uncertainty, and the next check. An unanswered product mapping question could remain open without blocking an unrelated event notice. A duplicate receipt repair could be closed once the delivery event and retry evidence agreed. The notebook deliberately records transitions between logistics, measurement, and customer communication as ordinary prose. Readers should recover the right evidence from the topic itself and its identifiers, while recognizing that nearby paragraphs are not automatically supporting evidence for the same claim.
        """,
    ),
    (
        'Operations handoff notebook central', 'mixed_notes', 'Document',
        'How should a timezone-free event timestamp be handled in the central notebook?',
        'Timestamp exception CH-731 stays unresolved until the source owner supplies the timezone; analysts must not infer it from the branch address.',
        """
        A central operations analyst found that an event file contained dates and times without an offset. The campaign involved several branches and a remote service center, so the branch location could not establish where the source clock ran. Timestamp exception CH-731 stays unresolved until the source owner supplies the timezone; analysts must not infer it from the branch address. The file can remain in the intake ledger with an unresolved state, but it cannot support a precise boundary decision. The owner is asked whether the export used a system zone, a user preference, or an already-converted campaign date. These possibilities require different repairs.

        The next note concerns a call center script that described a product benefit before confirming which offer revision the caller received. Two revisions were active for different audiences. The service coordinator added a step to retrieve the delivery reference and approved script version. Staff can explain general product information while the reference is checked, but cannot promise the specific campaign benefit from memory. The notebook saves a synthetic example of each revision and a case with no delivery reference. The missing-reference case should route to investigation rather than silently selecting the latest offer and assuming it applied to the earlier message.

        A separate discussion reviewed an audience count that fell after household deduplication. The export owner had treated each contact route as a person, while the campaign specification selected households. Removing duplicate routes therefore changed the delivery count without showing that any eligible household had been lost. The analyst retained both contact-route and household counts and labeled them explicitly. A comparison with earlier exports must use the same unit. The team rejected a proposal to restore duplicates merely to match the old total; a familiar count is not evidence that the underlying selection rule was correct.

        In the appointment system, a scheduled maintenance interval overlapped with a registration reminder. The reminder's link would lead to an unavailable service for some recipients. Operations delayed the reminder and posted a precise availability notice with an alternative route. The service owner confirmed when the registration database would accept changes again, rather than relying on the web page's ability to load. A static page can appear healthy while appointment creation fails. The follow-up check uses an invented registration and cancellation to verify the complete transaction, preserving its receipt so the next shift can tell what was actually tested.

        Another analyst asked to rank campaigns by acquisition cost across two product types. The notebook records the conditions needed for a useful comparison: consistent activation definitions, compatible attribution windows, complete spend, and matured observations. Even with those conditions, differences in product suitability and audience selection limit interpretation. A low observed cost may reflect an easier-to-reach audience rather than a transferable creative improvement. The team proposed grouping compatible campaigns and carrying the definitions into the comparison. Where a denominator is zero, the cost is unavailable; it is not zero and should not be placed at the top of a performance ranking.

        The privacy coordinator reviewed an internal training screenshot and found real contact details in an otherwise fictional walkthrough. The screenshot was removed from the training folder and replaced with a newly generated synthetic journey. Merely blurring a name would leave other identifying fields visible and would not make the example reliably fictional. The training owner now checks the source environment before capture and records that the examples use invented records. The notebook links to the approved synthetic fixture rather than copying images into several handoff messages, reducing the chance that an outdated image continues circulating after a correction.

        Finally, the lead reconciled the event-time issue, script revision, household unit, service maintenance, comparison request, and training repair. Each entry has a different resolution condition. Supplying the source timezone resolves one uncertainty but does not validate the offer script. Repairing the screenshot does not establish that all campaign measures are comparable. The shift note preserves these distinctions because informal handoffs often create false associations between adjacent facts. A retrieval exercise using this source should inspect whether the evidence selected for a timestamp question actually includes CH-731 and its resolution rule, rather than relying on another operational paragraph that happens to mention a date.
        """,
    ),
    (
        'Delivery receipt troubleshooting FAQ', 'troubleshooting', 'DR-905 recovery',
        'Can a delivery batch be retried after receipt timeout DR-905?',
        'For DR-905, query the partner using the original idempotency key before retrying; an accepted batch must not be resent.',
        """
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
        """,
    ),
    (
        'Enrollment feed troubleshooting FAQ', 'troubleshooting', 'EF-412 boundary',
        'How is a conversion exactly at the enrollment window endpoint treated?',
        'EF-412 includes a conversion exactly on the documented window endpoint, but excludes a conversion one second after that endpoint.',
        """
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
        """,
    ),
    (
        'Knowledge source troubleshooting FAQ', 'troubleshooting', 'KS-663 mismatch',
        'What should happen when a knowledge source checksum changes?',
        'KS-663 rejects a cached retrieval result when its source checksum differs from the current manifest, even if the document identifier is unchanged.',
        """
        ## Why can an old answer cite a familiar document?

        A document identifier names a source but does not establish which revision supplied the answer. The fictional knowledge service stores the manifest identity, source checksum, chunking configuration, embedding model identity, and retrieval settings with a result. If an author revises a policy under the same identifier, the old chunks may still exist in a recoverable collection. Their presence is useful for historical investigation but does not make them current evidence. The analyst checks the current manifest and source bytes before presenting a cached answer as a fresh response. A filename or a recent modification time alone is not enough to establish compatibility.

        ## KS-663 mismatch

        KS-663 rejects a cached retrieval result when its source checksum differs from the current manifest, even if the document identifier is unchanged.

        The check applies before a result is displayed as current. Preserve rejected result metadata for diagnosis without mixing its scores into the new run. The service may explain that an older run exists, but it must identify its original corpus and configuration. A stale answer can contain perfectly fluent prose and syntactically valid citations while supporting a rule that the author has since replaced. Fluency and citation shape cannot substitute for source identity.

        | Diagnostic code | Observed mismatch | Required response |
        |---|---|---|
        | KS-663 | Source checksum changed | Reject cached current result |
        | KS-664 | Embedding model changed | Rebuild compatible vectors |
        | KS-665 | Chunk boundaries changed | Use matching chunk collection |
        | KS-666 | Question case set changed | Recompute evaluation identity |

        ## Exception for historical investigation

        Exception KS-670 permits opening an old collection to investigate what evidence an earlier answer used. The interface labels its historical corpus identity and does not present the result as current. A reviewer may need to compare the earlier policy text with a revision to understand a past decision. This use preserves the original source checksum and configuration rather than silently substituting current text under old citations. The exception does not allow old evaluation scores to populate a new corpus dashboard. Historical reproducibility and current correctness answer different questions, and the record must make clear which one is being examined.

        ## Why did adding a source change rankings?

        New sources can introduce both relevant evidence and plausible distractors. Sparse term statistics can change, dense neighborhoods can become more crowded, and reranking can select a different final set from the candidate pool. A new ranking is not automatically an improvement or a regression. Inspect the retrieved text, the filters, and the question's expected evidence. A shared policy may legitimately outrank a campaign brief for a policy question while being irrelevant to a campaign-specific target question. Evaluation should therefore disclose its case set and scope instead of treating one aggregate score as proof that every kind of question improved.

        ## What if a citation points to the wrong passage?

        First verify that the cited chunk exists in the selected collection and matches the current source checksum. Then inspect whether its text supports the associated claim. A citation can be valid as an identifier yet irrelevant to the claim. A paragraph about delivery retries does not establish an enrollment window merely because both belong to the same campaign library. The analyst should distinguish missing retrieval, incorrect context selection, and unsupported answer synthesis. Those failure stages suggest different repairs. Adding more context indiscriminately can worsen the problem by surrounding a small relevant fact with attractive but unrelated instructions.

        ## Reproducing the comparison

        Record the question, effective metadata constraints, corpus identity, chunk strategy, embedding identity, retrieval mode, candidate count, final count, and reranker setting. Preserve the returned chunk identifiers and source text so another analyst can inspect the evidence. Compare methods using the same question and binding scope. A campaign-specific run should not be compared with a corpus-wide run as though only the chunking method changed. This FAQ offers development cases for exploring those controls. They are curated examples used during implementation, not a held-out benchmark, and no measured semantic advantage is claimed merely because the examples were designed to expose boundary behavior.
        """,
    ),
]


FIELD_EXERCISES = [
    """
    ## Worked recovery exercise

    In the rehearsal incident, a partner reports twelve rejected rows from a replacement batch. Eight have an expired purpose code, three are duplicate routes for otherwise permitted households, and one points to an evidence record that cannot be opened. The preparer initially proposes suppressing all twelve and releasing the rest. The independent reviewer asks whether the same export defect could have affected rows that the partner did not reject. This is a useful distinction: a partner rejection is a symptom, not a complete inventory of the export defect. The team examines the export rule and reconciles the entire quarantined population before describing the repair as complete.

    The duplicates can be resolved against stable household keys, while the expired codes require the source owner to establish current authority. The inaccessible evidence record remains unresolved. The team produces a replacement selection that excludes unresolved rows and records the reason for each exclusion. It then reconciles the approved selection with the partner's accepted payload, rather than treating a successful upload as release evidence. The reviewer records why no new permission was inferred from the household match. These decisions become part of the CR-217 record and can be inspected without reading the original customer file.

    A training observer asks why two signatures are needed when the automated checks pass. The exercise demonstrates a specific failure mode: the preparer had assumed that the partner's rejection list covered every affected row. An independent review challenged that assumption by checking the rule itself. Automation can validate specified conditions but may not identify a missing condition. The learning objective is therefore to connect signatures to actual review evidence. A form containing two names without the reconciliation and replacement checksum would satisfy the appearance of a control while leaving the original uncertainty unresolved.

    As a final challenge, the facilitator inserts a superseded batch receipt into the evidence bundle. The reviewer must reject it because its checksum does not identify the approved replacement. Recognizing the campaign name is insufficient. This tests whether the recovery decision follows the specific artifact that was reconciled, rather than accepting any successful receipt from the same campaign as proof that the quarantined file was safely replaced.
    """,
    """
    ## Worked arrival exercise

    The rehearsal starts with an invented visitor who registers for an afternoon appointment using only a keyboard. The visitor selects a time, receives confirmation, and then needs to move the appointment. The calendar's next-month control receives focus, but the confirmation button does not. The reviewer records the focus sequence and the point where progress stops. The event team repairs the control order and repeats the complete journey, including cancellation. Testing only the first registration screen would have left the rescheduling failure undiscovered. The completed trace becomes evidence for the gate rather than a general statement that the website is accessible.

    A second invented visitor calls the advertised alternative while the rehearsal is running. The agent must see the same appointment inventory and must be able to explain the replacement entrance. In the first attempt, the agent has a printed schedule from the previous day and offers a slot that is already occupied. The exercise therefore fails even though the phone was answered promptly. Operations gives the agent the current register and repeats the booking. The resulting confirmation identifies the actual appointment type and location, so the telephone route does not create a different promise from the online route.

    Finally, the coordinator simulates a staffing reduction shortly before opening. The system must remove unavailable specialist slots without canceling unrelated general-information visits. Staff practice explaining the difference to an invented caller and recording a rescheduling decision. The evidence bundle contains the changed capacity, the affected synthetic appointments, and the outgoing notices. The purpose is to verify a usable service under realistic changes, not simply to collect favorable screenshots. The BR-406 reviewer signs only after the keyboard journey, staffed alternative, and capacity adjustment all have a reproducible outcome in the same appointment register.

    The facilitator also asks a colleague unfamiliar with the branch to follow the confirmation directions from the public entrance. That colleague records each ambiguous turn and checks whether the temporary route agrees with the telephone script. The exercise fails if either route leads to the closed walkway. A correct registration transaction cannot compensate for arrival instructions that prevent the visitor from reaching the promised appointment, so both kinds of evidence remain attached to the same readiness gate.
    """,
    """
    ## Worked interruption exercise

    Consider an invented run with two wording variants assigned equally by household. On the third morning, a monitoring route discovers that variant B's eligibility link redirects to an expired page. The last successful check was the prior evening. The team knows the failure occurred within that interval but cannot identify the exact minute. A proposal to discard only the three hours after detection would leave an unknown number of impaired exposures in the analysis. The exercise asks the analyst to preserve this uncertainty and apply EX-552 instead of selecting an exclusion that makes the result appear most favorable.

    Operations repairs the redirect and confirms the correct destination using synthetic recipients assigned to both variants. That establishes current delivery health. It does not establish that the earlier groups had equivalent access. The experiment owner records a fresh-run decision with new assignment identifiers and preserves the interrupted run as an operational incident. A reader should be able to distinguish the repaired implementation from the evidence available for the interrupted experiment. Combining the two runs without a planned method would conceal the change in exposure conditions and the reason a new assignment was required.

    During review, the team also finds that one variant had more mobile recipients by chance. Random assignment does not guarantee identical composition in every realized sample. The analyst reports the predefined outcome and follows the planned method rather than repeatedly rearranging the groups after seeing the results. A future experiment may stratify assignment if device mix is an important source of variation. That is a design decision for the next run, not permission to redefine this run's groups. The example shows why interpretation, operational recovery, and future design improvements require separate evidence even when they arise in the same meeting.

    The archive includes the interrupted run even though it cannot establish a winner. A future investigator can inspect the failure interval, the assignment specification, and the repair decision without confusing them with the replacement experiment. Removing the unsuccessful run from the library would make the program's history look more decisive than it was. The exercise therefore checks that neutral and interrupted results remain searchable with the same care given to favorable results.
    """,
    """
    A worked custody example begins with a signed snapshot containing an event assigned to the wrong campaign. The source owner supplies the event's original delivery reference and a corrected association. The requester opens a revision against the signed snapshot, records the old and proposed campaign identifiers, and attaches the evidence reference. One campaign loses an accepted event and another gains one, so a library-wide total might remain unchanged. A total-only check would miss the correction. The reviewer verifies the membership change and its effect on both campaign records before approving the revision.

    The downstream register lists a saved answer, a chart extract, and an exported presentation. The answer and chart can be recomputed under the new revision. The presentation is a frozen record of an earlier decision, so its owner retains the original file and adds a notice linking to the later correction. This preserves what the decision makers actually saw. The notice does not imply misconduct or poor analysis; it simply identifies that new evidence became available. If the original event cannot be reconstructed from the retained source, the record states that reproducibility limitation rather than claiming full auditability from a checksum alone.

    In a second request, a manager asks to apply a longer window because the corrected result appears disappointing. That request is routed as a methodology proposal and does not enter the data-correction queue. Its business rationale may be discussed, but it cannot alter the meaning of the signed measurement retroactively without disclosure. The policy's custody controls preserve both the evidence and the distinction between repairing a source fact and changing the question being measured.
    """,
    """
    For a worked exception review, imagine an offer whose standard enrollment cutoff is a Friday. A system outage prevents a defined group from completing enrollment that afternoon. The product owner proposes an extension for that group through the following business day. The exception record identifies how the affected group is determined, the extended cutoff, the unchanged product requirements, and the explanation delivered to those recipients. A general statement that everyone gets more time would exceed the approved scope. The audience rule must therefore represent the outage group without relying on a service agent's recollection.

    The rehearsal includes a recipient affected by the outage, a recipient who enrolled before it, a recipient outside the offer geography, and a record with unknown eligibility. Only the first record receives the approved extension, assuming the unchanged conditions are met. The geographic failure remains a failure. The unknown state remains a review case. The test makes it difficult for an implementation to convert the exception into a universal pass. A reviewer checks the resulting explanation as well as the selected rows, because correct selection with the wrong promise would still fail the intended control.

    When the extension ends, the owner checks the delivery queue and the fulfillment register. Some recipients may have received a valid promise before expiration but will complete enrollment afterward under its terms. Those cases are governed by the approved transition rule, not by an operator deleting the exception from a configuration file. The closing note preserves the exact terms and their applicable population so later service staff can explain the decision consistently without inventing a new interpretation.
    """,
    """
    In the synthetic reconciliation exercise, a person withdraws promotional permission after an audience file is selected but before the partner releases it. New selections immediately exclude the record, yet the already selected file still contains it. The operations owner places that batch on hold and sends a replacement request with the suppression identifier. The partner returns an acknowledgment that the queued predecessor has been removed. The owner compares the replacement checksum and accepted count with the approved selection before releasing the hold. Updating only the master audience table would not have resolved the queue already outside the service.

    A later nightly refresh reads an upstream export created before the withdrawal. The synthetic health record must remain suppressed even though the upstream file describes the earlier state. The state transition ledger establishes which evidence is current. If the refresh overwrites it with the old value, the monitor flags a permission regression rather than reporting a routine audience increase. The analyst records the refresh version and the conflicting effective times so the source of the regression can be reproduced. Merely rerunning the job with a newer input would hide the defect without demonstrating that the control was repaired.

    The reviewer also submits the same withdrawal twice through different intake routes. Both receipts point to one effective transition. The service should not restart the emergency acknowledgment clock, create two independent reinstatement opportunities, or lose the original evidence. This small exercise connects idempotency with suppression custody: transport duplication must not change the meaning of a person's request. The final ledger shows the original receipt, the second receipt, and a single resolved state with its downstream acknowledgments.
    """,
    """
    The following morning, the analyst runs an invented intake exercise with a file labeled final and a file labeled rehearsal. Both have the same row count, and the rehearsal file happens to contain plausible product codes. Only the approved checksum identifies the intended production selection. The team deliberately leaves that checksum out of the partner receipt to test whether the operator will rely on the filename. The correct result is an intake hold under NH-143. A service that accepts the plausible-looking file has failed the exercise even if every subsequent transformation executes without an error.

    After the checksum is supplied, the exercise moves to appointment state. An invented visitor registers, cancels, and registers for another time. The reminder queue must send the current confirmation and suppress the superseded one. The observer records both queue membership and actual synthetic receipts. A total of one reminder is insufficient verification if the remaining reminder contains the canceled time. The test therefore checks identity and content together. This mirrors the broader notebook lesson that matching totals can conceal the wrong members or the wrong promise, especially when several state changes occur between selection and delivery.

    The shift lead uses these exercises in a handoff rehearsal. A colleague who did not prepare the incidents must locate the release condition and the next check from the ledger alone. If the colleague needs an unwritten explanation, the handoff is incomplete. The team improves the evidence links and owner fields rather than adding a long narrative about how busy the shift was. The finished record remains brief enough to operate from, while the supporting artifacts provide the detail needed to investigate an ambiguous result later.
    """,
    """
    On the next review, the product owner explains that the unfamiliar code denotes a migrated legacy product during one specific interval. The mapping is accepted with those effective dates and a source reference. It is not applied to every historical occurrence of the same string. The analyst regenerates the affected product view and preserves the earlier unknown count in the revision record. This makes it possible to distinguish a new enrollment from a newly understood legacy event. The explanation also prevents another analyst from reusing the mapping outside its valid interval simply because the display label now looks familiar.

    The team pairs that repair with a synthetic duplicate-receipt exercise. A request times out after remote acceptance, and a retry creates a second transport log entry with the same business payload. The reconciliation must show one accepted business batch and two attempts. In a separate case, a rejected payload is repaired and receives an approved revision. That revision is genuinely new business content, so it must remain distinguishable from an unchanged retry. Combining these cases into one transport count would obscure both reliability and delivery correctness. The exercise asks the next shift to explain the difference using the ledger evidence.

    The survey owner then reviews the changed answer option with the analysts who requested a trend. They decide to display the waves separately and annotate the wording change. No score is manufactured to bridge the difference. If a future study needs continuity, it can test both wordings in a planned design and measure their relationship. The notebook preserves that proposal as future work rather than describing it as completed calibration. This distinction matters because a plausible measurement repair can sound authoritative even when the evidence needed to support it has not yet been collected.
    """,
    """
    The timestamp owner eventually confirms that the export used a service-center clock rather than any branch's local clock. The analyst retains the supplied explanation and normalizes the affected records using that zone. Events near midnight move to a different reporting date than the earlier guess would have produced. The revision records which records changed eligibility and why. The result illustrates why CH-731 cannot be resolved by choosing the most geographically convenient assumption. The source system's clock behavior is evidence; a branch address is context that may or may not describe that behavior.

    For training, the team creates two invented events with the same visible local time but different offsets. One falls within the documented observation window and the other does not. A third event has no offset and remains unresolved. The analyst must preserve those distinct states through normalization and filtering. Converting the third record with a default offset would make the output look complete while concealing missing information. The exercise checks both accepted identifiers and rejection reasons, so an equal final count cannot hide a mistaken swap between eligible and ineligible events.

    The service coordinator uses the same training session to practice offer-version lookup. An invented caller has an old delivery reference and a new product-information page open. Staff retrieve the terms attached to the reference and explain any uncertainty through the approved route. The current page does not replace the promise actually delivered. The observer records whether staff located evidence before making an assurance. This test connects the notebook's separate topics through a useful operating habit: establish the relevant source version first, then reason about the event or promise under that version.
    """,
    """
    ## Reproduction trace

    The diagnostic harness begins with an approved synthetic payload and a durable original business key. It simulates remote acceptance, then drops the response before the sender stores a receipt. After restart, the sender must query that key and discover the accepted state. The expected ledger contains one accepted batch, the original attempt, the status query, and the recovered receipt. If restart instead creates a fresh business key, the harness records a duplicate-delivery failure even if both HTTP requests received successful responses. This is a business correctness check, not a test of network connectivity alone.

    A second trace simulates a rejection caused by a malformed campaign association. The preparer fixes the association in an approved payload revision. The revised checksum differs from the original, so the system follows DR-906 and links the replacement to its rejected predecessor. A retry route that silently reuses the original key with changed bytes fails the trace. The harness also tests a missing partner status response: the correct state is unknown with an assigned incident owner. Treating unknown as rejected would authorize an unsafe resend; treating it as accepted would conceal an undelivered batch.

    During review, compare the stored evidence with the decision table row that authorized the action. An operator should be able to explain why a retry was allowed without reconstructing the sequence from informal messages. The trace preserves status timestamps, checksums, keys, and revision links using invented data. It does not require copying audience content into the logs. The FAQ's lexical identifiers help find the specific recovery rule, while the surrounding explanation establishes why a plausible quick retry can produce a duplicate. Both are useful evidence for a grounded answer.
    """,
    """
    ## Reproduction trace

    Build a synthetic cohort with one event before the anchor, one exactly at the anchor, one exactly at the endpoint, and one immediately after it. Send the same events in a different arrival order and then delay the endpoint event until a later file. The accepted membership must remain determined by occurrence time and the approved rule. A pipeline that uses file order or arrival date can produce the correct total on one run and a different total on another. The test therefore compares accepted identifiers, rejection reasons, and normalized timestamps rather than only checking an aggregate activation count.

    Next, duplicate the endpoint event with a new transport receipt but the same stable enrollment key. The distinct verified activation count must not increase. Add an unrelated support reopening transition and verify that it does not create another product activation. Finally, submit an authorized timestamp correction that moves the endpoint event outside the window. The accepted set changes under a new revision, while the earlier snapshot remains reproducible. This sequence exercises deduplication, lifecycle state, and correction custody without confusing them with the endpoint rule itself.

    The reviewer asks which failures would be visible from a totals-only dashboard. A duplicated valid event and an omitted valid event can cancel numerically. A shifted timestamp can also move one event out while a different invalid event moves in. A stable total therefore does not prove stable membership or correct eligibility. Retaining synthetic event-level evidence makes these failures observable without exposing private customer records. The case supports teaching lexical retrieval around EF-412 and semantic retrieval around observation maturity; it does not claim that one chunk strategy will recover both topics equally well.
    """,
    """
    ## Reproduction trace

    The synthetic cache exercise starts with a policy source, an indexed collection, and a cited answer saved under the original manifest. An author then changes the policy's recovery gate while keeping its document identifier. The current manifest now contains a different checksum. Opening the saved answer as current must trigger KS-663 before any quality score or answer is presented as fresh. The investigator can still open the historical record under KS-670 and inspect the exact earlier text. The difference between those routes is visible in the corpus identity, not inferred from the answer's writing style.

    A second trace leaves the source bytes unchanged but changes the embedding model. The collection compatibility check rejects vectors built under the previous model identity. Merely updating a configuration label would misrepresent the stored vectors. A third trace changes chunk boundaries while retaining the source and embedding model. Chunk identifiers, citation spans, and retrieval results belong to the boundary configuration that produced them. The test checks that an old chunk result is not silently relabeled with the new strategy. These scenarios distinguish source invalidation from model and algorithm invalidation.

    The final exercise adds development questions and recomputes the evaluation identity. Historical results retain their original case list and denominator. A missing current run produces an unavailable result, not an inherited score with a new title. Reviewers inspect the cases that were actually run and the cases excluded by kind or scope. This keeps demonstration examples useful without pretending they are independent evidence of general quality. The teaching objective is reproducibility of a concrete retrieval comparison and honesty about measurement coverage, including the possibility that a carefully designed example exposes a weakness in the chosen strategy.
    """,
]


def learning_sources():
    """Yield compatible metadata, canonical Markdown bodies, and honest gold cases."""
    for index, (title, shape, heading, question, answer, body) in enumerate(SOURCES, 1):
        document_id = f'GLOBAL-learning-{index:02}'
        metadata = dict(
            campaign_id='GLOBAL', campaign_name=title,
            client_name='Synthetic course library', campaign_type='Shared campaign operations',
            region='ALL', year=2026, period='ALL', document_type='learning_guide',
            document_id=document_id, document_shape=shape,
            description=f'Original fictional {shape.replace("_", " ")} about {title.lower()}; authored for chunk-boundary and evidence retrieval exercises.',
        )
        citation_heading = heading.lower().replace(' ', '-')
        case = dict(
            id=f'dev-{index:02}', question=question, campaign_id=None,
            expected_answer=answer, expected_facts=[answer], expected_sources=[document_id],
            ground_truth_citations=[f'{document_id}#{citation_heading}'],
            split='development', kind='question',
            measurement_provenance={
                'purpose': 'curated development example', 'held_out': False,
                'origin': 'authored alongside synthetic source; exact source sentence is the answer gold',
                'usage': 'implementation and chunking demonstration; not independent quality measurement',
            },
        )
        body = textwrap.dedent(body).strip() + '\n\n' + textwrap.dedent(FIELD_EXERCISES[index - 1]).strip()
        yield metadata, body, case
