-- Badge System 2.0 Database Schema
-- Migration: Add role-specific badges with rarity tiers

-- Enhanced volunteer profiles table
CREATE TABLE IF NOT EXISTS volunteer_profiles (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    contact_id VARCHAR(100),
    total_hours DECIMAL(10,2) DEFAULT 0,
    assignments_count INTEGER DEFAULT 0,
    first_activity DATE,
    last_activity DATE,
    years_active INTEGER DEFAULT 1,
    is_member BOOLEAN DEFAULT FALSE,
    member_branch VARCHAR(100),
    current_role VARCHAR(50) DEFAULT 'VOLUNTEER',
    badge_score INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Volunteer roles and progression tracking
CREATE TABLE IF NOT EXISTS volunteer_roles (
    id SERIAL PRIMARY KEY,
    role_key VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    level INTEGER NOT NULL,
    required_hours DECIMAL(10,2) DEFAULT 0,
    required_years INTEGER DEFAULT 0,
    previous_role VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Badge definitions table
CREATE TABLE IF NOT EXISTS badge_definitions (
    id SERIAL PRIMARY KEY,
    badge_key VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    icon VARCHAR(10),
    color VARCHAR(7), -- hex color
    rarity VARCHAR(20) NOT NULL CHECK (rarity IN ('common', 'uncommon', 'rare', 'epic', 'legendary')),
    category VARCHAR(50), -- role, storyworld, special
    storyworld VARCHAR(100),
    required_hours DECIMAL(10,2) DEFAULT 0,
    required_years INTEGER DEFAULT 0,
    required_projects INTEGER DEFAULT 0,
    required_categories INTEGER DEFAULT 0,
    special_requirements JSONB,
    points INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Volunteer badge achievements
CREATE TABLE IF NOT EXISTS volunteer_badges (
    id SERIAL PRIMARY KEY,
    volunteer_id INTEGER REFERENCES volunteer_profiles(id) ON DELETE CASCADE,
    badge_id INTEGER REFERENCES badge_definitions(id) ON DELETE CASCADE,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    earned_hours DECIMAL(10,2), -- hours when badge was earned
    metadata JSONB, -- additional context about how badge was earned
    UNIQUE(volunteer_id, badge_id)
);

-- Volunteer storyworld participation
CREATE TABLE IF NOT EXISTS volunteer_storyworlds (
    id SERIAL PRIMARY KEY,
    volunteer_id INTEGER REFERENCES volunteer_profiles(id) ON DELETE CASCADE,
    storyworld_name VARCHAR(100) NOT NULL,
    hours_contributed DECIMAL(10,2) DEFAULT 0,
    projects_count INTEGER DEFAULT 0,
    first_participation DATE,
    last_participation DATE,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(volunteer_id, storyworld_name)
);

-- Training and certifications
CREATE TABLE IF NOT EXISTS volunteer_training (
    id SERIAL PRIMARY KEY,
    volunteer_id INTEGER REFERENCES volunteer_profiles(id) ON DELETE CASCADE,
    training_name VARCHAR(200) NOT NULL,
    completed_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,
    certification_body VARCHAR(200),
    certificate_id VARCHAR(100),
    is_current BOOLEAN DEFAULT TRUE
);

-- Achievement history for tracking badge progression
CREATE TABLE IF NOT EXISTS achievement_history (
    id SERIAL PRIMARY KEY,
    volunteer_id INTEGER REFERENCES volunteer_profiles(id) ON DELETE CASCADE,
    achievement_type VARCHAR(50) NOT NULL, -- badge_earned, milestone, role_change
    title VARCHAR(200) NOT NULL,
    description TEXT,
    icon VARCHAR(10),
    metadata JSONB,
    achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Volunteer recommendations and next steps
CREATE TABLE IF NOT EXISTS volunteer_recommendations (
    id SERIAL PRIMARY KEY,
    volunteer_id INTEGER REFERENCES volunteer_profiles(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- role_progress, training, diversification, special_badge
    title VARCHAR(200) NOT NULL,
    description TEXT,
    action VARCHAR(100),
    priority VARCHAR(20) DEFAULT 'medium', -- high, medium, low
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Insert default volunteer roles
INSERT INTO volunteer_roles (role_key, name, level, required_hours, required_years, previous_role, description) VALUES
('VOLUNTEER', 'Volunteer', 0, 0, 0, NULL, 'Entry level volunteer'),
('GREETER', 'Greeter', 1, 10, 0, NULL, 'Welcome desk and hospitality volunteer'),
('LEAD_VOLUNTEER', 'Lead Volunteer', 2, 25, 0, 'GREETER', 'Team leadership and volunteer coordination'),
('MENTOR', 'Mentor', 3, 50, 1, 'LEAD_VOLUNTEER', 'Youth mentoring and new volunteer training'),
('SPECIALIST', 'Specialist', 3, 50, 1, 'LEAD_VOLUNTEER', 'Specialized program expert'),
('SENIOR_MENTOR', 'Senior Mentor', 4, 100, 2, 'MENTOR', 'Advanced mentoring and leadership'),
('SENIOR_SPECIALIST', 'Senior Specialist', 4, 100, 2, 'SPECIALIST', 'Advanced specialized expertise');

-- Insert badge definitions for each storyworld category
-- Youth Spark badges
INSERT INTO badge_definitions (badge_key, name, description, icon, color, rarity, category, storyworld, required_hours, points) VALUES
('ROOKIE_MENTOR', 'Rookie Mentor', 'First steps in youth mentoring', '🌟', '#FFD700', 'common', 'storyworld', 'Youth Spark', 10, 1),
('YOUTH_ADVOCATE', 'Youth Advocate', 'Champion for youth development', '🎯', '#FF6B35', 'uncommon', 'storyworld', 'Youth Spark', 25, 2),
('EDUCATION_HERO', 'Education Hero', 'Dedicated to educational excellence', '📚', '#9B59B6', 'rare', 'storyworld', 'Youth Spark', 50, 5),
('YOUTH_CHAMPION', 'Youth Champion', 'Leader in youth empowerment', '🏆', '#E74C3C', 'epic', 'storyworld', 'Youth Spark', 100, 10),
('LEGENDARY_MENTOR', 'Legendary Mentor', 'Master of youth development', '👑', '#F39C12', 'legendary', 'storyworld', 'Youth Spark', 250, 25);

-- Healthy Together badges
INSERT INTO badge_definitions (badge_key, name, description, icon, color, rarity, category, storyworld, required_hours, points) VALUES
('FITNESS_FRIEND', 'Fitness Friend', 'Promoting health and wellness', '💪', '#27AE60', 'common', 'storyworld', 'Healthy Together', 10, 1),
('WELLNESS_GUIDE', 'Wellness Guide', 'Guiding others to better health', '🏃', '#3498DB', 'uncommon', 'storyworld', 'Healthy Together', 25, 2),
('HEALTH_CHAMPION', 'Health Champion', 'Champion of community health', '🏅', '#9B59B6', 'rare', 'storyworld', 'Healthy Together', 50, 5),
('FITNESS_MASTER', 'Fitness Master', 'Master of fitness and wellness', '🥇', '#E74C3C', 'epic', 'storyworld', 'Healthy Together', 100, 10),
('WELLNESS_LEGEND', 'Wellness Legend', 'Legendary wellness advocate', '⭐', '#F39C12', 'legendary', 'storyworld', 'Healthy Together', 250, 25);

-- Water & Wellness badges
INSERT INTO badge_definitions (badge_key, name, description, icon, color, rarity, category, storyworld, required_hours, points) VALUES
('POOL_HELPER', 'Pool Helper', 'Supporting aquatic programs', '🏊', '#3498DB', 'common', 'storyworld', 'Water & Wellness', 10, 1),
('SWIM_SUPPORTER', 'Swim Supporter', 'Champion of aquatic safety', '🌊', '#2ECC71', 'uncommon', 'storyworld', 'Water & Wellness', 25, 2),
('AQUATIC_ACE', 'Aquatic Ace', 'Expert in water safety and programs', '🏆', '#9B59B6', 'rare', 'storyworld', 'Water & Wellness', 50, 5),
('LIFEGUARD_LEADER', 'Lifeguard Leader', 'Leader in aquatic safety', '🚨', '#E74C3C', 'epic', 'storyworld', 'Water & Wellness', 100, 10),
('AQUATIC_LEGEND', 'Aquatic Legend', 'Legendary aquatic volunteer', '🌟', '#F39C12', 'legendary', 'storyworld', 'Water & Wellness', 250, 25);

-- Neighbor Power badges
INSERT INTO badge_definitions (badge_key, name, description, icon, color, rarity, category, storyworld, required_hours, points) VALUES
('NEIGHBOR_FRIEND', 'Neighbor Friend', 'Building community connections', '🤝', '#27AE60', 'common', 'storyworld', 'Neighbor Power', 10, 1),
('COMMUNITY_HELPER', 'Community Helper', 'Helping neighbors in need', '🏘️', '#3498DB', 'uncommon', 'storyworld', 'Neighbor Power', 25, 2),
('OUTREACH_CHAMPION', 'Outreach Champion', 'Champion of community outreach', '🌍', '#9B59B6', 'rare', 'storyworld', 'Neighbor Power', 50, 5),
('COMMUNITY_LEADER', 'Community Leader', 'Leader in community building', '👨‍👩‍👧‍👦', '#E74C3C', 'epic', 'storyworld', 'Neighbor Power', 100, 10),
('NEIGHBORHOOD_LEGEND', 'Neighborhood Legend', 'Legendary community builder', '🏛️', '#F39C12', 'legendary', 'storyworld', 'Neighbor Power', 250, 25);

-- Sports badges
INSERT INTO badge_definitions (badge_key, name, description, icon, color, rarity, category, storyworld, required_hours, points) VALUES
('SPORTS_STARTER', 'Sports Starter', 'Getting active in sports programs', '⚽', '#E67E22', 'common', 'storyworld', 'Sports', 10, 1),
('TEAM_PLAYER', 'Team Player', 'Supporting athletic teams', '🏀', '#3498DB', 'uncommon', 'storyworld', 'Sports', 25, 2),
('COACHING_ACE', 'Coaching Ace', 'Excellent coaching and leadership', '🏅', '#9B59B6', 'rare', 'storyworld', 'Sports', 50, 5),
('SPORTS_LEADER', 'Sports Leader', 'Leader in athletic programs', '🥇', '#E74C3C', 'epic', 'storyworld', 'Sports', 100, 10),
('ATHLETIC_LEGEND', 'Athletic Legend', 'Legendary sports volunteer', '👑', '#F39C12', 'legendary', 'storyworld', 'Sports', 250, 25);

-- Special achievement badges
INSERT INTO badge_definitions (badge_key, name, description, icon, color, rarity, category, required_categories, points) VALUES
('MULTI_TALENT', 'Multi-Talent Master', 'Active in multiple storyworlds', '🌈', '#8E44AD', 'epic', 'special', 3, 10),
('CONSISTENCY_CHAMPION', 'Consistency Champion', 'Consistent volunteer over time', '📅', '#16A085', 'rare', 'special', 0, 5),
('EARLY_BIRD', 'Early Bird', 'Early morning volunteer hero', '🌅', '#F39C12', 'uncommon', 'special', 0, 2),
('NIGHT_OWL', 'Night Owl', 'Evening volunteer champion', '🦉', '#8E44AD', 'uncommon', 'special', 0, 2),
('WEEKEND_WARRIOR', 'Weekend Warrior', 'Weekend volunteer dedication', '🏋️', '#E67E22', 'uncommon', 'special', 0, 2),
('HOLIDAY_HERO', 'Holiday Hero', 'Volunteering during holidays', '🎄', '#C0392B', 'rare', 'special', 0, 5),
('MILESTONE_MASTER', 'Milestone Master', 'Achieved all major milestones', '💎', '#2C3E50', 'legendary', 'special', 0, 25);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_volunteer_badges_volunteer_id ON volunteer_badges(volunteer_id);
CREATE INDEX IF NOT EXISTS idx_volunteer_badges_badge_id ON volunteer_badges(badge_id);
CREATE INDEX IF NOT EXISTS idx_volunteer_badges_earned_at ON volunteer_badges(earned_at);
CREATE INDEX IF NOT EXISTS idx_volunteer_storyworlds_volunteer_id ON volunteer_storyworlds(volunteer_id);
CREATE INDEX IF NOT EXISTS idx_achievement_history_volunteer_id ON achievement_history(volunteer_id);
CREATE INDEX IF NOT EXISTS idx_achievement_history_achieved_at ON achievement_history(achieved_at);
CREATE INDEX IF NOT EXISTS idx_volunteer_recommendations_volunteer_id ON volunteer_recommendations(volunteer_id);
CREATE INDEX IF NOT EXISTS idx_badge_definitions_category ON badge_definitions(category);
CREATE INDEX IF NOT EXISTS idx_badge_definitions_rarity ON badge_definitions(rarity);

-- Create triggers to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_volunteer_profiles_updated_at 
    BEFORE UPDATE ON volunteer_profiles 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();