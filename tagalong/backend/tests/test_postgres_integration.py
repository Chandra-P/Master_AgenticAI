"""Opt-in isolated Supabase/Postgres integration. Every inserted row is rolled back."""
import os
import uuid
from contextlib import contextmanager
import pytest
import psycopg
from tagalong.core import Actor, create, update, view
from tagalong.models import Create
from tagalong.repository import PostgresRepository

TEST_URL = os.getenv('TAGALONG_TEST_DATABASE_URL')
pytestmark = pytest.mark.skipif(not TEST_URL, reason='Dedicated migrated Supabase test database not configured')


class ExistingConnection:
    def __init__(self, connection): self.connection_object=connection
    @contextmanager
    def connection(self): yield self.connection_object


class RollbackTest(Exception): pass


def test_real_projection_transactions_and_rls():
    # Use only a dedicated disposable Supabase database with the migration applied.
    # No fallback to DATABASE_URL is allowed, and no live plans are overwritten.
    with psycopg.connect(TEST_URL, connect_timeout=10) as c:
        try:
            with c.transaction():
                state=c.execute('SELECT state FROM public.tagalong_state WHERE id=1 FOR UPDATE').fetchone()[0]
                if state['plans'] or state['members']:
                    pytest.skip('Integration database must contain no plans or memberships')
                owner_id=str(uuid.uuid4()); stranger_id=str(uuid.uuid4())
                c.execute('INSERT INTO auth.users(id,email) VALUES(%s,%s),(%s,%s)',(owner_id,'tagalong-owner@example.test',stranger_id,'tagalong-stranger@example.test'))
                repo=PostgresRepository.__new__(PostgresRepository); repo.pool=ExistingConnection(c)
                owner=Actor(owner_id,'tagalong-owner@example.test','test-owner')
                plan=repo.transact(lambda s:create(s,owner,Create(kind='trip',title='Database test',start='2026-12-04',end='2026-12-06')))
                pid=plan['id']
                assert c.execute('SELECT revision FROM public.tagalong_plans WHERE id=%s',(pid,)).fetchone()==(1,)
                assert c.execute('SELECT user_id::text FROM public.tagalong_memberships WHERE plan_id=%s',(pid,)).fetchone()==(owner_id,)
                plan['budget']=321
                saved=repo.transact(lambda s:update(s,owner,pid,plan,1))
                assert saved['revision']==2
                assert c.execute('SELECT revision FROM public.tagalong_revisions WHERE plan_id=%s',(pid,)).fetchone()==(2,)
                c.execute('SET LOCAL ROLE authenticated')
                c.execute("SELECT set_config('request.jwt.claim.sub',%s,true)",(owner_id,))
                assert c.execute('SELECT count(*) FROM public.tagalong_revisions WHERE plan_id=%s',(pid,)).fetchone()==(1,)
                c.execute("SELECT set_config('request.jwt.claim.sub',%s,true)",(stranger_id,))
                assert c.execute('SELECT count(*) FROM public.tagalong_revisions WHERE plan_id=%s',(pid,)).fetchone()==(0,)
                with pytest.raises(psycopg.errors.InsufficientPrivilege):
                    with c.transaction(): c.execute('SELECT state FROM public.tagalong_state')
                c.execute('RESET ROLE')
                raise RollbackTest()
        except RollbackTest:
            pass
