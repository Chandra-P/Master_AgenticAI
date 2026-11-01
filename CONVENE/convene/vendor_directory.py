"""Versioned directory. Public reads and explicit local administration are separate."""
from contextlib import contextmanager
from datetime import date,datetime
from decimal import Decimal
import hashlib
import json
from typing import Literal
from uuid import uuid4
from zoneinfo import ZoneInfo

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from pydantic import BaseModel,ConfigDict,Field,HttpUrl

from convene.repository import Conflict,NotFound


class VendorBody(BaseModel):
    model_config=ConfigDict(extra='allow',allow_inf_nan=False,str_strip_whitespace=True)
    id:str=Field(min_length=1,max_length=150,pattern=r'^[a-z0-9][a-z0-9_-]*$')
    name:str=Field(min_length=1,max_length=200)
    kind:Literal['venue','decorator','food']
    source_url:HttpUrl
    price:Decimal|None=Field(default=None,ge=0,le=10000000)
    capacity:int|None=Field(default=None,ge=1,le=100000)
    availability:Literal['unconfirmed']='unconfirmed'


def _body(value):
    if {'approval','directory_version','status','published_version'} & value.keys():
        raise ValueError('Approval/publication fields are controlled by the directory service.')
    body=VendorBody.model_validate(value).model_dump(mode='json')
    # Keep the existing public API numeric price shape.
    if body['price'] is not None:body['price']=float(body['price'])
    return body


def _digest(body):
    return hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


class DirectoryRepository:
    def __init__(self,dsn):self.dsn=dsn

    def list_approved(self):
        with psycopg.connect(self.dsn,connect_timeout=8,row_factory=dict_row) as connection:
            rows=connection.execute('SELECT v.body,v.version,a.id AS approval_id,a.actor_label,a.actor_kind,'
                'a.approved_on,a.recorded_at,a.reason,v.content_hash FROM vendor_records r '
                'JOIN vendor_versions v ON v.vendor_id=r.id AND v.version=r.published_version '
                'JOIN vendor_approval_history a ON a.id=r.published_decision '
                "WHERE r.status='approved' AND a.action='approved' ORDER BY v.body->>'kind',v.body->>'name'").fetchall()
        vendors=[]
        for row in rows:
            vendors.append({**row['body'],'directory_version':row['version'],'approval':{
                'status':'approved','approved_by':row['actor_label'],'actor_kind':row['actor_kind'],
                'approved_on':row['approved_on'].isoformat(),'recorded_at':row['recorded_at'].isoformat(),
                'approval_id':str(row['approval_id']),'basis':row['reason'],'content_hash':row['content_hash']}})
        return {'vendors':[v for v in vendors if v['kind']!='food'],
                'food':[v for v in vendors if v['kind']=='food'],
                'note':'Approved for consideration; dates, final quotes and reservation conditions need provider confirmation.'}


