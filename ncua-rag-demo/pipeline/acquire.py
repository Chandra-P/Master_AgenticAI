"""Download original NCUA online FPR documents without requesting email."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from hashlib import sha256
import json, re, time
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

BASE='https://fpr.ncua.gov/'
# Selection candidates; names are taken from returned source documents, not guessed.
CANDIDATES=['5536','227','62604','19976','67955','66310','68205','24694','24692','244']
KINDS={'summary':('ctl00$content$btnSummary','Financial Summary'),
       'historical':('ctl00$content$btnRatios','Historical Ratios')}

def write_manifest(path:Path, value:dict)->None:
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2),encoding='utf8');tmp.replace(path)

def validate_report(content:bytes, charter:str)->dict:
    soup=BeautifulSoup(content,'html.parser')
    tables=soup.find_all('table')
    if len(tables)<2 or 'Financial Performance Report' not in soup.get_text(' ',strip=True):
        raise ValueError('Response is not an NCUA financial report')
    rows=[row for row in tables[0].find_all('tr') if row.find('td')]
    if not rows:raise ValueError('Report identity is missing')
    cells=rows[0].find_all(['td','th'],recursive=False)
    if len(cells)<2 or cells[0].get_text(strip=True)!=str(charter):
        raise ValueError('Returned charter does not match requested institution')
    # Explanatory accounting notes mention years outside the report columns.
    headers=' '.join(c.get_text(' ',strip=True) for t in tables[1:] for c in t.find_all('th',attrs={'scope':'col'}))
    if not headers:headers=' '.join(t.find('tr').get_text(' ',strip=True) for t in tables[1:] if t.find('tr'))
    years=sorted(set(re.findall(r'\b20\d{2}\b',headers)))
    return {'institution':cells[1].get_text(' ',strip=True),'charter':str(charter),'years':years}

def download_reports(selection:list[str],destination:Path,*,pause:float=2.0)->dict:
    destination=Path(destination);dest=destination/'reports';dest.mkdir(parents=True,exist_ok=True)
    path=destination/'manifest.json'
    manifest=json.loads(path.read_text()) if path.exists() else {'reports':[],'requests_by_day':{},'format':'Original NCUA HTML financial reports'}
    session=requests.Session();session.headers['User-Agent']='NCUA-RAG-Education/1.0 (small public-report sample)'
    today=datetime.now(timezone.utc).date().isoformat()
    for charter in selection:
        for kind,(button,label) in KINDS.items():
            rid=f'{charter}-{kind}-2025';filename=f'{rid}.html';local=dest/filename
            old=next((x for x in manifest['reports'] if x['id']==rid),None)
            if old and old.get('status')=='downloaded' and local.exists() and sha256(local.read_bytes()).hexdigest()==old.get('sha256'):
                continue
            if manifest['requests_by_day'].get(today,0)>=30:
                raise RuntimeError('Daily demo request budget reached; resume another day')
            record={'id':rid,'charter':charter,'kind':kind,'filename':filename,'requested_period':'2025-12-31',
                    'source_url':BASE+'OnlineFPR.aspx?cu_number='+charter,'status':'pending'}
            if old:manifest['reports'].remove(old)
            manifest['reports'].append(record)
            try:
                time.sleep(pause)
                r=session.get(record['source_url'],timeout=45);r.raise_for_status()
                soup=BeautifulSoup(r.content,'html.parser')
                form=soup.find('form')
                if form is None:raise ValueError('Report request form unavailable')
                data={x['name']:x.get('value','') for x in form.find_all('input',attrs={'type':'hidden'}) if x.has_attr('name')}
                data.update({'ctl00$content$lstCycleDate':'12/31/2025','ctl00$content$lstInterval':'2',
                             'ctl00$content$txtCU_Number':charter,button:label})
                manifest['requests_by_day'][today]=manifest['requests_by_day'].get(today,0)+1
                write_manifest(path,manifest)
                # One report generation per record. Never retry POST blindly.
                r=session.post(urljoin(r.url,form.get('action',r.url)),data=data,timeout=60);r.raise_for_status()
                meta=validate_report(r.content,charter)
                tmp=local.with_suffix('.part');tmp.write_bytes(r.content);tmp.replace(local)
                record.update(meta,status='downloaded',sha256=sha256(r.content).hexdigest(),
                              retrieved_at=datetime.now(timezone.utc).isoformat(),format='html',
                              response_url=r.url,citation_type='table and row; HTML has no PDF page numbers')
            except (requests.RequestException,ValueError) as exc:
                record.update(status='unavailable',error=str(exc)[:240])
            write_manifest(path,manifest)
            print(rid,record['status'],record.get('institution',record.get('error')),flush=True)
            if record.get('error','').startswith(('403','429')):raise RuntimeError('Source restricted access; stopped')
    return manifest

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--destination',type=Path,default=Path('data'));a=p.parse_args()
    download_reports(CANDIDATES,a.destination)
