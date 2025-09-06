-- Resource/Equipment Assignment Feature - Database Schema Extension
-- Add these tables to the existing Volunteer PathFinder database schema

-- Shifts table to define work shifts/time periods
CREATE TABLE IF NOT EXISTS public.shifts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    branch VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    max_volunteers INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'active', 'completed', 'cancelled')),
    created_by UUID REFERENCES public.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Resources/Equipment table to define items that can be assigned
CREATE TABLE IF NOT EXISTS public.resources (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    resource_type VARCHAR(50) NOT NULL, -- 'equipment', 'supplies', 'facility', 'vehicle', etc.
    branch VARCHAR(100) NOT NULL,
    serial_number VARCHAR(100),
    model VARCHAR(100),
    manufacturer VARCHAR(100),
    purchase_date DATE,
    condition VARCHAR(20) DEFAULT 'good' CHECK (condition IN ('excellent', 'good', 'fair', 'poor', 'maintenance')),
    status VARCHAR(20) DEFAULT 'available' CHECK (status IN ('available', 'assigned', 'maintenance', 'retired')),
    max_concurrent_assignments INTEGER DEFAULT 1,
    requires_training BOOLEAN DEFAULT FALSE,
    maintenance_schedule_days INTEGER DEFAULT 30, -- days between maintenance
    last_maintenance_date DATE,
    next_maintenance_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Resource assignments table linking resources to shifts
CREATE TABLE IF NOT EXISTS public.resource_assignments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    shift_id UUID REFERENCES public.shifts(id) ON DELETE CASCADE,
    resource_id UUID REFERENCES public.resources(id) ON DELETE CASCADE,
    assigned_to_user_id UUID REFERENCES public.users(id), -- volunteer assigned to use this resource
    assigned_by_user_id UUID REFERENCES public.users(id), -- staff member who made the assignment
    quantity_assigned INTEGER DEFAULT 1,
    assignment_notes TEXT,
    status VARCHAR(20) DEFAULT 'assigned' CHECK (status IN ('assigned', 'checked_out', 'in_use', 'returned', 'damaged', 'lost')),
    checked_out_at TIMESTAMP WITH TIME ZONE,
    checked_in_at TIMESTAMP WITH TIME ZONE,
    condition_at_checkout VARCHAR(20),
    condition_at_return VARCHAR(20),
    return_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure no double-booking of resources
    CONSTRAINT unique_resource_shift_assignment UNIQUE (shift_id, resource_id)
);

-- Usage tracking table for detailed resource usage metrics
CREATE TABLE IF NOT EXISTS public.resource_usage_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    resource_assignment_id UUID REFERENCES public.resource_assignments(id) ON DELETE CASCADE,
    resource_id UUID REFERENCES public.resources(id),
    user_id UUID REFERENCES public.users(id),
    shift_id UUID REFERENCES public.shifts(id),
    action VARCHAR(50) NOT NULL, -- 'assigned', 'checked_out', 'checked_in', 'damaged', 'maintenance_required', etc.
    action_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    duration_minutes INTEGER, -- calculated usage duration
    condition_before VARCHAR(20),
    condition_after VARCHAR(20),
    notes TEXT,
    metadata JSONB DEFAULT '{}', -- flexible field for additional data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Maintenance schedules and history
