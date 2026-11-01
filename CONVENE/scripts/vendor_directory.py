"""Explicit local directory administration; never exposes a public approval route."""
import argparse
import json
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from convene.vendor_directory import DirectoryAdmin


def main():
    parser=argparse.ArgumentParser(description='Review and publish the CONVENE vendor directory locally.')
    parser.add_argument('--operator',required=True,help='Local operator audit label; not a verified Google identity')
    commands=parser.add_subparsers(dest='command',required=True)
    commands.add_parser('import-existing',help='One-time import of the five previously conversation-approved vendors')
    history=commands.add_parser('history');history.add_argument('vendor_id')
    draft=commands.add_parser('draft');draft.add_argument('--file',required=True)
    draft.add_argument('--expected-version',required=True,type=int);draft.add_argument('--reason',required=True)
    approve=commands.add_parser('approve');approve.add_argument('vendor_id');approve.add_argument('--version',required=True,type=int)
    approve.add_argument('--reason',required=True)
    suspend=commands.add_parser('suspend');suspend.add_argument('vendor_id');suspend.add_argument('--reason',required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    load_dotenv(root/'.env')
    admin=DirectoryAdmin(os.getenv('CONVENE_DIRECTORY_ADMIN_URL',''),operator=args.operator)
    if args.command=='import-existing':result={'imported':admin.import_existing()}
    elif args.command=='history':result=admin.history(args.vendor_id)
    elif args.command=='draft':result={'draft_version':admin.propose(json.loads(Path(args.file).read_text(encoding='utf-8-sig')),
        reason=args.reason,expected_version=args.expected_version)}
    elif args.command=='approve':result={'approval_id':admin.approve(args.vendor_id,args.version,reason=args.reason)}
    else:admin.suspend(args.vendor_id,reason=args.reason);result={'status':'suspended','vendor_id':args.vendor_id}
    print(json.dumps(result,indent=2,default=str,ensure_ascii=True))


if __name__=='__main__':main()
