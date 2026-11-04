"""Local preview factory. Not the public deployment entrypoint."""
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from convene.planner_api import create_planner_app
from convene.repository import Repository


def create_app():
    root=Path(__file__).resolve().parents[1]
    load_dotenv(root/'.env')
    repository=Repository(os.getenv('CONVENE_DATABASE_URL',''))
    app=create_planner_app(repository,secure_cookies=False)
    frontend=root/'frontend'/'dist'
    if not (frontend/'index.html').is_file():
        raise RuntimeError('Build frontend first: cd frontend; npm run build')
    app.mount('/assets',StaticFiles(directory=frontend/'assets'),name='planner-assets')

    @app.get('/',include_in_schema=False)
    def index():return FileResponse(frontend/'index.html')
    return app
