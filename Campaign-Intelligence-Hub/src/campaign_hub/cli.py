import argparse
import json
from campaign_hub.config import Settings
from campaign_hub.models import RetrievalOptions


def main():
    parser=argparse.ArgumentParser(description='Campaign Intelligence Hub')
    parser.add_argument('command',choices=['generate','validate','index','ask','report','client-report','compare','evaluate'])
    parser.add_argument('--chunking',choices=['fixed','semantic','all'],default='semantic')
    parser.add_argument('--retrieval',choices=['dense','hybrid'],default='hybrid')
    parser.add_argument('--rerank',action='store_true')
    parser.add_argument('--campaign',default='TX-CHK-001')
    parser.add_argument('--question',default='What were the objectives?')
    parser.add_argument('--period')
    parser.add_argument('--smoke',action='store_true')
    parser.add_argument('--full',action='store_true')
    parser.add_argument('--judge',action='store_true',help='Run an additional local model support judge (slower)')
    parser.add_argument('--extractive',action='store_true',help='Skip model prose generation; preserve retrieved source wording')
    args=parser.parse_args()
    settings=Settings()
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
        packet=retrieve_client_packet(service,args.campaign,RetrievalOptions(chunking=args.chunking if args.chunking!='all' else 'semantic',retrieval=args.retrieval,reranking=args.rerank))
        if args.period and args.period!=packet['period']:
            raise ValueError('Requested period differs from source campaign reporting period')
        out=settings.data/'reports'
        out.mkdir(parents=True,exist_ok=True)
        (out/f'{args.campaign}-client.html').write_text(export_html(packet),encoding='utf-8')
        (out/f'{args.campaign}-client.md').write_text(packet_markdown(packet),encoding='utf-8')
        (out/f'{args.campaign}-client.json').write_text(json.dumps(packet,indent=2),encoding='utf-8')
        print(f'Validated client report exported: {out}')
        return
    options=RetrievalOptions(chunking=args.chunking if args.chunking!='all' else 'semantic',retrieval=args.retrieval,reranking=args.rerank)
    if args.command=='index':
        for strategy in ['fixed','semantic'] if args.chunking=='all' else [args.chunking]:
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
        from campaign_hub.evaluation.runner import run_experiments
        rows=run_experiments(service,settings.data/'runs/latest',smoke=not args.full,use_llm=not args.extractive,judge=args.judge)
        print(f"{len(rows)} experiments; {sum(bool(r.get('error')) for r in rows)} errors. See data/runs/latest/results.json")


if __name__=='__main__':
    main()
