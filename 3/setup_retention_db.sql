-- Data Retention Policy Database Setup
-- Run this script in your Supabase SQL editor to create the retention tables

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Retention Policies Table
CREATE TABLE IF NOT EXISTS retention_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    data_category VARCHAR(50) NOT NULL CHECK (data_category IN (
        'user_profiles', 'messages', 'analytics', 'feedback', 'matches', 'conversations', 'preferences'
    )),
    retention_period_days INTEGER NOT NULL CHECK (retention_period_days > 0),
    archive_after_days INTEGER CHECK (archive_after_days IS NULL OR archive_after_days > 0),
    action VARCHAR(20) NOT NULL DEFAULT 'delete' CHECK (action IN ('archive', 'delete', 'retain')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Legal Holds Table
CREATE TABLE IF NOT EXISTS legal_holds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_name VARCHAR(255) NOT NULL,
    description TEXT,
    data_categories TEXT[] NOT NULL,
    user_ids UUID[],
    keywords TEXT[],
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'pending', 'released', 'expired')),
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    released_at TIMESTAMP WITH TIME ZONE
);

-- Retention Events Table (audit log)
CREATE TABLE IF NOT EXISTS retention_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID REFERENCES retention_policies(id) ON DELETE SET NULL,
    table_name VARCHAR(100) NOT NULL,
    record_id VARCHAR(255) NOT NULL,
    action_taken VARCHAR(20) NOT NULL CHECK (action_taken IN ('archive', 'delete', 'retain')),
    records_affected INTEGER DEFAULT 1,
    reason TEXT,
    legal_hold_applied BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Archived Data Table
CREATE TABLE IF NOT EXISTS archived_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_table VARCHAR(100) NOT NULL,
    original_id VARCHAR(255) NOT NULL,
    data_content JSONB NOT NULL,
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    policy_id UUID REFERENCES retention_policies(id) ON DELETE SET NULL,
    restore_before TIMESTAMP WITH TIME ZONE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_retention_policies_active ON retention_policies(is_active);
