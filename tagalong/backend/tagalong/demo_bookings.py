"""Authenticated durable state for explicitly confirmed fictional reservations."""
import time
from datetime import date, datetime, timezone
from fastapi import Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt
from .core import access, fail, uid, now
from .demo_booking_gateway import DemoBookingGateway


class Search(BaseModel):
    model_config = ConfigDict(extra='forbid')
    date: date
    party_size: StrictInt = Field(ge=1, le=12)
    city: str = Field(min_length=1, max_length=100, pattern=r'\S')


class Quote(Search):
    restaurant_id: str = Field(pattern=r'^demo-(lantern|orchard|moon)$')
    time: str = Field(pattern=r'^([01][0-9]|2[0-3]):[0-5][0-9]$')


class Confirmation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    confirmed: StrictBool


class Confirm(Confirmation):
    quote_id: str = Field(min_length=1, max_length=100)


def install_demo_bookings(app, repo, actor):
    app.state.demo_booking_gateway = DemoBookingGateway()

    def guard(s, pid, a, day=None, revision=None):
        p = access(s, pid, a)
        if revision is not None and p['revision'] != revision:
            fail(409, 'Plan changed; request a new demo quote')
        if day is not None and not p['start'] <= day <= p['end']:
            fail(422, 'Demo reservation date must be within plan dates')
        return p

    def throttle(s, pid, a):
        guard(s, pid, a)
        bucket = int(time.time() // 60)
        limits = s.setdefault('demo_booking_limits', {})
        for key in list(limits):
            if limits[key]['bucket'] != bucket:
                del limits[key]
        key = a.id
        record = limits.setdefault(key, {'bucket': bucket, 'count': 0})
        if record['count'] >= 30 or len(limits) > 10000:
            fail(429, 'Too many demo actions; retry next minute')
        record['count'] += 1

    async def tool(name, arguments):
        try:
            return await app.state.demo_booking_gateway.call(name, arguments)
        except HTTPException:
            raise
        except Exception:
            fail(503, 'Demo restaurant tools unavailable; retry later')

    def envelope(booking, trace=None):
        return {'simulation': True, 'booking': booking, 'trace': trace or []}

    def existing(s, pid, qid):
        return next((b for b in s.get('demo_bookings', {}).values() if b['plan_id'] == pid and b['quote_id'] == qid), None)

    def quote_for(s, pid, a, qid):
        guard(s, pid, a)
        q = s.get('demo_booking_quotes', {}).get(qid)
        if not q or q['plan_id'] != pid or q['created_by'] != a.id:
            fail(404, 'Demo quote not found')
        return q

    def fresh(s, pid, a, q):
        guard(s, pid, a, q['date'], q['plan_revision'])
        if q['expires_epoch'] <= time.time():
            fail(409, 'Demo quote expired; request a new quote')

    @app.get('/v1/plans/{pid}/demo-bookings')
    def listing(pid: str, a=Depends(actor)):
        def read(s):
            guard(s, pid, a)
            return {'simulation': True, 'bookings': [b for b in s.get('demo_bookings', {}).values() if b['plan_id'] == pid]}
        return repo.transact(read)

    @app.post('/v1/plans/{pid}/demo-bookings/search')
    async def search(pid: str, b: Search, a=Depends(actor)):
        data = b.model_dump(mode='json')
        def before(s):
            throttle(s, pid, a)
            return guard(s, pid, a, data['date'])['revision']
        revision = repo.transact(before)
        result = await tool('search_restaurants', data)
        repo.transact(lambda s: guard(s, pid, a, data['date'], revision))
        return {'simulation': True, 'restaurants': result['result']['restaurants'], 'trace': result['trace']}

    @app.post('/v1/plans/{pid}/demo-bookings/quote')
    async def quote(pid: str, b: Quote, a=Depends(actor)):
        data = b.model_dump(mode='json')
        def before(s):
            throttle(s, pid, a)
            return guard(s, pid, a, data['date'])['revision']
        revision = repo.transact(before)
        result = await tool('check_availability', data)
        def save(s):
            guard(s, pid, a, data['date'], revision)
            quotes = s.setdefault('demo_booking_quotes', {})
            for key in list(quotes):
                if quotes[key]['expires_epoch'] <= time.time() and not existing(s, quotes[key]['plan_id'], key):
                    del quotes[key]
            if len(quotes) >= 10000 or sum(q['plan_id'] == pid and q['created_by'] == a.id and q['expires_epoch'] > time.time() for q in quotes.values()) >= 20:
                fail(429, 'Demo quote capacity reached; wait for quotes to expire')
            if not result['result'].get('available'):
                fail(409, 'Demo availability changed')
            expires = time.time() + 600
            q = {**data, 'id': uid(), 'restaurant_name': result['result']['restaurant_name'], 'estimated_total': result['result']['estimated_total'], 'currency': result['result']['currency'], 'expires_at': datetime.fromtimestamp(expires, timezone.utc).isoformat(), 'expires_epoch': expires, 'plan_id': pid, 'created_by': a.id, 'plan_revision': revision, 'simulation': True}
            quotes[q['id']] = q
            return {'simulation': True, 'quote': {k:v for k,v in q.items() if k not in ('expires_epoch','plan_revision','created_by','plan_id')}, 'trace': result['trace']}
        return repo.transact(save)

    @app.post('/v1/plans/{pid}/demo-bookings/confirm')
    async def confirm(pid: str, b: Confirm, a=Depends(actor)):
        if b.confirmed is not True:
            fail(422, 'Explicit demo reservation confirmation required')
        def before(s):
            q = quote_for(s, pid, a, b.quote_id)
            found = existing(s, pid, b.quote_id)
            if found:
                return q, found
            throttle(s, pid, a); fresh(s, pid, a, q)
            return q, None
        q, found = repo.transact(before)
        if found:
            return envelope(found)
        result = await tool('create_demo_booking', {'quote_id': q['id']})
        def save(s):
            current = quote_for(s, pid, a, b.quote_id)
            found = existing(s, pid, b.quote_id)
            if found:
                return envelope(found)
            fresh(s, pid, a, current)
            p = guard(s, pid, a)
            bookings = s.setdefault('demo_bookings', {})
            if len(bookings) >= 10000 or sum(x['plan_id'] == pid for x in bookings.values()) >= 100 or len(p['itinerary']) >= 200:
                fail(409, 'Demo reservation capacity reached')
            bid = uid(); entry = 'demo-booking-' + bid
            booking = {k: q[k] for k in ('restaurant_name','city','date','time','party_size','estimated_total','currency')}
            booking.update({'id': bid, 'quote_id': q['id'], 'plan_id': pid, 'reference': result['result']['reference'], 'status': 'confirmed', 'created_by': a.id, 'created_at': now(), 'simulation': True, 'itinerary_entry_id': entry})
            bookings[bid] = booking
            p['itinerary'].append({'id': entry, 'title': 'DEMO reservation: ' + q['restaurant_name'], 'time': q['time'], 'day': q['date'], 'category': 'Fictional demo — no real booking or charge', 'location': q['city']})
            p['revision'] += 1
            return envelope(booking, result['trace'])
        return repo.transact(save)

    @app.post('/v1/plans/{pid}/demo-bookings/{booking_id}/cancel')
    async def cancel(pid: str, booking_id: str, b: Confirmation, a=Depends(actor)):
        if b.confirmed is not True:
            fail(422, 'Explicit cancellation confirmation required')
        def check(s):
            p = guard(s, pid, a)
            booking = s.get('demo_bookings', {}).get(booking_id)
            if not booking or booking['plan_id'] != pid:
                fail(404, 'Demo reservation not found')
            if a.id not in (booking['created_by'], p['owner_id']):
                fail(403, 'Only the creator or plan owner may cancel')
            return booking, p
        def before(s):
            booking, p = check(s)
            if booking['status'] != 'cancelled':
                throttle(s, pid, a)
            return booking, p['revision']
        booking, revision = repo.transact(before)
        if booking['status'] == 'cancelled':
            return envelope(booking)
        result = await tool('cancel_demo_booking', {'reference': booking['reference']})
        def save(s):
            booking, p = check(s)
            if booking['status'] == 'cancelled':
                return envelope(booking)
            guard(s, pid, a, revision=revision)
            booking['status'] = 'cancelled'; booking['cancelled_by'] = a.id; booking['cancelled_at'] = now()
            p['itinerary'] = [item for item in p['itinerary'] if item['id'] != booking['itinerary_entry_id']]
            p['revision'] += 1
            return envelope(booking, result['trace'])
        return repo.transact(save)
