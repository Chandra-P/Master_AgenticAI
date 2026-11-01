CREATE TABLE browser_sessions (
    token_hash text PRIMARY KEY,
    actor_id uuid NOT NULL,
    authenticated boolean NOT NULL DEFAULT false,
    csrf_token text NOT NULL,
    expires_at timestamptz NOT NULL,
    revoked_at timestamptz
);
ALTER TABLE browser_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE browser_sessions FORCE ROW LEVEL SECURITY;
CREATE POLICY browser_session_secret ON browser_sessions USING
    (token_hash=current_setting('convene.session_hash',true));
