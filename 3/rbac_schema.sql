-- Branch-Scoped RBAC Schema Extension for Volunteer PathFinder
-- Implements granular role-based access control with least-privilege defaults

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Roles table - Define system roles
CREATE TABLE IF NOT EXISTS public.roles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_system_role BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Permissions table - Define granular permissions
CREATE TABLE IF NOT EXISTS public.permissions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(50) NOT NULL, -- users, volunteers, projects, analytics, etc.
    action VARCHAR(20) NOT NULL,   -- create, read, update, delete, manage
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Role permissions mapping
CREATE TABLE IF NOT EXISTS public.role_permissions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    role_id UUID REFERENCES public.roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES public.permissions(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(role_id, permission_id)
);

-- Branch-scoped user roles - Users can have different roles per branch
CREATE TABLE IF NOT EXISTS public.user_branch_roles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES public.roles(id) ON DELETE CASCADE,
    branch VARCHAR(100), -- NULL means global access
    granted_by UUID REFERENCES public.users(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE, -- NULL for no expiration
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, role_id, branch)
);

-- Permission overrides - Allow specific permission grants/denials per user/branch
CREATE TABLE IF NOT EXISTS public.user_permission_overrides (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES public.permissions(id) ON DELETE CASCADE,
    branch VARCHAR(100), -- NULL means global override
    granted BOOLEAN NOT NULL, -- TRUE = grant, FALSE = deny
    granted_by UUID REFERENCES public.users(id),
    reason TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, permission_id, branch)
);

