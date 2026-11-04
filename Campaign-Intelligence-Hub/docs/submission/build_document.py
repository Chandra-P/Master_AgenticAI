"""Build the course overview with the bundled runtime and python-docx."""
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT

OUT=Path(__file__).resolve().parent / 'Campaign_Knowledge_RAG.docx'
doc=Document()
sec=doc.sections[0]
sec.page_width=Inches(8.5);sec.page_height=Inches(11)
sec.top_margin=sec.bottom_margin=Inches(.7)
sec.left_margin=sec.right_margin=Inches(.8)
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2']:
    s=doc.styles[name];s.font.name='Calibri';s.font.color.rgb=RGBColor(0,0,0)
    s.paragraph_format.space_after=Pt(7)
    s.paragraph_format.line_spacing=1.08
normal=doc.styles['Normal'];normal.font.size=Pt(10.5)
for name,size in [('Title',25),('Subtitle',11),('Heading 1',15),('Heading 2',11.5)]:
    doc.styles[name].font.size=Pt(size)
    doc.styles[name].paragraph_format.space_before=Pt(13 if name.startswith('Heading') else 0)
    doc.styles[name].paragraph_format.keep_with_next=True

def p(text,style=None):return doc.add_paragraph(text,style)
def h(text):doc.add_heading(text,1)
def table(headers,rows,widths):
    t=doc.add_table(rows=1, cols=len(headers));t.autofit=False;t.alignment=WD_TABLE_ALIGNMENT.CENTER
    for i,w in enumerate(widths):t.columns[i].width=Inches(w)
    for i,v in enumerate(headers):t.rows[0].cells[i].text=v
    for row in rows:
        cells=t.add_row().cells
        for i,v in enumerate(row):cells[i].text=v
    for ri,row in enumerate(t.rows):
        for ci,c in enumerate(row.cells):
            c.width=Inches(widths[ci]);c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            pr=c._tc.get_or_add_tcPr();b=OxmlElement('w:tcBorders')
            for edge in ['top','left','bottom','right']:
                e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');b.append(e)
            pr.append(b)
            margins=OxmlElement('w:tcMar')
            for edge in ['top','bottom','left','right']:
                e=OxmlElement('w:'+edge);e.set(qn('w:w'),'100');e.set(qn('w:type'),'dxa');margins.append(e)
            pr.append(margins)
            sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E8EEF4' if ri==0 else ('F7F9FB' if ri%2==0 else 'FFFFFF'));pr.append(sh)
            for par in c.paragraphs:
                par.paragraph_format.space_after=Pt(2);par.paragraph_format.line_spacing=1.02
                for run in par.runs:run.font.size=Pt(9.5);run.bold=ri==0
    repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
    doc.add_paragraph().paragraph_format.space_after=Pt(0)

p('Campaign knowledge RAG course project','Title')
p('Week 2 submission overview  |  25 October 2026','Subtitle')
p('My RAG app helps campaign analysts answer objectives, measurement and operating-policy questions from 122 English synthetic campaign documents in Streamlit. It targets 90 percent generated-answer faithfulness and 80 percent passage relevance precision on a calibrated evaluation set. These are acceptance targets, not measured achievements.')
h('Use case and scope')
p('This project follows the bring-your-own use case on the LangChain and LangGraph code track. It applies chunking, reranking and evaluation experiments to a campaign knowledge base. Apple SEC filings, Pinecone and Jev are reference choices rather than additional project requirements. The active application contains Ask Questions, Analyst View, Chunking Lab and Evaluation.')
h('Dataset and stewardship')
table(['Source group','Documents','Purpose'],[
('Campaign documents','80','Brief, success plan, performance report and historical deck for each of 20 fictional campaigns'),
('Shared guides','30','Strategy, best practices, KPI definitions and methodology'),
('Longer learning guides','12','Playbooks, cohesive policies, mixed-topic notes and troubleshooting')],[1.65,.8,4.45])
p('All sources are English Markdown, explicitly fictional and free of customer records. The repository maintainer owns the corpus and manifest. Ingestion validates hashes and metadata, preserves tables and identifiers, and keeps source wording for exact evidence checks. All 122 checked-in source files are preserved byte-for-byte.')
p('The corpus is static and versioned. Its manual freshness policy is weekly review and review after approved changes, followed by source validation and rebuilding all three indexes within one working day. No scheduled ingestion service is claimed.')
h('Retrieval and answer flow')
p('LangChain supplies the provider interfaces. Persistent Chroma supports dense retrieval; hybrid retrieval adds BM25 with reciprocal-rank fusion. The pipeline retrieves 20 candidates, optionally applies the MiniLM cross-encoder and returns five chunks. Manual and inferred metadata constraints use OR within a field and AND across fields; conflicting constraints stop retrieval.')
p('LangGraph retrieves evidence, branches to generation with claim validation or refusal, then finalizes the response with retrieval and total latency. Local Ollama is the default; OpenAI and Groq are optional answer providers with private owner credentials.')

