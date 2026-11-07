import copy
from contextlib import contextmanager
import pytest
from tagalong.repository import PostgresRepository
from tagalong.core import MemoryRepository

class Connection:
    def __init__(self,state): self.state=state; self.calls=[]
    @contextmanager
    def transaction(self): yield self
    def execute(self,sql,params=None): self.calls.append((sql,params)); return self
    def fetchone(self): return (copy.deepcopy(self.state),)
class Pool:
    def __init__(self,state): self.c=Connection(state)
    @contextmanager
    def connection(self): yield self.c

def repository(state):
    r=PostgresRepository.__new__(PostgresRepository); r.pool=Pool(state); return r

def test_read_only_transactions_do_not_write():
    r=repository(MemoryRepository().state)
    assert r.transact(lambda s:len(s['plans']))==0
    assert len(r.pool.c.calls)==1
    assert r.pool.c.calls[0][0].startswith('SELECT')

def test_job_change_only_updates_changed_projection():
    state=MemoryRepository().state
    state['jobs']['job']={'id':'job','source_key':'p:source','status':'pending','attempts':0,'lease_until':0}
    state['plans']['p']={'id':'p','owner_id':'u','revision':1}
    state['members']['p']=['u']
    r=repository(state)
    r.transact(lambda s:s['jobs']['job'].update(status='running',attempts=1))
    writes=[sql for sql,_ in r.pool.c.calls if not sql.startswith('SELECT')]
    assert len(writes)==2
    assert any('tagalong_ingestion_jobs' in x for x in writes)
    assert not any('tagalong_memberships' in x or 'tagalong_plans' in x or 'tagalong_revisions' in x for x in writes)

def test_membership_removal_is_narrow():
    state=MemoryRepository().state; state['members']['plan']=['alice','bob']
    r=repository(state)
    r.transact(lambda s:s['members']['plan'].remove('bob'))
    deletes=[(sql,args) for sql,args in r.pool.c.calls if sql.startswith('DELETE')]
    assert deletes==[('DELETE FROM public.tagalong_memberships WHERE plan_id=%s AND user_id=%s',('plan','bob'))]


def test_owner_transfer_updates_normalized_owner_column():
    state=MemoryRepository().state
    state['plans']['p']={'id':'p','owner_id':'alice','revision':1}
    state['members']['p']=['alice','bob']
    r=repository(state)
    r.transact(lambda s:s['plans']['p'].update(owner_id='bob',revision=2))
    writes=[(sql,args) for sql,args in r.pool.c.calls if 'INSERT INTO public.tagalong_plans' in sql]
    assert len(writes)==1
    assert 'owner_id=EXCLUDED.owner_id' in writes[0][0]
    assert writes[0][1][1]=='bob'


def test_coordination_change_updates_only_its_projection():
    state=MemoryRepository().state;state['plans']['p']={'id':'p','owner_id':'alice','revision':1};state['members']['p']=['alice'];state['plan_activity']={'p':'2026-11-05T00:00:00+00:00'}
    r=repository(state)
    r.transact(lambda s:s.setdefault('coordination',{}).update(p={'plan_revision':1,'status':'ACTIVE','health':50,'summary':'Current facts','last_activity_at':'2026-11-05T00:00:00+00:00'}))
    writes=[sql for sql,_ in r.pool.c.calls if not sql.startswith('SELECT')]
    assert len(writes)==2
    assert any('tagalong_coordination' in sql for sql in writes)
    assert not any('INSERT INTO public.tagalong_plans' in sql for sql in writes)


def test_group_roster_persists_in_existing_state_without_plan_projection_changes():
    from tagalong.core import Actor
    from tagalong.groups import GroupDraft, save_group
    from tests.test_groups import body
    r=repository(MemoryRepository().state)
    saved=r.transact(lambda s:save_group(s,Actor('alice','alice@example.test','alice','Alice'),GroupDraft.model_validate(body())))
    writes=[(sql,args) for sql,args in r.pool.c.calls if not sql.startswith('SELECT')]
    assert len(writes)==1 and writes[0][0].startswith('UPDATE public.tagalong_state')
    state=writes[0][1][0].obj
    assert state['groups'][saved['id']]==saved
    assert state['members']=={} and state['plans']=={}
    assert 'private@example.test' not in str(state['group_events'])
