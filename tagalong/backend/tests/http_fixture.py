"""Explicit test-only ASGI factory for browser tests. Never import from production code."""
from tagalong.app import create_app
from tagalong.core import MemoryRepository, Actor
from tests.test_workflows import FakeAI

def app_factory():
    repo=MemoryRepository()
    repo.state['app_admins']={'alice':{'granted_by':'explicit_test_fixture'}}
    accounts={'test-alice':Actor('alice','alice@example.test','alice'),'test-bob':Actor('bob','bob@example.test','bob')}
    def authenticate(token):
        from tagalong.core import fail
        if token not in accounts: fail(401,'Invalid test session')
        return accounts[token]
    class BrowserAI(FakeAI):
        def answer(self,plan,message,resolve_sources):
            self.matches=repo.transact(lambda state:[{'id':src['id'],'version':src['version']} for src in state['sources'].values() if src['plan_id']==plan['id'] and src.get('kind')=='document' and not src['deleted']])
            return super().answer(plan,message,resolve_sources)
    class BrowserPlaces:
        def search(self,query,location,category):
            return [{'title':'Synthetic vegetarian restaurant','url':'https://places.example.test/restaurant','snippet':'Synthetic public source snippet for browser verification.'}]
    return create_app(repo,authenticate,BrowserAI(),places=BrowserPlaces())
