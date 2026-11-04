from types import SimpleNamespace
from pinecone.exceptions import NotFoundException, UnauthorizedException
import pytest
from tagalong.providers import ConnectedAI

def test_first_ingestion_creates_a_missing_namespace():
    calls=[]
    def delete(**kwargs):raise NotFoundException(status=404,reason='Namespace not found')
    ai=ConnectedAI.__new__(ConnectedAI)
    ai.index=SimpleNamespace(delete=delete,upsert=lambda **kwargs:calls.append(kwargs))
    ai.embedding=lambda text:[0.1,0.2]
    ai.upsert({'id':'source','plan_id':'new-plan','text':'First message','version':1,'chunks':1})
    assert calls[0]['namespace']=='tagalong:new-plan'
    assert calls[0]['vectors'][0]['metadata']['source_id']=='source'

def test_cleanup_never_swallows_authorization_errors():
    def delete(**kwargs):raise UnauthorizedException(status=401,reason='Unauthorized')
    ai=ConnectedAI.__new__(ConnectedAI);ai.index=SimpleNamespace(delete=delete)
    with pytest.raises(UnauthorizedException):ai.delete({'id':'source','plan_id':'plan','chunks':1})
