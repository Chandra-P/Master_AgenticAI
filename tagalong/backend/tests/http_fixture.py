"""Explicit test-only ASGI factory for browser tests. Never import from production code."""
from tagalong.app import create_app
from tagalong.core import MemoryRepository, Actor
from tests.test_workflows import FakeAI

def app_factory():
    repo=MemoryRepository()
    accounts={'test-alice':Actor('alice','alice@example.test','alice'),'test-bob':Actor('bob','bob@example.test','bob')}
    def authenticate(token):
        from tagalong.core import fail
        if token not in accounts: fail(401,'Invalid test session')
        return accounts[token]
    return create_app(repo,authenticate,FakeAI())
