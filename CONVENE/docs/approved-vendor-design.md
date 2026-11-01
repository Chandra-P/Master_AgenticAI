# Approved vendor operations: FDE design

Implementation update: the React approved directory now reads versioned PostgreSQL
records and stored approval decisions, with separate read-only web/admin database
roles. See [vendor-directory-admin.md](vendor-directory-admin.md). References below
to the initial Python-backed implementation describe the earlier milestone.

The confirmed-brief comparison, approved-provider RAG, saved shortlist and unsent
inquiry previews are now wired: [approved-catalog-planner.md](approved-catalog-planner.md).

## Intended parent experience

The agent greets the parent, understands the celebration, gathers one requirement
at a time, and shows a versioned brief. After confirmation/account save it compares
only the existing human-approved San Antonio directory. No normal-flow web search
or automatic vendor creation. A missing category or unsuitable list is an explicit
gap, not permission to invent a business or relax capacity/budget constraints.

Parents see venue/decor/food options, why each fits, published cost basis, unknown
extras, contact details, sources and last-check dates. They shortlist options and
review an inquiry before any communication. Approval to list a vendor does not
confirm a date, price, theme capability or reservation.

## Current inventory and contact addition

The existing `party_catalog.py` contains **three venues and two professional
decorators**. These five entries were approved for use by the project owner in
conversation on November 1, 2026. No food providers are configured. Do not create
five fictional entries just to meet a presentation target.

All three civic centers list Bexar County Parks & Recreation as a shared office:

| Venue | Venue address | Reservations contact |
|---|---|---|
| South San Civic Center | 503 E. Lovett, San Antonio, TX 78221 | 210-335-7275 |
| Navajo Civic Center | 2600 Rigsby, San Antonio, TX 78222 | 210-335-7275 |
| Harlandale Civic Center | 115 W. Southcross, San Antonio, TX 78221 | 210-335-7275 |

Office hours: Monday-Friday, 8 AM-5 PM, Central time, closed county holidays.
The sources were checked November 1. These are published contact details, not
proof of a phone conversation or the identity of an on-site manager. The official
email link is protected; a direct mailbox has not been verified. Keep email null
and offer the official contact page. A phone number/contact form must not become
an invented Gmail recipient. Decorator contacts remain visibly unverified.

Sources:
- [South San official listing](https://www.bexar.org/3665/South-San-Civic-Center)
- [Navajo official listing](https://www.bexar.org/3666/Navajo-Civic-Center)
- [Harlandale official listing](https://www.bexar.org/3664/Harlandale-Civic-Center)
- [Parks office contact](https://www.bexar.org/1240/Parks-and-Recreation)

## System boundaries

| Record | Responsibility |
|---|---|
| Organization | Provider/business identity; shared coordinator such as Bexar County Parks |
| Venue / service / package | Specific facility or offering; stable ID, category and suitability facts |
| Contact | Organization, role, public phone/email/contact URL, hours/timezone, verification evidence |
| Source fact | Published value, exact excerpt, source document/URL, checked time, applicable scope |
| Approval version | Human decision, actor, timestamp, reason; approved/suspended/retired state |
| Event shortlist | Parent/event/brief version plus selected vendor-record version |
| Inquiry | Exact recipient/content/attachments, approval, status, mailbox and linked thread |

The PostgreSQL published directory is the operational source for `GET /api/vendors`
and the React directory. No network or model call occurs when opening it. The
Python catalog remains legacy/demo data and explicit initial-import input. Do not
maintain independent vendor copies in frontend JavaScript or in model prompts.

Records and approval history are now in PostgreSQL, managed with a separate-role
local administration CLI. Next add an authenticated admin interface and publish
approved versions to the retrieval index. A package ID such as
`belle-arch` should link to the Belle of Balloons organization, not create a new
business per package. Keep published prices as dated evidence; parent-entered
quotes belong to the event and must not overwrite global directory rates.

## Agent and RAG behavior

The model interprets preferences and explains tradeoffs. Server code filters
approved IDs, location, published capacity including all adults/children, service
scope and known budget constraints. Unknown fees prevent all-in budget claims.
RAG retrieves only approved vendor facts plus current-event quotes/documents with
owner/version isolation. Every returned option resolves to a real approved ID.
Retrieved prose cannot approve a vendor, send mail, accept a quote or mark a
reservation secured. Catalog metadata and availability remain separate.

The RAG index is a derived view, not the approval authority. Suspending a vendor
must block new recommendations and outgoing inquiries even if an old chunk or
cached recommendation remains. Existing inquiries/reservations need an attention
item; suspension must not silently cancel anything.

## Contact and outreach workflow

1. Parent shortlists a venue; agent prepares questions from missing current-event facts.
2. Resolve the configured contact and its verification status. With no verified
   email, offer Call/official contact page and hold Gmail sending.
3. Group facilities under the same organization/contact so selecting the three
   civic centers does not blindly produce three duplicate coordinator emails.
   The parent reviews an explicit combined inquiry or individual inquiries.
4. Parent approves exact recipients, body and attachments. Sending uses the
   connected parent's Gmail only after separate Gmail consent.
5. Record provider replies as evidence for availability, fees and restrictions;
   a quote or acknowledgement does not prove a secured reservation.
6. Follow-ups obey the existing revocable grants: after 24 hours, once daily,
   maximum three per inquiry, stopping on reply/cancel/revocation.

## Operating the directory

Agents may prepare proposed additions/changes. A human approves publication.
Keep a revision log and source evidence; never silently replace a verified email
or pricing field. A periodic freshness review should queue stale contact/rate
records for review. Do not let the model assign fresh verification timestamps.
Availability is always event-specific. Missing evidence remains unknown.

For the November 2 demo, prove this path using the actual existing three venues
and two decorators. Food remains an empty-state until real approvals exist.
Gmail requires a verified recipient and actual Google OAuth setup. No booking,
contract acceptance, purchase or payment is executed.

## Implemented now versus next

Implemented: sourced venue contacts, versioned PostgreSQL directory and approval
history, separate-role local administration CLI, session-protected read endpoint,
React directory with Call/official links and stored approval/version details,
explicit missing-email/food states, and legacy venue details.

Next: authenticated admin publishing UI, verified email onboarding, account saving
and approved Gmail outreach. Normal planning now uses catalog retrieval; legacy
live web routes remain present but are disabled by default behind operator opt-in.
