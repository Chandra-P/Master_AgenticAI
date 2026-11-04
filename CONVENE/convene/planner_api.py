"""Private planner API, separate from localhost-only legacy demo routes."""
import hmac
import logging
import threading
from uuid import UUID

from fastapi import Depends,FastAPI,HTTPException,Request,Response,Query
from pydantic import BaseModel,ConfigDict,Field

from convene.browser_sessions import BrowserSessions
from convene.intake import IntakeService,next_question
from convene.intake_model import OpenAIIntakeExtractor
from convene.repository import Conflict,NotFound

logger=logging.getLogger(__name__)


class ReplyBody(BaseModel):
    model_config=ConfigDict(extra='forbid')
    message:str=Field(min_length=1,max_length=4000)
    expected_version:int=Field(ge=1)
    request_id:UUID


class ConfirmBody(BaseModel):
    model_config=ConfigDict(extra='forbid')
    expected_version:int=Field(ge=1)


class ShortlistBody(ConfirmBody):
    vendor_id:str=Field(min_length=1,max_length=150,pattern=r'^[a-z0-9][a-z0-9_-]*$')
    vendor_version:int=Field(ge=1)
    selected:bool


def create_planner_app(repository,*,secure_cookies=True,extractor=None):
    app=FastAPI(title='CONVENE private planner',version='0.2.0')
    sessions=BrowserSessions(repository.dsn)
    intake=IntakeService(repository,extractor=extractor or OpenAIIntakeExtractor())
    model_slots=threading.BoundedSemaphore(2)
    from convene.catalog_planner import CatalogPlanner
    from convene.policy import PolicyDenied
    catalog_planner=CatalogPlanner(repository)

    @app.exception_handler(PolicyDenied)
    async def policy_denied(request,error):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=403,content={'detail':str(error)})

    @app.middleware('http')
    async def private_headers(request,call_next):
        response=await call_next(request)
        response.headers['Cache-Control']='no-store'
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='same-origin'
        return response

    @app.exception_handler(NotFound)
    async def not_found(request,error):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404,content={'detail':'Event not found.'})

    @app.exception_handler(Conflict)
    async def conflict(request,error):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=409,content={'detail':str(error)})

    def principal(request:Request):
        try:
            actor,csrf=sessions.resolve(request.cookies.get('convene_session'))
        except PermissionError as error:
            raise HTTPException(401,'Session required.') from error
        if request.method not in ('GET','HEAD','OPTIONS'):
            supplied=request.headers.get('X-CSRF-Token','')
            if not supplied or not hmac.compare_digest(supplied,csrf):
                raise HTTPException(403,'Invalid CSRF token.')
        return actor

    @app.get('/health')
    def health():return {'status':'ok','mode':'private_planner_preview'}

    @app.post('/api/session')
    def session(request:Request,response:Response):
        # Browsers cannot use a cross-site request to mint a session.
        if request.headers.get('sec-fetch-site')=='cross-site':
            raise HTTPException(403,'Open CONVENE directly to start a session.')
        existing=request.cookies.get('convene_session')
        if existing:
            try:
                actor,csrf=sessions.resolve(existing)
                return {'authenticated':actor.authenticated,'csrf_token':csrf}
            except PermissionError:pass
        token,actor,csrf=sessions.create()
        response.set_cookie('convene_session',token,httponly=True,secure=secure_cookies,
                            samesite='lax',max_age=14*86400,path='/')
        return {'authenticated':False,'csrf_token':csrf}

    @app.post('/api/logout',status_code=204)
    def logout(request:Request,response:Response,actor=Depends(principal)):
        sessions.revoke(request.cookies.get('convene_session'))
        response.delete_cookie('convene_session',path='/',secure=secure_cookies,httponly=True,samesite='lax')

    @app.post('/api/events',status_code=201)
    def start(actor=Depends(principal)):
        if len(repository.list_events(actor))>=20:
            raise HTTPException(429,'Event limit reached.')
        return intake.start(actor)

    @app.get('/api/events')
    def events(actor=Depends(principal)):
        return {'events':[event.model_dump(mode='json') for event in repository.list_events(actor)]}

    @app.get('/api/vendors')
    def approved_vendors(actor=Depends(principal)):
        from convene.vendor_directory import DirectoryRepository
        return DirectoryRepository(repository.dsn).list_approved()

    @app.post('/api/events/{event_id}/recommendations')
    def recommendations(event_id:UUID,body:ConfirmBody,actor=Depends(principal)):
        return catalog_planner.compare(actor,event_id,expected_version=body.expected_version)

    @app.get('/api/events/{event_id}/shortlist')
    def shortlist(event_id:UUID,expected_version:int=Query(ge=1),actor=Depends(principal)):
        return catalog_planner.shortlist(actor,event_id,expected_version=expected_version)

    @app.post('/api/events/{event_id}/shortlist')
    def select_vendor(event_id:UUID,body:ShortlistBody,actor=Depends(principal)):
        try:return catalog_planner.select(actor,event_id,body.vendor_id,vendor_version=body.vendor_version,
            expected_version=body.expected_version,selected=body.selected)
        except (Conflict,NotFound):raise
        except ValueError as error:raise HTTPException(422,str(error)) from error

    @app.post('/api/events/{event_id}/drafts')
    def inquiry_drafts(event_id:UUID,body:ConfirmBody,actor=Depends(principal)):
        return catalog_planner.drafts(actor,event_id,expected_version=body.expected_version)

    @app.get('/api/events/{event_id}')
    def event(event_id:UUID,actor=Depends(principal)):
        saved=repository.get_event(actor,event_id)
        question=next_question(saved.brief)
        return {'event':saved.model_dump(mode='json'),
                'messages':repository.intake_history(actor,event_id),
                'next_action':'answer' if question else 'review_brief'}

    @app.post('/api/events/{event_id}/messages')
    def reply(event_id:UUID,body:ReplyBody,actor=Depends(principal)):
        if not model_slots.acquire(blocking=False):raise HTTPException(429,'Planner busy; retry shortly.')
        try:
            return intake.reply(actor,event_id,body.message,expected_version=body.expected_version,request_id=body.request_id)
        except (Conflict,NotFound):raise
        except ValueError as error:
            raise HTTPException(422,'Please clarify that answer; your saved brief has not changed.') from error
        except Exception as error:
            # Do not expose provider payloads, credentials or parent messages in logs.
            logger.warning('Intake provider failed (%s)',type(error).__name__)
            raise HTTPException(503,'The planner is temporarily unavailable; your saved brief has not changed.') from error
        finally:model_slots.release()

    @app.post('/api/events/{event_id}/confirm')
    def confirm(event_id:UUID,body:ConfirmBody,actor=Depends(principal)):
        try:return intake.confirm(actor,event_id,expected_version=body.expected_version)
        except (Conflict,NotFound):raise
        except ValueError as error:raise HTTPException(422,str(error)) from error

    return app