-- Access logs for auditing
CREATE TABLE IF NOT EXISTS public.access_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id),
    resource VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL,
    branch VARCHAR(100),
    resource_id VARCHAR(255), -- ID of the specific resource accessed
    granted BOOLEAN NOT NULL,
    reason TEXT, -- Why access was granted/denied
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_roles_name ON public.roles(name);
CREATE INDEX IF NOT EXISTS idx_permissions_resource_action ON public.permissions(resource, action);
CREATE INDEX IF NOT EXISTS idx_role_permissions_role_id ON public.role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_permission_id ON public.role_permissions(permission_id);
CREATE INDEX IF NOT EXISTS idx_user_branch_roles_user_id ON public.user_branch_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_branch_roles_branch ON public.user_branch_roles(branch);
CREATE INDEX IF NOT EXISTS idx_user_branch_roles_active ON public.user_branch_roles(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_user_permission_overrides_user_id ON public.user_permission_overrides(user_id);
CREATE INDEX IF NOT EXISTS idx_user_permission_overrides_branch ON public.user_permission_overrides(branch);
CREATE INDEX IF NOT EXISTS idx_access_logs_user_id ON public.access_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_resource_action ON public.access_logs(resource, action);
CREATE INDEX IF NOT EXISTS idx_access_logs_created_at ON public.access_logs(created_at);

-- Enable Row Level Security on RBAC tables
ALTER TABLE public.roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.role_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_branch_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_permission_overrides ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.access_logs ENABLE ROW LEVEL SECURITY;

-- Insert default system roles with least-privilege approach
INSERT INTO public.roles (name, description, is_system_role) VALUES
    ('volunteer', 'Basic volunteer - can view own profile and opportunities', TRUE),
    ('volunteer_coordinator', 'Branch volunteer coordinator - can manage volunteers in assigned branches', TRUE),
    ('branch_admin', 'Branch administrator - full access to branch resources', TRUE),
    ('staff', 'YMCA staff member - can view analytics and manage programs', TRUE),
    ('system_admin', 'System administrator - full system access', TRUE),
    ('guest', 'Unauthenticated user - very limited read access', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Insert granular permissions following least-privilege principle
INSERT INTO public.permissions (name, resource, action, description) VALUES
    -- User management
    ('users.read.own', 'users', 'read', 'Read own user profile'),
    ('users.update.own', 'users', 'update', 'Update own user profile'),
    ('users.read.branch', 'users', 'read', 'Read users in same branch'),
    ('users.create.branch', 'users', 'create', 'Create users in branch'),
    ('users.update.branch', 'users', 'update', 'Update users in branch'),
    ('users.delete.branch', 'users', 'delete', 'Delete users in branch'),
    ('users.manage.global', 'users', 'manage', 'Full user management globally'),
    
    -- Volunteer management
    ('volunteers.read.public', 'volunteers', 'read', 'Read public volunteer information'),
    ('volunteers.read.own', 'volunteers', 'read', 'Read own volunteer data'),
    ('volunteers.update.own', 'volunteers', 'update', 'Update own volunteer information'),
    ('volunteers.read.branch', 'volunteers', 'read', 'Read volunteer data in branch'),
    ('volunteers.manage.branch', 'volunteers', 'manage', 'Manage volunteers in branch'),
    ('volunteers.manage.global', 'volunteers', 'manage', 'Manage all volunteers globally'),
    
    -- Project management
    ('projects.read.public', 'projects', 'read', 'Read public project information'),
    ('projects.read.branch', 'projects', 'read', 'Read projects in branch'),
    ('projects.create.branch', 'projects', 'create', 'Create projects in branch'),
    ('projects.update.branch', 'projects', 'update', 'Update projects in branch'),
    ('projects.delete.branch', 'projects', 'delete', 'Delete projects in branch'),
    ('projects.manage.global', 'projects', 'manage', 'Full project management globally'),
    
    -- Analytics and reporting
    ('analytics.read.own', 'analytics', 'read', 'Read own analytics data'),
    ('analytics.read.branch', 'analytics', 'read', 'Read branch analytics'),
    ('analytics.read.global', 'analytics', 'read', 'Read global analytics'),
    ('analytics.export.branch', 'analytics', 'export', 'Export branch data'),
    ('analytics.export.global', 'analytics', 'export', 'Export global data'),
    
    -- RBAC management
    ('rbac.read.own', 'rbac', 'read', 'Read own roles and permissions'),
    ('rbac.read.branch', 'rbac', 'read', 'Read branch RBAC configuration'),
    ('rbac.manage.branch', 'rbac', 'manage', 'Manage branch roles and permissions'),
    ('rbac.manage.global', 'rbac', 'manage', 'Full RBAC management globally'),
    
    -- System administration
    ('system.read', 'system', 'read', 'Read system information'),
    ('system.manage', 'system', 'manage', 'Full system administration')
ON CONFLICT (name) DO NOTHING;

-- Assign least-privilege default permissions to roles
WITH role_permission_mappings AS (
    SELECT r.id as role_id, p.id as permission_id
    FROM public.roles r
    CROSS JOIN public.permissions p
    WHERE 
        -- Guest permissions (very minimal)
        (r.name = 'guest' AND p.name IN ('projects.read.public')) OR
        
        -- Volunteer permissions (self-service only)
        (r.name = 'volunteer' AND p.name IN (
            'users.read.own', 'users.update.own',
            'volunteers.read.own', 'volunteers.update.own',
            'projects.read.public',
            'analytics.read.own',
            'rbac.read.own'
        )) OR
        
        -- Staff permissions (branch-focused)
        (r.name = 'staff' AND p.name IN (
            'users.read.own', 'users.update.own',
            'volunteers.read.own', 'volunteers.update.own', 'volunteers.read.branch',
            'projects.read.public', 'projects.read.branch',
            'analytics.read.own', 'analytics.read.branch',
            'rbac.read.own', 'rbac.read.branch'
        )) OR
        
        -- Volunteer Coordinator permissions
        (r.name = 'volunteer_coordinator' AND p.name IN (
            'users.read.own', 'users.update.own', 'users.read.branch',
            'volunteers.read.own', 'volunteers.update.own', 'volunteers.read.branch', 'volunteers.manage.branch',
            'projects.read.public', 'projects.read.branch', 'projects.update.branch',
            'analytics.read.own', 'analytics.read.branch',
            'rbac.read.own', 'rbac.read.branch'
        )) OR
        
        -- Branch Admin permissions
        (r.name = 'branch_admin' AND p.name IN (
            'users.read.own', 'users.update.own', 'users.read.branch', 'users.create.branch', 'users.update.branch',
            'volunteers.read.own', 'volunteers.update.own', 'volunteers.manage.branch',
            'projects.read.public', 'projects.read.branch', 'projects.create.branch', 'projects.update.branch', 'projects.delete.branch',
            'analytics.read.own', 'analytics.read.branch', 'analytics.export.branch',
            'rbac.read.own', 'rbac.read.branch', 'rbac.manage.branch'
        )) OR
        
        -- System Admin permissions (everything)
        (r.name = 'system_admin')
)
INSERT INTO public.role_permissions (role_id, permission_id)
SELECT role_id, permission_id FROM role_permission_mappings
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Create helper functions for RBAC

-- Function to check if user has permission for a specific branch
CREATE OR REPLACE FUNCTION public.user_has_permission(
    p_user_id UUID,
    p_permission_name VARCHAR,
    p_branch VARCHAR DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    has_permission BOOLEAN := FALSE;
BEGIN
    -- Check for explicit override first (grants or denials)
    SELECT COALESCE(upo.granted, FALSE) INTO has_permission
    FROM public.user_permission_overrides upo
    JOIN public.permissions p ON upo.permission_id = p.id
    WHERE upo.user_id = p_user_id
      AND p.name = p_permission_name
      AND (upo.branch = p_branch OR (upo.branch IS NULL AND p_branch IS NULL))
      AND upo.expires_at IS NULL OR upo.expires_at > NOW();
    
    -- If override found, return it
    IF FOUND THEN
        RETURN has_permission;
    END IF;
    
    -- Check role-based permissions
    SELECT TRUE INTO has_permission
    FROM public.user_branch_roles ubr
    JOIN public.role_permissions rp ON ubr.role_id = rp.role_id
    JOIN public.permissions p ON rp.permission_id = p.id
    WHERE ubr.user_id = p_user_id
      AND p.name = p_permission_name
      AND ubr.is_active = TRUE
      AND (ubr.expires_at IS NULL OR ubr.expires_at > NOW())
      AND (ubr.branch = p_branch OR ubr.branch IS NULL) -- Global permissions apply everywhere
    LIMIT 1;
    
    RETURN COALESCE(has_permission, FALSE);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get user's branches
CREATE OR REPLACE FUNCTION public.user_accessible_branches(p_user_id UUID)
RETURNS TABLE(branch VARCHAR) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT ubr.branch
    FROM public.user_branch_roles ubr
    WHERE ubr.user_id = p_user_id
      AND ubr.is_active = TRUE
      AND (ubr.expires_at IS NULL OR ubr.expires_at > NOW())
      AND ubr.branch IS NOT NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to log access attempts
CREATE OR REPLACE FUNCTION public.log_access_attempt(
    p_user_id UUID,
    p_resource VARCHAR,
    p_action VARCHAR,
    p_branch VARCHAR DEFAULT NULL,
    p_resource_id VARCHAR DEFAULT NULL,
    p_granted BOOLEAN DEFAULT FALSE,
    p_reason TEXT DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    INSERT INTO public.access_logs (
        user_id, resource, action, branch, resource_id, granted, reason
    ) VALUES (
        p_user_id, p_resource, p_action, p_branch, p_resource_id, p_granted, p_reason
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Enhanced RLS policies for existing tables using RBAC

-- Drop existing policies that might conflict
DROP POLICY IF EXISTS "Users can view own profile" ON public.users;
DROP POLICY IF EXISTS "Users can update own profile" ON public.users;
DROP POLICY IF EXISTS "Users can manage own preferences" ON public.user_preferences;
DROP POLICY IF EXISTS "Users can manage own conversations" ON public.conversations;
DROP POLICY IF EXISTS "Users can manage own messages" ON public.messages;
DROP POLICY IF EXISTS "Users can manage own matches" ON public.volunteer_matches;
DROP POLICY IF EXISTS "Users can manage own feedback" ON public.volunteer_feedback;

-- New RBAC-based policies for users table
CREATE POLICY "RBAC: Users can read own profile" ON public.users
    FOR SELECT USING (
        auth.uid()::text = id::text OR
        public.user_has_permission(auth.uid(), 'users.read.branch', member_branch) OR
        public.user_has_permission(auth.uid(), 'users.manage.global')
    );

CREATE POLICY "RBAC: Users can update profiles" ON public.users
    FOR UPDATE USING (
        auth.uid()::text = id::text OR
        public.user_has_permission(auth.uid(), 'users.update.branch', member_branch) OR
        public.user_has_permission(auth.uid(), 'users.manage.global')
    );

CREATE POLICY "RBAC: Users can create profiles" ON public.users
    FOR INSERT WITH CHECK (
        public.user_has_permission(auth.uid(), 'users.create.branch', member_branch) OR
        public.user_has_permission(auth.uid(), 'users.manage.global')
    );

-- RBAC policies for volunteer matches
CREATE POLICY "RBAC: Volunteer matches access" ON public.volunteer_matches
    FOR ALL USING (
        user_id = auth.uid() OR
        public.user_has_permission(auth.uid(), 'volunteers.read.branch', branch) OR
        public.user_has_permission(auth.uid(), 'volunteers.manage.branch', branch) OR
        public.user_has_permission(auth.uid(), 'volunteers.manage.global')
    );

-- RBAC policies for analytics (restrict access to branch data)
CREATE POLICY "RBAC: Analytics access" ON public.analytics_events
    FOR SELECT USING (
        user_id = auth.uid() OR
        public.user_has_permission(auth.uid(), 'analytics.read.branch') OR
        public.user_has_permission(auth.uid(), 'analytics.read.global')
    );

-- RBAC table policies
CREATE POLICY "RBAC: Read roles" ON public.roles
    FOR SELECT USING (
        public.user_has_permission(auth.uid(), 'rbac.read.own') OR
        public.user_has_permission(auth.uid(), 'rbac.read.branch') OR
        public.user_has_permission(auth.uid(), 'rbac.manage.global')
    );

CREATE POLICY "RBAC: Manage roles" ON public.roles
    FOR ALL USING (
        public.user_has_permission(auth.uid(), 'rbac.manage.global')
    );

CREATE POLICY "RBAC: Read permissions" ON public.permissions
    FOR SELECT USING (
        public.user_has_permission(auth.uid(), 'rbac.read.own') OR
        public.user_has_permission(auth.uid(), 'rbac.read.branch') OR
        public.user_has_permission(auth.uid(), 'rbac.manage.global')
    );

CREATE POLICY "RBAC: Read user branch roles" ON public.user_branch_roles
    FOR SELECT USING (
        user_id = auth.uid() OR
        public.user_has_permission(auth.uid(), 'rbac.read.branch') OR
        public.user_has_permission(auth.uid(), 'rbac.manage.global')
    );

CREATE POLICY "RBAC: Manage user branch roles" ON public.user_branch_roles
    FOR ALL USING (
        public.user_has_permission(auth.uid(), 'rbac.manage.branch', branch) OR
        public.user_has_permission(auth.uid(), 'rbac.manage.global')
    );

-- Triggers for updated_at columns
CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON public.roles
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_user_branch_roles_updated_at BEFORE UPDATE ON public.user_branch_roles
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Insert default assignments (system admin gets global access, others get minimal)
-- This should be done through the API in production

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT INSERT, UPDATE, DELETE ON public.access_logs TO authenticated;
GRANT EXECUTE ON FUNCTION public.user_has_permission(UUID, VARCHAR, VARCHAR) TO authenticated;
GRANT EXECUTE ON FUNCTION public.user_accessible_branches(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION public.log_access_attempt(UUID, VARCHAR, VARCHAR, VARCHAR, VARCHAR, BOOLEAN, TEXT) TO authenticated;

SELECT 'Branch-scoped RBAC schema created successfully with least-privilege defaults!' AS result;