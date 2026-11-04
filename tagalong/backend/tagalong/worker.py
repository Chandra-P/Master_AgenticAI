import os,time
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

def main():
    repo=PostgresRepository(os.environ['DATABASE_URL']); provider=ConnectedAI()
    provider.verify_index_dimension()
    while True:
        if not process_one(repo,provider): time.sleep(2)
if __name__=='__main__': main()



