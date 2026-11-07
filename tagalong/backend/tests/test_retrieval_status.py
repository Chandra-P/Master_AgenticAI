import pytest
from tagalong.core import MemoryRepository, source
from tagalong.retrieval_status import indexing_status


def state_with_sources():
    repo=MemoryRepository()
    repo.transact(lambda s:(source(s,'plan-a','note-a','Note','Old preference',kind='document'),source(s,'plan-b','note-b','Note','Private preference',kind='document')))
    return repo.state


@pytest.mark.parametrize(('job_status','expected'),[
    ('pending','pending'),('running','pending'),('failed','failed'),('done','current'),
])
def test_index_status_counts_only_the_active_plan_current_source_version(job_status,expected):
    state=state_with_sources()
    source_key='plan-a:note-a'
    job=next(job for job in state['jobs'].values() if job['source_key']==source_key)
    job.update(status='done',lease_until=0)
    # A stale completed version must not mask a pending current version.
    source(state,'plan-a','note-a','Note','Updated preference',kind='document')
    current_job=next(job for job in state['jobs'].values() if job['source_key']==source_key and job['version']==2)
    current_job.update(status=job_status,lease_until=9999999999 if job_status=='running' else 0)
    status=indexing_status(state,'plan-a')
    assert status=={'status':expected,'current_sources':1,'indexed_sources':int(expected=='current'),'pending_sources':int(expected=='pending'),'failed_sources':int(expected=='failed')}


def test_empty_plan_index_status_is_current_and_other_plans_are_excluded():
    state=state_with_sources()
    empty=indexing_status(state,'plan-empty')
    assert empty=={'status':'current','current_sources':0,'indexed_sources':0,'pending_sources':0,'failed_sources':0}
    other=indexing_status(state,'plan-b')
    assert other['current_sources']==1 and other['pending_sources']==1
