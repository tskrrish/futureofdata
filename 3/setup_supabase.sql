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

-- Friend groups table
CREATE TABLE IF NOT EXISTS public.friend_groups (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    group_id VARCHAR(50) UNIQUE NOT NULL,
    group_name VARCHAR(200),
    member_ids JSONB DEFAULT '[]', -- Array of volunteer contact_ids
    group_size INTEGER DEFAULT 0,
    avg_friendship_score DECIMAL(4,3),
    group_cohesion DECIMAL(4,3),
    shared_activities JSONB DEFAULT '{}',
    stats JSONB DEFAULT '{}',
    detection_method VARCHAR(50) DEFAULT 'community_detection',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Friend relationships table (for tracking individual friendships)
CREATE TABLE IF NOT EXISTS public.friend_relationships (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    volunteer1_id VARCHAR(50) NOT NULL,
    volunteer2_id VARCHAR(50) NOT NULL,
    friendship_score DECIMAL(4,3) NOT NULL,
    shared_sessions INTEGER DEFAULT 0,
    shared_projects INTEGER DEFAULT 0,
    total_hours_together DECIMAL(8,2) DEFAULT 0,
    interaction_frequency DECIMAL(6,3) DEFAULT 0,
    first_interaction DATE,
    last_interaction DATE,
    relationship_strength VARCHAR(20) DEFAULT 'weak', -- 'weak', 'moderate', 'strong'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(volunteer1_id, volunteer2_id)
);

-- Team matching preferences table
CREATE TABLE IF NOT EXISTS public.team_preferences (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    prefer_friends BOOLEAN DEFAULT TRUE,
    team_size_preference VARCHAR(20) DEFAULT 'any', -- 'small', 'medium', 'large', 'any'
    friend_group_id VARCHAR(50), -- Reference to friend_groups.group_id
    team_matching_enabled BOOLEAN DEFAULT TRUE,
    min_team_size INTEGER DEFAULT 2,
    max_team_size INTEGER DEFAULT 8,
    preferences_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Team-aware volunteer matches table (extends volunteer_matches with team info)
CREATE TABLE IF NOT EXISTS public.team_volunteer_matches (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    project_id INTEGER,
    project_name VARCHAR(200),
    branch VARCHAR(100),
    category VARCHAR(100),
    match_score DECIMAL(3,2),
    team_score DECIMAL(3,2), -- Score including team factors
    friend_group_compatible BOOLEAN DEFAULT FALSE,
    estimated_team_size VARCHAR(50),
    team_factors JSONB DEFAULT '[]',
    group_benefits JSONB DEFAULT '[]',
    friend_group_id VARCHAR(50), -- If part of a friend group match
    team_members JSONB DEFAULT '[]', -- IDs of other team members
    reasons JSONB DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'suggested',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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
CREATE INDEX IF NOT EXISTS idx_friend_groups_group_id ON public.friend_groups(group_id);
CREATE INDEX IF NOT EXISTS idx_friend_groups_is_active ON public.friend_groups(is_active);
CREATE INDEX IF NOT EXISTS idx_friend_relationships_volunteer1_id ON public.friend_relationships(volunteer1_id);
CREATE INDEX IF NOT EXISTS idx_friend_relationships_volunteer2_id ON public.friend_relationships(volunteer2_id);
CREATE INDEX IF NOT EXISTS idx_friend_relationships_friendship_score ON public.friend_relationships(friendship_score);
CREATE INDEX IF NOT EXISTS idx_team_preferences_user_id ON public.team_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_team_preferences_friend_group_id ON public.team_preferences(friend_group_id);
CREATE INDEX IF NOT EXISTS idx_team_volunteer_matches_user_id ON public.team_volunteer_matches(user_id);
CREATE INDEX IF NOT EXISTS idx_team_volunteer_matches_friend_group_id ON public.team_volunteer_matches(friend_group_id);
CREATE INDEX IF NOT EXISTS idx_team_volunteer_matches_team_score ON public.team_volunteer_matches(team_score);

-- Enable Row Level Security (RLS)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.volunteer_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.volunteer_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.friend_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.friend_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.team_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.team_volunteer_matches ENABLE ROW LEVEL SECURITY;

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

-- Friend groups policies - viewable by all authenticated users, manageable by service
CREATE POLICY "Authenticated users can view friend groups" ON public.friend_groups
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Service can manage friend groups" ON public.friend_groups
    FOR ALL USING (auth.role() = 'service_role');

-- Friend relationships policies - viewable by involved users
CREATE POLICY "Users can view own friend relationships" ON public.friend_relationships
    FOR SELECT USING (auth.uid()::text = volunteer1_id::text OR auth.uid()::text = volunteer2_id::text);

CREATE POLICY "Service can manage friend relationships" ON public.friend_relationships
    FOR ALL USING (auth.role() = 'service_role');

-- Team preferences policies
CREATE POLICY "Users can manage own team preferences" ON public.team_preferences
    FOR ALL USING (auth.uid()::text = user_id::text);

-- Team volunteer matches policies
CREATE POLICY "Users can manage own team matches" ON public.team_volunteer_matches
    FOR ALL USING (auth.uid()::text = user_id::text);

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

CREATE TRIGGER update_friend_groups_updated_at BEFORE UPDATE ON public.friend_groups
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_friend_relationships_updated_at BEFORE UPDATE ON public.friend_relationships
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_team_preferences_updated_at BEFORE UPDATE ON public.team_preferences
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_team_volunteer_matches_updated_at BEFORE UPDATE ON public.team_volunteer_matches
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Insert some sample data (optional)
-- INSERT INTO public.users (email, first_name, last_name, age, city, state, is_ymca_member) VALUES
-- ('demo@example.com', 'Demo', 'User', 30, 'Cincinnati', 'OH', true);

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO anon, authenticated;

-- Dashboard sharing tables for shared dashboard permissions feature

-- Dashboards table - stores dashboard configurations
CREATE TABLE IF NOT EXISTS public.dashboards (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    owner_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    dashboard_data JSONB DEFAULT '{}', -- Store dashboard filters, settings, etc.
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Dashboard permissions table - manages who can access/edit dashboards
CREATE TABLE IF NOT EXISTS public.dashboard_permissions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    dashboard_id UUID REFERENCES public.dashboards(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    permission_type VARCHAR(20) NOT NULL CHECK (permission_type IN ('view', 'edit')),
    granted_by UUID REFERENCES public.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(dashboard_id, user_id) -- Prevent duplicate permissions for same user/dashboard
);

-- Dashboard access logs table - track dashboard usage
CREATE TABLE IF NOT EXISTS public.dashboard_access_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    dashboard_id UUID REFERENCES public.dashboards(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL, -- 'view', 'edit', 'share', 'export'
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for dashboard tables
CREATE INDEX IF NOT EXISTS idx_dashboards_owner_id ON public.dashboards(owner_id);
CREATE INDEX IF NOT EXISTS idx_dashboards_is_public ON public.dashboards(is_public);
CREATE INDEX IF NOT EXISTS idx_dashboard_permissions_dashboard_id ON public.dashboard_permissions(dashboard_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_permissions_user_id ON public.dashboard_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_permissions_permission_type ON public.dashboard_permissions(permission_type);
CREATE INDEX IF NOT EXISTS idx_dashboard_access_logs_dashboard_id ON public.dashboard_access_logs(dashboard_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_access_logs_user_id ON public.dashboard_access_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_access_logs_created_at ON public.dashboard_access_logs(created_at);

-- Enable RLS for dashboard tables
ALTER TABLE public.dashboards ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dashboard_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dashboard_access_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for dashboards
-- Owners can manage their own dashboards
CREATE POLICY "Dashboard owners can manage own dashboards" ON public.dashboards
    FOR ALL USING (auth.uid()::text = owner_id::text);

-- Users can view public dashboards
CREATE POLICY "Users can view public dashboards" ON public.dashboards
    FOR SELECT USING (is_public = TRUE);

-- Users can view dashboards they have permission to access
CREATE POLICY "Users can view shared dashboards" ON public.dashboards
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.dashboard_permissions dp 
            WHERE dp.dashboard_id = id 
            AND dp.user_id::text = auth.uid()::text
        )
    );

-- RLS Policies for dashboard permissions
-- Dashboard owners can manage permissions for their dashboards
CREATE POLICY "Dashboard owners can manage permissions" ON public.dashboard_permissions
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.dashboards d 
            WHERE d.id = dashboard_id 
            AND d.owner_id::text = auth.uid()::text
        )
    );

-- Users can view permissions granted to them
CREATE POLICY "Users can view their dashboard permissions" ON public.dashboard_permissions
    FOR SELECT USING (auth.uid()::text = user_id::text);

-- RLS Policies for access logs
-- Dashboard owners can view access logs for their dashboards
CREATE POLICY "Dashboard owners can view access logs" ON public.dashboard_access_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.dashboards d 
            WHERE d.id = dashboard_id 
            AND d.owner_id::text = auth.uid()::text
        )
    );

-- Users can view their own access logs
CREATE POLICY "Users can view their own access logs" ON public.dashboard_access_logs
    FOR SELECT USING (auth.uid()::text = user_id::text);

-- Insert access logs (users can only insert their own)
CREATE POLICY "Users can insert their own access logs" ON public.dashboard_access_logs
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

-- Create triggers for updated_at columns on new tables
CREATE TRIGGER update_dashboards_updated_at BEFORE UPDATE ON public.dashboards
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_dashboard_permissions_updated_at BEFORE UPDATE ON public.dashboard_permissions
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Grant permissions for new tables
GRANT ALL ON public.dashboards TO anon, authenticated;
GRANT ALL ON public.dashboard_permissions TO anon, authenticated;
GRANT ALL ON public.dashboard_access_logs TO anon, authenticated;

-- Show completion message
SELECT 'Volunteer PathFinder database schema with dashboard sharing created successfully!' AS result;