CREATE TABLE IF NOT EXISTS public.resource_maintenance (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    resource_id UUID REFERENCES public.resources(id) ON DELETE CASCADE,
    maintenance_type VARCHAR(50) NOT NULL, -- 'scheduled', 'repair', 'inspection', 'cleaning'
    scheduled_date DATE NOT NULL,
    completed_date DATE,
    performed_by_user_id UUID REFERENCES public.users(id),
    description TEXT,
    cost DECIMAL(10,2),
    parts_replaced TEXT,
    condition_before VARCHAR(20),
    condition_after VARCHAR(20),
    next_maintenance_date DATE,
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'in_progress', 'completed', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_shifts_branch ON public.shifts(branch);
CREATE INDEX IF NOT EXISTS idx_shifts_start_time ON public.shifts(start_time);
CREATE INDEX IF NOT EXISTS idx_shifts_status ON public.shifts(status);

CREATE INDEX IF NOT EXISTS idx_resources_branch ON public.resources(branch);
CREATE INDEX IF NOT EXISTS idx_resources_type ON public.resources(resource_type);
CREATE INDEX IF NOT EXISTS idx_resources_status ON public.resources(status);

CREATE INDEX IF NOT EXISTS idx_resource_assignments_shift_id ON public.resource_assignments(shift_id);
CREATE INDEX IF NOT EXISTS idx_resource_assignments_resource_id ON public.resource_assignments(resource_id);
CREATE INDEX IF NOT EXISTS idx_resource_assignments_assigned_to ON public.resource_assignments(assigned_to_user_id);
CREATE INDEX IF NOT EXISTS idx_resource_assignments_status ON public.resource_assignments(status);

CREATE INDEX IF NOT EXISTS idx_resource_usage_logs_resource_id ON public.resource_usage_logs(resource_id);
CREATE INDEX IF NOT EXISTS idx_resource_usage_logs_user_id ON public.resource_usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_resource_usage_logs_shift_id ON public.resource_usage_logs(shift_id);
CREATE INDEX IF NOT EXISTS idx_resource_usage_logs_action_timestamp ON public.resource_usage_logs(action_timestamp);

CREATE INDEX IF NOT EXISTS idx_resource_maintenance_resource_id ON public.resource_maintenance(resource_id);
CREATE INDEX IF NOT EXISTS idx_resource_maintenance_scheduled_date ON public.resource_maintenance(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_resource_maintenance_status ON public.resource_maintenance(status);

-- Enable Row Level Security (RLS)
ALTER TABLE public.shifts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resource_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resource_usage_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resource_maintenance ENABLE ROW LEVEL SECURITY;

-- RLS Policies for new tables
-- Shifts - users can view shifts for their branch, staff can manage
CREATE POLICY "Users can view shifts" ON public.shifts
    FOR SELECT USING (true); -- Allow all authenticated users to view shifts

CREATE POLICY "Staff can manage shifts" ON public.shifts
    FOR ALL USING (auth.uid()::text = created_by::text);

-- Resources - similar access pattern
CREATE POLICY "Users can view resources" ON public.resources
    FOR SELECT USING (true);

CREATE POLICY "Staff can manage resources" ON public.resources
    FOR ALL USING (true); -- In practice, you'd check for staff role

-- Resource assignments - users can see their own assignments
CREATE POLICY "Users can view own resource assignments" ON public.resource_assignments
    FOR SELECT USING (auth.uid()::text = assigned_to_user_id::text OR auth.uid()::text = assigned_by_user_id::text);

CREATE POLICY "Staff can manage resource assignments" ON public.resource_assignments
    FOR ALL USING (true); -- In practice, check for staff role

-- Usage logs - users can view their own usage
CREATE POLICY "Users can view own usage logs" ON public.resource_usage_logs
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert usage logs" ON public.resource_usage_logs
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

-- Maintenance - staff only typically
CREATE POLICY "Staff can manage maintenance" ON public.resource_maintenance
    FOR ALL USING (true); -- Check for maintenance staff role

-- Add triggers for updated_at columns
CREATE TRIGGER update_shifts_updated_at BEFORE UPDATE ON public.shifts
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_resources_updated_at BEFORE UPDATE ON public.resources
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_resource_assignments_updated_at BEFORE UPDATE ON public.resource_assignments
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_resource_maintenance_updated_at BEFORE UPDATE ON public.resource_maintenance
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Function to automatically log resource usage events
CREATE OR REPLACE FUNCTION public.log_resource_usage()
RETURNS TRIGGER AS $$
BEGIN
    -- Log when assignment status changes
    IF TG_OP = 'UPDATE' AND OLD.status != NEW.status THEN
        INSERT INTO public.resource_usage_logs (
            resource_assignment_id,
            resource_id,
            user_id,
            shift_id,
            action,
            action_timestamp,
            condition_before,
            condition_after,
            notes
        ) VALUES (
            NEW.id,
            NEW.resource_id,
            NEW.assigned_to_user_id,
            NEW.shift_id,
            NEW.status,
            NOW(),
            OLD.condition_at_checkout,
            NEW.condition_at_return,
            NEW.return_notes
        );
        
        -- Calculate duration if checking in
        IF NEW.status = 'returned' AND NEW.checked_out_at IS NOT NULL AND NEW.checked_in_at IS NOT NULL THEN
            UPDATE public.resource_usage_logs 
            SET duration_minutes = EXTRACT(EPOCH FROM (NEW.checked_in_at - NEW.checked_out_at)) / 60
            WHERE resource_assignment_id = NEW.id AND action = 'returned';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic usage logging
CREATE TRIGGER log_resource_usage_changes AFTER UPDATE ON public.resource_assignments
    FOR EACH ROW EXECUTE FUNCTION public.log_resource_usage();

-- Function to check resource availability before assignment
CREATE OR REPLACE FUNCTION public.check_resource_availability(
    p_resource_id UUID,
    p_shift_start TIMESTAMP WITH TIME ZONE,
    p_shift_end TIMESTAMP WITH TIME ZONE
) RETURNS BOOLEAN AS $$
DECLARE
    resource_record RECORD;
    conflict_count INTEGER;
BEGIN
    -- Get resource details
    SELECT * INTO resource_record FROM public.resources WHERE id = p_resource_id;
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Check if resource is available
    IF resource_record.status != 'available' THEN
        RETURN FALSE;
    END IF;
    
    -- Check for conflicting assignments
    SELECT COUNT(*) INTO conflict_count
    FROM public.resource_assignments ra
    JOIN public.shifts s ON ra.shift_id = s.id
    WHERE ra.resource_id = p_resource_id
    AND ra.status NOT IN ('returned', 'cancelled')
    AND s.status NOT IN ('completed', 'cancelled')
    AND (
        (s.start_time <= p_shift_start AND s.end_time > p_shift_start) OR
        (s.start_time < p_shift_end AND s.end_time >= p_shift_end) OR
        (s.start_time >= p_shift_start AND s.end_time <= p_shift_end)
    );
    
    -- Check if we're within max concurrent assignments limit
    RETURN conflict_count < resource_record.max_concurrent_assignments;
END;
$$ LANGUAGE plpgsql;

-- Insert sample data for testing
INSERT INTO public.resources (name, description, resource_type, branch, condition, status, max_concurrent_assignments) VALUES
('Pool Vacuum System', 'Professional pool cleaning vacuum with hose and attachments', 'equipment', 'Blue Ash', 'good', 'available', 1),
('First Aid Kit - Deluxe', 'Complete first aid kit for youth programs', 'supplies', 'Blue Ash', 'good', 'available', 3),
('Basketball Cart - 20 Ball', 'Mobile cart for storing and transporting basketballs', 'equipment', 'Campbell County', 'excellent', 'available', 1),
('Van - 15 Passenger', 'Large van for field trips and transportation', 'vehicle', 'Clippard', 'good', 'available', 1),
('Sound System - Portable', 'Wireless microphone and speaker system for events', 'equipment', 'Music Resource Center', 'excellent', 'available', 1),
('Tables - Folding (Set of 10)', 'Rectangular folding tables for events and activities', 'equipment', 'R.C. Durre YMCA', 'good', 'available', 2);

INSERT INTO public.shifts (name, description, branch, category, start_time, end_time, max_volunteers) VALUES
('Morning Pool Maintenance', 'Daily pool cleaning and chemical balance check', 'Blue Ash', 'Maintenance', '2025-09-07 06:00:00-05', '2025-09-07 08:00:00-05', 2),
('Youth Basketball Clinic Setup', 'Setup equipment and court preparation for youth clinic', 'Campbell County', 'Youth Programs', '2025-09-07 08:00:00-05', '2025-09-07 10:00:00-05', 3),
('Senior Center Transportation', 'Drive van to transport seniors to activities', 'Clippard', 'Senior Services', '2025-09-07 09:00:00-05', '2025-09-07 15:00:00-05', 1),
('Community Event Setup', 'Setup for community health fair', 'R.C. Durre YMCA', 'Community Services', '2025-09-07 07:00:00-05', '2025-09-07 09:00:00-05', 4);

-- Show completion message
SELECT 'Resource/Equipment Assignment feature database schema created successfully!' AS result;