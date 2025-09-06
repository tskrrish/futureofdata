-- Background Check Tracking Migration
-- Add background check tables to existing Supabase schema

-- Background checks table
CREATE TABLE IF NOT EXISTS public.background_checks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    volunteer_contact_id INTEGER, -- Reference to volunteer system contact ID
    check_type VARCHAR(50) NOT NULL, -- 'background', 'reference', 'child_protection'
    check_provider VARCHAR(100), -- 'Sterling', 'Checkr', 'Manual', etc.
    submission_date TIMESTAMP WITH TIME ZONE NOT NULL,
    completion_date TIMESTAMP WITH TIME ZONE,
    expiration_date TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'in_progress', 'completed', 'failed', 'expired', 'renewal_required')
    ),
    result VARCHAR(20) CHECK (
        result IN ('clear', 'conditional', 'disqualified', 'pending_review')
    ),
    notes TEXT,
    documents JSONB DEFAULT '[]', -- Array of document references/URLs
    alert_sent BOOLEAN DEFAULT FALSE,
    renewal_alert_date TIMESTAMP WITH TIME ZONE, -- Date when first renewal alert was sent
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Background check requirements table (defines what checks are needed for different volunteer types)
CREATE TABLE IF NOT EXISTS public.background_check_requirements (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    volunteer_type VARCHAR(100) NOT NULL, -- 'youth_mentor', 'coach', 'general', etc.
    check_type VARCHAR(50) NOT NULL,
    required BOOLEAN NOT NULL DEFAULT TRUE,
    validity_months INTEGER NOT NULL DEFAULT 24, -- How long the check is valid
    advance_warning_days INTEGER NOT NULL DEFAULT 30, -- Days before expiration to send warning
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(volunteer_type, check_type)
);

-- Background check alerts table
CREATE TABLE IF NOT EXISTS public.background_check_alerts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    background_check_id UUID REFERENCES public.background_checks(id) ON DELETE CASCADE,
    alert_type VARCHAR(30) NOT NULL CHECK (
        alert_type IN ('expiring_soon', 'expired', 'renewal_required', 'failed_check')
    ),
    alert_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    sent_to_volunteer BOOLEAN DEFAULT FALSE,
    sent_to_admin BOOLEAN DEFAULT FALSE,
    volunteer_email_date TIMESTAMP WITH TIME ZONE,
    admin_email_date TIMESTAMP WITH TIME ZONE,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_date TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Re-check workflow tracking table
CREATE TABLE IF NOT EXISTS public.recheck_workflows (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    original_check_id UUID REFERENCES public.background_checks(id) ON DELETE CASCADE,
    new_check_id UUID REFERENCES public.background_checks(id),
    workflow_status VARCHAR(30) NOT NULL DEFAULT 'initiated' CHECK (
        workflow_status IN ('initiated', 'volunteer_notified', 'in_progress', 'completed', 'abandoned')
    ),
    initiated_by VARCHAR(20) NOT NULL CHECK (
        initiated_by IN ('system_automatic', 'admin_manual', 'volunteer_request')
    ),
    due_date TIMESTAMP WITH TIME ZONE,
    completion_deadline TIMESTAMP WITH TIME ZONE,
    reminder_count INTEGER DEFAULT 0,
    last_reminder_date TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_background_checks_user_id ON public.background_checks(user_id);
CREATE INDEX IF NOT EXISTS idx_background_checks_status ON public.background_checks(status);
CREATE INDEX IF NOT EXISTS idx_background_checks_expiration_date ON public.background_checks(expiration_date);
CREATE INDEX IF NOT EXISTS idx_background_checks_check_type ON public.background_checks(check_type);
CREATE INDEX IF NOT EXISTS idx_background_checks_volunteer_contact_id ON public.background_checks(volunteer_contact_id);

CREATE INDEX IF NOT EXISTS idx_background_check_requirements_volunteer_type ON public.background_check_requirements(volunteer_type);
CREATE INDEX IF NOT EXISTS idx_background_check_requirements_check_type ON public.background_check_requirements(check_type);

CREATE INDEX IF NOT EXISTS idx_background_check_alerts_background_check_id ON public.background_check_alerts(background_check_id);
CREATE INDEX IF NOT EXISTS idx_background_check_alerts_alert_type ON public.background_check_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_background_check_alerts_alert_date ON public.background_check_alerts(alert_date);
CREATE INDEX IF NOT EXISTS idx_background_check_alerts_resolved ON public.background_check_alerts(resolved);

CREATE INDEX IF NOT EXISTS idx_recheck_workflows_user_id ON public.recheck_workflows(user_id);
CREATE INDEX IF NOT EXISTS idx_recheck_workflows_workflow_status ON public.recheck_workflows(workflow_status);
CREATE INDEX IF NOT EXISTS idx_recheck_workflows_due_date ON public.recheck_workflows(due_date);

-- Enable Row Level Security
ALTER TABLE public.background_checks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.background_check_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.background_check_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recheck_workflows ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own background checks" ON public.background_checks
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can view background check requirements" ON public.background_check_requirements
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Users can view own background check alerts" ON public.background_check_alerts
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.background_checks bc 
            WHERE bc.id = background_check_id AND bc.user_id::text = auth.uid()::text
        )
    );

