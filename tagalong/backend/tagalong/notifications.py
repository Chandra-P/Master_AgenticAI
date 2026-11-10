"""Bounded, account-private in-app notices with authorization at read time."""
from fastapi import Depends
from fastapi.responses import JSONResponse
from .core import fail, now, uid, visible


def notify(state,user_id,pid):
    records=state.setdefault('notifications',{})
    mine=sorted((n for n in records.values() if n['user_id']==user_id),key=lambda n:n['created_at'])
    while len(mine)>=200:records.pop(mine.pop(0)['id'])
    if len(records)>=100000:fail(503,'Notification capacity reached')
    nid=uid();records[nid]={'id':nid,'user_id':user_id,'plan_id':pid,'created_at':now(),'read_at':None}


def allowed(state,notice,actor):
    return notice and notice['user_id']==actor.id and visible(state,notice['plan_id'],actor)


def install_notifications(app,repo,actor):
    @app.get('/v1/notifications')
    def listing(a=Depends(actor)):
        def read(state):
            return sorted([{'id':n['id'],'plan_id':n['plan_id'],'title':state['plans'][n['plan_id']]['title'],
                            'created_at':n['created_at'],'read':bool(n['read_at'])}
                           for n in state.get('notifications',{}).values() if allowed(state,n,a)],
                          key=lambda n:(n['created_at'],n['id']),reverse=True)
        return JSONResponse(repo.transact(read),headers={'Cache-Control':'no-store'})

    @app.post('/v1/notifications/{nid}/read')
    def mark_read(nid:str,a=Depends(actor)):
        def change(state):
            notice=state.get('notifications',{}).get(nid)
            if not allowed(state,notice,a):fail(404,'Notification not found')
            if not notice['read_at']:notice['read_at']=now()
            return {'status':'read'}
        return repo.transact(change)