CREATE INDEX IF NOT EXISTS idx_retention_policies_category ON retention_policies(data_category);
CREATE INDEX IF NOT EXISTS idx_legal_holds_status ON legal_holds(status);
CREATE INDEX IF NOT EXISTS idx_legal_holds_expires ON legal_holds(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_retention_events_policy ON retention_events(policy_id);
CREATE INDEX IF NOT EXISTS idx_retention_events_table ON retention_events(table_name);
CREATE INDEX IF NOT EXISTS idx_retention_events_created ON retention_events(created_at);
CREATE INDEX IF NOT EXISTS idx_archived_data_table ON archived_data(original_table);
CREATE INDEX IF NOT EXISTS idx_archived_data_original ON archived_data(original_id);
CREATE INDEX IF NOT EXISTS idx_archived_data_restore ON archived_data(restore_before);

-- Row Level Security (RLS) Policies
-- Enable RLS on all retention tables
ALTER TABLE retention_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE legal_holds ENABLE ROW LEVEL SECURITY;
ALTER TABLE retention_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE archived_data ENABLE ROW LEVEL SECURITY;

-- Create policies to allow service role full access
-- Replace 'service_role' with your actual service role if different
CREATE POLICY "Service role can manage retention policies" ON retention_policies
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage legal holds" ON legal_holds
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage retention events" ON retention_events
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage archived data" ON archived_data
    FOR ALL USING (auth.role() = 'service_role');

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_retention_policies_updated_at
    BEFORE UPDATE ON retention_policies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Create function to validate retention policy constraints
CREATE OR REPLACE FUNCTION validate_retention_policy()
RETURNS TRIGGER AS $$
BEGIN
    -- Ensure archive_after_days is less than retention_period_days
    IF NEW.archive_after_days IS NOT NULL AND NEW.archive_after_days >= NEW.retention_period_days THEN
        RAISE EXCEPTION 'archive_after_days must be less than retention_period_days';
    END IF;
    
    -- Ensure archive action has archive_after_days set
    IF NEW.action = 'archive' AND NEW.archive_after_days IS NULL THEN
        RAISE EXCEPTION 'archive_after_days must be set when action is archive';
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to validate retention policy
CREATE TRIGGER validate_retention_policy_trigger
    BEFORE INSERT OR UPDATE ON retention_policies
    FOR EACH ROW
    EXECUTE FUNCTION validate_retention_policy();

-- Insert default retention policies
INSERT INTO retention_policies (name, description, data_category, retention_period_days, action, is_active) 
VALUES 
    ('Analytics Data Retention', 'Automatically delete analytics events older than 2 years', 'analytics', 730, 'delete', true),
    ('Old Match Data Cleanup', 'Delete volunteer match data older than 1 year', 'matches', 365, 'delete', true)
ON CONFLICT DO NOTHING;

INSERT INTO retention_policies (name, description, data_category, retention_period_days, archive_after_days, action, is_active)
VALUES 
    ('Message Archive Policy', 'Archive conversation messages older than 1 year, delete after 3 years', 'messages', 1095, 365, 'archive', true),
    ('Feedback Retention Policy', 'Archive feedback older than 6 months, delete after 2 years', 'feedback', 730, 180, 'archive', true),
    ('Inactive User Cleanup', 'Archive user profiles inactive for 3 years, delete after 7 years', 'user_profiles', 2555, 1095, 'archive', true)
ON CONFLICT DO NOTHING;

-- Create a view for retention policy summary
CREATE OR REPLACE VIEW retention_policy_summary AS
SELECT 
    rp.id,
    rp.name,
    rp.data_category,
    rp.retention_period_days,
    rp.action,
    rp.is_active,
    COUNT(re.id) as executions_count,
    MAX(re.created_at) as last_execution,
    SUM(re.records_affected) as total_records_affected
FROM retention_policies rp
LEFT JOIN retention_events re ON rp.id = re.policy_id
GROUP BY rp.id, rp.name, rp.data_category, rp.retention_period_days, rp.action, rp.is_active;

-- Create a view for legal hold summary
CREATE OR REPLACE VIEW legal_hold_summary AS
SELECT 
    lh.id,
    lh.case_name,
    lh.status,
    lh.data_categories,
    CASE 
        WHEN lh.user_ids IS NOT NULL THEN array_length(lh.user_ids, 1)
        ELSE NULL
    END as affected_users_count,
    lh.created_at,
    lh.expires_at,
    CASE 
        WHEN lh.expires_at IS NOT NULL AND lh.expires_at < NOW() THEN 'Expired'
        WHEN lh.status = 'active' THEN 'Active'
        ELSE INITCAP(lh.status)
    END as current_status
FROM legal_holds lh;

-- Grant necessary permissions
GRANT ALL ON retention_policies TO service_role;
GRANT ALL ON legal_holds TO service_role;
GRANT ALL ON retention_events TO service_role;
GRANT ALL ON archived_data TO service_role;
GRANT SELECT ON retention_policy_summary TO service_role;
GRANT SELECT ON legal_hold_summary TO service_role;

-- Create notification function for policy executions
CREATE OR REPLACE FUNCTION notify_retention_execution()
RETURNS TRIGGER AS $$
BEGIN
    -- You can customize this to send notifications via webhook, email, etc.
    -- For now, just log to the database log
    RAISE NOTICE 'Retention policy executed: % records affected for policy %', 
        NEW.records_affected, NEW.policy_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for retention execution notifications
CREATE TRIGGER notify_retention_execution_trigger
    AFTER INSERT ON retention_events
    FOR EACH ROW
    EXECUTE FUNCTION notify_retention_execution();

COMMENT ON TABLE retention_policies IS 'Data retention policies defining how long different types of data should be kept';
COMMENT ON TABLE legal_holds IS 'Legal holds that prevent data deletion for litigation or compliance purposes';
COMMENT ON TABLE retention_events IS 'Audit log of all retention policy executions and their results';
COMMENT ON TABLE archived_data IS 'Archived data that has been moved from production tables but not yet deleted';

-- Sample queries for monitoring

-- Check policy execution history
-- SELECT * FROM retention_policy_summary ORDER BY last_execution DESC;

-- Check active legal holds
-- SELECT * FROM legal_hold_summary WHERE current_status = 'Active';

-- View recent retention activities
-- SELECT * FROM retention_events ORDER BY created_at DESC LIMIT 50;

-- Check data ready for archival/deletion (example for messages table)
-- SELECT COUNT(*) FROM messages WHERE created_at < (NOW() - INTERVAL '365 days');

COMMIT;