CREATE POLICY "Users can view own recheck workflows" ON public.recheck_workflows
    FOR SELECT USING (auth.uid()::text = user_id::text);

-- Update triggers
CREATE TRIGGER update_background_checks_updated_at BEFORE UPDATE ON public.background_checks
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_background_check_requirements_updated_at BEFORE UPDATE ON public.background_check_requirements
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_recheck_workflows_updated_at BEFORE UPDATE ON public.recheck_workflows
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Insert default requirements
INSERT INTO public.background_check_requirements (volunteer_type, check_type, validity_months, advance_warning_days, description) VALUES
('youth_mentor', 'background', 24, 30, 'Criminal background check for youth-facing volunteers'),
('youth_mentor', 'reference', 24, 30, 'Professional/personal reference verification'),
('youth_mentor', 'child_protection', 12, 30, 'Child protection training certification'),
('coach', 'background', 24, 30, 'Criminal background check for coaching positions'),
('coach', 'reference', 24, 30, 'Coaching reference verification'),
('event_volunteer', 'background', 36, 30, 'Basic background check for event volunteers'),
('general', 'background', 36, 30, 'Standard background check for general volunteers'),
('facility_volunteer', 'background', 24, 30, 'Background check for facility access volunteers')
ON CONFLICT (volunteer_type, check_type) DO NOTHING;

-- Functions for automated alert management
CREATE OR REPLACE FUNCTION public.check_expiring_background_checks()
RETURNS void AS $$
DECLARE
    check_record RECORD;
    requirement_record RECORD;
    alert_exists BOOLEAN;
BEGIN
    -- Find background checks that are expiring soon
    FOR check_record IN 
        SELECT bc.*, u.email, u.first_name, u.last_name
        FROM public.background_checks bc
        JOIN public.users u ON bc.user_id = u.id
        WHERE bc.status = 'completed' 
        AND bc.result = 'clear'
        AND bc.expiration_date <= (NOW() + INTERVAL '30 days')
        AND bc.expiration_date > NOW()
    LOOP
        -- Check if alert already exists
        SELECT EXISTS (
            SELECT 1 FROM public.background_check_alerts 
            WHERE background_check_id = check_record.id 
            AND alert_type = 'expiring_soon'
            AND resolved = false
        ) INTO alert_exists;
        
        IF NOT alert_exists THEN
            INSERT INTO public.background_check_alerts (
                background_check_id, 
                alert_type, 
                alert_date,
                notes
            ) VALUES (
                check_record.id, 
                'expiring_soon', 
                NOW(),
                'Background check expires on ' || check_record.expiration_date::date
            );
        END IF;
    END LOOP;
    
    -- Find expired background checks
    FOR check_record IN 
        SELECT bc.*, u.email, u.first_name, u.last_name
        FROM public.background_checks bc
        JOIN public.users u ON bc.user_id = u.id
        WHERE bc.status = 'completed'
        AND bc.expiration_date < NOW()
        AND bc.status != 'expired'
    LOOP
        -- Update status to expired
        UPDATE public.background_checks 
        SET status = 'expired' 
        WHERE id = check_record.id;
        
        -- Create expired alert
        SELECT EXISTS (
            SELECT 1 FROM public.background_check_alerts 
            WHERE background_check_id = check_record.id 
            AND alert_type = 'expired'
            AND resolved = false
        ) INTO alert_exists;
        
        IF NOT alert_exists THEN
            INSERT INTO public.background_check_alerts (
                background_check_id, 
                alert_type, 
                alert_date,
                notes
            ) VALUES (
                check_record.id, 
                'expired', 
                NOW(),
                'Background check expired on ' || check_record.expiration_date::date
            );
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant necessary permissions
GRANT ALL ON public.background_checks TO authenticated, anon;
GRANT ALL ON public.background_check_requirements TO authenticated, anon;  
GRANT ALL ON public.background_check_alerts TO authenticated, anon;
GRANT ALL ON public.recheck_workflows TO authenticated, anon;

SELECT 'Background check tracking tables created successfully!' AS result;