"""CLI for the active question-answering RAG workspace."""
import argparse,json
from campaign_hub.config import Settings
from campaign_hub.models import RetrievalOptions
from campaign_hub.chunking.pipeline import STRATEGIES


def main():
    parser=argparse.ArgumentParser(description='Campaign Intelligence Hub: pure RAG')
    parser.add_argument('command',choices=['generate','validate','index','ask','evaluate'])
    parser.add_argument('--chunking',choices=[*STRATEGIES,'all'],default=RetrievalOptions().chunking)
    parser.add_argument('--retrieval',choices=['dense','hybrid'],default='hybrid')
    parser.add_argument('--rerank',action='store_true')
    parser.add_argument('--focus-context',action='store_true')
    parser.add_argument('--campaign',default=None,help='Optional campaign scope; default searches the entire corpus')
    parser.add_argument('--question',default='What are the tracking validation procedures?')
    parser.add_argument('--filters',default='{}',help='JSON metadata selections; values within fields use OR')
    parser.add_argument('--classify',action='store_true',help='Infer additional metadata constraints with configured classifier')
    parser.add_argument('--split',choices=['held_out','development'],default='held_out')
    parser.add_argument('--full',action='store_true',help='Evaluate every case in the selected split')
    parser.add_argument('--smoke',action='store_true',help='Evaluate one case per configuration')
    parser.add_argument('--extractive',action='store_true',help='Retrieval-only evaluation; no answer generation')
    parser.add_argument('--generated',action='store_true',help='Evaluate actual generated answers instead of retrieval only')
    parser.add_argument('--include-reranking',action='store_true',help='Include both reranking states in evaluation')
    parser.add_argument('--ragas',action='store_true',help='Opt-in measured generated-answer assessment')
    parser.add_argument('--ragas-limit',type=int,default=1)
    parser.add_argument('--quality',action='store_true',help='Add the existing complete-set quality gate to RAGAS')
    parser.add_argument('--metric-timeout',type=int,default=180)
    parser.add_argument('--judge-model')
    parser.add_argument('--judge-provider',choices=['ollama','openai','groq'])
    args=parser.parse_args()
    if args.ragas and (args.command!='evaluate' or args.extractive):parser.error('--ragas requires evaluate with generated answers, not --extractive')
    if args.quality and not args.ragas:parser.error('--quality requires --ragas')
    if args.ragas_limit<1 or args.metric_timeout<1:parser.error('Limits and timeouts must be positive')
    if args.generated and args.extractive:parser.error('Choose generated or retrieval-only evaluation')
    if args.smoke and args.full:parser.error('Choose smoke or full evaluation')
    if args.ragas and args.split!='held_out':parser.error('RAGAS assessment currently uses held_out cases')
    settings=Settings()
    if args.command=='generate':
        from campaign_hub.synthetic_data.generator import generate_corpus
        print(f"Generated {len(generate_corpus(settings.data)['documents'])} source documents.");return
    if args.command=='validate':
        from campaign_hub.synthetic_data.validation import validate_corpus
        errors=validate_corpus(settings.data)
        if errors:raise SystemExit(chr(10).join(errors))
        print('Corpus valid.');return
    from campaign_hub.rag.service import RAGService
    service=RAGService(settings)
    options=RetrievalOptions(chunking=args.chunking if args.chunking!='all' else 'section',
        retrieval=args.retrieval,reranking=args.rerank,focus_context=args.focus_context)
    if args.command=='index':
        for strategy in STRATEGIES if args.chunking=='all' else [args.chunking]:
            print(f'Indexing {strategy}...',flush=True);print(f'{service.index(strategy)} chunks indexed.',flush=True)
    elif args.command=='ask':
        result=service.answer_question(args.question,args.campaign,options,filters=json.loads(args.filters),automatic=args.classify)
        print(result['answer'])
        if result.get('status')=='filter_conflict':print(result['message'])
        print('Applied filters: '+json.dumps(result.get('effective_filters',{})))
    elif args.ragas:
        from campaign_hub.evaluation.ragas_assessment import RagasAssessor,run_assessment
        from campaign_hub.evaluation.quality import configure_evaluation_key
        configure_evaluation_key(settings.root/'.streamlit/secrets.toml')
        output=settings.data/('runs/quality/latest' if args.quality else 'runs/ragas/latest')
        with RagasAssessor(settings,quality=args.quality,timeout=args.metric_timeout,
                           judge_provider=args.judge_provider,judge_model=args.judge_model) as assessor:
            rows=run_assessment(service,output,[options],assessor,limit=args.ragas_limit,quality=args.quality)
        print(f'{len(rows)} assessments; see {output}/results.json')
    else:
        from campaign_hub.rag.evaluation import run_evaluation
        rows=run_evaluation(service,split=args.split,smoke=not args.full,generated=args.generated,
                            include_reranking=args.include_reranking)
        print(f"{len(rows)} measured question/configuration rows; {sum(bool(r.get('error')) for r in rows)} errors.")


if __name__=='__main__':main()
