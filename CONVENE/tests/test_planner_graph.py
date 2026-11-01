from datetime import date
from uuid import uuid4

import pytest

from convene.domain import Principal,EventBriefVersion
from convene.repository import Conflict,NotFound


def ready(repository):
    parent=Principal(authenticated=True)
    event=repository.create_event(parent,EventBriefVersion(occasion='graduation',services=['venue'],
        guest_estimate=40,event_date=date(2026,12,6),budget=2000,time_window='afternoon',priorities='All guests'))
    repository.confirm_event(parent,event.id,expected_version=1)
    return parent,event


def test_six_nodes_are_durable_and_reopen_does_not_repeat_research(repository):
    from convene.planner_graph import PlannerGraph,setup_checkpoints
    setup_checkpoints(repository.dsn)
    actor,event=ready(repository);calls=[]
    graph=PlannerGraph(repository,research=lambda brief:calls.append(brief) or {'options':[],'gaps':['Needs quotes']})
    run_id=graph.start(actor,event.id,expected_version=1)
    result=graph.resume(actor,event.id,run_id,expected_version=1)
    assert result['completed_nodes']==['Requirements','Budget','Vendor','Schedule','Creative','Review']
    assert result['status']=='needs_quotes' and len(calls)==1
    reopened=PlannerGraph(repository,research=lambda _:pytest.fail('Research must not repeat'))
    assert reopened.resume(actor,event.id,run_id,expected_version=1)==result
    assert reopened.read(actor,event.id,run_id)['status']=='needs_quotes'


def test_checkpoint_scope_and_stale_brief_are_enforced(repository):
    from convene.planner_graph import PlannerGraph,setup_checkpoints
    setup_checkpoints(repository.dsn)
    actor,event=ready(repository);graph=PlannerGraph(repository,research=lambda _: {'options':[],'gaps':[]})
    run_id=graph.start(actor,event.id,expected_version=1)
    with pytest.raises(NotFound):graph.read(Principal(authenticated=True),event.id,run_id)
    with pytest.raises(NotFound):graph.read(actor,event.id,uuid4())
    other=repository.create_event(actor)
    with pytest.raises(NotFound):graph.read(actor,other.id,run_id)
    repository.revise_event(actor,event.id,{'budget':2500},expected_version=1)
    with pytest.raises(Conflict):graph.resume(actor,event.id,run_id,expected_version=1)
    with repository.transaction(Principal(authenticated=True)) as connection:
        assert connection.execute('SELECT thread_id FROM checkpoints WHERE thread_id=%s',(str(run_id),)).fetchone() is None
