import os, json
from contextlib import contextmanager
from psycopg_pool import ConnectionPool
from psycopg.types.json import Jsonb
from .core import MemoryRepository

class PostgresRepository:
    """Serialized durable unit of work; lock guarantees membership + revision checks are atomic."""
    def __init__(self,url):
        self.pool=ConnectionPool(url,min_size=1,max_size=8,timeout=10,kwargs={'connect_timeout':10,'options':'-c statement_timeout=15000'})
    def transact(self,fn):
        from psycopg import Error
        from .core import fail
        try: return self._transact(fn)
        except Error: fail(503,'Database unavailable')

    def _transact(self,fn):
        with self.pool.connection() as c, c.transaction():
            row=c.execute('SELECT state FROM public.tagalong_state WHERE id=1 FOR UPDATE').fetchone()
            if not row: raise RuntimeError('Apply Tagalong migration first')
            state=row[0]
            result=fn(state)
            c.execute('UPDATE public.tagalong_state SET state=%s WHERE id=1',(Jsonb(state),))
            # Normalized membership drives RLS/Realtime invalidation; never public plan content.
            c.execute('DELETE FROM public.tagalong_memberships')
            for pid,users in state['members'].items():
                for user in users: c.execute('INSERT INTO public.tagalong_memberships(plan_id,user_id) VALUES(%s,%s)',(pid,user))
            for pid,p in state['plans'].items():
                c.execute('INSERT INTO public.tagalong_revisions(plan_id,revision) VALUES(%s,%s) ON CONFLICT(plan_id) DO UPDATE SET revision=EXCLUDED.revision WHERE tagalong_revisions.revision<>EXCLUDED.revision',(pid,p['revision']))
            for p in state['plans'].values():
                c.execute('INSERT INTO public.tagalong_plans VALUES(%s,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET revision=EXCLUDED.revision,document=EXCLUDED.document',(p['id'],p['owner_id'],p['revision'],Jsonb(p)))
            for p in state['proposals'].values():
                c.execute('INSERT INTO public.tagalong_proposals VALUES(%s,%s,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET status=EXCLUDED.status,document=EXCLUDED.document',(p['id'],p['plan_id'],p['label'],p['status'],Jsonb(p)))
            for key,p in state['sources'].items():
                c.execute('INSERT INTO public.tagalong_sources VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(source_key) DO UPDATE SET version=EXCLUDED.version,deleted=EXCLUDED.deleted,document=EXCLUDED.document',(key,p['plan_id'],p['id'],p['version'],p['deleted'],Jsonb(p)))
            for p in state['jobs'].values():
                c.execute('INSERT INTO public.tagalong_ingestion_jobs VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET status=EXCLUDED.status,attempts=EXCLUDED.attempts,lease_until=EXCLUDED.lease_until,document=EXCLUDED.document',(p['id'],p['source_key'],p['status'],p['attempts'],p['lease_until'],Jsonb(p)))
            return result


