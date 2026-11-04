"""Owner/event/version-bound LangGraph checkpoints. No messaging tools here."""
from contextlib import contextmanager
from datetime import date,timedelta
from typing import TypedDict
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import StateGraph,START,END

from convene.policy import authorize_action
from convene.repository import Conflict,NotFound


def setup_checkpoints(dsn):
    """Administrative setup only; public requests never create schemas/policies."""
    with psycopg.connect(dsn,autocommit=True,prepare_threshold=0,row_factory=dict_row) as connection:
        connection.execute('SELECT pg_advisory_lock(7421402)')
        try:
            PostgresSaver(connection).setup()
            for table in ('checkpoints','checkpoint_blobs','checkpoint_writes'):
                # Identifiers below are a fixed allowlist, never request data.
                connection.execute(f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY')
                connection.execute(f'ALTER TABLE {table} FORCE ROW LEVEL SECURITY')
                if not connection.execute("SELECT 1 FROM pg_policies WHERE schemaname=current_schema() AND tablename=%s AND policyname='checkpoint_owner'",(table,)).fetchone():
                    connection.execute(f'CREATE POLICY checkpoint_owner ON {table} USING '
                        f'(EXISTS (SELECT 1 FROM planner_runs r WHERE r.id::text={table}.thread_id))')
        finally:connection.execute('SELECT pg_advisory_unlock(7421402)')


class PlannerState(TypedDict,total=False):
    brief:dict
    completed_nodes:list[str]
    budget:dict
    research:dict
    schedule:dict
    creative:dict
    status:str


class PlannerGraph:
    def __init__(self,repository,*,research,action='research'):
        if action not in ('research','compare_catalog'):raise ValueError('Unsupported planner capability.')
        self.repository=repository
        self.research=research
        self.action=action

    def start(self,actor,event_id,*,expected_version):
        with self.repository.transaction(actor) as connection:
            event=self.repository._load(connection,actor,event_id,lock=True)
            if event.brief.version!=expected_version:raise Conflict('Stale brief version.')
            authorize_action(actor,event,self.action)
            run_id=uuid4()
            connection.execute('INSERT INTO planner_runs(id,event_id,brief_version,action) VALUES(%s,%s,%s,%s)',
                               (run_id,event.id,expected_version,self.action))
            self.repository._audit(connection,actor,event.id,'planner_run_started',{'run_id':str(run_id),'version':expected_version})
        return run_id

    def _authorize_run(self,actor,event_id,run_id,*,expected_version=None):
        with self.repository.transaction(actor) as connection:
            event=self.repository._load(connection,actor,event_id)
            row=connection.execute('SELECT brief_version,action FROM planner_runs WHERE id=%s AND event_id=%s',
                                   (run_id,event_id)).fetchone()
            if not row:raise NotFound('Planner run not found.')
            if row['action']!=self.action:raise NotFound('Planner run not found for this capability.')
            if expected_version is not None:
                if row['brief_version']!=expected_version or event.brief.version!=expected_version:
                    raise Conflict('This run belongs to an older brief; start a new run.')
                authorize_action(actor,event,self.action)
            return event

    @contextmanager
    def _graph(self,actor,event_id,run_id,version):
        # Dedicated session: the owner setting cannot bleed into another request.
        with psycopg.connect(self.repository.dsn,autocommit=True,prepare_threshold=0,row_factory=dict_row) as connection:
            connection.execute("SELECT set_config('convene.actor_id',%s,false)",(str(actor.id),))
            def checked(node,work):
                def execute(state):
                    self._authorize_run(actor,event_id,run_id,expected_version=version)
                    return {**work(state),'completed_nodes':state.get('completed_nodes',[])+[node]}
                return execute
            graph=StateGraph(PlannerState)
            graph.add_node('Requirements',checked('Requirements',lambda s:{}))
            graph.add_node('Budget',checked('Budget',lambda s:{'budget':{
                'ceiling':s['brief']['budget'],'estimate':None,'status':'needs_published_rates_or_quotes'}}))
            graph.add_node('Vendor',checked('Vendor',lambda s:{'research':self.research(s['brief'])}))
            def schedule(state):
                value=state['brief']['event_date']
                if not value:return {'schedule':{'status':'date_needed','milestones':[]}}
                event_date=date.fromisoformat(value)
                # Dates are planning reminders, not claims of a reservation.
                return {'schedule':{'status':'proposed','milestones':[
                    {'kind':'readiness','date':(event_date-timedelta(days=30)).isoformat()},
                    {'kind':'reconfirmation','date':(event_date-timedelta(days=7)).isoformat()}]}}
            graph.add_node('Schedule',checked('Schedule',schedule))
            graph.add_node('Creative',checked('Creative',lambda s:{'creative':{
                'theme':s['brief']['theme'],'professional_quote_required':'decoration' in s['brief']['services']}}))
            graph.add_node('Review',checked('Review',lambda s:{'status':'needs_quotes' if not s['research'].get('options')
                or s['research'].get('gaps') else 'ready_for_parent_review'}))
            nodes=['Requirements','Budget','Vendor','Schedule','Creative','Review']
            graph.add_edge(START,nodes[0])
            for left,right in zip(nodes,nodes[1:]):graph.add_edge(left,right)
            graph.add_edge(nodes[-1],END)
            yield graph.compile(checkpointer=PostgresSaver(connection))

    def resume(self,actor,event_id,run_id,*,expected_version):
        event=self._authorize_run(actor,event_id,run_id,expected_version=expected_version)
        # Serialize retries for this run across processes, including paid research.
        with self.repository.transaction(actor) as lock_connection:
            lock_connection.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(str(run_id),))
            with self._graph(actor,event_id,run_id,expected_version) as graph:
                config={'configurable':{'thread_id':str(run_id)}}
                snapshot=graph.get_state(config)
                if snapshot.values and not snapshot.next:return snapshot.values
                initial={'brief':event.brief.model_dump(mode='json'),'completed_nodes':[]} if not snapshot.values else None
                result=graph.invoke(initial,config)
                self._authorize_run(actor,event_id,run_id,expected_version=expected_version)
                return result

    def read(self,actor,event_id,run_id):
        event=self._authorize_run(actor,event_id,run_id)
        with self._graph(actor,event_id,run_id,event.brief.version) as graph:
            return graph.get_state({'configurable':{'thread_id':str(run_id)}}).values
