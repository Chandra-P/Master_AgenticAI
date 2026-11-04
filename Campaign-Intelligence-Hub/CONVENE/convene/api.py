import logging
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from convene.models import EventBrief
from convene.storage import Store
from convene.workflow import plan_event

load_dotenv()
logger = logging.getLogger(__name__)

def create_app(db_path=None):
    app = FastAPI(title='CONVENE', version='0.1.0')
    store = Store(db_path or os.getenv('CONVENE_DB_PATH', 'data/convene.db'))

    @app.get('/health')
    def health():
        return {'status': 'ok'}

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
