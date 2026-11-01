"""Public-source starter shortlist, checked October 31, 2026; not live quotes."""
from copy import deepcopy

VENUES = [
    dict(id='south-san', name='South San Civic Center', kind='venue', area='South Side',
         address='503 E. Lovett, San Antonio, TX 78221', capacity=160, price=235,
         price_type='published_base', price_note='Published private rental rate',
         description='A practical blank canvas for games, cake and the whole family.',
         image='/assets/south-san.jpg', image_credit='Bexar County',
         source_url='https://www.bexar.org/3665/South-San-Civic-Center',
         badge='Lowest published base', features=['160 chairs', 'Tables', 'Kitchen', 'Parking'],
         exclusions=['Required security charges', 'Any deposits, taxes and additional fees'],
         confirm=['December 6 availability', 'Seated layout with space for games', 'Outside food and cake rules',
                  'Balloon installation and wall-attachment rules', 'Complete rental quote including security']),
    dict(id='navajo', name='Navajo Civic Center', kind='venue', area='East Side',
         address='2600 Rigsby, San Antonio, TX 78222', capacity=200, price=250,
         price_type='published_base', price_note='Published private rental rate',
         description='More published capacity for a celebration with everyone on the guest list.',
         image='/assets/navajo.jpg', image_credit='Bexar County',
         source_url='https://www.bexar.org/3666/Navajo-Civic-Center',
         badge='Room for the whole family', features=['194 chairs', 'Tables', 'Kitchen', 'Parking'],
         exclusions=['Required security charges', 'Any deposits, taxes and additional fees'],
         confirm=['December 6 availability', 'Seated layout with space for games', 'Outside food and cake rules',
                  'Decor setup and teardown access', 'Complete rental quote including security']),
    dict(id='harlandale', name='Harlandale Civic Center', kind='venue', area='South Side',
         address='115 W. Southcross, San Antonio, TX 78221', capacity=170, price=250,
         price_type='published_base', price_note='Published private rental rate',
         description='A community gathering space with tables, a kitchen and Wi-Fi.',
         image='/assets/harlandale.jpg', image_credit='Bexar County',
         source_url='https://www.bexar.org/3664/Harlandale-Civic-Center',
         badge='Tables & kitchen', features=['150 chairs', 'Tables', 'Kitchen', 'Wi-Fi'],
         exclusions=['Required security charges', 'Any deposits, taxes and additional fees'],
         confirm=['December 6 availability', 'Seated layout with space for games', 'Outside food and cake rules',
                  'Professional decorator access', 'Complete rental quote including security']),
]
DECORATORS = [
    dict(id='belle-arch', name='Belle of Balloons', kind='decorator', area='San Antonio',
         package='Balloon arch', price=375, price_type='starting_at',
         price_note='Published balloon-arch starting rate', capacity=None,
         description='A photo-worthy balloon focal point. Ask for a custom blue-and-lilac Stitch proposal.',
         image='/assets/belle.jpg', image_credit='Belle of Balloons',
         source_url='https://belleofballoons.com/balloon-arch-products-san-antonio/',
         badge='Professional balloon design', features=['Balloon arches', 'Custom design enquiries'],
         exclusions=['Custom Stitch theme and character pieces', 'Delivery, installation and teardown', 'Any taxes and added rentals'],
         confirm=['December 6 availability', 'Stitch theme capability and artwork', 'Exact size and included items',
                  'All-in delivery, installation and teardown quote', 'Venue attachment and access rules']),
    dict(id='bewitchin', name='Bewitchin Balloons', kind='decorator', area='San Antonio',
         package='Balloon decor · 12 ft minimum', price=390, price_type='starting_at',
         price_note='Published 12 ft balloon-service minimum; delivery extra', capacity=None,
         description='Custom balloons and backdrop styling. Request a compact Stitch-themed focal area.',
         image='/assets/bewitchin-styling.jpg', image_credit='Bewitchin Balloons',
         source_url='https://bewitchinballoons.com/',
         badge='Custom event styling', features=['12 ft balloon minimum', 'Backdrop styling enquiries'],
         exclusions=['Delivery', 'Backdrop, character pieces and custom theme', 'Any teardown, tax and added rentals'],
         confirm=['December 6 availability', 'Stitch theme capability and artwork', 'Whether a backdrop is included',
                  'All-in installation, delivery and teardown quote', 'Venue attachment and access rules']),
]


def get_catalog():
    venues, decorators = deepcopy(VENUES), deepcopy(DECORATORS)
    for venue in venues:
        venue['contact']=dict(organization_id='bexar-county-parks',
            organization='Bexar County Parks & Recreation Department',
            role='Shared parks reservations office; not an on-site venue manager',
            phone_display='210-335-7275',phone_e164='+12103357275',
            email=None,email_status='not_verified',
            contact_url='https://www.bexar.org/1240/Parks-and-Recreation',
            office_hours='Monday-Friday, 8:00 AM-5:00 PM; closed county holidays',
            timezone='America/Chicago',source_url=venue['source_url'],verified_on='2026-11-01',
            evidence='Parks & Recreation Department; Phone: 210-335-7275; Monday - Friday; 8:00 AM - 5:00 PM')
    for option in venues + decorators:
        option.update(availability='unconfirmed', checked_on='2026-10-31', stitch_confirmed=False)
    return dict(party=dict(title='Her big 10', age=10, theme='Stitch', date='2026-12-06',
                           city='San Antonio, Texas', children=30, family=90, guests=120,
                           budget=2000, reserve=1000), venues=venues, decorators=decorators)
