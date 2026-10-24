from pathlib import Path
import json,hashlib
import pypdfium2 as pdfium
root=Path(__file__).resolve().parents[1]
dest=root/'data/supplemental/ocr-work';dest.mkdir(exist_ok=True);manifest=json.loads((root/'data/supplemental/manifest.json').read_text())
selected={2023:[6,8,69,70,71,72,73,74],2024:[7,8,10,100,101,102,103,104,105,106,107]}
jobs=[]
for report in manifest['reports']:
    if report['charter']!='62604' or report['report_year'] not in selected:continue
    path=root/'data/supplemental'/report['filename'];pdf=pdfium.PdfDocument(path)
    digest=hashlib.sha256(path.read_bytes()).hexdigest();assert digest==report['sha256']
    for page in selected[report['report_year']]:
        target=dest/f"{report['report_year']}-{page}.png"
        pdf[page-1].render(scale=3).to_pil().save(target)
        jobs.append(dict(source=report['filename'],source_url=report['source_url'],institution=report['institution'],charter=report['charter'],report_year=report['report_year'],pdf_page=page,source_sha256=digest,image=str(target.resolve())))
(dest/'jobs.json').write_text(json.dumps(jobs,indent=2))
print('Rendered',len(jobs),'selected pages at 216 DPI')
