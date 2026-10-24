"""Catches losing financial column meanings or provenance during chunking."""
from langchain_core.documents import Document

def test_fixed_chunks_preserve_source_metadata():
    from pipeline.chunk import fixed_chunks
    d=Document(page_content='Assets loans delinquency. '*150,metadata={'charter':'5536','source':'report.html','section':'Financial Summary'})
    out=fixed_chunks([d],size=40,overlap=5)
    assert len(out)>1
    assert all(x.metadata['charter']=='5536' and x.metadata['source']=='report.html' for x in out)
    assert len({x.id for x in out})==len(out)

def test_table_rows_are_labeled_with_period():
    from pipeline.extract import extract_html
    html='''<html><h1>Financial Performance Report</h1><table><tr><th>Charter</th><th>Name</th></tr><tr><td>5536</td><td>NAVY FEDERAL</td></tr></table><table><tr><th>Line Item</th><th>Dec-2023</th><th>Dec-2024</th><th>%Chg</th></tr><tr><th>TOTAL ASSETS</th><td>100</td><td>110</td><td>10</td></tr></table></html>'''
    docs=extract_html(html,{'institution':'NAVY FEDERAL','charter':'5536','filename':'x.html','kind':'summary','source_url':'https://fpr.ncua.gov/','years':['2023','2024']})
    row=next(d for d in docs if 'TOTAL ASSETS' in d.page_content)
    assert 'Dec-2023: 100' in row.page_content
    assert 'Dec-2024: 110' in row.page_content
    assert '%Chg: 10' in row.page_content
    assert row.metadata['source']=='x.html'

def test_semantic_chunks_use_similarity_boundaries():
    from pipeline.chunk import semantic_chunks
    from langchain_core.embeddings import Embeddings
    class Topics(Embeddings):
        def embed_documents(self,texts):return [[1.,0.] if 'assets' in t else [0.,1.] for t in texts]
        def embed_query(self,text):return self.embed_documents([text])[0]
    docs=[Document(page_content=x,metadata={'source':'x','charter':'1','section':'s'}) for x in ['assets cash','assets investments','delinquency loans']]
    out=semantic_chunks(docs,Topics(),size=200)
    assert len(out)==2
    assert 'assets cash' in out[0].page_content and 'assets investments' in out[0].page_content
    assert 'delinquency' in out[1].page_content
