"""Operator-only additive bootstrap: python -m tagalong.bootstrap_admin --user-id UUID."""
import argparse
import os
import httpx
from .admin import audit
from .core import identity, register
from .repository import PostgresRepository


def grant(repo, actor):
    def change(state):
        register(state,actor)
        admins=state.setdefault('app_admins',{})
        if actor.id not in admins:
            event=audit(state,actor,'bootstrap_admin',actor.id,'Operator-authorized initial app administration')
            admins[actor.id]={'granted_at':event['at'],'granted_by':'operator_bootstrap'}
        return {'app_admin':True}
    return repo.transact(change)


def main():
    import uuid
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--user-id',required=True,type=uuid.UUID)
    args=parser.parse_args()
    try:
        key=os.environ['SUPABASE_SERVICE_ROLE_KEY']
        response=httpx.get(os.environ['SUPABASE_URL'].rstrip('/')+'/auth/v1/admin/users/'+str(args.user_id),headers={'apikey':key,'Authorization':'Bearer '+key},timeout=15)
        response.raise_for_status()
        user=response.json()
        if user.get('id')!=str(args.user_id) or not user.get('email_confirmed_at'):
            raise ValueError('A confirmed existing account is required')
        repo=PostgresRepository(os.environ['DATABASE_URL'])
        try: grant(repo,identity(user))
        finally: repo.pool.close()
    except Exception as exc:
        print('Admin bootstrap failed: '+type(exc).__name__)
        raise SystemExit(1) from None
    print('Selected confirmed account has app administrator access.')


if __name__=='__main__': main()
