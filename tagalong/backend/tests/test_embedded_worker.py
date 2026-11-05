"""No credentials or external data: lifecycle ingestion uses synthetic queued text."""
import threading
import time
from fastapi.testclient import TestClient
from tagalong.app import create_app
from tagalong.core import Actor, MemoryRepository, source


class SyntheticProvider:
    def __init__(self, unavailable=False):
        self.unavailable=unavailable
        self.verifications=0
        self.indexed=[]
        self.verified=threading.Event()
    def verify_index_dimension(self):
        self.verifications+=1
        self.verified.set()
        if self.unavailable: raise RuntimeError('private provider error; never log')
        return True
    def upsert(self, item): self.indexed.append(item)
    def delete(self, item): self.indexed.append(item)


def queued_app(provider):
    repo=MemoryRepository()
    repo.transact(lambda s:source(s,'synthetic-plan','synthetic-source','Test','Synthetic test text',kind='document'))
    app=create_app(repo,lambda token:Actor('synthetic-user','synthetic@example.test','synthetic'),provider)
    return repo,app


def wait_until(predicate, timeout=2):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if predicate(): return True
        time.sleep(0.01)
    return bool(predicate())


def test_enabled_embedded_worker_processes_queue_and_stops(monkeypatch):
    monkeypatch.setenv('TAGALONG_EMBEDDED_WORKER','true')
    provider=SyntheticProvider(); repo,app=queued_app(provider)
    with TestClient(app) as client:
        assert client.get('/health').status_code==200
        assert wait_until(lambda:repo.transact(lambda s:all(j['status']=='done' for j in s['jobs'].values())))
        assert provider.indexed[0]['id']=='synthetic-source'
        assert provider.verifications==1
        runner=app.state.ingestion_worker
        assert runner.is_alive()
        health=client.get('/health').json()
        assert health['indexing_mode']=='embedded' and health['indexing_worker_running'] is True
    assert not runner.is_alive()


def test_disabled_worker_has_no_provider_calls_or_queue_changes(monkeypatch):
    monkeypatch.delenv('TAGALONG_EMBEDDED_WORKER',raising=False)
    provider=SyntheticProvider(); repo,app=queued_app(provider)
    with TestClient(app) as client:
        assert client.get('/health').status_code==200
        assert app.state.ingestion_worker is None
        health=client.get('/health').json()
        assert health['indexing_mode']=='external' and health['indexing_worker_running'] is False
    assert provider.verifications==0 and provider.indexed==[]
    assert all(j['status']=='pending' and j['attempts']==0 for j in repo.state['jobs'].values())


def test_unavailable_provider_does_not_break_startup_health_or_lease_jobs(monkeypatch):
    monkeypatch.setenv('TAGALONG_EMBEDDED_WORKER','true')
    provider=SyntheticProvider(unavailable=True); repo,app=queued_app(provider)
    with TestClient(app) as client:
        assert client.get('/health').status_code==200
        assert provider.verified.wait(2)
        runner=app.state.ingestion_worker
        assert provider.indexed==[]
        assert all(j['status']=='pending' and j['attempts']==0 for j in repo.state['jobs'].values())
        # A retry must wait, rather than spinning on the unavailable provider.
        assert provider.verifications==1
    assert not runner.is_alive()


def test_health_metadata_before_lifespan_has_no_running_worker(monkeypatch):
    monkeypatch.setenv('TAGALONG_EMBEDDED_WORKER','true')
    provider=SyntheticProvider(); repo,app=queued_app(provider)
    client=TestClient(app)
    health=client.get('/health').json()
    assert health['indexing_mode']=='embedded' and health['indexing_worker_running'] is False
    assert provider.verifications==0

def test_transient_dimension_validation_recovers_once_then_processes_more_jobs(monkeypatch):
    from tagalong.worker import EmbeddedWorker
    monkeypatch.setenv('TAGALONG_EMBEDDED_WORKER','true')
    monkeypatch.setattr(EmbeddedWorker,'RETRY_SECONDS',0.02)
    monkeypatch.setattr(EmbeddedWorker,'POLL_SECONDS',0.02)
    provider=SyntheticProvider(unavailable=True); repo,app=queued_app(provider)
    with TestClient(app) as client:
        assert provider.verified.wait(2)
        assert provider.indexed==[]
        provider.unavailable=False
        assert wait_until(lambda:len(provider.indexed)==1)
        checks_after_success=provider.verifications
        repo.transact(lambda s:source(s,'synthetic-plan','synthetic-source-2','Test2','Second synthetic text'))
        assert wait_until(lambda:len(provider.indexed)==2)
        assert provider.verifications==checks_after_success
        runner=app.state.ingestion_worker
        assert client.get('/health').status_code==200
    assert not runner.is_alive()


def test_dimension_mismatch_never_indexes_or_leases_and_does_not_log(monkeypatch,capsys,caplog):
    monkeypatch.setenv('TAGALONG_EMBEDDED_WORKER','true')
    class Mismatch(SyntheticProvider):
        def verify_index_dimension(self):
            self.verifications+=1; self.verified.set()
            raise ValueError('private dimension mismatch, source or credential must not be logged')
    provider=Mismatch(); repo,app=queued_app(provider)
    with TestClient(app) as client:
        assert provider.verified.wait(2)
        assert client.get('/health').status_code==200
        assert provider.indexed==[]
        assert all(j['status']=='pending' and j['attempts']==0 for j in repo.state['jobs'].values())
    captured=capsys.readouterr()
    assert 'private dimension mismatch' not in captured.out+captured.err+caplog.text


def test_missing_components_do_not_start_worker(monkeypatch):
    monkeypatch.setenv('TAGALONG_EMBEDDED_WORKER','true')
    for key in ('DATABASE_URL','SUPABASE_URL','SUPABASE_SERVICE_ROLE_KEY','OPENAI_API_KEY','PINECONE_API_KEY','PINECONE_INDEX_HOST'):
        monkeypatch.delenv(key,raising=False)
    for missing in ('repo','auth','ai'):
        provider=SyntheticProvider()
        components={'repo':MemoryRepository(),'auth':lambda token:Actor('id','synthetic@example.test','synthetic'),'ai':provider}
        components[missing]=None
        app=create_app(components['repo'],components['auth'],components['ai'])
        with TestClient(app) as client:
            health=client.get('/health').json()
            assert health['indexing_mode']=='embedded' and health['indexing_worker_running'] is False
            assert app.state.ingestion_worker is None
        assert provider.verifications==0


def test_shutdown_join_is_bounded_for_inflight_provider_then_thread_exits(monkeypatch):
    from tagalong.worker import EmbeddedWorker
    monkeypatch.setenv('TAGALONG_EMBEDDED_WORKER','true')
    monkeypatch.setattr(EmbeddedWorker,'JOIN_SECONDS',0.02)
    entered=threading.Event(); release=threading.Event()
    class InFlight(SyntheticProvider):
        def upsert(self,item):
            entered.set()
            release.wait(3)
            self.indexed.append(item)
    provider=InFlight(); repo,app=queued_app(provider)
    runner=None
    try:
        with TestClient(app):
            assert entered.wait(2)
            runner=app.state.ingestion_worker
            started=time.monotonic()
        assert time.monotonic()-started<1
        assert runner.is_alive()
    finally:
        release.set()
        if runner: assert wait_until(lambda:not runner.is_alive())
