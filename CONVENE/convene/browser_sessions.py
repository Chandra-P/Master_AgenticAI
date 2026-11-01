"""Opaque, expiring, revocable sessions. Plaintext session tokens never enter SQL."""
from contextlib import contextmanager
from datetime import datetime,timedelta,timezone
import hashlib
import secrets

import psycopg
from psycopg.rows import dict_row

from convene.domain import Principal


class BrowserSessions:
    def __init__(self,dsn):self.dsn=dsn

    @contextmanager
    def _connection(self,token):
        if not token or not isinstance(token,str) or len(token)>200:
            raise PermissionError('Session required.')
        digest=hashlib.sha256(token.encode()).hexdigest()
        with psycopg.connect(self.dsn,connect_timeout=8,row_factory=dict_row) as connection:
            connection.execute("SELECT set_config('convene.session_hash',%s,true)",(digest,))
            yield connection,digest

    def create(self):
        actor=Principal();token=secrets.token_urlsafe(48);csrf=secrets.token_urlsafe(32)
        expires=datetime.now(timezone.utc)+timedelta(days=14)
        with self._connection(token) as (connection,digest):
            connection.execute('INSERT INTO browser_sessions(token_hash,actor_id,csrf_token,expires_at) VALUES(%s,%s,%s,%s)',
                               (digest,actor.id,csrf,expires))
        return token,actor,csrf

    def resolve(self,token):
        with self._connection(token) as (connection,digest):
            row=connection.execute('SELECT actor_id,authenticated,csrf_token FROM browser_sessions '
                'WHERE token_hash=%s AND revoked_at IS NULL AND expires_at>now()',(digest,)).fetchone()
            if not row:raise PermissionError('Session expired; please sign in again.')
            return Principal(id=row['actor_id'],authenticated=row['authenticated']),row['csrf_token']

    def revoke(self,token):
        with self._connection(token) as (connection,digest):
            connection.execute('UPDATE browser_sessions SET revoked_at=now() WHERE token_hash=%s',(digest,))
