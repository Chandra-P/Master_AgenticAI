CREATE TABLE knowledge_chunks (
 id text PRIMARY KEY,
 event_id uuid REFERENCES events(id),
 brief_version integer,
 kind text NOT NULL CHECK(kind IN ('planning','event_evidence')),
 title text NOT NULL,
 content text NOT NULL,
 source_id text NOT NULL,
 source_kind text NOT NULL,
 retrieved_at timestamptz NOT NULL DEFAULT now(),
 search tsvector GENERATED ALWAYS AS
  (to_tsvector('english',title||' '||content)) STORED,
 CHECK ((kind='planning' AND event_id IS NULL AND brief_version IS NULL) OR
        (kind='event_evidence' AND event_id IS NOT NULL AND brief_version IS NOT NULL))
);
CREATE INDEX knowledge_search ON knowledge_chunks USING gin(search);
INSERT INTO knowledge_chunks(id,kind,title,content,source_id,source_kind) VALUES
 ('planning-budget','planning','Budget, costs, prices and fees',
 'CONVENE compares sourced published costs and provider quotes for the selected services. Published base prices and minimums are not all-in quotes. Missing delivery, setup, security, tax and other required fees stay unknown. A typical spending range needs enough comparable local published rates; do not invent past-event spending. If the budget conflicts with the guest count or scope, explain the tradeoff and ask the parent which priority to protect before changing the plan.',
 'convene:approved-planner-design#budget','product_guidance'),
 ('planning-guests','planning','Guest count, children, parents and capacity',
 'Count every child and accompanying adult in total attendance. Venue capacity and seating layout must support the full guest count. Do not quietly drop accompanying parents or reduce the guest list to make an option fit. Ask the parent when a headcount is ambiguous. Capacity, age restrictions and outside-food rules require provider evidence.',
 'convene:approved-planner-design#guests','product_guidance'),
 ('planning-scope','planning','Venues, professional decorations and food planning',
 'CONVENE helps parents plan birthdays and other celebrations in San Antonio, Texas. Choose venues, professional decoration, restaurant party trays, any combination, or all three. Collect requirements one question at a time, allow unsure or tentative answers, and show a brief for parent confirmation before personalized research. Google sign-in saves the event before research; Gmail connection is separate.',
 'convene:approved-planner-design#scope','product_guidance'),
 ('planning-booking','planning','Availability, booking, payments and confirmation',
 'A suggestion, quote or automated acknowledgement does not prove a reservation is secured. Availability needs provider confirmation for the correct date, time, service and securing conditions. Booking, payment, contract and readiness are separate states. Payment pending differs from unknown. CONVENE does not make bookings, accept contracts or take payments. Parents approve exact initial provider emails before sending. Do not claim an inquiry was sent or a venue booked without recorded evidence.',
 'convene:approved-planner-design#confirmation','product_guidance'),
 ('planning-food','planning','Restaurant party trays, dietary needs and delivery',
 'For restaurant party trays, collect allergies, dietary preferences and pickup or delivery preference. Compare published serving quantities and the total order needed. Do not assume a child eats a fixed fraction of an adult serving. Outside-food permission, delivery area, delivery timing and required fees need provider confirmation.',
 'convene:approved-planner-design#food','product_guidance');
ALTER TABLE knowledge_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_chunks FORCE ROW LEVEL SECURITY;
CREATE POLICY knowledge_read ON knowledge_chunks FOR SELECT USING
 (kind='planning' OR EXISTS(SELECT 1 FROM events e WHERE e.id=knowledge_chunks.event_id));
CREATE POLICY knowledge_insert ON knowledge_chunks FOR INSERT WITH CHECK
 (kind='event_evidence' AND EXISTS(SELECT 1 FROM events e WHERE e.id=knowledge_chunks.event_id));
