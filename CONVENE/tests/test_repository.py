import os
from uuid import uuid4

import pytest


@pytest.fixture
def repository():
    from dotenv import dotenv_values
    from convene.repository import Repository
    dsn=os.getenv('CONVENE_TEST_DATABASE_URL') or dotenv_values('.env').get('CONVENE_TEST_DATABASE_URL')
    if not dsn:
        pytest.skip('Real PostgreSQL integration requires CONVENE_TEST_DATABASE_URL.')
    if not dsn.rsplit('/',1)[-1].startswith('convene_test'):
        pytest.fail('Integration tests require a separate convene_test database.')
    repo=Repository(dsn)
    repo.migrate()
    return repo


def test_event_survives_repository_reopen_and_other_parent_cannot_read(repository):
    from convene.domain import Principal,EventBriefVersion
    from convene.repository import Repository,NotFound
    parent=Principal(authenticated=True)
    event=repository.create_event(parent,EventBriefVersion(occasion='graduation'))
    reopened=Repository(repository.dsn)
    assert reopened.get_event(parent,event.id).brief.occasion=='graduation'
    with pytest.raises(NotFound):
        reopened.get_event(Principal(authenticated=True),event.id)


def test_brief_edit_is_atomic_and_stale_version_cannot_overwrite(repository):
    from convene.domain import Principal,EventBriefVersion
    from convene.repository import Conflict
    parent=Principal(authenticated=True)
    event=repository.create_event(parent,EventBriefVersion(occasion='birthday'))
    revised=repository.revise_event(parent,event.id,{'guest_estimate':120},expected_version=1)
    assert revised.brief.version==2
    with pytest.raises(Conflict):
        repository.revise_event(parent,event.id,{'guest_estimate':30},expected_version=1)
    assert repository.get_event(parent,event.id).brief.total_guests==120


def test_database_row_policy_blocks_cross_owner_even_without_query_filter(repository):
    from convene.domain import Principal,EventBriefVersion
    parent=Principal(authenticated=True)
    other=Principal(authenticated=True)
    event=repository.create_event(parent,EventBriefVersion(occasion='birthday'))
    with repository.transaction(other) as connection:
        assert connection.execute('SELECT * FROM events WHERE id=%s',(event.id,)).fetchone() is None
        assert connection.execute('SELECT * FROM brief_versions WHERE event_id=%s',(event.id,)).fetchone() is None


def test_confirmation_and_new_revision_remain_distinct_after_reload(repository):
    from convene.domain import Principal,EventBriefVersion
    from datetime import date
    parent=Principal(authenticated=True)
    brief=EventBriefVersion(occasion='birthday',guest_estimate=120,services=['venue'],budget=2000,event_date=date(2026,12,6))
    event=repository.create_event(parent,brief)
    confirmed=repository.confirm_event(parent,event.id,expected_version=1)
    assert confirmed.confirmed_version==1
    repository.revise_event(parent,event.id,{'budget':2500},expected_version=1)
    reloaded=repository.get_event(parent,event.id)
    assert reloaded.brief.version==2 and reloaded.confirmed_version is None