doc.add_page_break()
h('Chunking experiments')
table(['Method','Boundary rule','Shared bound'],[
('Fixed size','Token windows across cleaned source text','500 tokens'),
('Section based','Markdown heading and body groups','500 tokens'),
('Embedding semantic','Adjacent sentence or table unit cosine distances above percentile 65','500 tokens')],[1.5,4.15,1.25])
p('Long groups use 50-token overflow overlap measured with cl100k_base. Overlap is not inserted between every short section or natural semantic group. Semantic segmentation requires unit embeddings before final-chunk indexing. Headings retain citation context but do not force semantic boundaries. These defaults are comparison baselines rather than a proven optimum.')
h('Prompts and validation')
p('The answer prompt in rag/grounding.py restricts generation to retrieved evidence, asks for at most three concise verbatim claims and exact source IDs, and instructs the model to ignore instructions inside sources. Each accepted claim must occur in every cited chunk. Missing IDs and unsupported text are rejected. Empty accepted claims produce an evidence fallback.')
p('The classifier prompt requires structured allowed metadata values and an exact supporting quote from the question. It cannot relax existing filters, infer campaign IDs from year or region, or automatically assign shared ALL or GLOBAL metadata values. Classification can narrow compatible evidence; it cannot override an explicit scope.')
p('Exact text membership is deliberately conservative. A valid citation does not prove that a passage answers the question, that the source is true, or that the answer is complete. Provider failures remain visible and are not counted as successful answers.')
h('Iterations and learnings')
p('The earlier application mixed retrieval with report generation. The current build isolates question answering and chunking experiments. Report generation, presentations, maps and report history were removed from the runtime scope.')
p('Twelve longer guides were added because short documents gave a weak demonstration of boundary choices. They create varied document shapes while preserving the original corpus. The benchmark gained ambiguous terminology, questions that require distinct source documents and unsupported controls.')
p('The main learning is that document recall and valid citations do not establish faithful answers or relevant passages. Measurements must be separated, versioned and calibrated. Semantic segmentation can create many small chunks and hurt some questions; reranking must be measured rather than assumed to improve every case.')
p('Codex assisted with implementation, tests, synthetic examples and documentation. The project keeps source validation, explicit evidence contracts and reproducible comparisons as checks on AI-assisted changes.')

doc.add_page_break()
h('Evaluation design and current limits')
p('The active benchmark contains 30 cases under the retained held_out split name and 12 development examples. Calibration and legacy report-only cases are excluded. Eight new cases include three ambiguous questions, three requiring distinct documents and two unsupported controls. Gold facts and source citations are explicit. Source-derived references and newly authored cases are not independent blind validation.')
p('The paired comparison uses identical queries, scopes and top-k across three chunkers, dense or hybrid retrieval, and reranking off or on: 12 configurations. Document overlap and MRR are retrieval diagnostics. Real RAGAS faithfulness, context precision and context recall assess generated answers and ranked passages separately when a calibrated judge is available.')
p('A positive and three negative relevance controls must pass before judge scores are accepted. The local llama3.2:3b judge failed these controls, so its quality scores remain unavailable. An optional owner-configured judge is required before claiming the quality targets. Stale corpus, model, chunking and case identities are rejected as current results.')
table(['Acceptance target','Evidence still required'],[
('Faithfulness at least 90 percent','Complete generated-answer assessment using a judge that passes calibration'),
('Passage relevance precision at least 80 percent','Calibrated assessment of actual ranked passages'),
('Warm end to end p95 at most 60 seconds','Complete generated benchmark on the owner machine, excluding downloads and indexing')],[2.6,4.3])
p('These thresholds are pending acceptance checks. This overview does not reproduce the in-progress paired benchmark or present retrieval metrics as generated-answer quality. The repository evaluation results document carries measured outcomes and failure analysis once finalized.')
h('Submission assets and next steps')
p('The hand-in includes this overview of the app, dataset, prompts, iterations and learnings; the repository code and assets; and a video of at most five minutes. The video must demonstrate a live result and explain the use of AI coding tools. A script alone does not fulfill that requirement.')
p('This local document is prepared for native Google Docs import. Creation of the native document, recording of the video, publishing the latest local changes and submitting the course form are separate actions. Preparing assets does not certify a grade or claim external submission.')
p('Repository: https://github.com/Chandra-P/Master_AgenticAI')
h('Project evidence')
p('The overview follows docs/course-project.md and docs/requirements-matrix.md. Supporting implementation details are in docs/architecture.md, docs/methodology.md and docs/chunking-comparison.md. Source data and benchmark cases remain versioned in data/corpus, data/manifest.json and data/evaluation/questions.json.')
p('Credentials belong only in private environment settings or ignored Streamlit secrets. Publishing requires a source and artifact credential scan. The application remains a fictional campaign demonstration rather than a production service for private client data.')

doc.core_properties.title='Campaign knowledge RAG course project'
doc.core_properties.subject='Week 2 project overview datasets prompts iterations and learnings'
doc.core_properties.author=''
doc.core_properties.keywords='RAG LangChain LangGraph campaign knowledge course project'
doc.save(OUT)
print(OUT)
