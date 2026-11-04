import json, subprocess, sys
from types import SimpleNamespace
import pytest
from campaign_hub.config import Settings
from campaign_hub.models import Chunk, SearchHit, RetrievalOptions, EvidenceClaim


def test_active_service_has_no_report_dependency_or_report_methods():
    process=subprocess.run([sys.executable,'-c',
        'import sys; from campaign_hub.rag.service import RAGService; '
        'assert not any(n.startswith("campaign_hub.reporting") for n in sys.modules); '
        'assert not hasattr(RAGService,"generate_report"); assert not hasattr(RAGService,"campaign_snapshot")'],
        capture_output=True,text=True)
    assert process.returncode==0,process.stderr


def test_corpus_wide_answer_is_grounded_without_any_report_workflow(monkeypatch):
    from campaign_hub.rag.service import RAGService
    from campaign_hub.rag.grounding import Draft
    import campaign_hub.generation.providers as providers
    chunk=Chunk(chunk_id='source',text='Tracking incident TRK-017 requires a source replay.',metadata={'document_id':'guide'})
    class Generator:
        def generate_json(self,*args):return Draft(claims=[EvidenceClaim(text=chunk.text,citations=['source'])])
    monkeypatch.setattr(providers,'create_generator',lambda settings:Generator())
    service=RAGService.__new__(RAGService)
    service.settings=Settings()
    seen=[]
    service.analyze_query=lambda *args,**kwargs: seen.append((args,kwargs)) or {
        'hits':[SearchHit(chunk=chunk,score=1).model_dump()], 'effective_filters':{},'status':'retrieved'}
    result=service.answer_question('How do I handle TRK-017?',None,RetrievalOptions(),automatic=False)
    assert seen[0][0][3] is None
    assert 'source' in result['answer'] and chunk.text in result['answer']


def test_report_commands_are_not_part_of_active_cli():
    result=subprocess.run([sys.executable,'-m','campaign_hub','--help'],capture_output=True,text=True)
    assert result.returncode==0
    assert '{generate,validate,index,ask,evaluate}' in result.stdout


def test_active_evaluation_excludes_reports_and_respects_split(tmp_path):
    from campaign_hub.rag.evaluation import evaluation_cases
    (tmp_path/'evaluation').mkdir()
    cases=[{'id':'q','kind':'question','split':'held_out'},
           {'id':'r','kind':'report','split':'held_out'},
           {'id':'d','kind':'question','split':'development'},
           {'id':'c','kind':'question','split':'calibration'}]
    (tmp_path/'evaluation/questions.json').write_text(json.dumps(cases))
    assert [c['id'] for c in evaluation_cases(tmp_path,'held_out')]==['q']
    assert [c['id'] for c in evaluation_cases(tmp_path,'development')]==['d']


def test_current_results_reject_old_corpus_and_do_not_load_bundled_report_scores(tmp_path):
    from campaign_hub.rag.evaluation import load_current_results
    service=SimpleNamespace(settings=Settings(root=tmp_path),corpus_hash='new',ensure_current=lambda:None)
    out=tmp_path/'data/runs/rag/latest';out.mkdir(parents=True)
    (out/'results.json').write_text(json.dumps([{'identity':{'corpus':'old'}}]))
    assert load_current_results(service)==[]


def test_question_evaluation_measures_retrieval_only_and_excludes_report_cases(tmp_path,monkeypatch):
    from campaign_hub.rag.evaluation import run_evaluation,load_current_results
    from campaign_hub.rag.service import RAGService
    settings=Settings(root=tmp_path)
    (settings.data/'evaluation').mkdir(parents=True)
    cases=[{'id':'q','kind':'question','split':'held_out','question':'Known evidence?',
            'campaign_id':None,'expected_sources':['source']},
           {'id':'report','kind':'report','split':'held_out'}]
    (settings.data/'evaluation/questions.json').write_text(json.dumps(cases))
    chunk=Chunk(chunk_id='chunk',text='Known evidence.',metadata={'document_id':'source'})
    service=SimpleNamespace(settings=settings,corpus_hash='current',ensure_current=lambda:None,
                            search=lambda *a:[SearchHit(chunk=chunk,score=1)])
    rows=run_evaluation(service)
    assert len(rows)==6 and {r['case_id'] for r in rows}=={'q'}
    assert all(r['context_precision']==r['context_recall']==1 and r['faithfulness'] is None for r in rows)
    assert all(r['generation_skipped'] and r['answer'] is None for r in rows)
    assert len(load_current_results(service))==6
    service.settings=__import__('dataclasses').replace(settings,embedding_model='changed')
    assert load_current_results(service)==[]


