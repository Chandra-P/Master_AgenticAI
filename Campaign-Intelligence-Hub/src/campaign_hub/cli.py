import argparse
import json
from campaign_hub.config import Settings
from campaign_hub.models import RetrievalOptions
from campaign_hub.chunking.pipeline import STRATEGIES


def main():
    parser=argparse.ArgumentParser(description='Campaign Intelligence Hub')
    parser.add_argument('command',choices=['generate','validate','index','ask','report','client-report','compare','evaluate'])
    parser.add_argument('--chunking',choices=[*STRATEGIES,'all'],default='section')
    parser.add_argument('--retrieval',choices=['dense','hybrid'],default='hybrid')
    parser.add_argument('--rerank',action='store_true')
    parser.add_argument('--focus-context',action='store_true',help='Opt-in question-focused evidence sections; preserve baseline when off')
    parser.add_argument('--campaign',default='TX-CHK-001')
    parser.add_argument('--question',default='What were the objectives?')
    parser.add_argument('--period')
    parser.add_argument('--smoke',action='store_true')
    parser.add_argument('--full',action='store_true')
    parser.add_argument('--judge',action='store_true',help='Run an additional local model support judge (slower)')
    parser.add_argument('--extractive',action='store_true',help='Skip model prose generation; preserve retrieved source wording')
    parser.add_argument('--ragas',action='store_true',help='Assess actual generated question answers with optional RAGAS metrics')
    parser.add_argument('--ragas-limit',type=int,default=1,help='Maximum held-out question cases per RAGAS configuration (default: 1)')
    parser.add_argument('--quality',action='store_true',help='Add factual correctness, passage verdicts and complete-set 90% gates to --ragas')
    parser.add_argument('--metric-timeout',type=int,default=180,help='Seconds allowed per RAGAS metric')
    parser.add_argument('--judge-model',help='RAGAS judge model; defaults to the configured generation model')
    parser.add_argument('--judge-provider',choices=['ollama','groq'],help='RAGAS judge provider; defaults to generation provider')
    args=parser.parse_args()
    if args.quality and not args.ragas:parser.error('--quality requires --ragas')
    if args.metric_timeout<1:parser.error('--metric-timeout must be positive')
    if args.ragas and (args.command!='evaluate' or args.extractive or args.judge):
        parser.error('--ragas requires evaluate with generated answers; do not combine it with --extractive or --judge')
    if args.ragas and args.ragas_limit<1:
        parser.error('--ragas-limit must be positive')
    settings=Settings()
    if args.ragas and (args.judge_provider=='groq' or settings.generation_provider=='groq'):
        from campaign_hub.evaluation.quality import configure_evaluation_key
        configure_evaluation_key(settings.root/'.streamlit/secrets.toml')
    if args.command=='generate':
        from campaign_hub.synthetic_data.generator import generate_corpus
        print(f"Generated {len(generate_corpus(settings.data)['documents'])} documents.")
        return
    if args.command=='validate':
        from campaign_hub.synthetic_data.validation import validate_corpus
        errors=validate_corpus(settings.data)
        if errors:
            raise SystemExit('\n'.join(errors))
        print('Corpus valid.')
        return
    from campaign_hub.reporting.service import CampaignService
    service=CampaignService(settings)
    if args.command=='client-report':
        from campaign_hub.reporting.client_packet import packet_markdown
        from campaign_hub.reporting.client_retrieval import retrieve_client_packet
        from campaign_hub.reporting.html_report import export_html
        packet=retrieve_client_packet(service,args.campaign,RetrievalOptions(chunking=args.chunking if args.chunking!='all' else 'section',retrieval=args.retrieval,reranking=args.rerank))
        if args.period and args.period!=packet['period']:
            raise ValueError('Requested period differs from source campaign reporting period')
        out=settings.data/'reports'
        out.mkdir(parents=True,exist_ok=True)
        (out/f'{args.campaign}-client.html').write_text(export_html(packet),encoding='utf-8')
        (out/f'{args.campaign}-client.md').write_text(packet_markdown(packet),encoding='utf-8')
        (out/f'{args.campaign}-client.json').write_text(json.dumps(packet,indent=2),encoding='utf-8')
        print(f'Validated client report exported: {out}')
        return
    options=RetrievalOptions(chunking=args.chunking if args.chunking!='all' else 'section',retrieval=args.retrieval,reranking=args.rerank,focus_context=args.focus_context)
    if args.command=='index':
        for strategy in STRATEGIES if args.chunking=='all' else [args.chunking]:
            print(f'Indexing {strategy}...',flush=True)
            print(f'{service.index(strategy)} chunks indexed.',flush=True)
    elif args.command=='report':
        from campaign_hub.reporting.render import render_report
        period=args.period or service.campaigns.get(args.campaign,{}).get('period','unknown')
        report=service.generate_report(args.campaign,period,options,use_llm=not args.extractive)
        out=settings.data/'reports'
        out.mkdir(parents=True,exist_ok=True)
        (out/f'{args.campaign}.md').write_text(render_report(report,client_facing=True),encoding='utf-8')
        (out/f'{args.campaign}-technical.md').write_text(render_report(report),encoding='utf-8')
        (out/f'{args.campaign}.json').write_text(report.model_dump_json(indent=2),encoding='utf-8')
        print(f"Report: {out/args.campaign}.md — {report.status}")
    elif args.command=='ask':
        print(service.answer_question(args.question,args.campaign,options)['answer'])
    elif args.command=='compare':
        result=service.compare_with_history(args.campaign,options)
        print(json.dumps({k:v for k,v in result.items() if k!='evidence'},indent=2))
    elif args.command=='evaluate':
        if args.ragas:
            from dataclasses import replace
            from campaign_hub.evaluation.ragas_assessment import RagasAssessor,run_assessment,METRICS
            from campaign_hub.evaluation.runner import configurations
            judge_settings=replace(settings,generation_provider=args.judge_provider or settings.generation_provider,
                generation_model=args.judge_model or settings.generation_model)
            output=settings.data/('runs/quality/latest' if args.quality else 'runs/ragas/latest')
            with RagasAssessor(judge_settings,quality=args.quality,timeout=args.metric_timeout) as assessor:
                configs=configurations() if args.full else [options]
                if args.focus_context:configs=[c.model_copy(update={'focus_context':True}) for c in configs]
                rows=run_assessment(service,output,configs,assessor,limit=args.ragas_limit,quality=args.quality)
            available={m:sum(r.get(m) is not None for r in rows) for m in METRICS}
            print(f'{len(rows)} RAGAS assessments; measured scores: {available}. See {output}/results.json')
            if args.quality:
                summaries=json.loads((output/'quality-summary.json').read_text(encoding='utf-8'))
                print('Quality target statuses: '+', '.join(s['status'] for s in summaries))
            return
        from campaign_hub.evaluation.runner import run_experiments
        rows=run_experiments(service,settings.data/'runs/latest',smoke=not args.full,use_llm=not args.extractive,judge=args.judge)
        print(f"{len(rows)} experiments; {sum(bool(r.get('error')) for r in rows)} errors. See data/runs/latest/results.json")


if __name__=='__main__':
    main()
