"""Download official portable PostgreSQL binaries for workspace-only development."""
from pathlib import Path
from zipfile import ZipFile
import httpx

root=Path(__file__).resolve().parents[1]
folder=root/'.dev'
folder.mkdir(exist_ok=True)
archive=folder/'postgresql-windows.zip'
url='https://get.enterprisedb.com/postgresql/postgresql-17.11-3-windows-x64-binaries.zip'
if not archive.exists():
 with httpx.Client(timeout=60,follow_redirects=True,trust_env=False) as client:
  with client.stream('GET',url) as response:
   response.raise_for_status()
   size=0
   with archive.open('wb') as output:
    for chunk in response.iter_bytes(1024*1024):
     size+=len(chunk)
     if size>600_000_000: raise ValueError('Unexpected download size')
     output.write(chunk)
 print('Official PostgreSQL archive downloaded.')
with ZipFile(archive) as bundle:
 for item in bundle.infolist():
  path=Path(item.filename)
  if len(path.parts)>1 and path.parts[0]=='pgsql' and path.parts[1] in ('bin','lib','share'):
   target=(folder/path).resolve()
   if not target.is_relative_to(folder.resolve()): raise ValueError('Unsafe archive path')
   bundle.extract(item,folder)
print('Portable PostgreSQL extracted under ignored .dev directory.')
