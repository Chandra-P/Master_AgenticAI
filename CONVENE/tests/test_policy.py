from datetime import date,datetime,timedelta,timezone
from uuid import uuid4

import pytest


def fixture_context():
    from convene.domain import Principal,EventRecord,EventBriefVersion,Approval,InquiryPayload
    from convene.policy import payload_digest
    actor=Principal(authenticated=True)
    event=EventRecord(owner_id=actor.id,brief=EventBriefVersion(occasion='birthday',guest_estimate=120,
                     services=['venue'],event_date=date(2026,12,6),budget=2000)).confirm(1)
    payload=InquiryPayload(to=['venue@example.com'],subject='Birthday inquiry',body='Please confirm the date.')
    approval=Approval(actor_id=actor.id,event_id=event.id,brief_version=1,capability='send_inquiry',
                      inquiry_id=uuid4(),provider_id='venue',mailbox_id=uuid4(),payload_digest=payload_digest(payload),
                      expires_at=datetime.now(timezone.utc)+timedelta(hours=1))
    return actor,event,payload,approval


def test_exact_approved_inquiry_and_context_are_required():
    from convene.policy import authorize_action,PolicyDenied
    actor,event,payload,approval=fixture_context()
    authorize_action(actor,event,'send_inquiry',approval=approval,payload=payload,
                     inquiry_id=approval.inquiry_id,provider_id=approval.provider_id,mailbox_id=approval.mailbox_id)
    for changes in ({'to':['different@example.com']},{'body':'Different content'},{'subject':'Changed subject'}):
        with pytest.raises(PolicyDenied):
            authorize_action(actor,event,'send_inquiry',approval=approval,payload=payload.model_copy(update=changes),
                inquiry_id=approval.inquiry_id,provider_id=approval.provider_id,mailbox_id=approval.mailbox_id)


def test_cross_account_research_and_commitments_are_denied():
    from convene.domain import Principal
    from convene.policy import authorize_action,PolicyDenied
    actor,event,payload,approval=fixture_context()
    for action in ('research','send_inquiry','pay','book','accept_contract'):
        with pytest.raises(PolicyDenied):
            authorize_action(Principal(authenticated=True),event,action)
    for action in ('pay','book','accept_contract'):
        with pytest.raises(PolicyDenied):
            authorize_action(actor,event,action)


def test_old_brief_revoked_expired_and_wrong_mailbox_grants_fail():
    from convene.policy import authorize_action,PolicyDenied
    actor,event,payload,approval=fixture_context()
    changed=event.revise({'budget':2500},expected_version=1).confirm(2)
    bad_approvals=[approval.model_copy(update={'revoked_at':datetime.now(timezone.utc)}),
                   approval.model_copy(update={'expires_at':datetime.now(timezone.utc)-timedelta(seconds=1)}),
                   approval.model_copy(update={'mailbox_id':uuid4()})]
    for candidate in bad_approvals:
        with pytest.raises(PolicyDenied):
            authorize_action(actor,event,'send_inquiry',approval=candidate,payload=payload,
                inquiry_id=approval.inquiry_id,provider_id=approval.provider_id,mailbox_id=approval.mailbox_id)
    with pytest.raises(PolicyDenied):
        authorize_action(actor,changed,'send_inquiry',approval=approval,payload=payload,
            inquiry_id=approval.inquiry_id,provider_id=approval.provider_id,mailbox_id=approval.mailbox_id)


def test_followup_cap_is_enforced_even_with_an_active_grant():
    from convene.policy import authorize_action,PolicyDenied
    actor,event,payload,approval=fixture_context()
    grant=approval.model_copy(update={'capability':'followup','payload_digest':None})
    with pytest.raises(PolicyDenied,match='(?i)follow'):
        authorize_action(actor,event,'followup',approval=grant,inquiry_id=approval.inquiry_id,
            provider_id=approval.provider_id,mailbox_id=approval.mailbox_id,followups_sent=3,
            last_sent_at=datetime.now(timezone.utc)-timedelta(days=2))
