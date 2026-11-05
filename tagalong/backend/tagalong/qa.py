"""Repeatable synthetic review scenarios; no fake auth users or real invitations."""
from .core import create, update, source, uid, now
from .models import Create


def seed_review_plans(state, actor):
    runs=state.setdefault('qa_runs',{})
    if actor.id in runs: return {'plan_ids':runs[actor.id]['plan_ids']}
    scenarios=[
        ('Chicago dinner','outing','Chicago, Illinois','2026-11-21','2026-11-21',65,'vegetarian-friendly dinner','Keep dinner within $65 per person. At least one vegetarian main is required.'),
        ('Austin weekend','trip','Austin, Texas','2026-12-04','2026-12-06',350,'relaxed outdoor weekend','Budget is $350 per person for the whole weekend. Prefer free outdoor activities and a relaxed pace.'),
        ('Toronto city break','trip','Toronto, Ontario','2026-12-11','2026-12-13',500,'accessible city break','Budget is $500 per person. Step-free access is required. Avoid booking claims; venue availability has not been checked.'),
    ]
    ids=[]
    for title,kind,location,start,end,budget,activity,note in scenarios:
        p=create(state,actor,Create(title='[QA Review] '+title,kind=kind,start=start,end=end))
        p['location']=location;p['budget']=budget
        p['messages']=[{'id':uid(),'author':actor.name,'user_id':actor.id,'text':'Synthetic QA scenario for admin review. '+note,'time':now()}]
        p['polls'].append({'id':uid(),'question':'Preferred planning pace?','options':['Relaxed','Packed schedule'],'votes':{actor.name:0}})
        p['itinerary']=[{'id':uid(),'title':'Draft: '+activity,'time':'18:00' if kind=='outing' else '10:00','category':'Draft suggestion','location':location+' — specific venue to decide'}]
        p['tasks']=[{'label':'Review synthetic scenario and budget','done':True},{'label':'Verify preferences and document retrieval','done':False},{'label':'Choose a real venue after checking availability','done':False}]
        update(state,actor,p['id'],p,p['revision'])
        source(state,p['id'],uid(),'QA brief — '+title,note+' This is synthetic test content, not a reservation or invitation.',kind='document')
        ids.append(p['id'])
    runs[actor.id]={'plan_ids':ids,'created_at':now()}
    from .admin import audit
    audit(state,actor,'create_qa_plans',','.join(ids),'Create persistent synthetic review scenarios')
    return {'plan_ids':ids}
