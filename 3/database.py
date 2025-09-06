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
        
        # Message templates table
        message_templates_sql = """
        CREATE TABLE IF NOT EXISTS message_templates (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            category VARCHAR(50), -- 'welcome', 'follow_up', 'reminder', 'thank_you', 'general'
            subject VARCHAR(200),
            content TEXT NOT NULL,
            merge_fields JSONB, -- Available merge fields for this template
            is_active BOOLEAN DEFAULT TRUE,
            created_by UUID REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Template usage tracking table
        template_usage_sql = """
        CREATE TABLE IF NOT EXISTS template_usage (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            template_id UUID REFERENCES message_templates(id) ON DELETE CASCADE,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            recipient_email VARCHAR(255),
            rendered_subject VARCHAR(200),
            rendered_content TEXT,
            merge_data JSONB, -- The actual data used for merge fields
            sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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
        
        # Task assignments table
        tasks_sql = """
        CREATE TABLE IF NOT EXISTS tasks (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            priority INTEGER DEFAULT 2, -- 1=low, 2=medium, 3=high, 4=urgent
            status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'cancelled'
            project_id INTEGER,
            category VARCHAR(100),
            estimated_hours DECIMAL(4,2),
            created_by UUID REFERENCES users(id),
            assigned_to UUID REFERENCES users(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            completed_at TIMESTAMP WITH TIME ZONE,
            
            -- Event-driven deadline fields
            deadline_type VARCHAR(20) DEFAULT 'fixed', -- 'fixed', 'event_based', 'flexible'
            fixed_deadline TIMESTAMP WITH TIME ZONE,
            event_trigger VARCHAR(100), -- e.g., 'volunteer_signup', 'project_start', 'event_date'
            deadline_offset_days INTEGER DEFAULT 0, -- Days relative to event trigger
            deadline_calculated TIMESTAMP WITH TIME ZONE, -- Computed deadline based on event
            
            -- Task metadata
            task_data JSONB,
            dependencies JSONB, -- Array of task IDs this task depends on
            tags JSONB -- Array of tags for categorization
        );
        """
        
        # Task assignments table (many-to-many relationship)
        assignments_sql = """
        CREATE TABLE IF NOT EXISTS task_assignments (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            assigned_by UUID REFERENCES users(id),
            assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            status VARCHAR(20) DEFAULT 'assigned', -- 'assigned', 'accepted', 'declined', 'completed'
            progress_percentage INTEGER DEFAULT 0,
            notes TEXT,
            time_logged DECIMAL(4,2) DEFAULT 0.0,
            last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            UNIQUE(task_id, user_id)
        );
        """
        
        # Events table for deadline triggers
        deadline_events_sql = """
        CREATE TABLE IF NOT EXISTS deadline_events (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            event_name VARCHAR(100) UNIQUE NOT NULL, -- e.g., 'volunteer_signup', 'project_start'
            event_date TIMESTAMP WITH TIME ZONE,
            event_data JSONB,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Task deadline history for tracking changes
        deadline_history_sql = """
        CREATE TABLE IF NOT EXISTS task_deadline_history (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
            old_deadline TIMESTAMP WITH TIME ZONE,
            new_deadline TIMESTAMP WITH TIME ZONE,
            change_reason VARCHAR(100), -- 'event_triggered', 'manual_update', 'dependency_change'
            changed_by UUID REFERENCES users(id),
            changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Task notifications for deadline alerts
        task_notifications_sql = """
        CREATE TABLE IF NOT EXISTS task_notifications (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            notification_type VARCHAR(50), -- 'deadline_approaching', 'overdue', 'assignment_new', 'status_change'
            message TEXT,
            is_read BOOLEAN DEFAULT false,
            sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            read_at TIMESTAMP WITH TIME ZONE
        );
        """
        
        # Execute table creation (Note: In production, use proper migrations)

        
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

                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            

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
    
    # Task Management Methods
    async def create_task(self, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new task with optional event-driven deadlines"""
        if not self._is_available():
            logger.warning("Database not available, skipping task creation")
            return None
            
        try:
            # Set timestamps
            task_data['created_at'] = datetime.now().isoformat()
            task_data['updated_at'] = datetime.now().isoformat()
            
            # Calculate deadline if event-based
            if task_data.get('deadline_type') == 'event_based':
                await self._calculate_event_deadline(task_data)
            
            response = self.supabase.table('tasks').insert(task_data).execute()
            
            if response.data and len(response.data) > 0:
                task = response.data[0]
                logger.info(f"✅ Created task: {task['title']}")
                
                # Create assignment if assigned_to is specified
                if task_data.get('assigned_to'):
                    await self.assign_task(task['id'], task_data['assigned_to'], task_data.get('created_by'))
                
                return task
            else:
                logger.error(f"Failed to create task: {response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating task: {e}")
            return None
    
    async def assign_task(self, task_id: str, user_id: str, assigned_by: str = None) -> bool:
        """Assign a task to a user"""
        try:
            assignment_data = {
                'task_id': task_id,
                'user_id': user_id,
                'assigned_by': assigned_by,
                'assigned_at': datetime.now().isoformat(),
                'status': 'assigned',
                'last_updated': datetime.now().isoformat()
            }
            
            # Use upsert to handle duplicate assignments
            result = self.supabase.table('task_assignments').upsert(assignment_data).execute()
            
            if result.data:
                # Create notification for the assigned user
                await self.create_task_notification(
                    task_id, user_id, 'assignment_new',
                    f"You have been assigned a new task"
                )
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error assigning task: {e}")
            return False
    
    async def update_task_status(self, task_id: str, status: str, user_id: str = None, progress: int = None) -> bool:
        """Update task status and optionally progress"""
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            if status == 'completed':
                update_data['completed_at'] = datetime.now().isoformat()
            
            # Update main task
            result = self.supabase.table('tasks').update(update_data).eq('id', task_id).execute()
            
            # Update assignment if user_id provided
            if user_id:
                assignment_update = {
                    'status': 'completed' if status == 'completed' else 'accepted',
                    'last_updated': datetime.now().isoformat()
                }
                if progress is not None:
                    assignment_update['progress_percentage'] = progress
                
                self.supabase.table('task_assignments')\
                    .update(assignment_update)\
                    .eq('task_id', task_id)\
                    .eq('user_id', user_id)\
                    .execute()
            
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"❌ Error updating task status: {e}")
            return False
    
    async def get_user_tasks(self, user_id: str, status: str = None, include_created: bool = False) -> List[Dict[str, Any]]:
        """Get tasks assigned to a user"""
        try:
            # Base query for assigned tasks
            query = self.supabase.table('tasks')\
                .select('*, task_assignments!inner(status, progress_percentage, assigned_at, time_logged)')\
                .eq('task_assignments.user_id', user_id)
            
            if status:
                query = query.eq('task_assignments.status', status)
            
            assigned_tasks = query.order('created_at', desc=True).execute()
            
            tasks = []
            for task in assigned_tasks.data:
                # Flatten assignment data
                assignment = task['task_assignments'][0] if task['task_assignments'] else {}
                task['assignment_status'] = assignment.get('status')
                task['progress_percentage'] = assignment.get('progress_percentage', 0)
                task['time_logged'] = assignment.get('time_logged', 0.0)
                task['assigned_at'] = assignment.get('assigned_at')
                del task['task_assignments']
                tasks.append(task)
            
            # Optionally include tasks created by user
            if include_created:
                created_tasks = self.supabase.table('tasks')\
                    .select('*')\
                    .eq('created_by', user_id)\
                    .execute()
                
                for task in created_tasks.data:
                    if not any(t['id'] == task['id'] for t in tasks):
                        task['assignment_status'] = 'created'
                        tasks.append(task)
            
            return tasks
        except Exception as e:
            logger.error(f"❌ Error getting user tasks: {e}")
            return []
    
    async def get_task_details(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed task information including assignments"""
        try:
            # Get task with assignments
            task_result = self.supabase.table('tasks')\
                .select('*, task_assignments(*, users(first_name, last_name, email))')\
                .eq('id', task_id)\
                .execute()
            
            if not task_result.data:
                return None
            
            task = task_result.data[0]
            
            # Get deadline history
            history_result = self.supabase.table('task_deadline_history')\
                .select('*')\
                .eq('task_id', task_id)\
                .order('changed_at', desc=True)\
                .execute()
            
            task['deadline_history'] = history_result.data
            
            return task
        except Exception as e:
            logger.error(f"❌ Error getting task details: {e}")
            return None
    
    async def create_deadline_event(self, event_name: str, event_date: datetime, event_data: Dict[str, Any] = None) -> bool:
        """Create or update a deadline trigger event"""
        try:
            event_record = {
                'event_name': event_name,
                'event_date': event_date.isoformat(),
                'event_data': json.dumps(event_data or {}),
                'is_active': True,
                'updated_at': datetime.now().isoformat()
            }
            
            # Use upsert to handle existing events
            result = self.supabase.table('deadline_events').upsert(event_record).execute()
            
            if result.data:
                # Recalculate deadlines for affected tasks
                await self._recalculate_event_deadlines(event_name)
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error creating deadline event: {e}")
            return False
    
    async def _calculate_event_deadline(self, task_data: Dict[str, Any]) -> None:
        """Calculate deadline based on event trigger"""
        try:
            event_trigger = task_data.get('event_trigger')
            offset_days = task_data.get('deadline_offset_days', 0)
            
            if event_trigger:
                # Get the event date
                event_result = self.supabase.table('deadline_events')\
                    .select('event_date')\
                    .eq('event_name', event_trigger)\
                    .eq('is_active', True)\
                    .execute()
                
                if event_result.data:
                    event_date = datetime.fromisoformat(event_result.data[0]['event_date'].replace('Z', '+00:00'))
                    calculated_deadline = event_date + timedelta(days=offset_days)
                    task_data['deadline_calculated'] = calculated_deadline.isoformat()
        except Exception as e:
            logger.error(f"❌ Error calculating event deadline: {e}")
    
    async def _recalculate_event_deadlines(self, event_name: str) -> None:
        """Recalculate deadlines for all tasks using this event trigger"""
        try:
            # Get all tasks that use this event trigger
            tasks_result = self.supabase.table('tasks')\
                .select('id, deadline_calculated, deadline_offset_days')\
                .eq('event_trigger', event_name)\
                .eq('deadline_type', 'event_based')\
                .execute()
            
            # Get the updated event date
            event_result = self.supabase.table('deadline_events')\
                .select('event_date')\
                .eq('event_name', event_name)\
                .eq('is_active', True)\
                .execute()
            
            if not event_result.data:
                return
            
            event_date = datetime.fromisoformat(event_result.data[0]['event_date'].replace('Z', '+00:00'))
            
            # Update deadlines for each task
            for task in tasks_result.data:
                offset_days = task.get('deadline_offset_days', 0)
                new_deadline = event_date + timedelta(days=offset_days)
                old_deadline = task.get('deadline_calculated')
                
                # Update the task
                self.supabase.table('tasks')\
                    .update({
                        'deadline_calculated': new_deadline.isoformat(),
                        'updated_at': datetime.now().isoformat()
                    })\
                    .eq('id', task['id'])\
                    .execute()
                
                # Record the deadline change
                if old_deadline != new_deadline.isoformat():
                    await self.record_deadline_change(
                        task['id'], old_deadline, new_deadline.isoformat(), 'event_triggered'
                    )
        except Exception as e:
            logger.error(f"❌ Error recalculating event deadlines: {e}")
    
    async def record_deadline_change(self, task_id: str, old_deadline: str, new_deadline: str, 
                                   reason: str, changed_by: str = None) -> bool:
        """Record a deadline change in history"""
        try:
            history_record = {
                'task_id': task_id,
                'old_deadline': old_deadline,
                'new_deadline': new_deadline,
                'change_reason': reason,
                'changed_by': changed_by,
                'changed_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('task_deadline_history').insert(history_record).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"❌ Error recording deadline change: {e}")
            return False
    
    async def create_task_notification(self, task_id: str, user_id: str, notification_type: str, message: str) -> bool:
        """Create a task notification for a user"""
        try:
            notification_data = {
                'task_id': task_id,
                'user_id': user_id,
                'notification_type': notification_type,
                'message': message,
                'is_read': False,
                'sent_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('task_notifications').insert(notification_data).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"❌ Error creating task notification: {e}")
            return False
    
    async def get_user_notifications(self, user_id: str, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get notifications for a user"""
        try:
            query = self.supabase.table('task_notifications')\
                .select('*, tasks(title)')\
                .eq('user_id', user_id)
            
            if unread_only:
                query = query.eq('is_read', False)
            
            result = query.order('sent_at', desc=True).execute()
            return result.data
        except Exception as e:
            logger.error(f"❌ Error getting user notifications: {e}")
            return []
    
    async def mark_notification_read(self, notification_id: str) -> bool:
        """Mark a notification as read"""
        try:
            result = self.supabase.table('task_notifications')\
                .update({
                    'is_read': True,
                    'read_at': datetime.now().isoformat()
                })\
                .eq('id', notification_id)\
                .execute()
            
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"❌ Error marking notification as read: {e}")
            return False
    
    async def get_overdue_tasks(self) -> List[Dict[str, Any]]:
        """Get all overdue tasks for deadline monitoring"""
        try:
            current_time = datetime.now().isoformat()
            
            # Get tasks with fixed deadlines
            fixed_overdue = self.supabase.table('tasks')\
                .select('*, task_assignments(user_id, users(first_name, last_name, email))')\
                .eq('deadline_type', 'fixed')\
                .lt('fixed_deadline', current_time)\
                .neq('status', 'completed')\
                .execute()
            
            # Get tasks with calculated deadlines
            calculated_overdue = self.supabase.table('tasks')\
                .select('*, task_assignments(user_id, users(first_name, last_name, email))')\
                .eq('deadline_type', 'event_based')\
                .lt('deadline_calculated', current_time)\
                .neq('status', 'completed')\
                .execute()
            
            # Combine results
            overdue_tasks = []
            if fixed_overdue.data:
                overdue_tasks.extend(fixed_overdue.data)
            if calculated_overdue.data:
                overdue_tasks.extend(calculated_overdue.data)
            
            return overdue_tasks
        except Exception as e:
            logger.error(f"❌ Error getting overdue tasks: {e}")
            return []

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
