"""Preserve original NCUA HTML table headers and row provenance as Documents."""
from pathlib import Path
import re
from bs4 import BeautifulSoup
from langchain_core.documents import Document

def extract_html(html:str,report:dict)->list[Document]:
    soup=BeautifulSoup(html,'html.parser');out=[]
    tables=soup.find_all('table')
    for ti,table in enumerate(tables[1:],start=2):
        rows=table.find_all('tr')
        if not rows:continue
        headers=[c.get_text(' ',strip=True) for c in rows[0].find_all(['th','td'],recursive=False)]
        section='Financial Summary' if report['kind']=='summary' else 'Historical Ratios'
        for ri,row in enumerate(rows[1:],start=2):
            cells=[c.get_text(' ',strip=True) for c in row.find_all(['th','td'],recursive=False)]
            if not cells:continue
            if len(cells)==1 or cells[0].endswith(':'):
                section=cells[0].rstrip(':');continue
            label=cells[0]
            # Duplicate '%Chg' headings acquire the preceding period explicitly.
            fields=[];period=''
            for h,v in zip(headers[1:],cells[1:]):
                if re.search(r'20\d{2}',h):period=h
                heading=(period+' %Chg') if h.lower().startswith('%') else h
                fields.append(f'{heading}: {v}')
            warning='' if len(cells)==len(headers) else 'Column count differs from header; inspect original table.'
            units='USD amounts; %Chg columns are annual percentage changes' if report['kind']=='summary' else 'Ratios use the units in their row labels; see original table'
            body=f"{report['institution']} | Charter {report['charter']} | {section}\nRow: {label}\n"+' | '.join(fields)+f'\nUnits: {units}'
            metadata={'source':report['filename'],'source_url':report['source_url'],'institution':report['institution'],
                      'charter':report['charter'],'section':section,'row':label,'table':ti,'row_number':ri,
                      'format':'html','warning':warning,'years':','.join(report.get('years',[]))}
            for year in report.get('years',[]):metadata['year_'+year]=True
            out.append(Document(page_content=body,metadata=metadata))
    return out

def extract_membership_table(page:dict)->list[Document]:
    """Recover an unambiguous two-year membership-count row without OCR or guessed units."""
    text=page['text']
    heading=re.search(r'\bFinancial\s+Summary\b',text,re.I)
    if not heading or not re.search(r'\bAs\s+of\s+December\s+31\b',text,re.I):return []
    integer=r'(?:\d{1,3}(?:,\d{3})+|\d{4,})'
    matches=list(re.finditer(r'(?im)^[ \t]*(?:Members|Membership)[ \t]+('+integer+r')[ \t]+('+integer+r')[ \t]*$',text))
    if len(matches)!=1:return []
    match=matches[0]
    if match.start()<heading.start():return []
    headers=[]
    for line in text[heading.end():match.start()].splitlines():
        years=re.findall(r'\b20\d{2}\b',line)
        if len(years)>2:return []
        if len(years)==2:headers.append(years)
    if len(headers)!=1:return []
    years=headers[0]
    if len(set(years))!=2 or max(map(int,years))!=int(page['report_year']) or abs(int(years[0])-int(years[1]))!=1:return []
    values=[int(value.replace(',','')) for value in match.groups()]
    if any(value<1000 for value in values):return []
    metadata={'source':page['source'],'source_url':page['source_url'],'institution':page['institution'],'charter':page['charter'],
              'source_type':'institution_annual_report','report_year':int(page['report_year']),'pdf_page':page['pdf_page'],
              'section':'Financial Summary membership table','row':'Members (membership count)','row_number':f"membership-table-{page['pdf_page']}",
              'format':'pdf','years':','.join(years),'extraction_method':'validated two-year membership row','warning':'Institution-published exact member counts; physical PDF page citation.'}
    metadata.update({'year_'+year:True for year in years})
    body=f"{page['institution']} | Institution annual report {page['report_year']} | PDF page {page['pdf_page']}\nFinancial Summary as of December 31\nRow: Members (exact year-end membership counts)\n"+' | '.join(f'Dec-{year}: {value:,}' for year,value in zip(years,values))+'\nUnits: individual members'
    return [Document(page_content=body,metadata=metadata)]

def load_supplemental(data:Path)->list[Document]:
    import json
    path=Path(data)/'supplemental/pages.jsonl'
    if not path.exists():return []
    out=[];table_rows=[]
    for line in path.read_text(encoding='utf8').splitlines():
        page=json.loads(line);text=page['text'].strip()
        if not text:continue
        table_rows.extend(extract_membership_table(page))
        year=str(page['report_year']);number=page['pdf_page']
        paragraphs=[p.strip() for p in re.split(r'\n\s*\n',text) if p.strip()]
        for i,paragraph in enumerate(paragraphs):
            metadata={'source':page['source'],'source_url':page['source_url'],'institution':page['institution'],
                      'charter':page['charter'],'source_type':'institution_annual_report','report_year':int(year),
                      'pdf_page':number,'section':'Annual report','row':'Annual report passage','row_number':number*10000+i,
                      'format':'pdf','years':year,'year_'+year:True,
                      'warning':'Institution-published annual report. Preserve printed units and definitions. PDF text order may require checking the original page.'}
            body=f"{page['institution']} | Institution annual report {year} | PDF page {number}\n{paragraph}"
            out.append(Document(page_content=body,metadata=metadata))
    # Append reviewed OCR last to preserve identifiers/order of existing passages.
    ocr_path=Path(data)/'supplemental/ocr-pages.jsonl'
    ocr_docs=[]
    if ocr_path.exists():
        for line in ocr_path.read_text(encoding='utf8').splitlines():
            page=json.loads(line)
            if page.get('reviewed') is not True or not page.get('text','').strip():continue
            year=str(page['report_year']);number=page['pdf_page']
            metadata={'source':page['source'],'source_url':page['source_url'],'institution':page['institution'],
                      'charter':page['charter'],'source_type':'institution_annual_report','report_year':int(year),
                      'pdf_page':number,'section':'Reviewed OCR annual report','row':'Reviewed OCR passage',
                      'row_number':f'ocr-{number}','format':'pdf','years':year,'year_'+year:True,
                      'extraction_method':'OCR: '+page['engine'],'source_sha256':page.get('source_sha256',''),
                      'warning':'OCR text checked against the physical PDF page; retain printed units and definitions.'}
            passages=page.get('passages',[{'text':page['text'],'context':''}])
            for i,passage in enumerate(passages):
                body=f"{page['institution']} | Institution annual report {year} | PDF page {number}\n{passage.get('context','')}\n{passage['text'].strip()}"
                ocr_docs.append(Document(page_content=body,metadata={**metadata,'row_number':f'ocr-{number}-{i}'}))
    return out+table_rows+ocr_docs

def load_documents(data:Path)->list[Document]:
    import json
    manifest=json.loads((Path(data)/'manifest.json').read_text())
    out=[]
    for r in manifest['reports']:
        if r['status']=='downloaded':out.extend(extract_html((Path(data)/'reports'/r['filename']).read_text(encoding='utf8'),r))
    return out+load_supplemental(data)
