import logging
import os
import json
from queue import Queue, Empty
import threading
import time
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from convene.party_catalog import get_catalog
from convene.models import EventBrief
from convene.storage import Store
from convene.workflow import plan_event
from convene import venue_research
from convene.party_agent import AgentRequest, AgentError, run_agent
from convene.deadlines import DeadlineError

load_dotenv()
logger = logging.getLogger(__name__)
_agent_slots = threading.BoundedSemaphore(2)

def create_app(db_path=None,*,allow_web_research=None):
    allow_web_research=(os.getenv('CONVENE_ALLOW_WEB_RESEARCH','false').lower()=='true'
                        if allow_web_research is None else allow_web_research)
    app = FastAPI(title='CONVENE', version='0.1.0')
    web_root = Path(__file__).resolve().parent.parent / 'web'
    app.mount('/assets', StaticFiles(directory=web_root / 'assets'), name='party-assets')

    @app.get('/', include_in_schema=False)
    def website():
        return FileResponse(web_root / 'index.html')

    @app.get('/web/{filename}', include_in_schema=False)
    def website_asset(filename: str):
        if filename not in {'styles.css', 'app.js', 'planner.mjs'}:
            raise HTTPException(status_code=404)
        media = 'text/css' if filename.endswith('.css') else 'application/javascript'
        return FileResponse(web_root / filename, media_type=media)

    @app.get('/party/catalog')
    def party_catalog():
        return get_catalog()

    @app.post('/party/agent')
    def party_agent(request: AgentRequest):
        if request.mode=='live' and not allow_web_research:
            raise HTTPException(status_code=403,detail='Web research is disabled; use the approved catalog planner on port 8001.')
        if request.mode == 'live' and not os.getenv('OPENAI_API_KEY'):
            raise HTTPException(status_code=503, detail='Live planning requires OPENAI_API_KEY.')
        if not _agent_slots.acquire(blocking=False):
            raise HTTPException(status_code=429, detail='Planning agents are busy; retry shortly.')
        events = Queue()
        stopped = threading.Event()

        def emit(event):
            if not stopped.is_set():
                events.put(event)

        def work():
            try:
                result = run_agent(request, emit, stopped.is_set)
                emit({'type': 'result', 'result': result})
            except (AgentError, DeadlineError) as error:
                emit({'type': 'error', 'message': str(error)})
            except Exception:
                emit({'type': 'error', 'message': 'Agent run failed; no bookings or messages were made.'})
            finally:
                _agent_slots.release()

        def stream():
            deadline = time.monotonic() + 120
            try:
                while time.monotonic() < deadline:
                    try:
                        event = events.get(timeout=0.5)
                    except Empty:
                        continue
                    yield json.dumps(event) + '\n'
                    if event['type'] in ('result', 'error'):
                        return
                yield json.dumps({'type': 'error', 'message': 'Planning deadline exceeded; try catalog-only comparison.'}) + '\n'
            finally:
                stopped.set()

        threading.Thread(target=work, daemon=True).start()
        return StreamingResponse(stream(), media_type='application/x-ndjson',
                                 headers={'Cache-Control': 'no-store', 'X-Accel-Buffering': 'no'})
    store = Store(db_path or os.getenv('CONVENE_DB_PATH', 'data/convene.db'))

    @app.get('/health')
    def health():
        return {'status': 'ok'}

    @app.post('/venues/research')
    def research_venues(request: venue_research.ResearchRequest):
        if not allow_web_research:
            raise HTTPException(status_code=403,detail='Web research is disabled; use the approved vendor directory.')
        try:
            return venue_research.research_venues(request)
        except venue_research.ResearchError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

    @app.post('/plans', status_code=201)
    def create_plan(brief: EventBrief):
        try:
            result = plan_event(brief.model_dump(mode='json'))
        except ValueError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        except Exception as error:
            logger.exception('Planning workflow failed')
            raise HTTPException(status_code=502, detail='Planning service failed; check server logs and service configuration.') from error
        store.save(result)
        return result

    @app.get('/plans')
    def list_plans():
        return store.list()

    @app.get('/plans/{plan_id}')
    def get_plan(plan_id: str):
        plan = store.get(plan_id)
        if plan is None:
            raise HTTPException(status_code=404, detail='Plan not found')
        return plan

    return app

app = create_app()
