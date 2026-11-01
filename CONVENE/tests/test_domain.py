from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError


def test_guest_breakdown_never_omits_accompanying_family():
    from convene.domain import EventBriefVersion
    brief=EventBriefVersion(occasion='birthday',children=30,family=90,
                            services=['venue','decoration','food'],event_date=date(2026,12,6),budget=2000)
    assert brief.total_guests==120
    with pytest.raises(ValidationError):
        EventBriefVersion(children=30,family=90,guest_estimate=30)


def test_uncertain_budget_is_distinct_from_zero_and_can_be_acknowledged():
    from convene.domain import EventBriefVersion
    brief=EventBriefVersion(occasion='graduation',guest_estimate=40,event_date=date(2026,12,6),
                            services=['venue'],explicit_unknown={'budget'})
    assert brief.budget is None
    assert brief.confirmation_gaps()==[]
    with pytest.raises(ValidationError):
        EventBriefVersion(budget=0)


def test_incomplete_brief_cannot_be_confirmed():
    from convene.domain import EventRecord,EventBriefVersion
    event=EventRecord(owner_id=uuid4(),brief=EventBriefVersion())
    with pytest.raises(ValueError,match='brief'):
        event.confirm(1)


def test_material_edit_requires_new_confirmation_and_optimistic_version():
    from convene.domain import EventRecord,EventBriefVersion
    event=EventRecord(owner_id=uuid4(),brief=EventBriefVersion(occasion='birthday',guest_estimate=120,
                       services=['venue'],event_date=date(2026,12,6),budget=2000))
    event=event.confirm(1)
    assert event.confirmed_version==1
    changed=event.revise({'guest_estimate':130},expected_version=1)
    assert changed.brief.version==2 and changed.confirmed_version is None
    with pytest.raises(ValueError,match='version'):
        changed.revise({'budget':3000},expected_version=1)


def test_payment_pending_and_unknown_are_not_confirmed_booking():
    from convene.domain import BookingRecord
    event_id=uuid4()
    pending=BookingRecord(event_id=event_id,provider_id='test-provider',payment='pending')
    unknown=BookingRecord(event_id=event_id,provider_id='test-provider')
    assert pending.payment=='pending' and unknown.payment=='unknown'
    assert pending.reservation=='unconfirmed'
    with pytest.raises(ValidationError):
        BookingRecord(event_id=event_id,provider_id='test-provider',reservation='confirmed')
