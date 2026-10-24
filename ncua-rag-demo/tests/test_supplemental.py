import json
import pytest
from pipeline.graph import validate_answer

def test_pdf_page_metadata_and_year_filter_survive_loading(tmp_path):
    from pipeline.extract import load_supplemental
    directory=tmp_path/'supplemental';directory.mkdir()
    (directory/'pages.jsonl').write_text(json.dumps({'source':'5536-annual-2024.pdf','source_url':'https://www.navyfederal.org/report.pdf','source_type':'institution_annual_report','charter':'5536','institution':'NAVY FEDERAL','report_year':2024,'pdf_page':2,'text':'Membership grew to 14.2 million members.','empty_text':False})+'\n')
    docs=load_supplemental(tmp_path)
    assert docs[0].metadata['pdf_page']==2
    assert docs[0].metadata['source_type']=='institution_annual_report'
    assert docs[0].metadata['year_2024'] is True
    assert '14.2 million' in docs[0].page_content

def test_scaled_number_allowed_only_when_cited_source_uses_same_scale():
    assert validate_answer('Membership was 14.2 million in 2024 [E1].',[{'id':'E1','text':'2024: 14.2 million members'}])
    with pytest.raises(ValueError):validate_answer('Membership was 14.2 billion in 2024 [E1].',[{'id':'E1','text':'2024: 14.2 million members'}])
    with pytest.raises(ValueError):validate_answer('Membership was 14.2 billion in 2024 [E1].',[{'id':'E1','text':'2024: 14.2 million members and assets of 180 billion'}])

def test_membership_query_uses_annual_documents_instead_of_regulatory_ratios():
    from pipeline.retrieve import select_documents
    from langchain_core.documents import Document
    docs=[Document(page_content='Members / Potential Members 8.23',metadata={'format':'html','charter':'5536'}),Document(page_content='2024: 14.2 million members',metadata={'source_type':'institution_annual_report','report_year':2024,'charter':'5536'})]
    assert select_documents('How many members in 2024?',docs)==docs[1:]

def test_pdf_semantic_groups_do_not_cross_page_boundaries():
    from pipeline.chunk import semantic_chunks
    from langchain_core.documents import Document
    class Encoder:
        def embed_documents(self,texts):return [[1.,0.] for _ in texts]
    docs=[Document(page_content='Membership grew.',metadata={'source':'report.pdf','section':'Annual report','pdf_page':p,'row_number':p}) for p in (1,2)]
    assert len(semantic_chunks(docs,Encoder()))==2

def test_membership_ratio_keeps_ncua_denominator_source():
    from pipeline.retrieve import select_documents
    from langchain_core.documents import Document
    docs=[Document(page_content='Members / Potential Members 8.23',metadata={'format':'html'}),Document(page_content='15 million members',metadata={'source_type':'institution_annual_report'})]
    assert select_documents('What was the members / potential members ratio?',docs)==docs[:1]

def test_membership_word_is_an_allowed_retrieval_topic():
    from pipeline.retrieve import retrieve
    from langchain_core.documents import Document
    doc=Document(id='annual',page_content='Navy Federal membership in 2024 was 14.2 million.',metadata={'source_type':'institution_annual_report','report_year':2024})
    class Store:
        def all_documents(self,filters):return [doc]
        def search(self,*args,**kwargs):return [doc]
    assert retrieve(Store(),'Navy Federal membership in 2024')==[doc]

def test_explicit_year_overrides_default_ui_year_for_annual_reports():
    from pipeline.retrieve import retrieve
    from langchain_core.documents import Document
    doc=Document(id='annual',page_content='2024: 14.2 million members',metadata={'source_type':'institution_annual_report','report_year':2024})
    class Store:
        def all_documents(self,filters):return [] if filters.get('year_2025') else [doc]
        def search(self,*args,**kwargs):return [doc]
    assert retrieve(Store(),'How many members in 2024?',{'year_2025':True})==[doc]

def test_annual_report_phrase_does_not_override_membership_ratio_routing():
    from pipeline.retrieve import wants_annual
    assert not wants_annual('What was the members / potential members ratio in the annual report?')

def test_annual_financial_coverage_uses_pdf_metric_and_report_period():
    from pipeline.graph import coverage_report
    from langchain_core.documents import Document
    corpus=[Document(page_content='',metadata={'charter':'5536','institution':'NAVY FEDERAL CREDIT UNION'})]
    evidence=[{'charter':'5536','row':'Annual report passage','format':'pdf','report_year':2024,'text':'Annual report 2024\nTotal assets: 180 million USD'}]
    assert coverage_report('What were Navy Federal total assets in its 2024 annual report?',{},evidence,corpus)['complete']
    assert not coverage_report('What were Navy Federal total assets in its 2023 annual report?',{},evidence,corpus)['complete']

def test_ratio_coverage_agrees_with_ncua_routing_even_when_annual_is_mentioned():
    from pipeline.graph import coverage_report
    from langchain_core.documents import Document
    corpus=[Document(page_content='',metadata={'charter':'5536','institution':'NAVY FEDERAL CREDIT UNION'})]
    evidence=[{'charter':'5536','row':'Delinquent Loans / Assets','format':'html','text':'Dec-2024: 1.26'}]
    assert coverage_report('What was Navy Federal delinquent loans / assets ratio in the 2024 annual report?',{},evidence,corpus)['complete']
