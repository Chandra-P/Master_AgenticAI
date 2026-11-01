"""Owned, confirmed-brief comparisons against the current approved directory only."""
from decimal import Decimal
import hashlib
import json
import re

from convene.domain import EventBriefVersion
from convene.planner_graph import PlannerGraph
from convene.policy import authorize_action
from convene.repository import Conflict
from convene.vendor_directory import DirectoryRepository


KINDS={'venue':'venue','decoration':'decorator','food':'food'}


def directory_revision(directory):
    return hashlib.sha256(json.dumps(directory,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def match_catalog(brief,directory):
    groups={};options=[];gaps=[]
    for service in brief.services:
        group={'options':[],'conditional':[],'excluded':[]};groups[service]=group
        candidates=directory.get('food',[]) if service=='food' else directory.get('vendors',[])
        for vendor in candidates:
            if vendor['kind']!=KINDS[service] or vendor.get('approval',{}).get('status')!='approved':continue
            reasons=[];missing=[];excluded=[];conditional=[]
            location=vendor.get('address','') if service=='venue' else vendor.get('area','')
            if not re.search(r'\bsan antonio\b',location,re.IGNORECASE):
                conditional.append('San Antonio location/service area needs confirmation.')
            else:reasons.append('Listed in the approved San Antonio directory.')
            if service=='venue':
                capacity=vendor.get('capacity')
                if capacity is None:conditional.append('Published guest capacity is missing.')
                elif capacity<brief.total_guests:excluded.append(f'Published maximum {capacity} is below all {brief.total_guests} guests.')
                else:reasons.append(f'Published maximum {capacity} covers the {brief.total_guests}-guest headcount; layout still needs confirmation.')
                missing.extend(['Seated layout and activity space','Required security, deposits and other rental fees'])
                if 'food' in brief.services:missing.append('Outside-food and cake rules')
                if 'decoration' in brief.services:missing.append('Professional decorator setup/attachment access')
            elif service=='decoration':
                missing.extend(['Delivery, installation, teardown and taxes','Exact design, size and included items'])
                if brief.theme:missing.append(f'Whether the provider can supply the requested {brief.theme} theme')
            else:missing.extend(['Serving quantities for all guests','Dietary requirements','Pickup/delivery timing and fees'])
            price=vendor.get('price')
            if price is None:missing.append('No published price; request an itemized quote')
            else:
                if brief.budget is not None and Decimal(str(price))>brief.budget:
                    excluded.append(f'Published base/minimum ${price:g} already exceeds the ${brief.budget:g} total ceiling.')
                reasons.append(f'Published base/minimum ${price:g}; required extras are not fully priced.')
            date_label=brief.event_date.isoformat() if brief.event_date else 'the chosen date/time'
            missing.insert(0,f'Availability for {date_label} and {brief.time_window or "the chosen time"}')
            missing.append('Complete itemized quote and reservation-securing conditions')
            entry={'vendor':vendor,'service':service,'reasons':reasons,'missing':missing,
                   'status':'excluded' if excluded else 'conditional' if conditional else 'candidate',
                   'conditions':conditional,'exclusion_reasons':excluded}
            group['excluded' if excluded else 'conditional' if conditional else 'options'].append(entry)
        for key in ('options','conditional'):
            group[key].sort(key=lambda x:(x['vendor'].get('price') is None,x['vendor'].get('price') or 0,x['vendor']['name']))
            group[key]=group[key][:5]
        options.extend(group['options'])
        if not group['options']:gaps.append(f'No approved {service} option currently meets the known constraints.')
        elif len(group['options'])<5:gaps.append(f'Only {len(group["options"])} approved {service} options match; no filler vendors added.')
    lower=[]
    for group in groups.values():
        prices=[Decimal(str(o['vendor']['price'])) for o in group['options'] if o['vendor'].get('price') is not None]
        if not prices or any(o['vendor'].get('price') is None for o in group['options']):break
        lower.append(min(prices))
    known=float(sum(lower)) if len(lower)==len(groups) else None
    impossible=any(not group['options'] and not group['conditional'] for group in groups.values())
    pressure=known is not None and brief.budget is not None and Decimal(str(known))>brief.budget
    if pressure:gaps.append('Even the cheapest known base/minimum combination exceeds the total budget; ask which priority to protect.')
    return {'groups':groups,'options':options,'gaps':gaps,'guests':brief.total_guests,
            'budget_ceiling':float(brief.budget) if brief.budget is not None else None,
            'budget_status':'needs_changes' if impossible or pressure else 'needs_quotes',
            'known_minimum_combination':known,
            'cost_note':'Selected-scope published base/minimum comparison, not an all-in quote or a typical market spending estimate.',
            'mode':'approved_catalog','availability':'unconfirmed'}


class CatalogPlanner:
    def __init__(self,repository):
        self.repository=repository;self.directory=DirectoryRepository(repository.dsn)

    def compare(self,actor,event_id,*,expected_version):
        event=self.repository.get_event(actor,event_id)
        if event.brief.version!=expected_version:raise Conflict('Stale brief version; reload before comparing.')
        authorize_action(actor,event,'compare_catalog')
        with self.repository.transaction(actor) as connection:
            connection.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',('compare:'+str(event_id),))
            snapshot=self.directory.list_approved();revision=directory_revision(snapshot)
            graph=PlannerGraph(self.repository,research=lambda body:match_catalog(EventBriefVersion.model_validate(body),snapshot),action='compare_catalog')
            row=connection.execute('SELECT run_id FROM catalog_comparisons WHERE event_id=%s AND brief_version=%s AND directory_revision=%s',
                                   (event_id,expected_version,revision)).fetchone()
            run_id=row['run_id'] if row else graph.start(actor,event_id,expected_version=expected_version)
            state=graph.resume(actor,event_id,run_id,expected_version=expected_version)
            if directory_revision(self.directory.list_approved())!=revision:
                raise Conflict('Approved directory changed; compare again for current options.')
            latest=self.repository._load(connection,actor,event_id,lock=True)
            if latest.brief.version!=expected_version:raise Conflict('Brief changed during comparison; reload.')
            authorize_action(actor,latest,'compare_catalog')
            if not row:connection.execute('INSERT INTO catalog_comparisons(event_id,brief_version,directory_revision,run_id) VALUES(%s,%s,%s,%s)',
                                         (event_id,expected_version,revision,run_id))
            result={**state['research'],'run_id':str(run_id),'brief_version':expected_version,'directory_revision':revision,
                    'completed_nodes':state['completed_nodes'],'schedule':state['schedule'],'creative':state['creative']}
            return result

    def _event(self,actor,event_id,expected_version):
        event=self.repository.get_event(actor,event_id)
        if event.brief.version!=expected_version:raise Conflict('Stale brief version; reload before continuing.')
        authorize_action(actor,event,'compare_catalog')
        return event

    def select(self,actor,event_id,vendor_id,*,vendor_version,expected_version,selected):
        event=self._event(actor,event_id,expected_version)
        if selected:
            current=self.compare(actor,event_id,expected_version=expected_version)
            candidates=[item for group in current['groups'].values() for key in ('options','conditional') for item in group[key]]
            choice=next((item['vendor'] for item in candidates if item['vendor']['id']==vendor_id),None)
            if not choice:raise ValueError('This vendor is not a current candidate for the confirmed brief.')
            if choice['directory_version']!=vendor_version:raise Conflict('Vendor changed; review the latest approved version.')
        with self.repository.transaction(actor) as connection:
            event=self.repository._load(connection,actor,event_id,lock=True)
            if event.brief.version!=expected_version:raise Conflict('Brief changed; review again.')
            authorize_action(actor,event,'compare_catalog')
            if selected:
                connection.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',('vendor:'+vendor_id,))
                live=self.directory.list_approved()
                choice=next((v for v in live['vendors']+live['food'] if v['id']==vendor_id),None)
                if not choice or choice['directory_version']!=vendor_version:
                    raise Conflict('Vendor is no longer approved at this version; compare again.')
                count=connection.execute('SELECT count(*) AS n FROM event_shortlist WHERE event_id=%s AND brief_version=%s',
                                         (event_id,expected_version)).fetchone()['n']
                if count>=15:raise ValueError('Shortlist limit reached.')
                connection.execute('INSERT INTO event_shortlist(event_id,brief_version,vendor_id,vendor_version,approval_id) '
                    'VALUES(%s,%s,%s,%s,%s) ON CONFLICT(event_id,brief_version,vendor_id) DO UPDATE '
                    'SET vendor_version=EXCLUDED.vendor_version,approval_id=EXCLUDED.approval_id',
                    (event_id,expected_version,vendor_id,vendor_version,choice['approval']['approval_id']))
            else:
                connection.execute('DELETE FROM event_shortlist WHERE event_id=%s AND brief_version=%s AND vendor_id=%s',
                                   (event_id,expected_version,vendor_id))
            self.repository._audit(connection,actor,event_id,'vendor_shortlisted' if selected else 'vendor_unshortlisted',
                {'vendor_id':vendor_id,'vendor_version':vendor_version,'brief_version':expected_version})
        return self.shortlist(actor,event_id,expected_version=expected_version)

    def context(self,actor,event_id,query):
        event=self.repository.get_event(actor,event_id)
        if event.status!='planning' or event.confirmed_version!=event.brief.version:return []
        assessment=match_catalog(event.brief,self.directory.list_approved())
        chunks=[]
        for group in assessment['groups'].values():
            for key in ('options','conditional','excluded'):
                for option in group[key]:
                    vendor=option['vendor'];contact=vendor.get('contact') or {}
                    content=[f"Approved provider: {vendor['name']}.",f"Category: {option['service']}."]
                    if vendor.get('address'):content.append('Published address: '+vendor['address']+'.')
                    if vendor.get('capacity') is not None:content.append(f"Published maximum capacity: {vendor['capacity']} people. Layout suitability still needs confirmation.")
                    if vendor.get('price') is not None:content.append(f"Published base/minimum: ${vendor['price']:g}. This is not an all-in quote; required extras remain unknown.")
                    else:content.append('Published price is unknown; an itemized quote is required.')
                    if contact.get('phone_display'):content.append(f"Reservations office: {contact['organization']}; phone {contact['phone_display']}.")
                    content.append('Date availability and reservation status are unconfirmed. No inquiry has been sent or booking made.')
                    content.append('Published source snapshot checked '+vendor.get('checked_on','unknown')+'.')
                    chunks.append({'id':f"directory:{vendor['id']}:v{vendor['directory_version']}:{vendor['approval']['approval_id']}",
                        'kind':'approved_vendor','title':vendor['name'],'content':' '.join(content),
                        'source_id':vendor['source_url'],'source_kind':'approved_directory',
                        'retrieved_at':vendor['approval']['recorded_at'],'brief_version':event.brief.version,
                        'vendor_id':vendor['id'],'vendor_version':vendor['directory_version'],
                        'approval_id':vendor['approval']['approval_id']})
        terms=set(re.findall(r'\w+',query.lower()))
        chunks.sort(key=lambda c:len(terms&set(re.findall(r'\w+',c['content'].lower()))),reverse=True)
        return chunks[:6]

    def shortlist(self,actor,event_id,*,expected_version):
        self._event(actor,event_id,expected_version)
        live=self.directory.list_approved();approved={v['id']:v for v in live['vendors']+live['food']}
        with self.repository.transaction(actor) as connection:
            rows=connection.execute('SELECT vendor_id,vendor_version,approval_id FROM event_shortlist WHERE event_id=%s AND brief_version=%s ORDER BY created_at,vendor_id',
                                    (event_id,expected_version)).fetchall()
        selected=[];stale=[]
        for row in rows:
            vendor=approved.get(row['vendor_id'])
            if not vendor or vendor['directory_version']!=row['vendor_version'] or vendor['approval']['approval_id']!=str(row['approval_id']):
                stale.append({'vendor_id':row['vendor_id'],'reason':'Approval/version changed; review before preparing an inquiry.'})
            else:selected.append(vendor)
        return {'selected':selected,'stale':stale,'brief_version':expected_version}

    def drafts(self,actor,event_id,*,expected_version):
        event=self._event(actor,event_id,expected_version)
        shortlist=self.shortlist(actor,event_id,expected_version=expected_version)
        groups={}
        for vendor in shortlist['selected']:
            contact=vendor.get('contact') or {}
            key=contact.get('organization_id') or vendor['id']
            groups.setdefault(key,[]).append(vendor)
        drafts=[]
        for key,vendors in groups.items():
            contacts=[v.get('contact') or {} for v in vendors]
            emails={c.get('email') for c in contacts if c.get('email') and c.get('email_status')=='verified'}
            recipients=sorted(emails) if len(emails)==1 and all(c.get('email_status')=='verified' and c.get('email') in emails for c in contacts) else []
            names=', '.join(v['name'] for v in vendors)
            b=event.brief
            date_text=b.event_date.isoformat() if b.event_date else b.date_flexibility or 'date not decided'
            subject='Availability and itemized quote: '+' '.join(b.occasion.split())[:120]
            lines=['Hello,',f'I am planning a {b.occasion} in San Antonio for {b.total_guests} guests.',
                   f'Date: {date_text}. Time preference: {b.time_window or "not decided"}.',
                   f'I am considering: {names}.']
            if len(vendors)>1:lines.append('These are alternatives; please confirm availability and pricing separately for each.')
            if b.theme:lines.append(f'Theme preference: {b.theme}; please confirm whether it is possible.')
            lines.extend(['Please confirm availability, permitted layout, included services, all required fees, deposits and securing conditions.',
                          'Please confirm outside-food rules and professional-decorator access where applicable.',
                          'This is an inquiry only; it does not accept a quote or request a booking.','Thank you.'])
            missing=['Parent must review the exact inquiry and connect Gmail before any sending.']
            if not recipients:missing.insert(0,'No verified recipient email configured; use the published phone/contact page to confirm it.')
            drafts.append({'group_id':key,'vendor_ids':[v['id'] for v in vendors],
                'vendor_versions':{v['id']:v['directory_version'] for v in vendors},'brief_version':expected_version,
                'to':recipients,'subject':subject,'body':'\n\n'.join(lines),'attachments':[],
                'status':'draft — not sent','sendable':False,'missing':missing})
        return {'drafts':drafts,'stale':shortlist['stale'],'brief_version':expected_version,'messages_sent':0}
