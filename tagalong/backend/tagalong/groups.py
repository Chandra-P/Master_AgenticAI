"""Reusable adult rosters with explicit, view-only sharing. Never grants plan access."""
import copy
import re
from fastapi import Depends
from fastapi.responses import JSONResponse
from pydantic import Field, StrictBool, StrictInt, field_validator, model_validator
from .models import Item
from .core import fail, now, uid


def normalized(value):
    return ' '.join(value.split())


class Contact(Item):
    id: str = Field(min_length=1, max_length=128)
    preferredName: str = Field(min_length=1, max_length=40)
    color: str = Field(pattern=r'^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$')
    firstName: str | None = Field(default=None, max_length=40)
    lastName: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=254)

    @field_validator('preferredName', mode='before')
    @classmethod
    def alias(cls, value):
        return normalized(value) if isinstance(value, str) else value

    @field_validator('email', 'firstName', 'lastName', mode='before')
    @classmethod
    def optional_text(cls, value):
        return value.strip() or None if isinstance(value, str) else value

    @field_validator('email')
    @classmethod
    def email_address(cls, value):
        if value and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
            raise ValueError('Use a valid email address or leave it blank')
        return value


class GroupDraft(Item):
    name: str = Field(min_length=1, max_length=80)
    theme: str = Field(min_length=1, max_length=60)
    members: list[Contact] = Field(min_length=1, max_length=13)

    @field_validator('name', 'theme', mode='before')
    @classmethod
    def trim(cls, value):
        return normalized(value) if isinstance(value, str) else value

    @model_validator(mode='after')
    def distinct_contacts(self):
        for values in ([m.id for m in self.members], [m.preferredName.casefold() for m in self.members],
                       [m.email.casefold() for m in self.members if m.email]):
            if len(values) != len(set(values)):
                raise ValueError('Use distinct member IDs, preferred aliases and email addresses')
        return self


class GroupEdit(GroupDraft):
    expected_revision: StrictInt = Field(ge=1)
    archived: bool


class GroupDelete(Item):
    expected_revision: StrictInt = Field(ge=1)


class GroupSharing(GroupDelete):
    shared: StrictBool


def can_view(group, actor):
    return group['ownerId'] == actor.id or (
        group.get('shared', False) and actor.email_verified and bool(actor.email.strip())
        and any((m.get('email') or '').strip().casefold() == actor.email.strip().casefold()
                for m in group['members'] if m['id'] != group['ownerId']))


def group_view(group, actor):
    result = copy.deepcopy(group)
    result['role'] = 'owner' if group['ownerId'] == actor.id else 'member'
    result['shared'] = group.get('shared', False)
    result['ownerName'] = next((m['preferredName'] for m in group['members'] if m['id'] == group['ownerId']), 'Group owner')
    if result['role'] == 'member':
        result['members'] = [{key: m[key] for key in ('id', 'preferredName', 'color')} for m in group['members']]
    return result


def read_group(state, actor, group_id):
    group = state.get('groups', {}).get(group_id)
    if not group or not can_view(group, actor):
        fail(404, 'Group not found')
    return group_view(group, actor)


def access_group(state, actor, group_id, revision=None):
    group = state.get('groups', {}).get(group_id)
    if not group or group['ownerId'] != actor.id:
        fail(404, 'Group not found')
    if revision is not None and revision != group['revision']:
        fail(409, 'This group changed. Reload groups before retrying.')
    return group


def save_group(state, actor, body, group_id=None):
    old = access_group(state, actor, group_id, body.expected_revision) if group_id else None
    groups = state.setdefault('groups', {})
    if any(g['id'] != group_id and g['ownerId'] == actor.id and g['name'].casefold() == body.name.casefold() for g in groups.values()):
        fail(409, 'That group name is already in use, including archived groups.')
    if not old and sum(g['ownerId'] == actor.id for g in groups.values()) >= 100:
        fail(409, 'Group limit reached. Remove an unused group before adding another.')
    owner = next((m for m in body.members if m.id == actor.id), None)
    owner_name = (actor.display_name or actor.name)[:40]
    if not owner or owner.preferredName != owner_name:
        fail(422, 'Keep your signed-in account as the group owner.')
    # Contact IDs are opaque roster IDs, never memberships or trusted account IDs.
    group = {'id': old['id'] if old else uid(), 'name': body.name, 'theme': body.theme,
             'ownerId': actor.id, 'members': [m.model_dump(exclude_none=True) for m in body.members],
             'archived': body.archived if old else False, 'revision': old['revision'] + 1 if old else 1,
             'shared': old.get('shared', False) if old else False}
    groups[group['id']] = group
    record_event(state, actor, group['id'], 'update' if old else 'create')
    return group


def record_event(state, actor, group_id, action):
    events = state.setdefault('group_events', [])
    if len(events) >= 100000:
        fail(503, 'Group activity capacity reached. Contact the administrator.')
    events.append({'id': uid(), 'actor_id': actor.id, 'group_id': group_id, 'action': action, 'at': now()})


def plan_group(state, actor, group_id, revision):
    if not group_id:
        return None
    group = access_group(state, actor, group_id, revision)
    if group['archived']:
        fail(409, 'This group is archived. Restore it or choose another group.')
    # Only aliases and labels are copied; never emails, legal names or contact IDs.
    return {'id': group['id'], 'name': group['name'], 'theme': group['theme'],
            'revision': group['revision'], 'participants': [m['preferredName'] for m in group['members']]}


def install_groups(app, repo, actor):
    @app.get('/v1/groups')
    def listing(a=Depends(actor)):
        return JSONResponse(repo.transact(lambda s: sorted(
            (group_view(g, a) for g in s.get('groups', {}).values() if can_view(g, a)),
            key=lambda g: (g['name'].casefold(), g['id']))), headers={'Cache-Control': 'no-store'})

    @app.get('/v1/groups/{group_id}')
    def read(group_id: str, a=Depends(actor)):
        return JSONResponse(repo.transact(lambda s: read_group(s, a, group_id)), headers={'Cache-Control': 'no-store'})

    @app.post('/v1/groups/{group_id}/sharing')
    def sharing(group_id: str, body: GroupSharing, a=Depends(actor)):
        def change(state):
            group = access_group(state, a, group_id, body.expected_revision)
            if group.get('shared', False) != body.shared:
                group['shared'] = body.shared
                group['revision'] += 1
                record_event(state, a, group_id, 'share' if body.shared else 'unshare')
            return group_view(group, a)
        return repo.transact(change)

    @app.post('/v1/groups')
    def create(body: GroupDraft, a=Depends(actor)):
        return repo.transact(lambda s: group_view(save_group(s, a, body), a))

    @app.patch('/v1/groups/{group_id}')
    def edit(group_id: str, body: GroupEdit, a=Depends(actor)):
        return repo.transact(lambda s: group_view(save_group(s, a, body, group_id), a))

    @app.delete('/v1/groups/{group_id}')
    def remove(group_id: str, body: GroupDelete, a=Depends(actor)):
        def change(state):
            access_group(state, a, group_id, body.expected_revision)
            del state['groups'][group_id]
            record_event(state, a, group_id, 'remove')
            return {'status': 'removed'}
        return repo.transact(change)
