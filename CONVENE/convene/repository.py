"""PostgreSQL records with owner-scoped transactions and optimistic versions."""
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from convene.domain import Approval,EventBriefVersion,EventRecord,Principal


class NotFound(LookupError):
    pass


class Conflict(ValueError):
    pass


class Repository:
    def __init__(self,dsn:str):
        if not dsn or not dsn.startswith(('postgresql://','postgres://')):
            raise ValueError('A PostgreSQL database URL is required; no production SQLite fallback.')
        self.dsn=dsn

    def migrate(self):
        # Explicit administrative command/test setup only; never run from a public route.
        folder=Path(__file__).resolve().parents[1]/'migrations'
        with psycopg.connect(self.dsn,connect_timeout=8) as connection:
            connection.execute('SELECT pg_advisory_xact_lock(7421401)')
            connection.execute('CREATE TABLE IF NOT EXISTS schema_migrations (name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())')
            for path in sorted(folder.glob('*.sql')):
                if connection.execute('SELECT 1 FROM schema_migrations WHERE name=%s',(path.name,)).fetchone():continue
                connection.execute(path.read_text(encoding='utf-8-sig'))
                connection.execute('INSERT INTO schema_migrations(name) VALUES (%s)',(path.name,))

    @contextmanager
    def transaction(self,actor:Principal):
        with psycopg.connect(self.dsn,connect_timeout=8,row_factory=dict_row) as connection:
            connection.execute("SELECT set_config('convene.actor_id',%s,true)",(str(actor.id),))
            yield connection

    @staticmethod
    def _from_row(row):
        if row is None:raise NotFound('Event not found.')
        return EventRecord(id=row['id'],owner_id=row['owner_id'],confirmed_version=row['confirmed_version'],
                           status=row['status'],brief=EventBriefVersion.model_validate(row['body']))

    @staticmethod
    def _load(connection,actor,event_id,*,lock=False):
        suffix=' FOR UPDATE OF e' if lock else ''
        row=connection.execute('SELECT e.*,v.body FROM events e JOIN brief_versions v '
            'ON v.event_id=e.id AND v.version=e.active_version WHERE e.id=%s AND e.owner_id=%s'+suffix,
            (event_id,actor.id)).fetchone()
        return Repository._from_row(row)

    @staticmethod
    def _audit(connection,actor,event_id,action,metadata):
        connection.execute('INSERT INTO audit_events(id,event_id,actor_id,action,metadata) VALUES(%s,%s,%s,%s,%s)',
                           (uuid4(),event_id,actor.id,action,Jsonb(metadata)))

    def create_event(self,actor:Principal,brief:EventBriefVersion|None=None):
        brief=brief or EventBriefVersion()
        if brief.version!=1:raise ValueError('New events start at brief version 1.')
        event=EventRecord(owner_id=actor.id,brief=brief)
        with self.transaction(actor) as connection:
            connection.execute('INSERT INTO app_users(id) VALUES(%s) ON CONFLICT DO NOTHING',(actor.id,))
            connection.execute('INSERT INTO events(id,owner_id,active_version) VALUES(%s,%s,1)',(event.id,actor.id))
            connection.execute('INSERT INTO brief_versions(event_id,version,body) VALUES(%s,1,%s)',
                               (event.id,Jsonb(brief.model_dump(mode='json'))))
            self._audit(connection,actor,event.id,'event_created',{'version':1})
        return event

    def get_event(self,actor,event_id):
        with self.transaction(actor) as connection:
            return self._load(connection,actor,event_id)

    def list_events(self,actor):
        with self.transaction(actor) as connection:
            rows=connection.execute('SELECT e.*,v.body FROM events e JOIN brief_versions v '
                'ON v.event_id=e.id AND v.version=e.active_version WHERE e.owner_id=%s ORDER BY e.updated_at DESC LIMIT 100',
                (actor.id,)).fetchall()
            return [self._from_row(row) for row in rows]

    def revise_event(self,actor,event_id,patch,*,expected_version):
        with self.transaction(actor) as connection:
            event=self._load(connection,actor,event_id,lock=True)
            if event.brief.version!=expected_version:raise Conflict('Stale brief version; reload before editing.')
            changed=event.revise(patch,expected_version)
            connection.execute('INSERT INTO brief_versions(event_id,version,body) VALUES(%s,%s,%s)',
                (event.id,changed.brief.version,Jsonb(changed.brief.model_dump(mode='json'))))
            connection.execute('UPDATE events SET active_version=%s,confirmed_version=NULL,updated_at=now() WHERE id=%s AND owner_id=%s',
                               (changed.brief.version,event.id,actor.id))
            self._audit(connection,actor,event.id,'brief_revised',{'version':changed.brief.version,'fields':sorted(patch)})
            return changed

    def confirm_event(self,actor,event_id,*,expected_version):
        with self.transaction(actor) as connection:
            event=self._load(connection,actor,event_id,lock=True)
            if event.brief.version!=expected_version:raise Conflict('Stale brief version; review the latest brief.')
            event=event.confirm(expected_version)
            connection.execute('UPDATE events SET confirmed_version=%s,updated_at=now() WHERE id=%s AND owner_id=%s',
                               (expected_version,event.id,actor.id))
            self._audit(connection,actor,event.id,'brief_confirmed',{'version':expected_version})
            return event

    def store_approval(self,actor,approval:Approval):
        from datetime import datetime,timezone
        with self.transaction(actor) as connection:
            event=self._load(connection,actor,approval.event_id,lock=True)
            if (not actor.authenticated or approval.actor_id!=actor.id or approval.brief_version!=event.brief.version
                    or event.confirmed_version!=event.brief.version or approval.expires_at<=datetime.now(timezone.utc)
                    or approval.revoked_at is not None):
                raise PermissionError('Approval must bind the authenticated owner and current confirmed brief.')
            connection.execute('INSERT INTO approvals(id,event_id,body) VALUES(%s,%s,%s)',
                (approval.id,event.id,Jsonb(approval.model_dump(mode='json'))))
            self._audit(connection,actor,event.id,'approval_recorded',{'approval_id':str(approval.id),'capability':approval.capability})

    def get_approval(self,actor,event_id,approval_id):
        with self.transaction(actor) as connection:
            self._load(connection,actor,event_id)
            row=connection.execute('SELECT body FROM approvals WHERE id=%s AND event_id=%s',(approval_id,event_id)).fetchone()
            if not row:raise NotFound('Approval not found.')
            return Approval.model_validate(row['body'])

    def record_intake_greeting(self,actor,event_id,text):
        with self.transaction(actor) as connection:
            self._load(connection,actor,event_id,lock=True)
            connection.execute('INSERT INTO intake_turns(event_id,sequence,role,body) VALUES(%s,1,%s,%s)',
                               (event_id,'assistant',text))

    def intake_history(self,actor,event_id):
        with self.transaction(actor) as connection:
            self._load(connection,actor,event_id)
            return connection.execute('SELECT sequence,role,body,sources FROM intake_turns WHERE event_id=%s ORDER BY sequence',
                                      (event_id,)).fetchall()

    def get_intake_receipt(self,actor,event_id,request_id):
        with self.transaction(actor) as connection:
            self._load(connection,actor,event_id)
            row=connection.execute('SELECT response FROM intake_receipts WHERE event_id=%s AND request_id=%s',
                                   (event_id,request_id)).fetchone()
            return row['response'] if row else None

    def commit_intake(self,actor,event_id,message,patch,response,*,expected_version,request_id):
        with self.transaction(actor) as connection:
            event=self._load(connection,actor,event_id,lock=True)
            receipt=connection.execute('SELECT response FROM intake_receipts WHERE event_id=%s AND request_id=%s',
                                       (event_id,request_id)).fetchone()
            if receipt:return receipt['response']
            if event.brief.version!=expected_version:raise Conflict('Stale brief version; reload before replying.')
            provider_sources=[s for s in response.get('sources',[]) if s.get('kind') in ('event_evidence','approved_vendor') and s.get('vendor_id')]
            for vendor_id in sorted({s['vendor_id'] for s in provider_sources}):
                connection.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',('vendor:'+vendor_id,))
                published=connection.execute("SELECT published_version,published_decision FROM vendor_records WHERE id=%s AND status='approved'",(vendor_id,)).fetchone()
                if not published or any(s.get('vendor_version')!=published['published_version'] or s.get('approval_id')!=str(published['published_decision']) for s in provider_sources if s['vendor_id']==vendor_id):
                    raise Conflict('Vendor approval changed while answering; refresh the approved options.')
            changed=event if patch is None else event.revise(patch,expected_version)
            if patch is not None:
                connection.execute('INSERT INTO brief_versions(event_id,version,body) VALUES(%s,%s,%s)',
                    (event.id,changed.brief.version,Jsonb(changed.brief.model_dump(mode='json'))))
                connection.execute('UPDATE events SET active_version=%s,confirmed_version=NULL,updated_at=now() WHERE id=%s',
                                   (changed.brief.version,event.id))
            sequence=connection.execute('SELECT COALESCE(MAX(sequence),0) AS n FROM intake_turns WHERE event_id=%s',
                                        (event.id,)).fetchone()['n']
            assistant=response.get('assistant_message') or (response['question']['text'] if response['question'] else 'Here is your brief. Please review and confirm it before I research options.')
            connection.execute('INSERT INTO intake_turns(event_id,sequence,role,body) VALUES(%s,%s,%s,%s),(%s,%s,%s,%s)',
                               (event.id,sequence+1,'user',message,event.id,sequence+2,'assistant',assistant))
            if response.get('sources'):
                connection.execute('UPDATE intake_turns SET sources=%s WHERE event_id=%s AND sequence=%s',
                                   (Jsonb(response['sources']),event.id,sequence+2))
            connection.execute('INSERT INTO intake_receipts(event_id,request_id,response) VALUES(%s,%s,%s)',
                               (event.id,request_id,Jsonb(response)))
            self._audit(connection,actor,event.id,'intake_answered',{'version':changed.brief.version})
            return response
