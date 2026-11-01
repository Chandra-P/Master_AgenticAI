"""Start an isolated local development/test PostgreSQL server, never a system service."""
from pathlib import Path
import os,re,secrets,subprocess
from urllib.parse import quote
import psycopg
from psycopg import sql

root=Path(__file__).resolve().parents[1]
folder=root/'.dev'
bin_dir=folder/'pgsql'/'bin'
data=folder/'pgdata'
flags=getattr(subprocess,'CREATE_NO_WINDOW',0)

def command(args):
 options={'stdout':subprocess.DEVNULL,'stderr':subprocess.DEVNULL} if 'start' in args else {'capture_output':True}
 result=subprocess.run([str(arg) for arg in args],text=True,creationflags=flags,timeout=45,**options)
 if result.returncode:
  raise RuntimeError('PostgreSQL command failed: '+(result.stderr or 'See .dev/postgres.log')[-1500:])
 return result

password_file=folder/'pg-admin-password'
app_file=folder/'pg-app-password'
if not password_file.exists():password_file.write_text(secrets.token_urlsafe(32),encoding='utf-8')
if not app_file.exists():app_file.write_text(secrets.token_urlsafe(32),encoding='utf-8')
admin_password=password_file.read_text(encoding='utf-8').strip()
app_password=app_file.read_text(encoding='utf-8').strip()
if not (data/'PG_VERSION').exists():
 command([bin_dir/'initdb.exe','-D',data,'-U','convene_local','--encoding=UTF8','--locale=C','--auth=scram-sha-256','--pwfile',password_file])
status=subprocess.run([str(bin_dir/'pg_ctl.exe'),'-D',str(data),'status'],capture_output=True,creationflags=flags)
if status.returncode:
 command([bin_dir/'pg_ctl.exe','-D',data,'-l',folder/'postgres.log','-o','-h 127.0.0.1 -p 55432','-w','start'])
with psycopg.connect(host='127.0.0.1',port=55432,user='convene_local',password=admin_password,dbname='postgres',autocommit=True) as connection:
 if not connection.execute("SELECT 1 FROM pg_roles WHERE rolname='convene_app'").fetchone():
  connection.execute(sql.SQL('CREATE ROLE convene_app LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD {}').format(sql.Literal(app_password)))
 for name in ['convene_dev','convene_test']:
  if not connection.execute('SELECT 1 FROM pg_database WHERE datname=%s',(name,)).fetchone():
   connection.execute(sql.SQL('CREATE DATABASE {} OWNER convene_app').format(sql.Identifier(name)))
env_path=root/'.env'
text=env_path.read_text(encoding='utf-8') if env_path.exists() else ''
for name,database in [('CONVENE_DATABASE_URL','convene_dev'),('CONVENE_TEST_DATABASE_URL','convene_test')]:
 value=f'postgresql://convene_app:{quote(app_password,safe="")}@127.0.0.1:55432/{database}'
 line=name+'='+value
 pattern=r'(?m)^'+re.escape(name)+r'=.*$'
 text=re.sub(pattern,lambda match:line,text) if re.search(pattern,text) else text+'\n'+line+'\n'
env_path.write_text(text,encoding='utf-8')
print('Local PostgreSQL ready on 127.0.0.1:55432; separate development/test databases configured in ignored .env.')
