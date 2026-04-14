-- Audit log table for tracking data modifications
CREATE TABLE IF NOT EXISTS iainmobiliaria_audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    record_id BIGINT,
    action VARCHAR(10) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_data JSONB,
    new_data JSONB,
    changed_by TEXT DEFAULT current_setting('request.jwt.claims', true)::json->>'sub',
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    ip_address TEXT,
    request_id TEXT
);

-- Index for querying by table and time
CREATE INDEX IF NOT EXISTS idx_audit_log_table_time ON iainmobiliaria_audit_log(table_name, changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON iainmobiliaria_audit_log(action);

-- Enable RLS
ALTER TABLE iainmobiliaria_audit_log ENABLE ROW LEVEL SECURITY;

-- Only service_role can insert/read audit logs
CREATE POLICY "Service role full access to audit log"
ON iainmobiliaria_audit_log
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Anon can only read (for transparency)
CREATE POLICY "Public read access to audit log"
ON iainmobiliaria_audit_log
FOR SELECT
TO anon, authenticated
USING (true);

-- Audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO iainmobiliaria_audit_log (table_name, record_id, action, new_data)
        VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO iainmobiliaria_audit_log (table_name, record_id, action, old_data, new_data)
        VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO iainmobiliaria_audit_log (table_name, record_id, action, old_data)
        VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', to_jsonb(OLD));
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers to main tables
CREATE TRIGGER audit_comparables
    AFTER INSERT OR UPDATE OR DELETE ON iainmobiliaria_comparables
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER audit_predictions
    AFTER INSERT OR UPDATE OR DELETE ON iainmobiliaria_predictions
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER audit_amenities
    AFTER INSERT OR UPDATE OR DELETE ON iainmobiliaria_amenities
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER audit_grid_tiles
    AFTER INSERT OR UPDATE OR DELETE ON iainmobiliaria_grid_tiles
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
