"""
Supabase Database Integration for Volunteer PathFinder
Handles user sessions, volunteer profiles, and conversation history
"""
from supabase import create_client, Client
from config import settings
from typing import Dict, List, Optional, Any
import json
import uuid
from datetime import datetime, timedelta
import pandas as pd
import asyncio
import logging

logger = logging.getLogger(__name__)

class VolunteerDatabase:
    def __init__(self):
        """Initialize Supabase clients with proper error handling"""
        try:
            if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                logger.warning("Supabase credentials not configured. Database features will be disabled.")
                self.supabase = None
                self.service_client = None
                return
            
            # Initialize clients (using current supabase-py format)
            self.supabase: Client = create_client(
                settings.SUPABASE_URL, 
                settings.SUPABASE_KEY
            )
            
            # Service client for admin operations
            if settings.SUPABASE_SERVICE_KEY:
                self.service_client: Client = create_client(
                    settings.SUPABASE_URL, 
                    settings.SUPABASE_SERVICE_KEY
                )
            else:
                self.service_client = self.supabase
                
            logger.info("Supabase clients initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase clients: {e}")
            self.supabase = None
            self.service_client = None
    
    def _is_available(self) -> bool:
        """Check if database is available"""
        return self.supabase is not None
        
    async def initialize_tables(self):
        """Initialize database tables (run this once to set up schema)"""
        
        # Users table
        users_sql = """
        CREATE TABLE IF NOT EXISTS users (
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
        """
        
        # User preferences table
        preferences_sql = """
        CREATE TABLE IF NOT EXISTS user_preferences (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            interests TEXT,
            skills TEXT,
            availability JSONB,
            time_commitment INTEGER, -- 1=low, 2=medium, 3=high
            location_preference VARCHAR(100),
            experience_level INTEGER, -- 1=beginner, 2=some, 3=experienced
            volunteer_type VARCHAR(50),
            preferences_data JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Conversations table
        conversations_sql = """
        CREATE TABLE IF NOT EXISTS conversations (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            session_id VARCHAR(100),
            conversation_data JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Messages table
        messages_sql = """
        CREATE TABLE IF NOT EXISTS messages (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
            user_id UUID,
            role VARCHAR(20), -- 'user' or 'assistant'
            content TEXT,
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Volunteer matches table
        matches_sql = """
        CREATE TABLE IF NOT EXISTS volunteer_matches (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            project_id INTEGER,
            project_name VARCHAR(200),
            branch VARCHAR(100),
            category VARCHAR(100),
            match_score DECIMAL(3,2),
            reasons JSONB,
            status VARCHAR(20) DEFAULT 'suggested', -- 'suggested', 'interested', 'applied', 'matched'
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Volunteer feedback table
        feedback_sql = """
        CREATE TABLE IF NOT EXISTS volunteer_feedback (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            match_id UUID REFERENCES volunteer_matches(id) ON DELETE CASCADE,
            rating INTEGER, -- 1-5 rating
            feedback_text TEXT,
            feedback_type VARCHAR(20), -- 'recommendation', 'experience', 'general'
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Analytics table
        analytics_sql = """
        CREATE TABLE IF NOT EXISTS analytics_events (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID,
            session_id VARCHAR(100),
            event_type VARCHAR(50),
            event_data JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Events table for RSVP system
        events_sql = """
        CREATE TABLE IF NOT EXISTS events (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            event_date TIMESTAMP WITH TIME ZONE NOT NULL,
            end_date TIMESTAMP WITH TIME ZONE,
            location VARCHAR(200),
            branch VARCHAR(100),
            category VARCHAR(100),
            max_participants INTEGER,
            contact_email VARCHAR(255),
            contact_phone VARCHAR(20),
            requirements JSONB,
            created_by UUID REFERENCES users(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # RSVPs table
        rsvps_sql = """
        CREATE TABLE IF NOT EXISTS rsvps (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            event_id UUID REFERENCES events(id) ON DELETE CASCADE,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            email VARCHAR(255) NOT NULL,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            status VARCHAR(20) DEFAULT 'confirmed', -- 'confirmed', 'tentative', 'declined', 'cancelled'
            calendar_invite_sent BOOLEAN DEFAULT FALSE,
            calendar_invite_id VARCHAR(255),
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(event_id, email)
        );
        """
        
        # Reminders table
        reminders_sql = """
        CREATE TABLE IF NOT EXISTS reminders (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            rsvp_id UUID REFERENCES rsvps(id) ON DELETE CASCADE,
            reminder_type VARCHAR(50), -- 'email', 'sms', 'calendar'
            reminder_time TIMESTAMP WITH TIME ZONE NOT NULL,
            sent BOOLEAN DEFAULT FALSE,
            sent_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Execute table creation (Note: In production, use proper migrations)
        tables = [users_sql, preferences_sql, conversations_sql, messages_sql, matches_sql, feedback_sql, analytics_sql, events_sql, rsvps_sql, reminders_sql]
        
        print("🗄️  Setting up database tables...")
        for sql in tables:
            try:
                # Note: Supabase doesn't support direct SQL execution via Python client for DDL
                # In production, run these manually in Supabase SQL editor
                print(f"  📝 Table SQL prepared: {sql.split('(')[0].split()[-1]}")
            except Exception as e:
                print(f"  ⚠️  Table setup note: {e}")
        
        print("✅ Database schema ready! Run SQL commands in Supabase dashboard.")
    
    # User Management
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new user"""
        if not self._is_available():
            logger.warning("Database not available, skipping user creation")
            return None
            
        try:
            # Add timestamp
            user_data['created_at'] = datetime.now().isoformat()
            user_data['updated_at'] = datetime.now().isoformat()
            
            response = self.supabase.table('users').insert(user_data).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"✅ Created user: {user_data.get('email', 'unknown')}")
                return response.data[0]
            else:
                logger.error(f"Failed to create user: {response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating user: {e}")
            return None
    
    async def get_user(self, user_id: str = None, email: str = None) -> Optional[Dict[str, Any]]:
        """Get user by ID or email"""
        try:
            query = self.supabase.table('users')
            
            if user_id:
                result = query.eq('id', user_id).execute()
            elif email:
                result = query.eq('email', email).execute()
            else:
                return None
            
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            print(f"❌ Error getting user: {e}")
            return None
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user information"""
        try:
            updates['updated_at'] = datetime.now().isoformat()
            result = self.supabase.table('users').update(updates).eq('id', user_id).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"❌ Error updating user: {e}")
            return False
    
    # User Preferences
    async def save_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Save or update user preferences"""
        try:
            # Check if preferences exist
            existing = self.supabase.table('user_preferences').eq('user_id', user_id).execute()
            
            preference_data = {
                'user_id': user_id,
                'interests': preferences.get('interests', ''),
                'skills': preferences.get('skills', ''),
                'availability': json.dumps(preferences.get('availability', {})),
                'time_commitment': preferences.get('time_commitment', 2),
                'location_preference': preferences.get('location_preference', ''),
                'experience_level': preferences.get('experience_level', 1),
                'volunteer_type': preferences.get('volunteer_type', ''),
                'preferences_data': json.dumps(preferences),
                'updated_at': datetime.now().isoformat()
            }
            
            if existing.data:
                # Update existing
                result = self.supabase.table('user_preferences').update(preference_data).eq('user_id', user_id).execute()
            else:
                # Create new
                preference_data['created_at'] = datetime.now().isoformat()
                result = self.supabase.table('user_preferences').insert(preference_data).execute()
            
            return len(result.data) > 0
        except Exception as e:
            print(f"❌ Error saving preferences: {e}")
            return False
    
    async def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user preferences"""
        try:
            result = self.supabase.table('user_preferences').eq('user_id', user_id).execute()
            if result.data:
                prefs = result.data[0]
                # Parse JSON fields
                if prefs.get('availability'):
                    prefs['availability'] = json.loads(prefs['availability'])
                if prefs.get('preferences_data'):
                    prefs['preferences_data'] = json.loads(prefs['preferences_data'])
                return prefs
            return None
        except Exception as e:
            print(f"❌ Error getting preferences: {e}")
            return None
    
    # Conversations
    async def create_conversation(self, user_id: str = None, session_id: str = None) -> str:
        """Create a new conversation"""
        try:
            conversation_id = str(uuid.uuid4())
            
            conversation_data = {
                'id': conversation_id,
                'user_id': user_id,
                'session_id': session_id or str(uuid.uuid4()),
                'conversation_data': json.dumps({}),
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('conversations').insert(conversation_data).execute()
            if result.data:
                return conversation_id
            return conversation_id  # Return ID even if insert fails
        except Exception as e:
            print(f"❌ Error creating conversation: {e}")
            return str(uuid.uuid4())  # Fallback ID
    
    async def save_message(self, conversation_id: str, role: str, content: str, 
                          user_id: str = None, metadata: Dict[str, Any] = None) -> bool:
        """Save a message to the conversation"""
        try:
            message_data = {
                'conversation_id': conversation_id,
                'user_id': user_id,
                'role': role,
                'content': content,
                'metadata': json.dumps(metadata or {}),
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('messages').insert(message_data).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"❌ Error saving message: {e}")
            return False
    
    async def get_conversation_history(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history"""
        try:
            result = self.supabase.table('messages')\
                .select('*')\
                .eq('conversation_id', conversation_id)\
                .order('created_at')\
                .limit(limit)\
                .execute()
            
            messages = []
            for msg in result.data:
                if msg.get('metadata'):
                    msg['metadata'] = json.loads(msg['metadata'])
                messages.append(msg)
            
            return messages
        except Exception as e:
            print(f"❌ Error getting conversation history: {e}")
            return []
    
    # Volunteer Matches
    async def save_volunteer_matches(self, user_id: str, matches: List[Dict[str, Any]]) -> bool:
        """Save volunteer matches for a user"""
        try:
            # Clear existing matches for this user
            self.supabase.table('volunteer_matches').delete().eq('user_id', user_id).execute()
            
            # Insert new matches
            match_data = []
            for match in matches:
                match_record = {
                    'user_id': user_id,
                    'project_id': match.get('project_id'),
                    'project_name': match.get('project_name', ''),
                    'branch': match.get('branch', ''),
                    'category': match.get('category', ''),
                    'match_score': match.get('score', 0.0),
                    'reasons': json.dumps(match.get('reasons', [])),
                    'created_at': datetime.now().isoformat()
                }
                match_data.append(match_record)
            
            if match_data:
                result = self.supabase.table('volunteer_matches').insert(match_data).execute()
                return len(result.data) > 0
            
            return True
        except Exception as e:
            print(f"❌ Error saving matches: {e}")
            return False
    
    async def get_user_matches(self, user_id: str, status: str = None) -> List[Dict[str, Any]]:
        """Get volunteer matches for a user"""
        try:
            query = self.supabase.table('volunteer_matches').select('*').eq('user_id', user_id)
            
            if status:
                query = query.eq('status', status)
            
            result = query.order('match_score', desc=True).execute()
            
            matches = []
            for match in result.data:
                if match.get('reasons'):
                    match['reasons'] = json.loads(match['reasons'])
                matches.append(match)
            
            return matches
        except Exception as e:
            print(f"❌ Error getting matches: {e}")
            return []
    
    async def update_match_status(self, match_id: str, status: str) -> bool:
        """Update the status of a volunteer match"""
        try:
            result = self.supabase.table('volunteer_matches')\
                .update({'status': status, 'updated_at': datetime.now().isoformat()})\
                .eq('id', match_id)\
                .execute()
            
            return len(result.data) > 0
        except Exception as e:
            print(f"❌ Error updating match status: {e}")
            return False
    
    # Feedback
    async def save_feedback(self, user_id: str, feedback_data: Dict[str, Any]) -> bool:
        """Save user feedback"""
        try:
            feedback_record = {
                'user_id': user_id,
                'match_id': feedback_data.get('match_id'),
                'rating': feedback_data.get('rating'),
                'feedback_text': feedback_data.get('feedback_text', ''),
                'feedback_type': feedback_data.get('feedback_type', 'general'),
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('volunteer_feedback').insert(feedback_record).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"❌ Error saving feedback: {e}")
            return False
    
    # Analytics
    async def track_event(self, event_type: str, event_data: Dict[str, Any] = None, 
                         user_id: str = None, session_id: str = None) -> bool:
        """Track analytics event"""
        try:
            event_record = {
                'user_id': user_id,
                'session_id': session_id,
                'event_type': event_type,
                'event_data': json.dumps(event_data or {}),
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('analytics_events').insert(event_record).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"❌ Error tracking event: {e}")
            return False
    
    # Analytics Queries
    async def get_user_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get user analytics for the past N days"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Total users
            users_result = self.supabase.table('users')\
                .select('id', count='exact')\
                .gte('created_at', start_date)\
                .execute()
            
            # Conversations
            conversations_result = self.supabase.table('conversations')\
                .select('id', count='exact')\
                .gte('created_at', start_date)\
                .execute()
            
            # Messages
            messages_result = self.supabase.table('messages')\
                .select('id', count='exact')\
                .gte('created_at', start_date)\
                .execute()
            
            # Matches created
            matches_result = self.supabase.table('volunteer_matches')\
                .select('id', count='exact')\
                .gte('created_at', start_date)\
                .execute()
            
            return {
                'period_days': days,
                'new_users': users_result.count,
                'conversations': conversations_result.count,
                'messages': messages_result.count,
                'matches_created': matches_result.count,
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"❌ Error getting analytics: {e}")
            return {}
    
    async def get_popular_matches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular volunteer matches"""
        try:
            result = self.supabase.table('volunteer_matches')\
                .select('project_name', 'branch', 'category')\
                .order('match_score', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data
        except Exception as e:
            print(f"❌ Error getting popular matches: {e}")
            return []
    
    # Data Export
    async def export_volunteer_data(self) -> Dict[str, pd.DataFrame]:
        """Export all volunteer data for analysis"""
        try:
            tables = {}
            
            # Users
            users_result = self.supabase.table('users').select('*').execute()
            tables['users'] = pd.DataFrame(users_result.data)
            
            # Preferences
            prefs_result = self.supabase.table('user_preferences').select('*').execute()
            tables['preferences'] = pd.DataFrame(prefs_result.data)
            
            # Matches
            matches_result = self.supabase.table('volunteer_matches').select('*').execute()
            tables['matches'] = pd.DataFrame(matches_result.data)
            
            # Messages
            messages_result = self.supabase.table('messages').select('*').execute()
            tables['messages'] = pd.DataFrame(messages_result.data)
            
            # Feedback
            feedback_result = self.supabase.table('volunteer_feedback').select('*').execute()
            tables['feedback'] = pd.DataFrame(feedback_result.data)
            
            print(f"📊 Exported data: {len(tables)} tables")
            return tables
        except Exception as e:
            print(f"❌ Error exporting data: {e}")
            return {}
    
    # RSVP System Methods
    async def create_event(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new event"""
        if not self._is_available():
            logger.warning("Database not available, skipping event creation")
            return None
            
        try:
            event_data['created_at'] = datetime.now().isoformat()
            event_data['updated_at'] = datetime.now().isoformat()
            
            response = self.supabase.table('events').insert(event_data).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"✅ Created event: {event_data.get('title', 'unknown')}")
                return response.data[0]
            else:
                logger.error(f"Failed to create event: {response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating event: {e}")
            return None
    
    async def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get an event by ID"""
        if not self._is_available():
            return None
            
        try:
            response = self.supabase.table('events').select('*').eq('id', event_id).single().execute()
            return response.data if response.data else None
        except Exception as e:
            logger.error(f"❌ Error getting event: {e}")
            return None
    
    async def get_events(self, branch: str = None, upcoming_only: bool = True) -> List[Dict[str, Any]]:
        """Get events, optionally filtered by branch"""
        if not self._is_available():
            return []
            
        try:
            query = self.supabase.table('events').select('*')
            
            if branch:
                query = query.eq('branch', branch)
                
            if upcoming_only:
                query = query.gte('event_date', datetime.now().isoformat())
            
            response = query.order('event_date').execute()
            return response.data or []
        except Exception as e:
            logger.error(f"❌ Error getting events: {e}")
            return []
    
    async def create_rsvp(self, rsvp_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new RSVP"""
        if not self._is_available():
            logger.warning("Database not available, skipping RSVP creation")
            return None
            
        try:
            rsvp_data['created_at'] = datetime.now().isoformat()
            rsvp_data['updated_at'] = datetime.now().isoformat()
            
            response = self.supabase.table('rsvps').insert(rsvp_data).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"✅ Created RSVP: {rsvp_data.get('email', 'unknown')}")
                return response.data[0]
            else:
                logger.error(f"Failed to create RSVP: {response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating RSVP: {e}")
            return None
    
    async def get_rsvp(self, event_id: str, email: str) -> Optional[Dict[str, Any]]:
        """Get an RSVP by event and email"""
        if not self._is_available():
            return None
            
        try:
            response = self.supabase.table('rsvps')\
                .select('*')\
                .eq('event_id', event_id)\
                .eq('email', email)\
                .single()\
                .execute()
            return response.data if response.data else None
        except Exception as e:
            logger.error(f"❌ Error getting RSVP: {e}")
            return None
    
    async def get_event_rsvps(self, event_id: str) -> List[Dict[str, Any]]:
        """Get all RSVPs for an event"""
        if not self._is_available():
            return []
            
        try:
            response = self.supabase.table('rsvps')\
                .select('*')\
                .eq('event_id', event_id)\
                .order('created_at')\
                .execute()
            return response.data or []
        except Exception as e:
            logger.error(f"❌ Error getting event RSVPs: {e}")
            return []
    
    async def update_rsvp_status(self, rsvp_id: str, status: str) -> bool:
        """Update RSVP status"""
        if not self._is_available():
            return False
            
        try:
            response = self.supabase.table('rsvps')\
                .update({'status': status, 'updated_at': datetime.now().isoformat()})\
                .eq('id', rsvp_id)\
                .execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"❌ Error updating RSVP status: {e}")
            return False
    
    async def mark_calendar_invite_sent(self, rsvp_id: str, calendar_invite_id: str = None) -> bool:
        """Mark calendar invite as sent"""
        if not self._is_available():
            return False
            
        try:
            update_data = {
                'calendar_invite_sent': True,
                'updated_at': datetime.now().isoformat()
            }
            if calendar_invite_id:
                update_data['calendar_invite_id'] = calendar_invite_id
                
            response = self.supabase.table('rsvps')\
                .update(update_data)\
                .eq('id', rsvp_id)\
                .execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"❌ Error marking calendar invite sent: {e}")
            return False
    
    async def create_reminder(self, reminder_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a reminder"""
        if not self._is_available():
            return None
            
        try:
            reminder_data['created_at'] = datetime.now().isoformat()
            
            response = self.supabase.table('reminders').insert(reminder_data).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"✅ Created reminder: {reminder_data.get('reminder_type', 'unknown')}")
                return response.data[0]
            else:
                logger.error(f"Failed to create reminder: {response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating reminder: {e}")
            return None
    
    async def get_pending_reminders(self) -> List[Dict[str, Any]]:
        """Get reminders that need to be sent"""
        if not self._is_available():
            return []
            
        try:
            response = self.supabase.table('reminders')\
                .select('*, rsvps(*, events(*))')\
                .eq('sent', False)\
                .lte('reminder_time', datetime.now().isoformat())\
                .execute()
            return response.data or []
        except Exception as e:
            logger.error(f"❌ Error getting pending reminders: {e}")
            return []
    
    async def mark_reminder_sent(self, reminder_id: str) -> bool:
        """Mark reminder as sent"""
        if not self._is_available():
            return False
            
        try:
            response = self.supabase.table('reminders')\
                .update({'sent': True, 'sent_at': datetime.now().isoformat()})\
                .eq('id', reminder_id)\
                .execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"❌ Error marking reminder sent: {e}")
            return False

# Usage example and testing
async def test_database():
    """Test database functionality"""
    db = VolunteerDatabase()
    
    # Test user creation
    test_user = {
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'age': 25,
        'city': 'Cincinnati'
    }
    
    user = await db.create_user(test_user)
    if user:
        print(f"✅ Created test user: {user['id']}")
        
        # Test preferences
        preferences = {
            'interests': 'youth development, fitness',
            'availability': {'weekday': True, 'evening': True},
            'time_commitment': 2,
            'location_preference': 'Blue Ash'
        }
        
        await db.save_user_preferences(user['id'], preferences)
        print("✅ Saved preferences")
        
        # Test conversation
        conv_id = await db.create_conversation(user['id'])
        await db.save_message(conv_id, 'user', 'Hello, I want to volunteer!')
        await db.save_message(conv_id, 'assistant', 'Great! I can help you find opportunities.')
        print("✅ Saved conversation")
        
        # Test analytics
        await db.track_event('user_signup', {'source': 'web'}, user['id'])
        print("✅ Tracked event")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_database())
