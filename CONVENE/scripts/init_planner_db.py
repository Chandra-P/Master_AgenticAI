"""Explicit schema setup. Never invoked by a public HTTP request."""
from pathlib import Path
import argparse
import os
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from convene.repository import Repository
from convene.planner_graph import setup_checkpoints

load_dotenv()
parser=argparse.ArgumentParser(description='Explicit planner schema initialization')
parser.add_argument('--test',action='store_true',help='Initialize only the separately configured test database')
args=parser.parse_args()
dsn=os.getenv('CONVENE_TEST_DATABASE_URL' if args.test else 'CONVENE_DATABASE_URL','')
if args.test:
    from psycopg.conninfo import conninfo_to_dict
    if not conninfo_to_dict(dsn).get('dbname','').startswith('convene_test'):
        raise ValueError('Test initialization requires a separate convene_test database.')
repository=Repository(dsn)
repository.migrate()
setup_checkpoints(repository.dsn)
print('Planner database schema and private checkpoints initialized.')
