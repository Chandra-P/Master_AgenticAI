from pathlib import Path
from urllib.parse import urljoin,urlparse
from datetime import datetime,timezone
from hashlib import sha256
import json,re,time,requests
from pypdf import PdfReader
from bs4 import BeautifulSoup
root=Path(__file__).resolve().parents[1]
dest=root/'data/supplemental';dest.mkdir(parents=True,exist_ok=True)
session=requests.Session();session.headers['User-Agent']='CreditUnionEvidenceLab/1.0 educational document collection'
library='https://www.becu.org/about-us/reports'
r=session.get(library,timeout=45);r.raise_for_status();soup=BeautifulSoup(r.content,'html.parser')
sources=[('5536','NAVY FEDERAL CREDIT UNION',y,f'https://www.navyfederal.org/content/dam/nfculibs/pdfs/financial-reports/{y}-annual-report.pdf') for y in range(2021,2026)]
sources=[(c,n,y,u.replace('/financial-reports/','/membership/') if y==2022 else u) for c,n,y,u in sources]
for a in soup.find_all('a',href=True):
    title=a.get_text(' ',strip=True);match=re.search(r'(202[1-5]) Annual Report \(PDF\)',title,re.I)
    if match:sources.append(('62604','BOEING EMPLOYEES',int(match[1]),urljoin(library,a['href'])))
records=[];pages=[]
for charter,name,year,url in sources:
    rec={'charter':charter,'institution':name,'report_year':year,'source_url':url,'source_type':'institution_annual_report','status':'pending'}
    filename=f'{charter}-annual-{year}.pdf';path=dest/filename;rec['filename']=filename
    try:
        time.sleep(1)
        if path.exists():content=path.read_bytes();resolved=url
        else:
            r=session.get(url,timeout=60);r.raise_for_status();content=r.content;resolved=r.url
        if not content.startswith(b'%PDF'):raise ValueError('Source did not return a PDF')
        if urlparse(resolved).hostname not in ('www.navyfederal.org','www.becu.org'):raise ValueError('Unexpected source host')
        path.write_bytes(content)
        rec.update(status='downloaded',sha256=sha256(content).hexdigest(),retrieved_at=datetime.now(timezone.utc).isoformat(),resolved_url=resolved)
        pdf=PdfReader(path);rec['page_count']=len(pdf.pages)
        for number,page in enumerate(pdf.pages,1):
            text=page.extract_text() or ''
            pages.append({'source':filename,'source_url':url,'source_type':'institution_annual_report','charter':charter,'institution':name,'report_year':year,'pdf_page':number,'text':text,'empty_text':not bool(text.strip())})
    except (requests.RequestException,ValueError) as error:rec.update(status='unavailable',error=str(error)[:250])
    records.append(rec)
    (dest/'manifest.json').write_text(json.dumps({'reports':records,'integration_status':'Downloaded and extracted; run index and export to refresh application data.'},indent=2),encoding='utf8')
    (dest/'pages.jsonl').write_text(''.join(json.dumps(p,ensure_ascii=False)+'\n' for p in pages),encoding='utf8')
    print(filename,rec['status'],rec.get('page_count',''),flush=True)
print('Downloaded',sum(r['status']=='downloaded' for r in records),'reports; extracted',len(pages),'pages',flush=True)
