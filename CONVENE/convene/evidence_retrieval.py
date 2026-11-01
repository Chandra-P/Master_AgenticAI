"""PostgreSQL full-text RAG with current-event evidence isolation."""
import re

from convene.policy import authorize_action


class EvidenceIndex:
    def __init__(self,repository):self.repository=repository

    def add(self,actor,fact):
        with self.repository.transaction(actor) as connection:
            event=self.repository._load(connection,actor,fact.event_id,lock=True)
            authorize_action(actor,event,'research')
            if fact.brief_version!=event.brief.version:raise ValueError('Evidence belongs to an older brief.')
            from convene.vendor_directory import DirectoryRepository
            directory=DirectoryRepository(self.repository.dsn).list_approved()
            vendor=next((v for v in directory['vendors']+directory['food'] if v['id']==fact.provider_id),None)
            connection.execute('INSERT INTO knowledge_chunks(id,event_id,brief_version,kind,title,content,source_id,source_kind,retrieved_at,vendor_id,vendor_version,approval_id) '
                'VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING',
                (str(fact.id),fact.event_id,fact.brief_version,'event_evidence',fact.provider_id+' '+fact.field,
                 fact.excerpt,fact.source_id,fact.source_kind,fact.retrieved_at,
                 vendor['id'] if vendor else None,vendor['directory_version'] if vendor else None,
                 vendor['approval']['approval_id'] if vendor else None))

    def retrieve(self,actor,event_id,query,*,limit=4):
        # Bound input; OR terms allow relevant passages despite filler in natural language.
        terms=re.findall(r'[\w]+',query[:2000],flags=re.UNICODE)[:40]
        query=' OR '.join(terms)
        with self.repository.transaction(actor) as connection:
            event=self.repository._load(connection,actor,event_id)
            include_private=actor.authenticated and event.confirmed_version==event.brief.version
            rows=connection.execute(
                "WITH q AS (SELECT websearch_to_tsquery('english',%s) AS query) "
                'SELECT id,kind,title,content,source_id,source_kind,retrieved_at,brief_version,vendor_id,vendor_version,approval_id FROM knowledge_chunks,q '
                'WHERE search @@ q.query AND (kind=%s OR (%s AND event_id=%s AND brief_version=%s)) '
                'ORDER BY ts_rank_cd(search,q.query) DESC,id LIMIT %s',
                (query,'planning',include_private,event.id,event.brief.version,min(max(limit,1),6))).fetchall()
            return [{**row,'content':row['content'][:3500],'retrieved_at':row['retrieved_at'].isoformat(),
                     'approval_id':str(row['approval_id']) if row['approval_id'] else None} for row in rows]
