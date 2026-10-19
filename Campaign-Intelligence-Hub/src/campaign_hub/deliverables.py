"""Reproducible HTML handoff documents from code and measured artifacts.

Run from the project: python -m campaign_hub.deliverables
No model calls or network requests are made by this command.
"""
import ast
import csv
from html import escape
import json
from pathlib import Path
from statistics import mean
from campaign_hub.reporting.dashboard import vendor, chart_runtime, STYLE
from campaign_hub.reporting.html_report import CSS, export_html


def technical_kit(root):
    root=Path(root);src=root/'src/campaign_hub'
    def text(path):return (src/path).read_text(encoding='utf-8')
    def code(path):return '<details><summary>'+escape(path)+' · exact implementation</summary><pre>'+escape(text(path))+'</pre></details>'
    def section(n,title,body):return f'<section id="section-{n}"><div class="section-head"><span>{n:02d}</span><h2>{title}</h2></div>{body}</section>'
    def card(title,body):return '<article class="copy-card"><h3>'+title+'</h3>'+body+'</article>'
    def p(value):return '<p>'+value+'</p>'
    columns=list(csv.DictReader((root/'docs/evaluation/three-chunking-comparison.csv').open(encoding='utf-8',newline='')))
    rows=json.loads((root/'docs/evaluation/three-chunking-results.json').read_text(encoding='utf-8'))
    ragas=json.loads((root/'docs/evaluation/ragas-smoke-results.json').read_text(encoding='utf-8'))
    manifest=json.loads((root/'data/manifest.json').read_text(encoding='utf-8'))
    parts=['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Campaign Intelligence Hub · Technical Solution Kit</title><style>',
        vendor('bootstrap.min.css'),CSS,STYLE,
        '.flow{display:flex;gap:12px;flex-wrap:wrap}.flow div{background:#eaf5f3;border:1px solid #c2dcd7;padding:17px;border-radius:8px;flex:1;min-width:140px}.copy-card h3{font-size:20px}.copy-card{margin-bottom:14px}.kit-table{background:white;padding:16px;border-radius:9px}pre{max-height:550px}.diagram{background:#10263d;color:#fff;padding:25px;border-radius:10px;white-space:pre-wrap}section>p{max-width:950px}.copy-card code{color:#087f80}',
        '</style></head><body><header class="hero"><div class="wrap"><div class="brand">Campaign Intelligence Hub / Engineering handoff</div><div class="eyebrow">Technical Solution Kit</div><h1>Evidence to executive reporting.</h1><p class="lead">Transform campaign objectives, success plans, KPI definitions, campaign results, and historical insight decks into executive-ready performance reporting and actionable insights.</p><div class="hero-rule"></div><div class="hero-meta">Implementation review · 18 October 2026 · Synthetic demonstration</div></div></header>',
        '<nav aria-label="Kit sections"><div class="wrap">'+''.join(f'<a href="#section-{i}">{label}</a>' for i,label in enumerate(['Solution','Components','Decisions','Prompts','Alternatives','Results','Handoff'],1))+'</div></nav><main class="wrap">']
    flow='<div class="flow">'+''.join('<div>'+x+'</div>' for x in ['Generate &amp; validate sources →','Clean &amp; chunk →','Embed &amp; persist in Chroma →','Filter / retrieve / rerank →','Validate evidence →','Calculate &amp; cite →','Present HTML'])+'</div>'
    parts.append(section(1,'The solution we built',card('Business problem and use case',p('Campaign analysts reconcile briefs, success plans, results and previous campaigns before client meetings. This application centralizes evidence, compares approved goals with attributed outcomes, and prepares chart-led, cited HTML reports for analyst review.')+
        p('The business workflow is client → campaign → live map and KPIs → historical standing → generated client report. Questions use a separate cited RAG answer path. Visitors use the hosted app without installing models or supplying credentials.'))+
        flow+card('Architecture and workflow',p('LangChain supplies model, embedding, structured-output and Chroma adapters. Chroma persists model/configuration-isolated collections. LangGraph orchestrates the eleven-section analytical report. The final client dashboard follows a separate retrieval-backed frozen-packet path; it does not publish arbitrary model prose.')+
        '<pre class="diagram">Synthetic Markdown + manifest\n  ├─ source validation → campaign snapshot → Streamlit KPIs / map\n  ├─ chunking → embedding cache → persistent Chroma\n  │    ├─ metadata filter → dense or BM25 fusion → optional reranker\n  │    │    ├─ question → structured claims → verbatim support / citations\n  │    │    └─ client report → validated parent expansion → frozen packet\n  │    │         → Python metrics → validation → HTML / Chart.js\n  │    └─ LangGraph analytical report → evidence / citation validation\n  └─ held-out questions → saved retrieval / optional RAGAS artifacts</pre>')))
    components=[
        ('2.1 Synthetic data generation','synthetic_data/generator.py',
         f'Seed 42 produces {len(manifest["documents"])} documents and {len(manifest["campaigns"])} campaigns across five fictional clients. Counts: 20 briefs, 20 plans, 20 performance reports, 20 historical insight documents, 10 strategies, 10 best-practice guides, five KPI dictionaries and five methodologies. Campaign ID joins documents; client/product/period define comparison eligibility. Geography and audience observations reconcile with attributed accounts. These are fictional source facts, not real client results.'),
        ('2.2 Data preprocessing','ingestion/markdown.py','Manifest paths and hashes are checked before use; YAML metadata is extracted, front matter/title removed and heading/body spans preserved. Generated reports are not ingested. Real PDF, DOCX, PPTX, spreadsheet and database connectors remain FUTURE WORK.'),
        ('2.3 Fixed chunking','chunking/pipeline.py','Fixed chunks use a 500-token bound and 50-token overflow overlap with cl100k_base token accounting. Configuration identity is stored with the index; model token windows separately prevent silent encoder truncation.'),
        ('2.4 Semantic chunking','chunking/semantic.py','Sentence/unit embeddings detect topic changes using cosine-distance breakpoints at the 65th percentile, preserving source spans with bounded overflow. The separate section mode uses document headings. These three strategies are evaluated separately.'),
        ('2.5 Embedding model','embeddings/providers.py','Local default: embeddinggemma through Ollama. Hosted default and saved three-chunker experiment: all-MiniLM-L6-v2 on CPU. BAAI/bge-small-en-v1.5 is selectable through the existing CPU provider, but it has not been measured here. Changing models requires fresh compatible indexes; no BGE superiority claim is made.'),
        ('2.6 ChromaDB architecture','vectordb/chroma_store.py','PersistentClient and the LangChain Chroma adapter store chunk text, vectors and scalar metadata. Model/chunker identity isolates collections. Corpus hash and compatibility manifest prevent querying stale indexes. Metadata includes document, campaign, client, product, period, source hash, heading and chunk spans.'),
        ('2.7 Retrieval','retrieval/pipeline.py','Dense similarity retrieval filters the campaign/document type before candidate ranking. Default candidate K is 20 and final K is five. Final report source planning also fetches eligible historical evidence; arbitrary cross-client mixing is excluded.'),
        ('2.8 Hybrid retrieval','retrieval/pipeline.py','BM25 tokenizes lexical terms; dense and lexical ranks combine using reciprocal-rank fusion with constant 60. Fusion preserves underlying scores and deterministic tie order; it does not interpret embedding similarity as calibrated confidence.'),
        ('2.9 Reranking','reranking/cross_encoder.py','Optional cross-encoder/ms-marco-MiniLM-L-6-v2 scores query–passage relevance. UI/CLI toggles permit on/off comparisons. The saved experiments show additional latency and no uniform quality improvement.'),
        ('2.10 LangGraph workflow','langgraph/workflow.py','The executable graph has query_understanding → retrieve_rerank_generate_sections → citation_validation. Retrieval, fusion, reranking, context checks, generation and citation assembly execute inside the combined service node. Six independently executable stage nodes remain FUTURE WORK; they are not separate nodes today.'),
        ('2.11 Campaign report generation','reporting/client_retrieval.py','The final report retrieves source chunks, validates parent expansion, freezes a cited source packet and calculates KPIs in Python. Identity, source hashes, source table totals, goals, cohort maturity and narrative are revalidated at export. Chart.js adds interaction; inline SVG/table fallbacks remain available. Source-based findings are deterministic. No guarantee of perfect real-world accuracy follows from these checks.'),
        ('2.12 Evaluation framework','evaluation/runner.py','Thirty gold questions include expected facts and source/section citations; three are calibration and 27 are held out. Twelve configurations cover three chunkers, two retrieval modes and reranking on/off. Real RAGAS assessments are optional and saved separately from document-overlap metrics. Missing judgments are null, never perfect scores.')]
    parts.append(section(2,'Component deep dives',''.join(card(title,p(body)+code(path)) for title,path,body in components)))
    decisions=[('Why synthetic data','Reproducibility, shareability and no exposure of client records. Tradeoff: synthetic source-derived gold can inflate apparent retrieval quality.'),
        ('Why ChromaDB','A local persistent vector store with metadata filters fits the free demonstration. Tradeoff: shared multi-tenant durability, access controls and operations need a production design.'),
        ('Why BGE is an alternative','BGE is an open embedding option named in the brief. The working hosted profile uses MiniLM for its CPU footprint; there is no matched BGE experiment to justify replacing a working index.'),
        ('Why semantic boundaries','Embedding changes can split topic shifts within headings; heading-based chunks remain a cheaper structural baseline. Topic segmentation adds preprocessing cost and is not always better.'),
        ('Why hybrid search','Exact campaign/KPI terms complement dense meaning. Measured recall can improve, while precision and latency must still be checked.'),
        ('Why LangGraph','Explicit orchestration and citation validation make analytical report flow inspectable. The current small graph is intentionally described as implemented; full stage decomposition remains future work.'),
        ('Why constrained client narrative','Client-facing figures and observations come from validated tables and source sentences. Generated hypotheses cannot become facts; causes, ROI and expected impact are unavailable without evidence.')]
    parts.append(section(3,'Key design decisions','<div class="panel-grid">'+''.join(card(a,p(b)) for a,b in decisions)+'</div>'))
    # Extract literal system instructions directly from executable call sites.
    prompt_cards=[]
    for node in ast.walk(ast.parse(text('reporting/service.py'))):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='generate_json' and node.args and isinstance(node.args[0],ast.Constant):
            value=node.args[0].value
            prompt_cards.append(card('Runtime system prompt · reporting/service.py:'+str(node.lineno),'<pre>'+escape(value)+'</pre>'))
    parts.append(section(4,'Exact prompt library',''.join(prompt_cards)+p('Human messages supply JSON containing the question/section, campaign and source IDs/text. LangChain templates bind system and question fields; provider adapters enforce the Pydantic schema. The client dashboard uses validated source facts rather than a narrative generation prompt.')+
        code('generation/providers.py')+code('evaluation/judge.py')+code('evaluation/precision_prompt.py')))
    parts.append(section(5,'Alternatives considered','<div class="panel-grid">'+
        card('Fixed vs section vs semantic',p('Fixed: cheapest deterministic token windows. Section: strong structural baseline for well-authored documents. Semantic: embedding-derived topic boundaries, with additional preprocessing and model dependence. Choose using held-out measurements, not the label.'))+
        card('Dense vs hybrid',p('Dense captures paraphrases. BM25 fusion adds lexical matches for campaign IDs and KPI terminology. Hybrid may increase recall without improving precision; use the tables below.'))+
        card('Reranking vs no reranking',p('Reranking can reorder the candidate pool but cannot recover evidence absent from it. CPU latency is materially higher in several saved configurations.'))+
        card('Local vs hosted generation',p('Local Ollama Llama needs no API key. Hosted generation uses the owner-configured Groq model and server key; the currently documented hosted profile differs from Llama. Final deterministic dashboard export needs retrieval embeddings, not LLM prose.'))+'</div>'))
    headers=['Chunking','Retrieval','Rerank','MRR@5','Document overlap precision','Document overlap recall','Mean latency (s)','Expected-fact completeness']
    table=['<div class="table-wrap kit-table"><table class="table table-sm"><caption>Measured 12-configuration comparison · 27 held-out cases each</caption><thead><tr>'+''.join('<th scope="col">'+x+'</th>' for x in headers)+'</tr></thead><tbody>']
    def score(value):return f'{float(value):.4f}' if value not in ('',None) else 'Unavailable'
    for row in columns:
        match=[r for r in rows if r['chunking']==row['chunking'] and r['retrieval']==row['retrieval'] and str(r['reranking'])==row['reranking']]
        complete=[r['completeness'] for r in match if isinstance(r.get('completeness'),(int,float))]
        vals=[row['chunking'],row['retrieval'],row['reranking']]+[score(row[k]) for k in ['mrr','context_precision','context_recall','latency_seconds']]+[score(mean(complete)) if complete else 'Unavailable']
        table.append('<tr>'+''.join('<td>'+escape(v)+'</td>' for v in vals)+'</tr>')
    table.append('</tbody></table></div>')
    charts=[]
    for key,title in [('context_precision','Document overlap precision'),('context_recall','Document overlap recall'),('latency_seconds','Mean latency by configuration')]:
        labels=[r['chunking']+'/'+r['retrieval']+('/rerank' if r['reranking']=='True' else '') for r in columns]
        panels=dict(labels=labels,values=[float(r[key]) for r in columns],unit='seconds' if key=='latency_seconds' else 'percent',highlights=list(range(len(columns))))
        charts.append(panels)
        table.append('<figure class="chart-card"><h3>'+title+'</h3><div class="interactive-chart" hidden><canvas id="interactive-'+str(len(charts))+'" role="img" aria-label="'+title+'"></canvas></div><div class="static-chart"><p>Exact values remain available in the comparison table above.</p></div><p class="chart-note">Source: docs/evaluation/three-chunking-comparison.csv</p></figure>')
    table.append('<h3>Actual RAGAS smoke assessments</h3><div class="table-wrap kit-table"><table class="table"><thead><tr><th>Case / run</th><th>Faithfulness</th><th>Passage precision</th><th>Reference-claim recall</th></tr></thead><tbody>')
    for row in ragas:
        vals=[row['case_id']+' / prompt v'+str(row['identity'].get('precision_prompt_version',1))]+[score(row.get(k)) for k in ['ragas_faithfulness','ragas_context_precision','ragas_context_recall']]
        table.append('<tr>'+''.join('<td>'+escape(v)+'</td>' for v in vals)+'</tr>')
    table.extend(['</tbody></table></div>',p('Missing judgment means unavailable: abstention, parser failure, timeout, or a metric not reassessed. The precision-only retry reuses a saved answer/context and is not a new full evaluation. Scores from different prompt versions are not pooled. The same Llama model generated and judged these smoke answers; they are not an independent factual benchmark.'),
        p(f'Raw evidence: {len(rows)} rows; {sum(bool(r.get("error")) for r in rows)} execution errors. The saved matrix is extractive/retrieval-oriented, not a 324-answer LLM quality benchmark. Document overlap precision/recall are not RAGAS passage judgments. Expected-fact completeness is string matching, not report quality. Faithfulness is unavailable for the full matrix. Small samples and uncontrolled cold starts limit interpretation.'),
        p('Artifacts: docs/evaluation/three-chunking-results.json; three-chunking-comparison.csv; ragas-smoke-results.json. These measured values are reproduced, not fabricated or copied from peer projects.')])
    parts.append(section(6,'Experimental results',''.join(table)))
    parts.append(section(7,'Setup, deployment and implementation boundaries',card('Run the project','<pre>python -m pip install -e .\npython -m campaign_hub generate\npython -m campaign_hub validate\npython -m campaign_hub index --chunking all\npython -m streamlit run app.py\npython -m pytest -q\npython -m campaign_hub.deliverables</pre>'+p('Local defaults require Ollama models llama3.2:3b and embeddinggemma. The live public demo uses the hosted server-side model profile; keys stay in Streamlit secrets. See README.md and docs/cloud-quickstart.md for complete setup and Community Cloud deployment.'))+
        card('Explicit BGE profile','<pre>$env:CIH_EMBEDDING_PROVIDER="sentence_transformers"\n$env:CIH_EMBEDDING_MODEL="BAAI/bge-small-en-v1.5"\npython -m campaign_hub index --chunking all\npython -m streamlit run app.py</pre>'+p('This profile is configurable but unbenchmarked. Never mix existing MiniLM measurements with a BGE claim. New model downloads require internet; model inference is local.'))+
        card('Folder structure','<pre>app.py                    Client-facing Streamlit workspace\nassets/                   Generated decorative app image\nsrc/campaign_hub/\n  synthetic_data/         Corpus generator and validation\n  ingestion/              Markdown parsing and metadata\n  chunking/               Fixed, section, semantic\n  embeddings/             Ollama / CPU encoder adapters\n  vectordb/               Persistent Chroma\n  retrieval/              Dense / BM25 fusion\n  reranking/              Cross-encoder\n  langgraph/              Analytical report workflow\n  reporting/              Facts, citations, HTML dashboard\n  evaluation/             Held-out experiments / RAGAS\n  ui/                     Client pages / retained dev views\ndata/corpus/              110 synthetic inputs\ndata/evaluation/          30 gold cases\ndocs/evaluation/          Saved measured artifacts\ndocs/technical_solution_kit.html\ndocs/campaign_performance_dashboard.html</pre>')+
        card('Readiness and future work',p('The original checklist remains 94/102 implemented (92.2% feature coverage). It is not a production-readiness or factual-accuracy percentage. Six independently executable graph stages, calibrated confidence and a matched embedding-model experiment remain FUTURE WORK.')+
        p('Additional production gaps: real-file ingestion, authenticated client isolation, durable multi-user storage, independently reviewed factual evaluation, licensed industry benchmarks and sustained load/accessibility testing. The new dashboard honestly marks unavailable net-deposit trends, opening-date trends, funded stages, funnel events and ROI. Temporal/funding source collection is FUTURE WORK, not simulated performance evidence.')+
        p('Report-only technical pages remain hidden from the client UI per the product decision. The current demonstration supports direct mail and display only; attribution windows are 60 days from mail/drop and 30 days from exposure. Opening balances are neither net deposit growth nor revenue.'))+
        card('Frontend provenance',p('Pinned, bundled MIT assets: <a href="https://www.chartjs.org/docs/latest/getting-started/installation.html">Chart.js 4.5.1</a> and <a href="https://getbootstrap.com/docs/5.3/getting-started/introduction/">Bootstrap 5.3.8</a>. Licenses accompany the vendor assets. Reports make no CDN requests; JavaScript charts have static/table fallbacks.'))))
    parts.extend(['</main><footer><div class="wrap">Campaign Intelligence Hub · Technical handoff · Implementation facts and measured artifacts; no invented benchmark results.</div></footer>',chart_runtime(charts),'</body></html>'])
    return ''.join(parts)


def build_deliverables(root,packet_path=None):
    root=Path(root)
    packet_path=Path(packet_path) if packet_path else root/'data/reports/TX-CHK-001-client.json'
    packet=json.loads(packet_path.read_text(encoding='utf-8'))
    html=export_html(packet)
    outputs={'technical_solution_kit.html':technical_kit(root),'campaign_performance_dashboard.html':html}
    for name,value in outputs.items():
        (root/'docs'/name).write_text(value,encoding='utf-8')
    return list(outputs)


if __name__=='__main__':
    from campaign_hub.config import Settings
    print('\n'.join(build_deliverables(Settings().root)))
