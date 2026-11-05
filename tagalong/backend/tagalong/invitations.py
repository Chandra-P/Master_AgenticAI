"""Owner-controlled invitations; plaintext tokens are returned only at creation."""
import hashlib
import secrets
import time
from datetime import datetime, timezone
from .core import access, fail, register
from .models import MAX_MEMBERS


def owner_plan(state, pid, actor):
    plan = access(state, pid, actor)
    if plan['owner_id'] != actor.id:
        fail(403, 'Only the owner can manage invitation links')
    return plan


def issue(state, pid, actor):
    owner_plan(state, pid, actor)
    token = secrets.token_urlsafe(32)
    expires = time.time() + 7 * 24 * 60 * 60
    state.setdefault('invitations', {})[pid] = {
        'digest': hashlib.sha256(token.encode()).hexdigest(), 'expires_at': expires,
    }
    return {'token': token, 'expires_at': datetime.fromtimestamp(expires, timezone.utc).isoformat()}


def revoke(state, pid, actor):
    owner_plan(state, pid, actor)
    state.setdefault('invitations', {}).pop(pid, None)
    return {'status': 'disabled'}


def accept(state, token, actor):
    register(state, actor)
    digest = hashlib.sha256(token.encode()).hexdigest()
    pid = next((pid for pid, link in state.get('invitations', {}).items()
                if secrets.compare_digest(link['digest'], digest) and link['expires_at'] > time.time()), None)
    if not pid or pid not in state['plans']:
        fail(404, 'This invitation is unavailable or expired. Ask the owner for a new link.')
    if actor.id in state['members'][pid]:
        return {'plan_id': pid}
    if len(state['members'][pid]) >= MAX_MEMBERS:
        fail(409, 'Plan member limit reached')
    register(state, actor)
    state['members'][pid].append(actor.id)
    state['plans'][pid]['members'].append({'name': actor.name, 'user_id': actor.id, 'color': '#14b8a6'})
    state['plans'][pid]['revision'] += 1
    return {'plan_id': pid}
