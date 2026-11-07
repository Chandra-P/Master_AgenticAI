"""Transactional persistence with narrow normalized projection updates."""
import copy
from psycopg import Error
from psycopg_pool import ConnectionPool, PoolTimeout
from psycopg.types.json import Jsonb
from .core import fail


class PostgresRepository:
    """The locked state row serializes authorization and revisions across processes."""

    def __init__(self, url):
        self.pool = ConnectionPool(
            url, min_size=1, max_size=8, timeout=10,
            kwargs={'connect_timeout':10, 'options':'-c statement_timeout=15000'},
        )

    def health(self):
        try:
            with self.pool.connection(timeout=3) as c:
                return c.execute('SELECT 1 FROM public.tagalong_state WHERE id=1').fetchone() == (1,)
        except (Error, PoolTimeout):
            return False

    def transact(self, fn):
        try:
            return self._transact(fn)
        except (Error, PoolTimeout):
            fail(503, 'Database unavailable')

    @staticmethod
    def changed(before, after, key):
        return (value for item_id, value in after.get(key, {}).items()
                if before.get(key, {}).get(item_id) != value)

    def _transact(self, fn):
        with self.pool.connection() as c, c.transaction():
            row = c.execute('SELECT state FROM public.tagalong_state WHERE id=1 FOR UPDATE').fetchone()
            if not row:
                fail(503, 'Database schema is not configured')
            state = row[0]
            before = copy.deepcopy(state)
            result = fn(state)
            from .decisions import reconcile
            reconcile(before,state)
            from .coordination import track_activity
            track_activity(before,state)
            if state == before:
                return copy.deepcopy(result)
            c.execute('UPDATE public.tagalong_state SET state=%s WHERE id=1', (Jsonb(state),))
            # Membership changes are narrow so a read/job poll cannot churn RLS state.
            old_members = {(pid, user) for pid, users in before['members'].items() for user in users}
            new_members = {(pid, user) for pid, users in state['members'].items() for user in users}
            for pair in old_members - new_members:
                c.execute('DELETE FROM public.tagalong_memberships WHERE plan_id=%s AND user_id=%s', pair)
            for pair in new_members - old_members:
                c.execute('INSERT INTO public.tagalong_memberships(plan_id,user_id) VALUES(%s,%s)', pair)
            for p in self.changed(before, state, 'plans'):
                previous = before['plans'].get(p['id'])
                if not previous or previous['revision'] != p['revision']:
                    c.execute('INSERT INTO public.tagalong_revisions(plan_id,revision) VALUES(%s,%s) ON CONFLICT(plan_id) DO UPDATE SET revision=EXCLUDED.revision', (p['id'], p['revision']))
                c.execute('INSERT INTO public.tagalong_plans VALUES(%s,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET owner_id=EXCLUDED.owner_id,revision=EXCLUDED.revision,document=EXCLUDED.document', (p['id'], p['owner_id'], p['revision'], Jsonb(p)))
            for p in self.changed(before, state, 'proposals'):
                c.execute('INSERT INTO public.tagalong_proposals VALUES(%s,%s,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET status=EXCLUDED.status,document=EXCLUDED.document', (p['id'], p['plan_id'], p['label'], p['status'], Jsonb(p)))
            for key, p in state['sources'].items():
                if before['sources'].get(key) != p:
                    c.execute('INSERT INTO public.tagalong_sources VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(source_key) DO UPDATE SET version=EXCLUDED.version,deleted=EXCLUDED.deleted,document=EXCLUDED.document', (key, p['plan_id'], p['id'], p['version'], p['deleted'], Jsonb(p)))
            for p in self.changed(before, state, 'jobs'):
                c.execute('INSERT INTO public.tagalong_ingestion_jobs VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET status=EXCLUDED.status,attempts=EXCLUDED.attempts,lease_until=EXCLUDED.lease_until,document=EXCLUDED.document', (p['id'], p['source_key'], p['status'], p['attempts'], p['lease_until'], Jsonb(p)))
            for pid,record in state.get('coordination',{}).items():
                if before.get('coordination',{}).get(pid)!=record:
                    c.execute('INSERT INTO public.tagalong_coordination(plan_id,plan_revision,status,health,last_activity_at,document) VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(plan_id) DO UPDATE SET plan_revision=EXCLUDED.plan_revision,status=EXCLUDED.status,health=EXCLUDED.health,last_activity_at=EXCLUDED.last_activity_at,document=EXCLUDED.document', (pid,record['plan_revision'],record['status'],record['health'],record.get('last_activity_at') or state.get('plan_activity',{}).get(pid),Jsonb(record)))
            return copy.deepcopy(result)

