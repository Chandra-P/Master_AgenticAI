"""Fictional, stateless restaurant tools. This module never contacts a vendor."""
import hashlib
from mcp.server.fastmcp import FastMCP

mcp = FastMCP('Tagalong fictional restaurant demo')
LABEL = 'Demo reservation—no real booking or charge'
VENUES = {'demo-lantern': 'The Imaginary Lantern', 'demo-orchard': 'Fictional Orchard Kitchen', 'demo-moon': 'Make Believe Moon Cafe'}
SLOTS = ['17:30', '18:00', '19:00', '20:30']


@mcp.tool()
def search_restaurants(city: str, date: str, party_size: int) -> dict:
    return {'simulation': True, 'label': LABEL, 'restaurants': [{'id': key, 'name': name, 'city': city, 'description': 'Fictional restaurant for a simulated reservation.', 'times': SLOTS} for key, name in VENUES.items()]}


@mcp.tool()
def check_availability(restaurant_id: str, city: str, date: str, time: str, party_size: int) -> dict:
    if restaurant_id not in VENUES or not 1 <= party_size <= 12:
        raise ValueError('Unknown fictional restaurant or party size')
    return {'simulation': True, 'label': LABEL, 'available': time in SLOTS, 'restaurant_name': VENUES[restaurant_id], 'estimated_total': party_size * 35, 'currency': 'USD'}


@mcp.tool()
def create_demo_booking(quote_id: str) -> dict:
    return {'simulation': True, 'label': LABEL, 'reference': 'DEMO-' + hashlib.sha256(quote_id.encode()).hexdigest()[:10].upper()}


@mcp.tool()
def cancel_demo_booking(reference: str) -> dict:
    if not reference.startswith('DEMO-'):
        raise ValueError('Only demo reservations can be cancelled')
    return {'simulation': True, 'label': LABEL, 'status': 'cancelled', 'reference': reference}


if __name__ == '__main__':
    mcp.run(transport='stdio')
