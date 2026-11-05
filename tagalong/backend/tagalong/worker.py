import os,time,threading
from .repository import PostgresRepository
from .providers import ConnectedAI

def process_one(repo,provider,clock=time.time):
    def lease(s):
        busy={j['source_key'] for j in s['jobs'].values() if j['status']=='running' and j['lease_until']>clock()}
        for job in s['jobs'].values():
            if job['source_key'] in busy: continue
            if job['status'] in ('pending','running') and job['lease_until']<=clock():
                job['status']='running'; job['attempts']+=1; job['lease_until']=clock()+1800
                return dict(job),dict(s['sources'][job['source_key']])
    leased=repo.transact(lease)
    if not leased: return False
    job,src=leased
    try:
        # Only the newest source version is indexed. Deletes use the same stable ID.
        if job['version']==src['version']:
            if src['deleted']: provider.delete(src)
            else: provider.upsert(src)
        def done(s):
            j=s['jobs'][job['id']]
            if j['attempts']==job['attempts']: j['status']='done'
        repo.transact(done)
    except Exception:
        def retry(s):
            j=s['jobs'][job['id']]
            if j['attempts']==job['attempts']:
                j['status']='failed' if j['attempts']>=5 else 'pending'; j['lease_until']=clock()+min(300,2**j['attempts'])
        repo.transact(retry)
    return True

class EmbeddedWorker:
    """Opt-in daemon consuming the same durable leased queue as the standalone worker.

    Event waits make idle/backoff periods interruptible. An in-flight provider call
    retains its existing timeout; stop never blocks the API shutdown indefinitely.
    """
    POLL_SECONDS = 2.0
    RETRY_SECONDS = 15.0
    JOIN_SECONDS = 2.0

    def __init__(self, repo, provider):
        self.repo = repo
        self.provider = provider
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name='tagalong-ingestion', daemon=True)

    def start(self):
        self._thread.start()

    def is_alive(self):
        return self._thread.is_alive()

    def stop(self):
        self._stop.set()
        if self._thread.ident is not None:
            self._thread.join(timeout=self.JOIN_SECONDS)

    def _run(self):
        verified = False
        while not self._stop.is_set():
            if not verified:
                try:
                    self.provider.verify_index_dimension()
                    verified = True
                except Exception:
                    # Availability and dimension failures never expose provider errors
                    # or lease/index a source until a dimension check succeeds.
                    self._stop.wait(self.RETRY_SECONDS)
                    continue
            if self._stop.is_set():
                break
            try:
                process_one(self.repo, self.provider)
            except Exception:
                # Database outages also back off without terminating the API process.
                self._stop.wait(self.RETRY_SECONDS)
                continue
            # Wait even after work, preventing a fast empty/error queue from spinning.
            self._stop.wait(self.POLL_SECONDS)


def main():
    repo=PostgresRepository(os.environ['DATABASE_URL']); provider=ConnectedAI()
    provider.verify_index_dimension()
    while True:
        if not process_one(repo,provider): time.sleep(2)
if __name__=='__main__': main()
