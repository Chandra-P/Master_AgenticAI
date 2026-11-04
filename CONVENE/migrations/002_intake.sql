CREATE TABLE intake_turns (
    event_id uuid NOT NULL REFERENCES events(id),
    sequence integer NOT NULL,
    role text NOT NULL CHECK (role IN ('user','assistant')),
    body text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY(event_id,sequence)
);
CREATE TABLE intake_receipts (
    event_id uuid NOT NULL REFERENCES events(id),
    request_id uuid NOT NULL,
    response jsonb NOT NULL,
    PRIMARY KEY(event_id,request_id)
);
ALTER TABLE intake_turns ENABLE ROW LEVEL SECURITY;
ALTER TABLE intake_turns FORCE ROW LEVEL SECURITY;
CREATE POLICY intake_turn_owner ON intake_turns USING
    (EXISTS (SELECT 1 FROM events WHERE events.id=intake_turns.event_id));
ALTER TABLE intake_receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE intake_receipts FORCE ROW LEVEL SECURITY;
CREATE POLICY intake_receipt_owner ON intake_receipts USING
    (EXISTS (SELECT 1 FROM events WHERE events.id=intake_receipts.event_id));
