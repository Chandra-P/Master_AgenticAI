"""Usage: python run.py download|index|evaluate|export|serve."""
from pathlib import Path
import argparse

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['download','index','evaluate','export','serve']);a=p.parse_args()
    root=Path(__file__).resolve().parent
    from dotenv import load_dotenv
    load_dotenv(root/'.env',override=False)
    if a.command=='download':
        from pipeline.acquire import download_reports,CANDIDATES
        download_reports(CANDIDATES,root/'data')
    elif a.command=='index':
        from pipeline.index import build_index
        build_index(root/'data',root/'data/chroma')
    elif a.command=='evaluate':
        from pipeline.evaluate import evaluate
        evaluate(root)
    elif a.command=='export':
        from pipeline.export import export_site
        export_site(root)
    else:
        from pipeline.server import serve
        serve(root)