def test_coverage_keeps_configurations_where_every_case_failed():
    from campaign_hub.rag.evaluation import evaluation_coverage
    rows=[{'split':'held_out','chunking':'fixed','retrieval':'dense','reranking':False,
           'case_id':case,'expected_cases_per_configuration':2,'error':'failed'} for case in ('a','b')]
    coverage=evaluation_coverage(rows)
    assert len(coverage)==1 and coverage[0]['completed']==0 and coverage[0]['expected']==2


def test_saved_scores_are_rejected_when_source_files_changed(tmp_path):
    from campaign_hub.rag.evaluation import load_current_results
    out=tmp_path/'data/runs/rag/latest';out.mkdir(parents=True)
    (out/'results.json').write_text('[]')
    seen=[]
    def ensure():seen.append(True);raise ValueError('Source documents changed')
    service=SimpleNamespace(settings=Settings(root=tmp_path),ensure_current=ensure)
    assert load_current_results(service)==[] and seen


def test_each_citation_must_support_the_claim():
    from campaign_hub.rag.grounding import supported_claim
    evidence={'a':Chunk(chunk_id='a',text='Known evidence.',metadata={}),
              'b':Chunk(chunk_id='b',text='Unrelated source.',metadata={})}
    assert not supported_claim(EvidenceClaim(text='Known evidence.',citations=['a','b']),evidence)
    assert supported_claim(EvidenceClaim(text='Known evidence.',citations=['a']),evidence)


def test_unsupported_cases_do_not_receive_zero_retrieval_relevance(tmp_path,monkeypatch):
    import campaign_hub.rag.evaluation as module
    settings=Settings(root=tmp_path)
    (settings.data/'evaluation').mkdir(parents=True)
    case={'id':'unsupported','kind':'unsupported','split':'held_out','question':'Unknown fact?',
          'campaign_id':None,'expected_sources':[]}
    (settings.data/'evaluation/questions.json').write_text(json.dumps([case]))
    service=SimpleNamespace(settings=settings,corpus_hash='current',search=lambda *a:[])
    monkeypatch.setattr(module,'configurations',lambda *a:[RetrievalOptions()])
    row=module.run_evaluation(service)[0]
    assert row['context_precision'] is row['context_recall'] is row['mrr'] is row['ndcg'] is None


def test_generated_evaluation_keeps_retrieval_and_end_to_end_timing_separate(tmp_path,monkeypatch):
    import campaign_hub.rag.evaluation as module
    settings=Settings(root=tmp_path)
    (settings.data/'evaluation').mkdir(parents=True)
    (settings.data/'evaluation/questions.json').write_text(json.dumps([{
        'id':'q','kind':'question','split':'held_out','question':'Known?',
        'expected_sources':['source']}]))
    chunk=Chunk(chunk_id='c',text='Known.',metadata={'document_id':'source'})
    service=SimpleNamespace(settings=settings,corpus_hash='current',answer_question=lambda *a:{
        'answer':'Known. [c]','hits':[SearchHit(chunk=chunk,score=1).model_dump()],
        'retrieval_seconds':.2,'latency_seconds':3.0})
    monkeypatch.setattr(module,'configurations',lambda *a:[RetrievalOptions()])
    row=module.run_evaluation(service,generated=True)[0]
    assert row['retrieval_seconds']==.2
    assert row['answer_seconds']==3.0


def test_retrieval_identity_does_not_depend_on_answer_prompt():
    from campaign_hub.rag.evaluation import run_identity
    service=SimpleNamespace(corpus_hash='corpus',settings=Settings())
    identity=run_identity(service,RetrievalOptions(),[],False,{'model':'test'})
    assert 'generation_prompt_sha256' not in identity
    generated=run_identity(service,RetrievalOptions(),[],True,{'model':'test'})
    assert len(generated['generation_prompt_sha256'])==64
