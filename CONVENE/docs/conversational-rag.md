# Conversational RAG milestone

The confirmed-brief chat now also retrieves current approved PostgreSQL vendor
facts, with live approval/version checks. [Approved catalog planner](approved-catalog-planner.md)
describes recommendations, freshness guards, shortlist and inquiry previews.

The local React planner now retrieves PostgreSQL knowledge before its model turn.
The model sees the current message, saved brief, safe recent conversation, next
question and retrieved passages. It classifies social/help/event-answer intent,
interprets informal language, and proposes typed event facts with per-field quotes
from the current message. Server validation owns the brief and action gates.

## Knowledge and retrieval

`migrations/005_knowledge.sql` seeds five **CONVENE product/planning guidance**
passages from the approved design: scope, budgeting, all guests, food and booking
confirmation. These are not provider facts, published local rates or historical
event budgets. They are labeled as planning guidance in the model context and UI.

`EvidenceIndex.retrieve` uses PostgreSQL full-text search with a GIN index,
English stemming, ranked OR terms and a bounded result/context size. Recent user
messages supply context for follow-up questions. This is retrieval-augmented
generation using lexical retrieval; embedding/vector search is not implemented.

`EvidenceIndex.add` can index validated EvidenceFact excerpts for an owned event,
current confirmed version and authenticated principal. This is an internal
interface, not an open upload route. New chat integration with live web discovery,
provider extraction and uploads remains pending; no provider corpus is silently
invented or populated with synthetic venue quotes.

## Grounding and privacy

The model selects short exact source excerpts into `grounded_quotes`. The server
only displays them when each quote is a substring of its retrieved passage and
all referenced IDs match. It adds the next intake question itself. Arbitrary model
reply text is not displayed as verified factual help; even a valid but unrelated
source ID cannot support an invented price or reservation claim. Extractive
answers are deliberately conservative; fluent paraphrase verification is future
work. Quoted provider pages remain claims by that source, not a booking transition.

PostgreSQL FORCE RLS isolates private chunks by owner. Retrieval additionally
requires the correct event/current version and an authenticated, confirmed brief
before supplying provider evidence. Stale private assistant messages are omitted
from model history; source objects are not forwarded through history. A correction
turn discards previous-version provider citations from the outgoing reply.

Each new fact needs current-message evidence; echoed unchanged brief facts are
ignored. A redundant total derived from unchanged children/family is ignored,
but changed headcounts still validate their total. Social/help turns preserve
brief version and confirmation. Conversation turns and their cited source snapshots
persist; reopening the event restores the source details.

The React chat exposes **Knowledge used** beneath sourced answers. Expand it to
see the passage, source title and planning-guide/provider-evidence distinction.
RAG does not grant permission to research, send email, book, or pay.

## Setup and demo

Run `scripts/init_planner_db.py` explicitly after installing requirements to apply
knowledge/source migrations. Rebuild the frontend. The local preview remains
http://127.0.0.1:8001; restart the server after Python changes and refresh the browser.

Try an event description with age and both child/adult counts, then a question
such as “What if my budget does not fit everyone?” The response should retrieve
planning guidance and show its source without changing any event facts.

Google account saving, live provider ingestion, uploaded-document retrieval and
the complete Gmail/public-hosting path remain separate unfinished milestones.
