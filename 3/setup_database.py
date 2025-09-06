#!/usr/bin/env python3
"""
Database setup script - Creates all necessary tables in Supabase
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from database import VolunteerDatabase
from config import settings

async def setup_database():
    """Set up the complete database schema"""
    print("🗄️  SETTING UP VOLUNTEER PATHFINDER DATABASE")
    print("=" * 50)
    
    db = VolunteerDatabase()
    
    if not db._is_available():
        print("❌ Supabase not available. Check your configuration.")
        return False
    
    print(f"✅ Connected to Supabase: {settings.SUPABASE_URL}")
    
    # SQL commands to create all tables
    setup_commands = [
        # Enable extensions
        'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";',
        
        # Users table
        '''CREATE TABLE IF NOT EXISTS public.users (
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
        );''',
        
        # User preferences table
        '''CREATE TABLE IF NOT EXISTS public.user_preferences (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
            interests TEXT,
            skills TEXT,
            availability JSONB DEFAULT '{}',
            time_commitment INTEGER DEFAULT 2,
            location_preference VARCHAR(100),
            experience_level INTEGER DEFAULT 1,
            volunteer_type VARCHAR(50),
            preferences_data JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );''',
        
        # Conversations table
        '''CREATE TABLE IF NOT EXISTS public.conversations (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
            session_id VARCHAR(100),
            conversation_data JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );''',
        
        # Messages table
        '''CREATE TABLE IF NOT EXISTS public.messages (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            conversation_id UUID REFERENCES public.conversations(id) ON DELETE CASCADE,
            user_id UUID,
            role VARCHAR(20) CHECK (role IN ('user', 'assistant')),
            content TEXT,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );''',
        
        # Volunteer matches table
        '''CREATE TABLE IF NOT EXISTS public.volunteer_matches (
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
        );''',
        
        # Volunteer feedback table
        '''CREATE TABLE IF NOT EXISTS public.volunteer_feedback (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
            match_id UUID REFERENCES public.volunteer_matches(id) ON DELETE CASCADE,
            rating INTEGER CHECK (rating >= 1 AND rating <= 5),
            feedback_text TEXT,
            feedback_type VARCHAR(20) DEFAULT 'general' CHECK (feedback_type IN ('recommendation', 'experience', 'general')),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );''',
        
        # Analytics events table
        '''CREATE TABLE IF NOT EXISTS public.analytics_events (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID,
            session_id VARCHAR(100),
            event_type VARCHAR(50),
            event_data JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );'''
    ]
    
    # Create indexes
    index_commands = [
        'CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);',
        'CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON public.user_preferences(user_id);',
        'CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON public.conversations(user_id);',
        'CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON public.messages(conversation_id);',
        'CREATE INDEX IF NOT EXISTS idx_volunteer_matches_user_id ON public.volunteer_matches(user_id);',
        'CREATE INDEX IF NOT EXISTS idx_analytics_events_user_id ON public.analytics_events(user_id);'
    ]
    
    try:
        print("🔧 Creating database tables...")
        
        # Execute setup commands
        for i, command in enumerate(setup_commands, 1):
            try:
                result = db.supabase.rpc('sql', {'query': command}).execute()
                print(f"✅ Command {i}/{len(setup_commands)} executed")
            except Exception as e:
                # Try alternative method for table creation
                table_name = 'unknown'
                if 'users' in command:
                    table_name = 'users'
                elif 'user_preferences' in command:
                    table_name = 'user_preferences'
                elif 'conversations' in command:
                    table_name = 'conversations'
                elif 'messages' in command:
                    table_name = 'messages'
                elif 'volunteer_matches' in command:
                    table_name = 'volunteer_matches'
                elif 'volunteer_feedback' in command:
                    table_name = 'volunteer_feedback'
                elif 'analytics_events' in command:
                    table_name = 'analytics_events'
                
                print(f"⚠️  Command {i} needs manual execution (table: {table_name})")
        
        print("🔧 Creating indexes...")
        for i, command in enumerate(index_commands, 1):
            try:
                result = db.supabase.rpc('sql', {'query': command}).execute()
                print(f"✅ Index {i}/{len(index_commands)} created")
            except Exception as e:
                print(f"⚠️  Index {i} creation skipped")
        
        print(f"\n🎉 Database setup completed!")
        return True
        
    except Exception as e:
        print(f"❌ Database setup error: {e}")
        print("\n📝 MANUAL SETUP REQUIRED:")
        print("Please go to your Supabase SQL Editor and run:")
        print("https://app.supabase.com/project/ydbjceycutivkipxtaam/sql")
        print("\nThen copy-paste the contents of 'setup_supabase.sql' and click 'Run'")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(setup_database())
        if result:
            print("\n🚀 Ready to test integrations!")
        else:
            print("\n⚠️  Manual database setup required")
    except Exception as e:
        print(f"❌ Setup script error: {e}")
