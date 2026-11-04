"""Isolated loopback API for browser tests. Never mutates the developer's demo DB."""
import os
from pathlib import Path
import sys
import tempfile

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'backend'))

if __name__=='__main__':
    with tempfile.TemporaryDirectory(prefix='finpilot-e2e-') as workspace:
        os.environ['DATABASE_PATH']=str(Path(workspace)/'e2e.db')
        os.environ['MODEL_MODE']='deterministic'
        os.environ['LANGSMITH_TRACING']='false'
        os.environ['EMBEDDING_PROVIDER']='local'
        os.environ['FINPILOT_ACCESS_TOKEN']='finpilot-local-e2e-service-token'
        import uvicorn
        uvicorn.run('finpilot.api:app',host='127.0.0.1',port=8100)
