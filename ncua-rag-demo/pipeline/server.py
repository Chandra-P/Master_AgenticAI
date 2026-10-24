"""Small Python API: all live retrieval runs through LangChain and Chroma."""
from __future__ import annotations
import json,os,re,time,threading,hmac
from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from collections import defaultdict,deque

def validate_request(payload:dict)->dict:
    if not isinstance(payload,dict):raise ValueError('Request must be an object')
    q=payload.get('question','')
    if not isinstance(q,str) or not 3<=len(q.strip())<=1200:raise ValueError('Question must contain 3–1200 characters')
    strategy=payload.get('strategy','semantic')
    if strategy not in ('fixed','semantic'):raise ValueError('Unknown chunking strategy')
    charter=payload.get('charter','');year=str(payload.get('year',''))
    if not isinstance(charter,str) or (charter and not re.fullmatch(r'\d{1,5}',charter)):raise ValueError('Invalid charter')
    if year and year not in ('2021','2022','2023','2024','2025'):raise ValueError('Unsupported reporting year')
    filters={}
    if charter:filters['charter']=charter
    if year:filters['year_'+year]=True
    return {'question':q.strip(),'filters':filters,'strategy':strategy,'rerank':bool(payload.get('rerank',True))}

def serve(root:Path,port:int=8765):
    from dotenv import load_dotenv
    load_dotenv(Path(root)/'.env',override=False)
    from .index import Store,LocalEmbeddings,RERANKER_REVISION
    from .graph import build_graph,groq_model
    from sentence_transformers import CrossEncoder
    root=Path(root).resolve();manifest=json.loads((root/'data/manifest.json').read_text())
    embedder=LocalEmbeddings();reranker=CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2',revision=RERANKER_REVISION,local_files_only=os.getenv('HF_HUB_OFFLINE')=='1')
    llm=groq_model();graphs={s:build_graph(Store(root/'data/chroma',s,embedder),llm,reranker) for s in ('fixed','semantic')}
    lock=threading.Lock();traffic=defaultdict(deque);global_traffic=deque();total_generation=0
    token=os.getenv('RAG_BACKEND_TOKEN','')
    if llm and not token:raise RuntimeError('A server token is required before enabling public Groq generation')
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send_json(self,value,status=200):
            body=json.dumps(value).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
        def authorized(self):
            # Loopback development may run without token; remote proxy always gets a token.
            return not token or hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+token)
        def do_GET(self):
            if not self.authorized():return self.send_json({'error':'Unauthorized'},401)
            if self.path!='/api/status':return self.send_json({'error':'Not found'},404)
            self.send_json({'ready':True,'generation':bool(llm),'vector_store':'ChromaDB','framework':'LangChain + LangGraph',
                            'institutions':len({r['charter'] for r in manifest['reports'] if r['status']=='downloaded'}),'reports':sum(r['status']=='downloaded' for r in manifest['reports'])})
        def do_POST(self):
            nonlocal total_generation
            if not self.authorized():return self.send_json({'error':'Unauthorized'},401)
            if self.path!='/api/ask':return self.send_json({'error':'Not found'},404)
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=8000:raise ValueError('Invalid request size')
                payload=json.loads(self.rfile.read(length));request=validate_request(payload)
            except (ValueError,TypeError,json.JSONDecodeError):return self.send_json({'error':'Invalid question or filters'},400)
            # Shared demo budget and single inference lock protect the local CPU and Groq quota.
            now=time.monotonic();identity=self.headers.get('X-Visitor-Id','anonymous')[:100]
            while global_traffic and now-global_traffic[0]>60:global_traffic.popleft()
            if len(global_traffic)>=12:return self.send_json({'error':'The shared demo request limit has been reached. Try again in a minute.'},429)
            history=traffic[identity]
            while history and now-history[0]>60:history.popleft()
            if len(history)>=6:return self.send_json({'error':'Please wait a minute before asking more questions.'},429)
            if llm and total_generation>=int(os.getenv('RAG_GENERATION_BUDGET','100')):return self.send_json({'error':'Demo generation budget reached.'},429)
            if not lock.acquire(blocking=False):return self.send_json({'error':'Another question is being processed. Please try again shortly.'},429)
            history.append(now)
            global_traffic.append(now)
            try:
                start=time.perf_counter()
                if llm:total_generation+=1
                result=graphs[request.pop('strategy')].invoke(request)
                result['seconds']=round(time.perf_counter()-start,3)
                self.send_json(result)
            except Exception:return self.send_json({'error':'Retrieval is temporarily unavailable. Please try again.'},503)
            finally:lock.release()
    print(f'RAG API ready http://127.0.0.1:{port}; generation={bool(llm)}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()

if __name__=='__main__':
    import argparse,getpass
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--port',type=int,default=8765);p.add_argument('--runtime-stdin',action='store_true');args=p.parse_args()
    if args.runtime_stdin:
        raw=getpass.getpass('Runtime configuration JSON (hidden): ')
        settings=json.loads(raw)
        for k,v in settings.items():
            if k in {'RAG_BACKEND_TOKEN','GROQ_API_KEY','GROQ_MODEL'}:os.environ[k]=str(v)
    serve(args.root,args.port)
