from uuid import uuid4

import pytest

from convene.domain import Principal


def admin_for(repository):
    from convene.vendor_directory import DirectoryAdmin
    import os
    from dotenv import dotenv_values
    dsn=os.getenv('CONVENE_TEST_DIRECTORY_ADMIN_URL') or dotenv_values('.env').get('CONVENE_TEST_DIRECTORY_ADMIN_URL')
    return DirectoryAdmin(dsn,operator='test reviewer')


def test_existing_import_is_persisted_idempotent_and_exactly_approved(repository):
    from convene.vendor_directory import DirectoryRepository
    admin=admin_for(repository)
    admin.import_existing();admin.import_existing()
    data=DirectoryRepository(repository.dsn).list_approved()
    south=next(v for v in data['vendors'] if v['id']=='south-san')
    assert south['directory_version']==1
    assert south['approval']['approved_by']=='project-owner (conversation approval)'
    assert south['approval']['approved_on']=='2026-11-01'
    assert south['approval']['approval_id']
    assert south['contact']['phone_e164']=='+12103357275'
    assert len(admin.history('south-san')['decisions'])==1


def test_drafts_require_exact_version_approval_and_suspension_hides_them(repository):
    from convene.vendor_directory import DirectoryRepository
    from convene.repository import Conflict
    admin=admin_for(repository);reader=DirectoryRepository(repository.dsn)
    vendor_id='test-'+uuid4().hex
    body={'id':vendor_id,'name':'Test only provider','kind':'venue','source_url':'https://example.org/test',
          'price':100,'availability':'unconfirmed'}
    try:
        v1=admin.propose(body,reason='Fixture',expected_version=0)
        assert not any(v['id']==vendor_id for v in reader.list_approved()['vendors'])
        admin.approve(vendor_id,v1,reason='Reviewed fixture')
        assert next(v for v in reader.list_approved()['vendors'] if v['id']==vendor_id)['price']==100
        v2=admin.propose({**body,'price':150},reason='Updated published rate',expected_version=1)
        assert next(v for v in reader.list_approved()['vendors'] if v['id']==vendor_id)['price']==100
        with pytest.raises(Conflict):admin.approve(vendor_id,1,reason='Stale review')
        admin.approve(vendor_id,v2,reason='Reviewed new rate')
        saved=next(v for v in reader.list_approved()['vendors'] if v['id']==vendor_id)
        assert saved['price']==150 and saved['directory_version']==2
        assert saved['approval']['approved_by']=='test reviewer'
        admin.suspend(vendor_id,reason='Needs recheck')
        assert not any(v['id']==vendor_id for v in reader.list_approved()['vendors'])
        assert len(admin.history(vendor_id)['versions'])==2
        assert len(admin.history(vendor_id)['decisions'])==3
    finally:
        admin.suspend(vendor_id,reason='Test cleanup')


def test_parent_cannot_write_directory_or_read_drafts(repository):
    from psycopg.errors import InsufficientPrivilege
    from psycopg.types.json import Jsonb
    actor=Principal()
    with pytest.raises(InsufficientPrivilege):
        with repository.transaction(actor) as connection:
            connection.execute("SELECT set_config('convene.directory_admin','true',true)")
            connection.execute('INSERT INTO vendor_records(id) VALUES(%s)',('forged-'+uuid4().hex,))
    with repository.transaction(actor) as connection:
        connection.execute("SELECT set_config('convene.directory_admin','true',true)")
        assert not connection.execute("SELECT id FROM vendor_records WHERE status='draft'").fetchall()


def test_website_credential_cannot_be_used_as_directory_admin(repository):
    from convene.vendor_directory import DirectoryAdmin
    with pytest.raises(PermissionError):
        DirectoryAdmin(repository.dsn,operator='forged').import_existing()
