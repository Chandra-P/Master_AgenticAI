"""Server-side action boundaries; model decisions never grant permissions."""
from datetime import datetime,timedelta,timezone
import hashlib
import hmac
import json

from convene.domain import Approval,EventRecord,InquiryPayload,Principal


class PolicyDenied(PermissionError):
    pass


def payload_digest(payload:InquiryPayload)->str:
    encoded=json.dumps(payload.model_dump(mode='json'),sort_keys=True,separators=(',',':'),ensure_ascii=False)
    return hashlib.sha256(encoded.encode('utf-8')).hexdigest()


def authorize_action(actor:Principal,event:EventRecord,action:str,*,approval:Approval|None=None,
                     payload:InquiryPayload|None=None,inquiry_id=None,provider_id=None,mailbox_id=None,
                     followups_sent=0,last_sent_at=None,replied=False,confirmed_fact_keys=(),
                     answered_fact_keys=(),recorded_reservation=False,checkpoint_sent=False,now=None):
    now=now or datetime.now(timezone.utc)
    if actor.id!=event.owner_id:raise PolicyDenied('Event not accessible.')
    if action in ('view','edit','confirm_brief'):return
    if action=='compare_catalog':
        if event.status!='planning' or event.confirmed_version!=event.brief.version:
            raise PolicyDenied('Confirm the current brief before comparing approved vendors.')
        return
    allowed={'research','send_inquiry','factual_reply','followup','reconfirmation'}
    if action not in allowed:raise PolicyDenied('Action is outside this application scope.')
    if not actor.authenticated:raise PolicyDenied('Sign in before research or provider communication.')
    if event.status!='planning' or event.confirmed_version!=event.brief.version:
        raise PolicyDenied('Confirm the current brief before continuing.')
    if action=='research':return
    if not approval or approval.capability!=action:raise PolicyDenied('Explicit action grant required.')
    if (approval.actor_id!=actor.id or approval.event_id!=event.id or approval.brief_version!=event.brief.version
            or approval.revoked_at is not None or approval.expires_at<=now):
        raise PolicyDenied('Grant is expired, revoked or bound to another event/brief.')
    if (approval.inquiry_id!=inquiry_id or approval.provider_id!=provider_id or approval.mailbox_id!=mailbox_id):
        raise PolicyDenied('Grant does not match this inquiry, provider and mailbox.')
    if action=='send_inquiry':
        if not payload or not approval.payload_digest or not hmac.compare_digest(approval.payload_digest,payload_digest(payload)):
            raise PolicyDenied('Exact recipients, content and attachments must be approved.')
    elif action=='followup':
        if replied or followups_sent>=3 or followups_sent<0:
            raise PolicyDenied('Follow-up limit reached or provider already replied.')
        if not last_sent_at or now-last_sent_at<timedelta(hours=24):
            raise PolicyDenied('Wait at least 24 hours before the next follow-up.')
    elif action=='factual_reply':
        if not answered_fact_keys or not set(answered_fact_keys)<=set(confirmed_fact_keys):
            raise PolicyDenied('Only current confirmed facts can be answered automatically.')
    elif action=='reconfirmation':
        if not recorded_reservation or checkpoint_sent:
            raise PolicyDenied('A recorded reservation and an unsent checkpoint are required.')
