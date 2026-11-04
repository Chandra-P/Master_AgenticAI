"""Deterministic fictional evidence pack; no model calls or benchmark-derived answers."""
import textwrap

# title, shape, status, heading, development question, exact fact, source body
SOURCES = [
('Canary campaign measurement dictionary', 'playbook', 'active', 'Balance meaning',
 'For fictional canary CL-640, what does opening balance measure?',
 'For CL-640, opening balance is the posted balance at account opening; it is not current balance, net new deposits, or revenue.',
 """
 ## Scope and custody
 This dictionary applies only to the fictional canary campaign CL-640. It defines fields before any campaign results exist. The exercise contains invented aggregate examples, not a customer extract. The measurement owner approves definitions, while the source custodian records which export implements them. A field name in a dashboard is not the authority for its meaning. When an export changes a definition, retain the old definition and create a versioned mapping rather than silently changing historical values.

 ## Balance meaning
 For CL-640, opening balance is the posted balance at account opening; it is not current balance, net new deposits, or revenue.
 A later withdrawal changes current balance but does not rewrite the opening observation. An internal transfer can contribute to opening balance without representing new money entering the institution. A campaign analyst cannot infer transfer treatment from a positive aggregate. If an analysis requires net new deposits, the owner must specify eligible flows and supply transfer evidence separately. This dictionary does not supply that evidence.

 ## Aggregate rehearsal
 | Field | Invented value | Unit | Interpretation |
 |---|---:|---|---|
 | Verified activations | 80 | distinct enrolled accounts | Completed verification, not clicks |
 | Direct mail activations | 48 | distinct enrolled accounts | Observational attribution |
 | Display activations | 32 | distinct enrolled accounts | Observational attribution |
 | Opening balance | 160000 | USD | Posted at opening |
 | Net new deposits | unavailable | USD | Transfer evidence absent |
 The channel counts reconcile to the total in this rehearsal. They do not establish that either channel caused an activation. Exposures use different units across channels, so a raw response-rate comparison also requires compatible denominators. Preserve the unit and maturity state next to any exported count.

 ## Missing values and zero
 An unavailable measurement must remain unavailable, rather than becoming zero during export. Zero means the owner measured the defined quantity and observed none. An empty cell can instead indicate missing evidence, a pending refresh, or a field outside the source scope. The analyst records the reason with the value. A formatting rule that replaces blanks with zeros would erase that distinction and can turn an honest limitation into an apparently precise result.

 ## Change control
 The rehearsal numbers are immutable teaching inputs. Correct a transcription error through a new revision linked to the original dictionary, with the changed field and reason stated. Do not change the rehearsal to make a model answer look better. A future measurement design may use different units, but it needs a new identifier and its own examples. The dictionary is one source of evidence; the separate timing policy determines whether an event is mature enough to enter a campaign snapshot.
 """),
('Canary attribution time and maturity policy', 'cohesive_policy', 'active', 'Timing policy',
 'Under CL-640 timing policy, does an in-window late-arriving observation remain eligible?',
 'Under CL-640 timing policy, eligibility follows event occurrence time; a late-arriving in-window observation enters a reviewed revision, not an overwritten signed snapshot.',
 """
 ## Timing policy
 This cohesive policy governs the fictional CL-640 rehearsal and uses UTC for all example timestamps. The direct-mail anchor is the recorded mail drop; the display anchor is the recorded exposure. Their windows remain sixty and thirty days respectively. An analyst must keep anchor time, occurrence time, arrival time, and snapshot cutoff separate. An observation arriving today might describe an earlier eligible event, while a promptly delivered event can still fall outside the window. Neither transport speed nor a convenient file date replaces occurrence evidence.

 Under CL-640 timing policy, eligibility follows event occurrence time; a late-arriving in-window observation enters a reviewed revision, not an overwritten signed snapshot.
 The reviewer checks the original anchor and rule version before accepting a correction. A new arrival does not justify recalculating every historical cohort with a different rule. The revision note lists included and excluded observations separately, identifies the prior snapshot, and explains what changed. Consumers can then decide whether an earlier answer is stale instead of mistaking an amended total for an unexplained fluctuation.

 Consider three invented events anchored to a fictional display exposure at midnight on July first. One occurs within the thirty-day window and arrives after the first snapshot; it can be reviewed as a correction. Another occurs before the exposure and remains excluded even if its file arrives later. A third occurs beyond the thirty-day limit and remains excluded regardless of when an analyst notices it. These examples explain rule application, not measured campaign performance, and they do not extend a window to accommodate a desired result.

 A source timestamp lacking an offset is unresolved evidence. The custodian must recover its documented time zone or keep the observation out of time-sensitive conclusions. Guessing a zone from the branch address is unsafe because collection systems can record a shared server zone. A conversion near midnight can change calendar date after normalization. Preserve the original timestamp alongside the normalized instant so a reviewer can reproduce the decision without relying on a screenshot of the analyst's workstation clock.

 A cohort is mature only after its applicable window has elapsed at the snapshot cutoff. A partially observed cohort may be described as provisional, with its cutoff and remaining observation time. It must not be ranked against a mature cohort as though both have equal follow-up. Event eligibility, cohort maturity, and data arrival completeness are separate checks. Passing one does not imply the others passed. A signed snapshot records all three states and its source checksum.

 The policy supplies no financial return, randomized assignment, or customer-level transfer evidence. It therefore cannot answer a question about causal lift, profit, or net new deposits. The measurement dictionary defines the balance field, and the release policy defines approval roles. A complete answer to a question spanning those topics must cite the relevant companion source rather than inventing a broader rule from this timing document alone.
 """),
('Canary release policy revision one archive', 'cohesive_policy', 'superseded', 'Archived release rule',
 'Is revision one the current approval rule for CL-640 releases?',
 'Revision one is superseded for CL-640 releases on or after 2026-10-01; use revision two for those releases.',
 """
 ## Archived release rule
 This document preserves revision one of the fictional CL-640 release policy as historical evidence. Its status is superseded, and retaining it does not authorize current release decisions. Revision one is superseded for CL-640 releases on or after 2026-10-01; use revision two for those releases. The relevant date is the release decision date, not the time a search index happened to ingest this file. A copied excerpt without this status notice is incomplete evidence for a current-policy question.

 Under revision one, a release controller could approve the rehearsal batch after checking its checksum and completed preparation record. That historical arrangement is recorded to explain earlier approvals. It does not waive the independent review introduced by revision two. An audit of a September rehearsal should use the rule that applied then, while a new October release should use the active version. The document title alone cannot establish which version governs a specific decision.

 The archived rule required the controller to compare the prepared batch identifier, row count, destination, and scheduled release time with the approved rehearsal record. A receipt showing only a successful upload was insufficient to prove that the partner accepted the intended business batch. The controller retained the original evidence even when a later correction was necessary. This distinction between transporting a file and accepting a batch remains relevant, but the approval roles have changed in the newer policy.

 The supersession record states why the owner changed the rule: a rehearsal showed that the preparer and controller could share the same mistaken interpretation of an unresolved exception. The exercise found a missing challenge step, not a measured loss or a real customer incident. Revision two introduces independent measurement review before release. The owner did not retroactively declare every earlier rehearsal invalid; each historical decision remains linked to its actual evidence and governing version.

 Retrieval systems should preserve the archive because historical questions are legitimate. Deleting every old policy would make it impossible to explain what a September controller was authorized to do. At the same time, a current-policy answer must not blend the archived one-person approval route with the newer two-role route. An analyst resolves this by checking scope, effective date, status, and explicit supersession, rather than selecting whichever isolated sentence looks easiest to quote.

 A source refresh must keep this document's identifier and archived status stable. If an editor discovers a transcription error in the archive, the correction receives a new content checksum and a note explaining the change; the effective policy date does not silently move. The current release source and the partner receipt protocol provide the operational rules for new decisions. This archive supplies historical context and version-precedence evidence only.
 """),
('Canary release policy revision two', 'playbook', 'active', 'Current approval gate',
 'Who must approve a current CL-640 release under revision two?',
 'For CL-640 releases on or after 2026-10-01, both the release controller and an independent measurement reviewer must approve the same batch checksum.',
 """
 ## Effective scope
 Revision two is active for fictional CL-640 release decisions on or after October first, 2026. It supersedes revision one for that scope while preserving the archive for historical questions. This policy concerns the canary release gate; it does not redefine the consent-recovery gate in another teaching source. A caller must identify the batch and applicable decision date before treating a retrieved approval sentence as the governing rule.

 ## Current approval gate
 For CL-640 releases on or after 2026-10-01, both the release controller and an independent measurement reviewer must approve the same batch checksum.
 The measurement reviewer must not have prepared the release file. Their approval covers measurement definitions, attribution maturity, unresolved exclusions, and consistency with the approved rehearsal. The controller covers destination, schedule, payload identity, and operational readiness. Two signatures on different payloads do not satisfy the gate. Both approvals must identify the same checksum and business batch identifier.

 ## Exception handling
 An unresolved checksum or definition discrepancy keeps the release on hold. A commercial deadline does not convert uncertainty into approval. The owner can cancel or reschedule a batch, but cannot mark a missing review as completed. If a reviewer discovers that a correction changes the payload, the controller obtains approvals for the replacement checksum. The old signoff remains evidence for the old artifact and is not silently attached to the replacement.

 ## Partner receipt boundary
 Passing the approval gate permits the authorized transmission; it does not prove that a partner accepted it. The separate receipt protocol governs accepted, rejected, and unknown outcomes. A timeout after an accepted transmission is a status-recovery problem, not permission to create a fresh business delivery. The controller keeps approval evidence and partner status evidence together while recognizing that they establish different facts.

 ## Handoff package
 The next shift receives the active revision identifier, batch checksum, two review decisions, transmission attempt identifiers, and last verified partner status. It also receives unresolved limitations in plain language. A handoff that says only ready can conceal a completed preparation step with an unfinished approval or receipt step. An analyst should be able to trace a current answer to the exact evidence state without needing access to personal recipient records.

 ## Revalidation after change
 A changed destination, payload, or material definition requires a new readiness check. A corrected spelling in an internal note does not necessarily change the payload; record what changed instead of treating every edit as the same event. The controller documents the distinction and obtains review when uncertain. This is a fictional operational policy designed to demonstrate scoped version precedence and cross-document retrieval, not a claim about real financial regulation or a course evaluation result.
 """),
('Canary launch preparation checklist', 'playbook', 'active', 'Payload identity',
 'Can the CL-640 launch checklist accept a payload without a checksum?',
 'The CL-640 checklist keeps a payload without a checksum on hold until the source custodian supplies a reproducible checksum.',
 """
 ## Preparation scope
 This checklist governs preparation of fictional CL-640 teaching batches before release approval. The example contains no customer addresses or real delivery records. Preparation, approval, transmission, and confirmed acceptance are different states. Completing this checklist means the preparation evidence is ready for review; it is not a substitute for the active release policy or the partner receipt protocol.

 ## Payload identity
 The CL-640 checklist keeps a payload without a checksum on hold until the source custodian supplies a reproducible checksum.
 A filename alone is insufficient because two different payloads can share a name. The custodian computes the checksum from the frozen artifact that reviewers will inspect. If line endings or export settings change that artifact, the record identifies the resulting checksum rather than assuming the display name preserves identity. Keep an original read-only copy and a separately identified correction copy.

 ## Audience and exclusions
 The preparer checks that suppression evidence applies to the actual queued population and effective time. An old approval for an earlier population does not establish eligibility for newly added rows. The checklist records excluded counts without copying personal details into the shared handoff. If aggregate counts do not reconcile, the custodian provides an approved masked sample for investigation through the access procedure. A convenient unrestricted export is not an acceptable substitute.

 ## Measurement attachment
 Attach the measurement dictionary version and timing-policy version used by the rehearsal. The attachment states whether balances are recorded at opening, whether the observation window is complete, and which values remain unavailable. Avoid a generic label such as campaign success when the source only measures activations. A release decision needs a reproducible definition and evidence state, not an optimistic summary of a chart.

 ## Dry run
 The internal dry run uses invented rows representing an eligible record, a suppressed record, a duplicate, and an unresolved exception. Confirm the intended disposition of each row. A system that uploads every test row successfully has not passed the suppression exercise. Save the synthetic inputs, expected dispositions, observed dispositions, and tool version so a later reviewer can reproduce the check after an exporter changes.

 ## Transfer to reviewers
 Send the frozen payload identity and preparation record to the roles named in the current release policy. Keep review status separate from preparation status. A late reviewer can postpone release without invalidating the completed dry run, while a changed payload can require repeating parts of preparation. The controller records which checks were reused and why. The partner receipt protocol applies only after an authorized transmission; it cannot repair missing preparation evidence before release.
 """),
('Canary partner receipt troubleshooting protocol', 'troubleshooting', 'active', 'Unknown receipt status',
 'For CL-640 receipt incident RP-664, should an accepted batch be resent after a receipt timeout?',
 'For RP-664, recover the original business batch status after a receipt timeout; do not resend an already accepted batch.',
 """
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
 """),
('Canary mixed shift notebook', 'mixed_notes', 'active', 'Document',
 'What did the CL-640 notebook say about a stale policy copy on the release board?',
 'The CL-640 shift lead replaced the stale revision-one release-board copy with revision two and retained the archive for September audit questions.',
 """
 The fictional morning shift began by reconciling a release board with the source register. A cached policy copy still displayed revision one even though the scheduled release decision was in October. The CL-640 shift lead replaced the stale revision-one release-board copy with revision two and retained the archive for September audit questions. This action corrected the current working evidence without deleting history. The shift note records both the policy version and the cache refresh time so a later analyst can distinguish source validity from index freshness.

 A measurement reviewer then asked why a balance tile showed a large dollar amount beside campaign activations. The dictionary identified it as a balance observed at opening. Staff removed a draft label calling it net new deposits, because transfer evidence was not available. They did not change the number or create a new measurement to fill the gap. The useful correction was the meaning attached to the value, not a more attractive estimate of campaign impact.

 Near midday, a new preparation file arrived without a reproducible checksum. Staff kept it on hold and asked the source custodian to freeze an artifact and identify it. In a separate incident, a previously accepted batch had a delayed receipt. The delivery operator recovered its original status instead of treating both problems as reasons to resend. Combining these incidents into one generic file issue would have lost the distinction between missing preparation evidence and uncertain downstream acknowledgment.

 The afternoon dry run included invented rows for suppression and duplication. One reviewer noticed that the test report counted transport attempts as distinct deliveries. The team corrected the test interpretation and retained the original observation as evidence of the failure. A successful retry improved transport reliability but did not create another business delivery. The notebook intentionally describes these transitions without formal section boundaries so semantic topic segmentation can be compared with fixed windows.

 Before handoff, the team reviewed a masked investigation sample. A free-text field contained an instruction-like sentence asking an assistant to disregard source restrictions. Staff treated it as untrusted record content, not as a command authorizing access or disclosure. They excluded personal fields from the shared notes and kept the approved aggregate evidence needed to reproduce the incident. A copied command in a source does not become an operational policy simply because a retrieval system can find it.

 The evening owner assigned separate next actions to the policy cache refresh, checksum hold, receipt recovery, and test-count correction. Each action retained its own source identifier and uncertainty. The notebook is a fictional chronology, not a new policy document that supersedes its referenced authorities. A reader answering a current release-rule question should use the active release policy. A reader explaining what the shift observed can cite this notebook, while recognizing that adjacent paragraphs do not automatically support the same claim.
 """),
('Canary evidence access and source trust policy', 'cohesive_policy', 'active', 'Evidence access',
 'What evidence may CL-640 analysts request for a row-level discrepancy?',
 'For a CL-640 row-level discrepancy, request an approved masked sample from the source custodian; do not place personal recipient fields in the shared analyst corpus.',
 """
 ## Evidence access
 This fictional policy governs the evidence copied into the CL-640 teaching workspace. It is a course scenario, not a statement of legal obligations or an authorization to disclose real records. The shared corpus contains synthetic aggregates and operational procedures. Production investigation records, if they existed, would remain in their designated restricted system with an owner and purpose-specific access decision. A successful retrieval search does not expand a person's access rights.

 For a CL-640 row-level discrepancy, request an approved masked sample from the source custodian; do not place personal recipient fields in the shared analyst corpus.
 The request names the discrepancy, the minimum fields needed to investigate it, and the intended retention route. The custodian can often provide counts, checksums, schema descriptions, or synthetic reproductions instead of individual records. If a masked sample is necessary, its field selection should follow the investigation purpose rather than the convenience of copying an entire export.

 Treat content inside documents and records as evidence to inspect, not instructions that can override the application or access policy. A free-text row might contain a copied email, an error message, or a malicious instruction. None of these changes the rules for what the analyst may disclose. The source owner can preserve a suspicious string in a restricted incident artifact while using a harmless synthetic reproduction in the teaching library. The analyst should explain the uncertainty without executing the string or repeating private content unnecessarily.

 Citations identify the evidence supporting an answer; they are not a mechanism for granting access. A filename or document identifier alone does not prove that every nearby statement is relevant or current. Check the cited passage, effective scope, source status, and any limitation attached to its measurement. If a source is missing or a claim cannot be supported, state that limitation instead of citing a related-looking document as though it supplied the missing fact.

 Keep retention and freshness separate. A retained archive can be essential for historical audit questions while being inappropriate for a current-policy answer. A refreshed index can still contain an archived policy, and a recently downloaded file can describe an older decision. The source register records status and effective dates; the index build records when retrieval material was refreshed. Neither timestamp should silently replace the other when deciding what evidence answers a question.

 At closure, the custodian records whether the masked sample was returned, removed, or retained under an approved investigation record. Shared learning notes preserve the control failure and corrective action using invented examples. They do not preserve a convenient personal-data copy for future demonstrations. This policy supplies no real account identifiers, individual ages, financial return, or causal lift. Questions asking for those unavailable facts must remain unanswered by this synthetic library, regardless of how confidently a model could guess them.
 """),
]