class DirectoryAdmin:
    """Local operator capability. Never instantiate from a parent/public request."""
    def __init__(self,dsn,*,operator):
        if not isinstance(operator,str) or not operator.strip() or len(operator)>120:
            raise ValueError('A local operator audit label is required.')
        self.dsn=dsn;self.operator=operator.strip()

    @contextmanager
    def _transaction(self):
        with psycopg.connect(self.dsn,connect_timeout=8,row_factory=dict_row) as connection:
            if connection.execute('SELECT current_user AS role').fetchone()['role']!='convene_directory_admin':
                raise PermissionError('Directory administration requires its dedicated database login.')
            yield connection

    @staticmethod
    def _lock(connection,vendor_id):
        connection.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',('vendor:'+vendor_id,))
        return connection.execute('SELECT * FROM vendor_records WHERE id=%s FOR UPDATE',(vendor_id,)).fetchone()

    def _propose(self,connection,body,reason,expected_version):
        record=self._lock(connection,body['id'])
        if (record['head_version'] if record else 0)!=expected_version:raise Conflict('Stale vendor version; review the latest record.')
        if not record:connection.execute('INSERT INTO vendor_records(id) VALUES(%s)',(body['id'],))
        version=expected_version+1
        evidence={'source_url':body['source_url'],'checked_on':body.get('checked_on'),
                  'contact':body.get('contact'),'change_reason':reason}
        connection.execute('INSERT INTO vendor_versions(vendor_id,version,body,content_hash,source_evidence,created_by) '
            'VALUES(%s,%s,%s,%s,%s,%s)',(body['id'],version,Jsonb(body),_digest(body),Jsonb(evidence),self.operator))
        connection.execute('UPDATE vendor_records SET head_version=%s WHERE id=%s',(version,body['id']))
        return version

    def propose(self,body,*,reason,expected_version):
        if not reason.strip():raise ValueError('Change reason required.')
        body=_body(body)
        with self._transaction() as connection:return self._propose(connection,body,reason,expected_version)

    def _approve(self,connection,vendor_id,version,reason,*,actor=None,kind='local_operator',approved_on=None):
        record=self._lock(connection,vendor_id)
        if not record:raise NotFound('Vendor not found.')
        if record['head_version']!=version:raise Conflict('Approval must bind the latest reviewed vendor version.')
        row=connection.execute('SELECT content_hash FROM vendor_versions WHERE vendor_id=%s AND version=%s',
                               (vendor_id,version)).fetchone()
        decision_id=uuid4()
        connection.execute('INSERT INTO vendor_approval_history(id,vendor_id,version,action,actor_label,actor_kind,approved_on,reason,content_hash) '
            'VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(decision_id,vendor_id,version,'approved',actor or self.operator,kind,
             approved_on or datetime.now(ZoneInfo('America/Chicago')).date(),reason,row['content_hash']))
        connection.execute("UPDATE vendor_records SET status='approved',published_version=%s,published_decision=%s WHERE id=%s",
                           (version,decision_id,vendor_id))
        return str(decision_id)

    def approve(self,vendor_id,version,*,reason):
        if not reason.strip():raise ValueError('Approval reason required.')
        with self._transaction() as connection:return self._approve(connection,vendor_id,version,reason)

    def suspend(self,vendor_id,*,reason):
        if not reason.strip():raise ValueError('Suspension reason required.')
        with self._transaction() as connection:
            record=self._lock(connection,vendor_id)
            if not record:return
            if record['status']=='suspended':return
            version=record['published_version'] or record['head_version']
            row=connection.execute('SELECT content_hash FROM vendor_versions WHERE vendor_id=%s AND version=%s',
                                   (vendor_id,version)).fetchone()
            connection.execute('INSERT INTO vendor_approval_history(id,vendor_id,version,action,actor_label,actor_kind,approved_on,reason,content_hash) '
                'VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(uuid4(),vendor_id,version,'suspended',self.operator,'local_operator',
                    datetime.now(ZoneInfo('America/Chicago')).date(),reason,row['content_hash']))
            connection.execute("UPDATE vendor_records SET status='suspended' WHERE id=%s",(vendor_id,))

    def history(self,vendor_id):
        with self._transaction() as connection:
            record=connection.execute('SELECT * FROM vendor_records WHERE id=%s',(vendor_id,)).fetchone()
            if not record:raise NotFound('Vendor not found.')
            versions=connection.execute('SELECT * FROM vendor_versions WHERE vendor_id=%s ORDER BY version',(vendor_id,)).fetchall()
            decisions=connection.execute('SELECT * FROM vendor_approval_history WHERE vendor_id=%s ORDER BY recorded_at,id',(vendor_id,)).fetchall()
            return {'record':record,'versions':versions,'decisions':decisions}

    def import_existing(self):
        from convene.party_catalog import get_catalog
        catalog=get_catalog();imported=[]
        for raw in catalog['venues']+catalog['decorators']:
            body=_body(raw)
            with self._transaction() as connection:
                if self._lock(connection,body['id']):continue
                version=self._propose(connection,body,'Initial import of existing configured directory',0)
                self._approve(connection,body['id'],version,
                    'Project owner explicitly approved the existing configured vendor list in conversation; imported without a new vendor review.',
                    actor='project-owner (conversation approval)',kind='conversation_approval',approved_on=date(2026,11,1))
                imported.append(body['id'])
        return imported
