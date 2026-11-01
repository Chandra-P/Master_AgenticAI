"""Workspace PostgreSQL role setup. Separate credentials; no system service/cloud changes."""
from pathlib import Path
import secrets
from urllib.parse import quote

import psycopg
from psycopg import sql

root=Path(__file__).resolve().parents[1]
folder=root/'.dev'
password_file=folder/'pg-directory-password'
if not password_file.exists():password_file.write_text(secrets.token_urlsafe(32),encoding='utf-8')
directory_password=password_file.read_text(encoding='utf-8').strip()
admin_password=(folder/'pg-admin-password').read_text(encoding='utf-8').strip()
role='convene_directory_admin'
for database in ('convene_dev','convene_test'):
    with psycopg.connect(host='127.0.0.1',port=55432,dbname=database,user='convene_local',password=admin_password) as connection:
        if not connection.execute('SELECT 1 FROM pg_roles WHERE rolname=%s',(role,)).fetchone():
            connection.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT').format(sql.Identifier(role),sql.Literal(directory_password)))
        connection.execute(sql.SQL('GRANT USAGE,CREATE ON SCHEMA public TO {}').format(sql.Identifier(role)))
        for table in ('vendor_records','vendor_versions','vendor_approval_history'):
            connection.execute(sql.SQL('ALTER TABLE {} OWNER TO {}').format(sql.Identifier(table),sql.Identifier(role)))
            connection.execute(sql.SQL('GRANT SELECT ON {} TO convene_app').format(sql.Identifier(table)))
        # The web login has no directory write grants and is not a member of the admin role.
        assert not connection.execute("SELECT pg_has_role('convene_app',%s,'MEMBER')",(role,)).fetchone()[0]

env_path=root/'.env'
lines=env_path.read_text(encoding='utf-8-sig').splitlines()
values={}
for database,key in [('convene_dev','CONVENE_DIRECTORY_ADMIN_URL'),('convene_test','CONVENE_TEST_DIRECTORY_ADMIN_URL')]:
    values[key]=f'postgresql://{role}:{quote(directory_password,safe="")}@127.0.0.1:55432/{database}'
for key,value in values.items():
    lines=[line for line in lines if not line.startswith(key+'=')]
    lines.append(key+'='+value)
env_path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Dedicated local directory role configured; credentials stored only in ignored local files.')