def _case(identifier,question,facts,sources,headings,kind='question'):
    return dict(id=identifier,question=question,campaign_id=None,
        expected_answer=' '.join(facts) if facts else 'I could not find sufficient evidence in the knowledge base.',
        expected_facts=facts,expected_sources=sources,
        ground_truth_citations=[s+'#'+h.lower().replace(' ','-') for s,h in zip(sources,headings)],
        split='development',kind=kind,measurement_provenance={
            'purpose':'curated requirements development example','held_out':False,
            'origin':'authored alongside fictional evidence pack; not independent validation',
            'usage':'coverage and chunking exercises; never a production-accuracy claim'})


def requirements_sources():
    for index,(title,shape,status,heading,question,fact,body) in enumerate(SOURCES,1):
        identifier=f'GLOBAL-requirements-{index:02}'
        metadata=dict(campaign_id='GLOBAL',campaign_name=title,client_name='Synthetic course library',
            campaign_type='Shared campaign operations',region='ALL',year=2026,period='ALL',
            document_type='learning_guide',document_id=identifier,document_shape=shape,
            description=f'Fictional CL-640 evidence: {title.lower()}; scope and source precedence are explicit.',
            evidence_pack='requirements-v1',source_status=status,
            source_version='1' if index==3 else '2' if index==4 else '1',
            effective_date='2026-09-01' if index==3 else '2026-10-01')
        yield metadata,textwrap.dedent(body).strip(),_case(f'dev-req-{index:02}',question,[fact],[identifier],[heading])


def requirements_cross_cases():
    def source(n):return f'GLOBAL-requirements-{n:02}'
    return [
        _case('dev-req-multi-01','For CL-640, what does opening balance mean and how is an in-window late-arriving event handled?',
            [SOURCES[0][5],SOURCES[1][5]],[source(1),source(2)],['Balance meaning','Timing policy']),
        _case('dev-req-multi-02','Who approves a current CL-640 release, and who reconciles a partner status checksum mismatch before further transmission?',
            [SOURCES[3][5],'The delivery owner and source custodian reconcile the mismatch before any further transmission.'],[source(4),source(6)],['Current approval gate','Exception and retry']),
        _case('dev-req-multi-03','How is a missing CL-640 payload checksum handled, and what must an investigation sample request name?',
            [SOURCES[4][5],'The request names the discrepancy, the minimum fields needed to investigate it, and the intended retention route.'],[source(5),source(8)],['Payload identity','Evidence access']),
        _case('dev-req-unsupported-01','What is the real account identifier of the first CL-640 customer?',[],[],[],kind='unsupported'),
        _case('dev-req-unsupported-02','What randomized causal lift did the CL-640 rehearsal measure?',[],[],[],kind='unsupported'),
    ]
