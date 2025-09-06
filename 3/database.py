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
        
        # Execute table creation (Note: In production, use proper migrations)
        tables = [users_sql, preferences_sql, conversations_sql, messages_sql, matches_sql, feedback_sql, analytics_sql]
        
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
    
    # Dashboard Management
    async def create_dashboard(self, owner_id: str, dashboard_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new dashboard"""
        if not self._is_available():
            logger.warning("Database not available, skipping dashboard creation")
            return None
            
        try:
            dashboard_record = {
                'owner_id': owner_id,
                'title': dashboard_data.get('title', 'Untitled Dashboard'),
                'description': dashboard_data.get('description', ''),
                'dashboard_data': json.dumps(dashboard_data.get('dashboard_data', {})),
                'is_public': dashboard_data.get('is_public', False),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            response = self.supabase.table('dashboards').insert(dashboard_record).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"✅ Created dashboard: {dashboard_record['title']}")
                return response.data[0]
            else:
                logger.error(f"Failed to create dashboard: {response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating dashboard: {e}")
            return None
    
    async def get_dashboard(self, dashboard_id: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """Get dashboard by ID with permission check"""
        try:
            result = self.supabase.table('dashboards').select('*').eq('id', dashboard_id).execute()
            
            if not result.data:
                return None
                
            dashboard = result.data[0]
            
            # Parse JSON fields
            if dashboard.get('dashboard_data'):
                dashboard['dashboard_data'] = json.loads(dashboard['dashboard_data'])
            
            # Check permissions if user_id provided
            if user_id and user_id != dashboard['owner_id']:
                has_permission = await self.check_dashboard_permission(dashboard_id, user_id)
                if not has_permission and not dashboard.get('is_public', False):
                    return None
            
            return dashboard
        except Exception as e:
            logger.error(f"❌ Error getting dashboard: {e}")
            return None
    
    async def update_dashboard(self, dashboard_id: str, updates: Dict[str, Any], user_id: str) -> bool:
        """Update dashboard with permission check"""
        try:
            # Check if user has edit permission
            has_edit_permission = await self.check_dashboard_permission(dashboard_id, user_id, 'edit')
            if not has_edit_permission:
                # Check if user is owner
                dashboard = await self.get_dashboard(dashboard_id)
                if not dashboard or dashboard['owner_id'] != user_id:
                    logger.warning(f"User {user_id} doesn't have edit permission for dashboard {dashboard_id}")
                    return False
            
            # Prepare update data
            update_data = updates.copy()
            if 'dashboard_data' in update_data:
                update_data['dashboard_data'] = json.dumps(update_data['dashboard_data'])
            update_data['updated_at'] = datetime.now().isoformat()
            
            result = self.supabase.table('dashboards').update(update_data).eq('id', dashboard_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"❌ Error updating dashboard: {e}")
            return False
    
    async def delete_dashboard(self, dashboard_id: str, user_id: str) -> bool:
        """Delete dashboard (only owner can delete)"""
        try:
            # Check if user is owner
            dashboard = await self.get_dashboard(dashboard_id)
            if not dashboard or dashboard['owner_id'] != user_id:
                logger.warning(f"User {user_id} is not owner of dashboard {dashboard_id}")
                return False
            
            result = self.supabase.table('dashboards').delete().eq('id', dashboard_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"❌ Error deleting dashboard: {e}")
            return False
    
    async def get_user_dashboards(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all dashboards accessible to a user (owned + shared + public)"""
        try:
            dashboards = []
            
            # Get owned dashboards
            owned_result = self.supabase.table('dashboards').select('*').eq('owner_id', user_id).execute()
            for dashboard in owned_result.data:
                if dashboard.get('dashboard_data'):
                    dashboard['dashboard_data'] = json.loads(dashboard['dashboard_data'])
                dashboard['permission'] = 'owner'
                dashboards.append(dashboard)
            
            # Get shared dashboards
            shared_result = self.supabase.table('dashboard_permissions')\
                .select('*, dashboards(*)')\
                .eq('user_id', user_id)\
                .execute()
            
            for perm in shared_result.data:
                if perm.get('dashboards'):
                    dashboard = perm['dashboards']
                    if dashboard.get('dashboard_data'):
                        dashboard['dashboard_data'] = json.loads(dashboard['dashboard_data'])
                    dashboard['permission'] = perm['permission_type']
                    dashboard['shared_at'] = perm['created_at']
                    dashboards.append(dashboard)
            
            # Get public dashboards (excluding already included ones)
            existing_ids = {d['id'] for d in dashboards}
            public_result = self.supabase.table('dashboards')\
                .select('*')\
                .eq('is_public', True)\
                .execute()
            
            for dashboard in public_result.data:
                if dashboard['id'] not in existing_ids:
                    if dashboard.get('dashboard_data'):
                        dashboard['dashboard_data'] = json.loads(dashboard['dashboard_data'])
                    dashboard['permission'] = 'view'
                    dashboards.append(dashboard)
            
            return dashboards
        except Exception as e:
            logger.error(f"❌ Error getting user dashboards: {e}")
            return []
    
    # Dashboard Permissions
    async def share_dashboard(self, dashboard_id: str, user_email: str, permission_type: str, granted_by: str) -> bool:
        """Share dashboard with a user"""
        try:
            # Get user by email
            user = await self.get_user(email=user_email)
            if not user:
                logger.error(f"User not found: {user_email}")
                return False
            
            user_id = user['id']
            
            # Check if user is dashboard owner
            dashboard = await self.get_dashboard(dashboard_id)
            if not dashboard or dashboard['owner_id'] != granted_by:
                logger.warning(f"User {granted_by} is not owner of dashboard {dashboard_id}")
                return False
            
            # Check if permission already exists
            existing = self.supabase.table('dashboard_permissions')\
                .select('*')\
                .eq('dashboard_id', dashboard_id)\
                .eq('user_id', user_id)\
                .execute()
            
            permission_data = {
                'dashboard_id': dashboard_id,
                'user_id': user_id,
                'permission_type': permission_type,
                'granted_by': granted_by,
                'updated_at': datetime.now().isoformat()
            }
            
            if existing.data:
                # Update existing permission
                result = self.supabase.table('dashboard_permissions')\
                    .update(permission_data)\
                    .eq('dashboard_id', dashboard_id)\
                    .eq('user_id', user_id)\
                    .execute()
            else:
                # Create new permission
                permission_data['created_at'] = datetime.now().isoformat()
                result = self.supabase.table('dashboard_permissions')\
                    .insert(permission_data)\
                    .execute()
            
            if len(result.data) > 0:
                logger.info(f"✅ Shared dashboard {dashboard_id} with {user_email} ({permission_type})")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Error sharing dashboard: {e}")
            return False
    
    async def revoke_dashboard_access(self, dashboard_id: str, user_id: str, revoked_by: str) -> bool:
        """Revoke dashboard access"""
        try:
            # Check if revoker is dashboard owner
            dashboard = await self.get_dashboard(dashboard_id)
            if not dashboard or dashboard['owner_id'] != revoked_by:
                logger.warning(f"User {revoked_by} is not owner of dashboard {dashboard_id}")
                return False
            
            result = self.supabase.table('dashboard_permissions')\
                .delete()\
                .eq('dashboard_id', dashboard_id)\
                .eq('user_id', user_id)\
                .execute()
            
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"❌ Error revoking dashboard access: {e}")
            return False
    
    async def get_dashboard_permissions(self, dashboard_id: str, owner_id: str) -> List[Dict[str, Any]]:
        """Get all permissions for a dashboard"""
        try:
            # Check if user is dashboard owner
            dashboard = await self.get_dashboard(dashboard_id)
            if not dashboard or dashboard['owner_id'] != owner_id:
                logger.warning(f"User {owner_id} is not owner of dashboard {dashboard_id}")
                return []
            
            result = self.supabase.table('dashboard_permissions')\
                .select('*, users(first_name, last_name, email)')\
                .eq('dashboard_id', dashboard_id)\
                .execute()
            
            return result.data
        except Exception as e:
            logger.error(f"❌ Error getting dashboard permissions: {e}")
            return []
    
    async def check_dashboard_permission(self, dashboard_id: str, user_id: str, required_permission: str = 'view') -> bool:
        """Check if user has required permission for dashboard"""
        try:
            # Check if user is owner
            dashboard = await self.get_dashboard(dashboard_id)
            if dashboard and dashboard['owner_id'] == user_id:
                return True
            
            # Check if dashboard is public and only view permission required
            if dashboard and dashboard.get('is_public', False) and required_permission == 'view':
                return True
            
            # Check explicit permissions
            result = self.supabase.table('dashboard_permissions')\
                .select('permission_type')\
                .eq('dashboard_id', dashboard_id)\
                .eq('user_id', user_id)\
                .execute()
            
            if not result.data:
                return False
            
            user_permission = result.data[0]['permission_type']
            
            # Edit permission includes view permission
            if required_permission == 'view':
                return user_permission in ['view', 'edit']
            elif required_permission == 'edit':
                return user_permission == 'edit'
            
            return False
        except Exception as e:
            logger.error(f"❌ Error checking dashboard permission: {e}")
            return False
    
    # Dashboard Access Logging
    async def log_dashboard_access(self, dashboard_id: str, user_id: str, action: str, metadata: Dict[str, Any] = None) -> bool:
        """Log dashboard access"""
        try:
            log_data = {
                'dashboard_id': dashboard_id,
                'user_id': user_id,
                'action': action,
                'metadata': json.dumps(metadata or {}),
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('dashboard_access_logs').insert(log_data).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"❌ Error logging dashboard access: {e}")
            return False
    
    async def get_dashboard_access_logs(self, dashboard_id: str, owner_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get dashboard access logs (only for dashboard owner)"""
        try:
            # Check if user is dashboard owner
            dashboard = await self.get_dashboard(dashboard_id)
            if not dashboard or dashboard['owner_id'] != owner_id:
                logger.warning(f"User {owner_id} is not owner of dashboard {dashboard_id}")
                return []
            
            result = self.supabase.table('dashboard_access_logs')\
                .select('*, users(first_name, last_name, email)')\
                .eq('dashboard_id', dashboard_id)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            logs = []
            for log in result.data:
                if log.get('metadata'):
                    log['metadata'] = json.loads(log['metadata'])
                logs.append(log)
            
            return logs
        except Exception as e:
            logger.error(f"❌ Error getting dashboard access logs: {e}")
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
