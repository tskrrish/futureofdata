-- Volunteer PathFinder Database Schema for Supabase
-- Run these SQL commands in your Supabase SQL Editor

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS public.users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    age INTEGER,
    gender VARCHAR(20),
    city VARCHAR(100),
    state VARCHAR(10),
    zip_code VARCHAR(10),
    is_ymca_member BOOLEAN DEFAULT FALSE,
    member_branch VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User preferences table
CREATE TABLE IF NOT EXISTS public.user_preferences (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    interests TEXT,
    skills TEXT,
    availability JSONB DEFAULT '{}',
    time_commitment INTEGER DEFAULT 2, -- 1=low, 2=medium, 3=high
    location_preference VARCHAR(100),
    experience_level INTEGER DEFAULT 1, -- 1=beginner, 2=some, 3=experienced
    volunteer_type VARCHAR(50),
    preferences_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Conversations table
CREATE TABLE IF NOT EXISTS public.conversations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    session_id VARCHAR(100),
    conversation_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Messages table
CREATE TABLE IF NOT EXISTS public.messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    conversation_id UUID REFERENCES public.conversations(id) ON DELETE CASCADE,
    user_id UUID,
    role VARCHAR(20) CHECK (role IN ('user', 'assistant')),
    content TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Volunteer matches table
CREATE TABLE IF NOT EXISTS public.volunteer_matches (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    project_id INTEGER,
    project_name VARCHAR(200),
    branch VARCHAR(100),
    category VARCHAR(100),
    match_score DECIMAL(3,2),
    reasons JSONB DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'suggested' CHECK (status IN ('suggested', 'interested', 'applied', 'matched')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Volunteer feedback table
CREATE TABLE IF NOT EXISTS public.volunteer_feedback (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    match_id UUID REFERENCES public.volunteer_matches(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    feedback_type VARCHAR(20) DEFAULT 'general' CHECK (feedback_type IN ('recommendation', 'experience', 'general')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Analytics events table
CREATE TABLE IF NOT EXISTS public.analytics_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID,
    session_id VARCHAR(100),
    event_type VARCHAR(50),
    event_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON public.user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON public.conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON public.conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON public.messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON public.messages(created_at);
CREATE INDEX IF NOT EXISTS idx_volunteer_matches_user_id ON public.volunteer_matches(user_id);
CREATE INDEX IF NOT EXISTS idx_volunteer_matches_status ON public.volunteer_matches(status);
CREATE INDEX IF NOT EXISTS idx_volunteer_feedback_user_id ON public.volunteer_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_user_id ON public.analytics_events(user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_event_type ON public.analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_events_created_at ON public.analytics_events(created_at);

-- Enable Row Level Security (RLS)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.volunteer_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.volunteer_feedback ENABLE ROW LEVEL SECURITY;

-- RLS Policies (basic - can be enhanced based on requirements)
-- Users can only see/modify their own data

-- Users table policies
CREATE POLICY "Users can view own profile" ON public.users
    FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (auth.uid()::text = id::text);

-- User preferences policies
CREATE POLICY "Users can manage own preferences" ON public.user_preferences
    FOR ALL USING (auth.uid()::text = user_id::text);

-- Conversations policies
CREATE POLICY "Users can manage own conversations" ON public.conversations
    FOR ALL USING (auth.uid()::text = user_id::text);

-- Messages policies  
CREATE POLICY "Users can manage own messages" ON public.messages
    FOR ALL USING (auth.uid()::text = user_id::text);

-- Volunteer matches policies
CREATE POLICY "Users can manage own matches" ON public.volunteer_matches
    FOR ALL USING (auth.uid()::text = user_id::text);

-- Volunteer feedback policies
CREATE POLICY "Users can manage own feedback" ON public.volunteer_feedback
    FOR ALL USING (auth.uid()::text = user_id::text);

-- Analytics events are insert-only for users
CREATE POLICY "Users can insert analytics events" ON public.analytics_events
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at columns
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON public.user_preferences
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON public.conversations
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_volunteer_matches_updated_at BEFORE UPDATE ON public.volunteer_matches
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Insert some sample data (optional)
-- INSERT INTO public.users (email, first_name, last_name, age, city, state, is_ymca_member) VALUES
-- ('demo@example.com', 'Demo', 'User', 30, 'Cincinnati', 'OH', true);

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO anon, authenticated;

-- Course enrollment and waitlist tables
CREATE TABLE IF NOT EXISTS public.courses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    course_name VARCHAR(200) NOT NULL,
    course_description TEXT,
    instructor VARCHAR(100),
    branch VARCHAR(100),
    category VARCHAR(100),
    max_capacity INTEGER NOT NULL DEFAULT 20,
    current_enrolled INTEGER DEFAULT 0,
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    schedule_days TEXT[], -- ['Monday', 'Wednesday', 'Friday']
    schedule_time TIME,
    price DECIMAL(8,2) DEFAULT 0.00,
    requirements TEXT,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'closed', 'cancelled', 'completed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Course enrollments table
CREATE TABLE IF NOT EXISTS public.course_enrollments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    course_id UUID REFERENCES public.courses(id) ON DELETE CASCADE,
    enrollment_status VARCHAR(20) DEFAULT 'enrolled' CHECK (enrollment_status IN ('enrolled', 'waitlisted', 'dropped', 'completed', 'no_show')),
    enrollment_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    waitlist_position INTEGER,
    waitlist_priority INTEGER DEFAULT 5, -- 1=highest, 5=normal, 10=lowest
    notification_sent BOOLEAN DEFAULT FALSE,
    payment_status VARCHAR(20) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'refunded')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, course_id)
);

-- Waitlist audit log for tracking auto-backfill actions
CREATE TABLE IF NOT EXISTS public.waitlist_audit_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    course_id UUID REFERENCES public.courses(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL, -- 'auto_enrolled', 'manual_enrolled', 'dropped', 'no_show'
    previous_status VARCHAR(20),
    new_status VARCHAR(20),
    reason TEXT,
    triggered_by VARCHAR(50) DEFAULT 'system', -- 'system', 'admin', 'user'
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Course attendance tracking
CREATE TABLE IF NOT EXISTS public.course_attendance (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    enrollment_id UUID REFERENCES public.course_enrollments(id) ON DELETE CASCADE,
    session_date DATE NOT NULL,
    attendance_status VARCHAR(20) DEFAULT 'scheduled' CHECK (attendance_status IN ('scheduled', 'present', 'absent', 'no_show')),
    notes TEXT,
    marked_at TIMESTAMP WITH TIME ZONE,
    marked_by UUID REFERENCES public.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for course-related tables
CREATE INDEX IF NOT EXISTS idx_courses_branch ON public.courses(branch);
CREATE INDEX IF NOT EXISTS idx_courses_category ON public.courses(category);
CREATE INDEX IF NOT EXISTS idx_courses_status ON public.courses(status);
CREATE INDEX IF NOT EXISTS idx_courses_start_date ON public.courses(start_date);

CREATE INDEX IF NOT EXISTS idx_course_enrollments_user_id ON public.course_enrollments(user_id);
CREATE INDEX IF NOT EXISTS idx_course_enrollments_course_id ON public.course_enrollments(course_id);
CREATE INDEX IF NOT EXISTS idx_course_enrollments_status ON public.course_enrollments(enrollment_status);
CREATE INDEX IF NOT EXISTS idx_course_enrollments_waitlist_position ON public.course_enrollments(waitlist_position);

CREATE INDEX IF NOT EXISTS idx_waitlist_audit_course_id ON public.waitlist_audit_log(course_id);
CREATE INDEX IF NOT EXISTS idx_waitlist_audit_user_id ON public.waitlist_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_waitlist_audit_action ON public.waitlist_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_waitlist_audit_created_at ON public.waitlist_audit_log(created_at);

CREATE INDEX IF NOT EXISTS idx_course_attendance_enrollment_id ON public.course_attendance(enrollment_id);
CREATE INDEX IF NOT EXISTS idx_course_attendance_session_date ON public.course_attendance(session_date);

-- Enable RLS for course tables
ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.course_enrollments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.waitlist_audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.course_attendance ENABLE ROW LEVEL SECURITY;

-- RLS Policies for courses (read-only for users)
CREATE POLICY "Anyone can view courses" ON public.courses
    FOR SELECT USING (true);

-- RLS Policies for course enrollments (users can only see their own)
CREATE POLICY "Users can view own enrollments" ON public.course_enrollments
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can manage own enrollments" ON public.course_enrollments
    FOR ALL USING (auth.uid()::text = user_id::text);

-- RLS Policies for waitlist audit log (users can view their own entries)
CREATE POLICY "Users can view own audit log" ON public.waitlist_audit_log
    FOR SELECT USING (auth.uid()::text = user_id::text);

-- RLS Policies for course attendance (users can view their own)
CREATE POLICY "Users can view own attendance" ON public.course_attendance
    FOR SELECT USING (auth.uid()::text IN (
        SELECT e.user_id::text FROM public.course_enrollments e WHERE e.id = enrollment_id
    ));

-- Add triggers for updated_at columns
CREATE TRIGGER update_courses_updated_at BEFORE UPDATE ON public.courses
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_course_enrollments_updated_at BEFORE UPDATE ON public.course_enrollments
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Function to automatically update course enrollment counts
CREATE OR REPLACE FUNCTION public.update_course_enrollment_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        -- Only count enrolled students, not waitlisted
        IF NEW.enrollment_status = 'enrolled' THEN
            UPDATE public.courses 
            SET current_enrolled = current_enrolled + 1 
            WHERE id = NEW.course_id;
        END IF;
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        -- Handle status changes
        IF OLD.enrollment_status != NEW.enrollment_status THEN
            IF OLD.enrollment_status = 'enrolled' AND NEW.enrollment_status != 'enrolled' THEN
                -- Student dropped or moved to waitlist
                UPDATE public.courses 
                SET current_enrolled = current_enrolled - 1 
                WHERE id = NEW.course_id;
            ELSIF OLD.enrollment_status != 'enrolled' AND NEW.enrollment_status = 'enrolled' THEN
                -- Student moved from waitlist to enrolled
                UPDATE public.courses 
                SET current_enrolled = current_enrolled + 1 
                WHERE id = NEW.course_id;
            END IF;
        END IF;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        -- Student completely removed
        IF OLD.enrollment_status = 'enrolled' THEN
            UPDATE public.courses 
            SET current_enrolled = current_enrolled - 1 
            WHERE id = OLD.course_id;
        END IF;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for enrollment count updates
CREATE TRIGGER update_enrollment_count_trigger
    AFTER INSERT OR UPDATE OR DELETE ON public.course_enrollments
    FOR EACH ROW EXECUTE FUNCTION public.update_course_enrollment_count();

-- Function to auto-assign waitlist positions
CREATE OR REPLACE FUNCTION public.assign_waitlist_position()
RETURNS TRIGGER AS $$
BEGIN
    -- Only assign position if enrollment_status is waitlisted and position is not set
    IF NEW.enrollment_status = 'waitlisted' AND (NEW.waitlist_position IS NULL OR NEW.waitlist_position = 0) THEN
        SELECT COALESCE(MAX(waitlist_position), 0) + 1
        INTO NEW.waitlist_position
        FROM public.course_enrollments
        WHERE course_id = NEW.course_id AND enrollment_status = 'waitlisted';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for waitlist position assignment
CREATE TRIGGER assign_waitlist_position_trigger
    BEFORE INSERT OR UPDATE ON public.course_enrollments
    FOR EACH ROW EXECUTE FUNCTION public.assign_waitlist_position();

-- Grant permissions for new tables
GRANT ALL ON public.courses TO anon, authenticated;
GRANT ALL ON public.course_enrollments TO anon, authenticated;
GRANT ALL ON public.waitlist_audit_log TO anon, authenticated;
GRANT ALL ON public.course_attendance TO anon, authenticated;

-- Show completion message
SELECT 'Volunteer PathFinder database schema with course enrollment and waitlist created successfully!' AS result;
