"""Catches filter leakage, stale vectors and invalid citations at real boundaries."""
import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

class ToyEmbeddings(Embeddings):
    identity='toy-test-only'
    def embed_documents(self,texts):
        return [[1.,0.,0.] if 'assets' in t.lower() else [0.,1.,0.] for t in texts]
    def embed_query(self,text):return self.embed_documents([text])[0]

def docs():
    return [Document(id='asset-a',page_content='Alpha total assets 100 dollars',metadata={'source':'a.html','charter':'1','institution':'Alpha','year_2025':True,'row':'TOTAL ASSETS'}),
            Document(id='asset-b',page_content='Beta total assets 200 dollars',metadata={'source':'b.html','charter':'2','institution':'Beta','year_2024':True,'row':'TOTAL ASSETS'})]

def test_chroma_filter_and_reopen(tmp_path):
    from pipeline.index import Store
    s=Store(tmp_path,'fixed',ToyEmbeddings());s.build(docs())
    reopened=Store(tmp_path,'fixed',ToyEmbeddings())
    found=reopened.search('assets',{'charter':'1','year_2025':True})
    assert [x.id for x in found]==['asset-a']
    assert reopened.search('assets',{'charter':'2','year_2025':True})==[]

def test_refresh_removes_stale_chunks(tmp_path):
    from pipeline.index import Store
    s=Store(tmp_path,'fixed',ToyEmbeddings());s.build(docs());s.build(docs()[:1])
    assert s.collection.count()==1

def test_unknown_citations_are_rejected():
    from pipeline.graph import validate_answer
    with pytest.raises(ValueError):validate_answer('Assets are 100 [E99].',[{'id':'E1'}])

def test_numeric_answer_requires_citation():
    from pipeline.graph import validate_answer
    with pytest.raises(ValueError):validate_answer('Assets are 100 dollars.',[{'id':'E1'}])

def test_no_evidence_abstains_without_model():
    from pipeline.graph import build_graph
    class Empty:
        def search(self,*a,**kw):return []
        def all_documents(self,*a,**kw):return []
    g=build_graph(Empty(),llm=None)
    result=g.invoke({'question':'What are assets?','filters':{},'rerank':False})
    assert result['status']=='insufficient_evidence'
    assert result.get('evidence',[])==[]

def test_invented_number_rejected_even_with_valid_citation():
    from pipeline.graph import validate_answer
    evidence=[{'id':'E1','text':'Navy Federal total assets Dec-2025: 100 USD.'}]
    with pytest.raises(ValueError):validate_answer('Navy Federal assets were 999 trillion USD in 2025 [E1].',evidence)

def test_each_numeric_claim_needs_its_own_support():
    from pipeline.graph import validate_answer
    evidence=[{'id':'E1','text':'Assets Dec-2025: 100 USD.'}]
    with pytest.raises(ValueError):validate_answer('Assets were 100 USD [E1]. Loans were 999 USD.',evidence)

def test_cross_institution_comparison_blocks_missing_metric():
    from pipeline.graph import coverage_report
    evidence=[{'charter':'5536','row':'TOTAL LOANS','text':'Dec-2025: 100'},
              {'charter':'227','row':'TOTAL ASSETS','text':'Dec-2025: 200'}]
    corpus=[Document(page_content='',metadata={'charter':'5536','institution':'NAVY FEDERAL CREDIT UNION'}),Document(page_content='',metadata={'charter':'227','institution':'PENTAGON'})]
    result=coverage_report('Compare Navy Federal and Pentagon total assets in 2025.',{},evidence,corpus)
    assert result['complete'] is False
    assert '5536' in result['missing'][0]

def test_complete_metric_period_evidence_passes_comparison_gate():
    from pipeline.graph import coverage_report
    corpus=[Document(page_content='',metadata={'charter':'5536','institution':'NAVY FEDERAL CREDIT UNION'}),Document(page_content='',metadata={'charter':'227','institution':'PENTAGON'})]
    evidence=[{'charter':c,'row':'TOTAL ASSETS','text':'Dec-2025: 100'} for c in ['5536','227']]
    assert coverage_report('Compare Navy Federal and Pentagon total assets in 2025.',{},evidence,corpus)['complete']

def test_provider_citation_syntax_normalizes_before_validation():
    from pipeline.graph import validate_answer
    e=[{'id':'E1','text':'TOTAL ASSETS Dec-2025: 100 USD'}]
    assert validate_answer('Assets were 100 USD in 2025 [cite:E1].',e)=='Assets were 100 USD in 2025 [E1].'

def test_unicode_provider_citations_are_normalized():
    from pipeline.graph import validate_answer
    e=[{'id':'E1','text':'TOTAL ASSETS Dec-2025: 100 USD'}]
    assert validate_answer('Assets were 100 USD in 2025 【E1】.',e)=='Assets were 100 USD in 2025 [E1].'

def test_generation_repairs_once_and_never_returns_invalid_draft():
    from pipeline.graph import generate_grounded
    from langchain_core.runnables import RunnableLambda
    from langchain_core.messages import AIMessage
    drafts=iter(['Assets were 999 USD in 2025 [E1].','Assets were 100 USD in 2025 [E1].'])
    llm=RunnableLambda(lambda _:AIMessage(content=next(drafts)))
    result=generate_grounded(llm,'What were assets?','[E1] TOTAL ASSETS Dec-2025: 100 USD',[{'id':'E1','text':'TOTAL ASSETS Dec-2025: 100 USD'}])
    assert result=='Assets were 100 USD in 2025 [E1].'

def test_repair_still_fails_closed_when_both_drafts_are_unsupported():
    from pipeline.graph import generate_grounded
    from langchain_core.runnables import RunnableLambda
    from langchain_core.messages import AIMessage
    with pytest.raises(ValueError):generate_grounded(RunnableLambda(lambda _:AIMessage(content='Assets were 999 USD [E1].')),'assets','source',[{'id':'E1','text':'100 USD'}])
