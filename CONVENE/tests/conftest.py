import os
import pytest


@pytest.fixture
def repository():
    from dotenv import dotenv_values
    from convene.repository import Repository
    dsn=os.getenv('CONVENE_TEST_DATABASE_URL') or dotenv_values('.env').get('CONVENE_TEST_DATABASE_URL')
    if not dsn:pytest.skip('Real PostgreSQL integration requires CONVENE_TEST_DATABASE_URL.')
    if not dsn.rsplit('/',1)[-1].startswith('convene_test'):pytest.fail('Separate test database required.')
    repo=Repository(dsn);repo.migrate()
    from convene.vendor_directory import DirectoryAdmin
    admin_dsn=os.getenv('CONVENE_TEST_DIRECTORY_ADMIN_URL') or dotenv_values('.env').get('CONVENE_TEST_DIRECTORY_ADMIN_URL')
    DirectoryAdmin(admin_dsn,operator='test fixture import').import_existing()
    return repo
