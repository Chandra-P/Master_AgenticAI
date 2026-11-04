ALTER TABLE knowledge_chunks ADD COLUMN vendor_id text;
ALTER TABLE knowledge_chunks ADD COLUMN vendor_version integer;
ALTER TABLE knowledge_chunks ADD COLUMN approval_id uuid;
