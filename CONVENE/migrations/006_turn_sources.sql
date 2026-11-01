ALTER TABLE intake_turns ADD COLUMN sources jsonb NOT NULL DEFAULT '[]'::jsonb;
