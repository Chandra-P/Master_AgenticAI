"""Export safe source views and real evaluation results for the public UI."""
from pathlib import Path
from html import escape
import json,shutil
from bs4 import BeautifulSoup

def source_view(source:str,report:dict)->str:
    soup=BeautifulSoup(source,'html.parser')
    for t in soup.find_all(['script','style','iframe','object']):t.decompose()
    tables=[]
    for i,table in enumerate(soup.find_all('table'),start=1):
        rows=[]
        for row in table.find_all('tr'):
            cells=row.find_all(['td','th'],recursive=False)
            if cells:rows.append('<tr>'+''.join(f'<{c.name}>'+escape(c.get_text(' ',strip=True))+f'</{c.name}>' for c in cells)+'</tr>')
        tables.append(f'<h2 id="table-{i}">Table {i}</h2><div class="scroll"><table>'+''.join(rows)+'</table></div>')
    name=escape(report['institution']);filename=escape(report['filename'],quote=True)
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{name} — NCUA source report</title>
<style>body{{font:14px/1.7 Arial;color:#284633;background:#f7f8f2;max-width:1200px;margin:35px auto;padding:0 25px}}h1{{font:32px Georgia}}h2{{font:23px Georgia;margin-top:35px}}table{{border-collapse:collapse;background:white;font-size:12px}}td,th{{padding:10px 13px;border:1px solid #dfe6d5;text-align:right;white-space:nowrap}}td:first-child,th:first-child{{text-align:left;white-space:normal;min-width:240px}}.scroll{{overflow:auto}}.note{{background:#eaf0e0;padding:20px}}a{{color:#375e2c}}</style>
<a href="/">← Credit Union Evidence Lab</a><h1>{name}</h1><p>Charter {escape(str(report['charter']))} · Retrieved {escape(report['retrieved_at'])}</p>
<p class="note">Readable table view of an original NCUA HTML report. This view removes executable markup; original bytes are preserved in the download. HTML reports have table and row references, not PDF pages. Ratio denominators and %Chg headings must be read as shown.</p>
<p><a href="{filename}.source.txt" download="{filename}">Download original HTML</a> · <a href="{escape(report['source_url'],quote=True)}" rel="noreferrer" target="_blank">NCUA report application</a></p>{''.join(tables)}</html>'''

def export_site(root:Path)->None:
    root=Path(root);public=root/'site/public';dest=public/'reports';dest.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((root/'data/manifest.json').read_text());institutions={}
    for r in manifest['reports']:
        if r['status']!='downloaded':continue
        institutions[r['charter']]=r['institution']
        original=(root/'data/reports'/r['filename']).read_bytes()
        (dest/r['filename']).write_text(source_view(original.decode('utf8'),r),encoding='utf8')
        (dest/(r['filename']+'.source.txt')).write_bytes(original)
    corpus={'reports':manifest['reports'],'institutions':[{'charter':c,'name':n} for c,n in sorted(institutions.items(),key=lambda x:x[1])],
            'source_format':'Original NCUA HTML','coverage':'2021–2025'}
    supplemental=root/'data/supplemental/manifest.json'
    if supplemental.exists():
        for r in json.loads(supplemental.read_text())['reports']:
            if r['status']!='downloaded':continue
            shutil.copyfile(root/'data/supplemental'/r['filename'],dest/r['filename'])
            corpus['reports'].append({**r,'id':r['filename'],'kind':'annual','format':'pdf','years':[str(r['report_year'])]})
        corpus['source_format']='NCUA HTML and institution annual-report PDFs'
    (public/'corpus.json').write_text(json.dumps(corpus,indent=2),encoding='utf8')
    if (root/'evaluation/results.json').exists():
        shutil.copyfile(root/'evaluation/results.json',public/'evaluation.json')
        shutil.copyfile(root/'evaluation/comparison-report.md',public/'comparison-report.txt')
    print('Exported',len(institutions),'institutions and',len(list(dest.glob('*.html'))),'report views',flush=True)
