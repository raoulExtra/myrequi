-- Optional lineage from an executed route receipt to an explicitly resolved clarification.
ALTER TABLE route_execution_receipts ADD COLUMN clarification_id INTEGER;
ALTER TABLE route_execution_receipts ADD COLUMN interpretation_hash TEXT;
CREATE INDEX IF NOT EXISTS idx_route_receipts_clarification ON route_execution_receipts(clarification_id);
