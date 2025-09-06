-- A/B Test Framework Database Schema
-- Add these tables to the existing Supabase database

-- A/B Tests configuration table
CREATE TABLE IF NOT EXISTS ab_tests (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    test_type VARCHAR(20) NOT NULL CHECK (test_type IN ('message', 'schedule', 'hybrid')),
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'paused', 'completed', 'archived')),
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    sample_size INTEGER NOT NULL DEFAULT 1000,
    confidence_level DECIMAL(3,2) DEFAULT 0.95,
    primary_metric VARCHAR(50) NOT NULL,
    secondary_metrics JSONB DEFAULT '[]',
    message_variants JSONB DEFAULT '[]',
    schedule_variants JSONB DEFAULT '[]',
    target_audience_filters JSONB DEFAULT '{}',
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Participant assignments for A/B tests
CREATE TABLE IF NOT EXISTS ab_test_participants (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    test_id UUID REFERENCES ab_tests(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    variant_id VARCHAR(255) NOT NULL,
    variant_type VARCHAR(20) NOT NULL CHECK (variant_type IN ('message', 'schedule', 'hybrid')),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    UNIQUE(test_id, user_id)
);

-- Events tracking for A/B tests
CREATE TABLE IF NOT EXISTS ab_test_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    test_id UUID REFERENCES ab_tests(id) ON DELETE CASCADE,
    user_id UUID,
    variant_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Test results storage
CREATE TABLE IF NOT EXISTS ab_test_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    test_id UUID REFERENCES ab_tests(id) ON DELETE CASCADE,
    variant_id VARCHAR(255) NOT NULL,
    variant_name VARCHAR(255),
    sample_size INTEGER NOT NULL,
    primary_metric_value DECIMAL(5,4),
    secondary_metrics JSONB DEFAULT '{}',
    confidence_interval_lower DECIMAL(5,4),
    confidence_interval_upper DECIMAL(5,4),
    p_value DECIMAL(10,8),
    is_statistically_significant BOOLEAN DEFAULT FALSE,
    lift_percentage DECIMAL(5,2),
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Campaign message templates
CREATE TABLE IF NOT EXISTS campaign_message_templates (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    subject_line VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    call_to_action VARCHAR(255),
    tone VARCHAR(50),
    personalization_level VARCHAR(20) CHECK (personalization_level IN ('none', 'basic', 'advanced')),
    message_length VARCHAR(20) CHECK (message_length IN ('short', 'medium', 'long')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Campaign schedules
CREATE TABLE IF NOT EXISTS campaign_schedules (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    send_time TIME NOT NULL,
    send_days JSONB NOT NULL, -- Array of day names
    frequency VARCHAR(20) CHECK (frequency IN ('once', 'daily', 'weekly', 'bi-weekly', 'monthly')),
    reminder_schedule JSONB DEFAULT '[]', -- Array of days before event
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Campaign executions tracking
CREATE TABLE IF NOT EXISTS campaign_executions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    test_id UUID REFERENCES ab_tests(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    message_template_id UUID REFERENCES campaign_message_templates(id),
    schedule_id UUID REFERENCES campaign_schedules(id),
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    delivery_status VARCHAR(20) DEFAULT 'sent' CHECK (delivery_status IN ('sent', 'delivered', 'opened', 'clicked', 'bounced', 'failed')),
    metadata JSONB DEFAULT '{}'
);

-- Volunteer turnout tracking
CREATE TABLE IF NOT EXISTS volunteer_turnout_tracking (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    test_id UUID REFERENCES ab_tests(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    event_id VARCHAR(255),
    event_name VARCHAR(255),
    event_date TIMESTAMP WITH TIME ZONE,
    registration_date TIMESTAMP WITH TIME ZONE,
    attended BOOLEAN DEFAULT FALSE,
    attendance_confirmed_at TIMESTAMP WITH TIME ZONE,
    hours_contributed DECIMAL(4,2) DEFAULT 0,
    feedback_rating INTEGER CHECK (feedback_rating >= 1 AND feedback_rating <= 5),
    metadata JSONB DEFAULT '{}'
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ab_tests_status ON ab_tests(status);
CREATE INDEX IF NOT EXISTS idx_ab_tests_dates ON ab_tests(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_ab_test_participants_test_user ON ab_test_participants(test_id, user_id);
CREATE INDEX IF NOT EXISTS idx_ab_test_events_test_timestamp ON ab_test_events(test_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_ab_test_events_user_type ON ab_test_events(user_id, event_type);
CREATE INDEX IF NOT EXISTS idx_campaign_executions_test_user ON campaign_executions(test_id, user_id);
CREATE INDEX IF NOT EXISTS idx_volunteer_turnout_test_attended ON volunteer_turnout_tracking(test_id, attended);

-- Views for easier reporting
CREATE OR REPLACE VIEW ab_test_summary AS
SELECT 
    t.id as test_id,
    t.name as test_name,
    t.status,
    t.start_date,
    t.end_date,
    COUNT(DISTINCT p.user_id) as total_participants,
    COUNT(DISTINCT CASE WHEN e.event_type = 'message_sent' THEN e.user_id END) as messages_sent,
    COUNT(DISTINCT CASE WHEN e.event_type = 'message_opened' THEN e.user_id END) as messages_opened,
    COUNT(DISTINCT CASE WHEN e.event_type = 'clicked' THEN e.user_id END) as clicks,
    COUNT(DISTINCT CASE WHEN e.event_type = 'registered' THEN e.user_id END) as registrations,
    COUNT(DISTINCT CASE WHEN e.event_type = 'attended' THEN e.user_id END) as attendees
FROM ab_tests t
LEFT JOIN ab_test_participants p ON t.id = p.test_id
LEFT JOIN ab_test_events e ON t.id = e.test_id
GROUP BY t.id, t.name, t.status, t.start_date, t.end_date;

CREATE OR REPLACE VIEW variant_performance AS
SELECT 
    t.id as test_id,
    t.name as test_name,
    p.variant_id,
    COUNT(DISTINCT p.user_id) as participants,
    COUNT(DISTINCT CASE WHEN e.event_type = 'message_sent' THEN e.user_id END) as messages_sent,
    COUNT(DISTINCT CASE WHEN e.event_type = 'message_opened' THEN e.user_id END) as messages_opened,
    COUNT(DISTINCT CASE WHEN e.event_type = 'clicked' THEN e.user_id END) as clicks,
    COUNT(DISTINCT CASE WHEN e.event_type = 'registered' THEN e.user_id END) as registrations,
    COUNT(DISTINCT CASE WHEN e.event_type = 'attended' THEN e.user_id END) as attendees,
    CASE 
        WHEN COUNT(DISTINCT p.user_id) > 0 THEN 
            ROUND(COUNT(DISTINCT CASE WHEN e.event_type = 'attended' THEN e.user_id END)::DECIMAL / COUNT(DISTINCT p.user_id) * 100, 2)
        ELSE 0 
    END as turnout_rate_percent,
    CASE 
        WHEN COUNT(DISTINCT CASE WHEN e.event_type = 'message_sent' THEN e.user_id END) > 0 THEN 
            ROUND(COUNT(DISTINCT CASE WHEN e.event_type = 'message_opened' THEN e.user_id END)::DECIMAL / COUNT(DISTINCT CASE WHEN e.event_type = 'message_sent' THEN e.user_id END) * 100, 2)
        ELSE 0 
    END as open_rate_percent
FROM ab_tests t
LEFT JOIN ab_test_participants p ON t.id = p.test_id
LEFT JOIN ab_test_events e ON t.id = e.test_id AND p.user_id = e.user_id
GROUP BY t.id, t.name, p.variant_id;

-- Row Level Security policies (optional, adjust based on your auth setup)
ALTER TABLE ab_tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab_test_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab_test_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab_test_results ENABLE ROW LEVEL SECURITY;

-- Example policies (adjust based on your authentication setup)
-- CREATE POLICY "Users can view their own test participation" ON ab_test_participants FOR SELECT USING (auth.uid()::text = user_id::text);
-- CREATE POLICY "Admin users can manage all tests" ON ab_tests FOR ALL USING (auth.jwt() ->> 'role' = 'admin');

-- Functions for common operations
CREATE OR REPLACE FUNCTION get_user_test_assignments(p_user_id UUID)
RETURNS TABLE(test_id UUID, test_name VARCHAR, variant_id VARCHAR, assigned_at TIMESTAMP WITH TIME ZONE)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.test_id,
        t.name as test_name,
        p.variant_id,
        p.assigned_at
    FROM ab_test_participants p
    JOIN ab_tests t ON p.test_id = t.id
    WHERE p.user_id = p_user_id
    AND t.status = 'active'
    ORDER BY p.assigned_at DESC;
END;
$$;

CREATE OR REPLACE FUNCTION calculate_test_metrics(p_test_id UUID, p_variant_id VARCHAR)
RETURNS TABLE(
    turnout_rate DECIMAL,
    engagement_rate DECIMAL,
    conversion_rate DECIMAL,
    retention_rate DECIMAL
)
LANGUAGE plpgsql
AS $$
DECLARE
    total_participants INTEGER;
    attended_count INTEGER;
    engaged_count INTEGER;
    converted_count INTEGER;
    retained_count INTEGER;
BEGIN
    -- Get total participants for this variant
    SELECT COUNT(DISTINCT user_id) INTO total_participants
    FROM ab_test_participants
    WHERE test_id = p_test_id AND variant_id = p_variant_id;
    
    IF total_participants = 0 THEN
        RETURN QUERY SELECT 0::DECIMAL, 0::DECIMAL, 0::DECIMAL, 0::DECIMAL;
        RETURN;
    END IF;
    
    -- Calculate attended count
    SELECT COUNT(DISTINCT user_id) INTO attended_count
    FROM ab_test_events
    WHERE test_id = p_test_id AND variant_id = p_variant_id AND event_type = 'attended';
    
    -- Calculate engaged count (opened or clicked)
    SELECT COUNT(DISTINCT user_id) INTO engaged_count
    FROM ab_test_events
    WHERE test_id = p_test_id AND variant_id = p_variant_id 
    AND event_type IN ('message_opened', 'clicked');
    
    -- Calculate converted count (registered)
    SELECT COUNT(DISTINCT user_id) INTO converted_count
    FROM ab_test_events
    WHERE test_id = p_test_id AND variant_id = p_variant_id AND event_type = 'registered';
    
    -- Calculate retained count (attended multiple times)
    SELECT COUNT(*) INTO retained_count
    FROM (
        SELECT user_id, COUNT(*) as attendance_count
        FROM ab_test_events
        WHERE test_id = p_test_id AND variant_id = p_variant_id AND event_type = 'attended'
        GROUP BY user_id
        HAVING COUNT(*) > 1
    ) retained_users;
    
    RETURN QUERY SELECT 
        ROUND(attended_count::DECIMAL / total_participants, 4) as turnout_rate,
        ROUND(engaged_count::DECIMAL / total_participants, 4) as engagement_rate,
        ROUND(converted_count::DECIMAL / total_participants, 4) as conversion_rate,
        ROUND(retained_count::DECIMAL / total_participants, 4) as retention_rate;
END;
$$;