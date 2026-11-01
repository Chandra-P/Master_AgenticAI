# CONVENE Party Website Design

User approved the venue/professional decorator experience and requested a website
similar to live booking/comparison sites. Implement that approved experience in
the existing local CONVENE app, not a disconnected hosted mockup.

Party: Stitch-themed 10th birthday, San Antonio Texas, December 6 2026,
30 children plus 90 family members = 120 guests, $2,000 whole-party ceiling.

Build a responsive photo-led marketplace: warm cream, dark navy, teal actions,
playful blue/lilac accents, editorial heading, visible party brief, venue and
professional decor tabs, filter/sort, source/date labels, shortlists, detail modal,
and sticky venue+decor budget panel. Never claim December 6 availability or
Stitch capability without provider confirmation. Published starting rates are
lower bounds; show exclusions and retain an editable reserve for other costs.
All sourced catalog cards have official-page links. Photos are actual provider
photos with source credit, or clearly labeled illustrative inspiration.

Curated public options appear immediately without paid calls. Optional discovery
uses Keenable (keyless by default) as user requested earlier; custom URLs reuse
existing evidence-checked venue extraction. Do not fabricate reviews, ratings,
quotes, photography, package contents, or live availability. Decor services
require custom Stitch quote; a public arch rate is not a complete Stitch package.

Selections, editable quotes, likes and party brief live in browser storage only.
Downloadable shortlist/quote-request text is prepared locally; never send messages
or book anything. Existing FastAPI routes, six-node graph and Streamlit app remain
available. Serve the new page at FastAPI /. Browser calls stay same-origin, all
API credentials remain server-side. No protected Git changes or commits.
