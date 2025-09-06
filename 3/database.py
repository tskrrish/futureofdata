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
    
    # Course Management
    async def create_course(self, course_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new course"""
        if not self._is_available():
            logger.warning("Database not available, skipping course creation")
            return None
            
        try:
            course_data['created_at'] = datetime.now().isoformat()
            course_data['updated_at'] = datetime.now().isoformat()
            
            response = self.supabase.table('courses').insert(course_data).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"✅ Created course: {course_data.get('course_name', 'unknown')}")
                return response.data[0]
            else:
                logger.error(f"Failed to create course: {response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating course: {e}")
            return None
    
    async def get_course(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Get course by ID"""
        try:
            result = self.supabase.table('courses').select('*').eq('id', course_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"❌ Error getting course: {e}")
            return None
    
    async def get_courses(self, branch: str = None, category: str = None, status: str = None) -> List[Dict[str, Any]]:
        """Get courses with optional filters"""
        try:
            query = self.supabase.table('courses').select('*')
            
            if branch:
                query = query.eq('branch', branch)
            if category:
                query = query.eq('category', category)
            if status:
                query = query.eq('status', status)
            
            result = query.order('start_date').execute()
            return result.data or []
        except Exception as e:
            logger.error(f"❌ Error getting courses: {e}")
            return []
    
    async def update_course(self, course_id: str, updates: Dict[str, Any]) -> bool:
        """Update course information"""
        try:
            updates['updated_at'] = datetime.now().isoformat()
            result = self.supabase.table('courses').update(updates).eq('id', course_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"❌ Error updating course: {e}")
            return False

    # Course Enrollment Management
    async def enroll_user_in_course(self, user_id: str, course_id: str, 
                                  waitlist_priority: int = 5) -> Dict[str, Any]:
        """Enroll user in course or add to waitlist if full"""
        try:
            # Get course info
            course = await self.get_course(course_id)
            if not course:
                return {'success': False, 'message': 'Course not found'}
            
            # Check if user already enrolled/waitlisted
            existing = self.supabase.table('course_enrollments')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('course_id', course_id)\
                .execute()
            
            if existing.data:
                return {'success': False, 'message': 'User already enrolled or waitlisted'}
            
            # Check if course is full
            enrollment_status = 'enrolled'
            if course['current_enrolled'] >= course['max_capacity']:
                enrollment_status = 'waitlisted'
            
            enrollment_data = {
                'user_id': user_id,
                'course_id': course_id,
                'enrollment_status': enrollment_status,
                'waitlist_priority': waitlist_priority,
                'enrollment_date': datetime.now().isoformat()
            }
            
            result = self.supabase.table('course_enrollments').insert(enrollment_data).execute()
            
            if result.data:
                # Log the enrollment
                await self.log_waitlist_action(
                    course_id, user_id, 
                    'enrolled' if enrollment_status == 'enrolled' else 'waitlisted',
                    None, enrollment_status,
                    f"User {'enrolled' if enrollment_status == 'enrolled' else 'added to waitlist'}"
                )
                
                return {
                    'success': True, 
                    'status': enrollment_status,
                    'enrollment': result.data[0]
                }
            
            return {'success': False, 'message': 'Failed to enroll user'}
            
        except Exception as e:
            logger.error(f"❌ Error enrolling user: {e}")
            return {'success': False, 'message': f'Error: {e}'}
    
    async def drop_user_from_course(self, user_id: str, course_id: str, reason: str = 'user_dropped') -> bool:
        """Drop user from course and trigger auto-backfill"""
        try:
            # Update enrollment status
            result = self.supabase.table('course_enrollments')\
                .update({'enrollment_status': 'dropped', 'updated_at': datetime.now().isoformat()})\
                .eq('user_id', user_id)\
                .eq('course_id', course_id)\
                .execute()
            
            if result.data:
                # Log the action
                await self.log_waitlist_action(
                    course_id, user_id, 'dropped', 'enrolled', 'dropped', reason
                )
                
                # Trigger auto-backfill
                await self.auto_backfill_course(course_id, reason)
                return True
            
            return False
        except Exception as e:
            logger.error(f"❌ Error dropping user: {e}")
            return False
    
    async def mark_no_show(self, user_id: str, course_id: str) -> bool:
        """Mark user as no-show and trigger auto-backfill"""
        try:
            result = self.supabase.table('course_enrollments')\
                .update({'enrollment_status': 'no_show', 'updated_at': datetime.now().isoformat()})\
                .eq('user_id', user_id)\
                .eq('course_id', course_id)\
                .execute()
            
            if result.data:
                # Log the action
                await self.log_waitlist_action(
                    course_id, user_id, 'no_show', 'enrolled', 'no_show', 
                    'Marked as no-show, auto-backfilling from waitlist'
                )
                
                # Trigger auto-backfill
                await self.auto_backfill_course(course_id, 'no_show')
                return True
            
            return False
        except Exception as e:
            logger.error(f"❌ Error marking no-show: {e}")
            return False

    # Waitlist Management
    async def get_waitlist_candidates(self, course_id: str) -> List[Dict[str, Any]]:
        """Get waitlisted candidates ordered by priority and enrollment date"""
        try:
            result = self.supabase.table('course_enrollments')\
                .select('*, users(*)')\
                .eq('course_id', course_id)\
                .eq('enrollment_status', 'waitlisted')\
                .order('waitlist_priority')\
                .order('enrollment_date')\
                .execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"❌ Error getting waitlist candidates: {e}")
            return []
    
    async def auto_backfill_course(self, course_id: str, trigger_reason: str) -> Dict[str, Any]:
        """Auto-backfill course from waitlist when spot becomes available"""
        try:
            # Get course info
            course = await self.get_course(course_id)
            if not course:
                return {'success': False, 'message': 'Course not found'}
            
            # Check if course has available spots
            available_spots = course['max_capacity'] - course['current_enrolled']
            if available_spots <= 0:
                return {'success': False, 'message': 'No available spots'}
            
            # Get waitlist candidates
            candidates = await self.get_waitlist_candidates(course_id)
            if not candidates:
                return {'success': False, 'message': 'No waitlist candidates'}
            
            enrolled_count = 0
            enrolled_users = []
            
            for candidate in candidates:
                if enrolled_count >= available_spots:
                    break
                
                # Move candidate from waitlist to enrolled
                update_result = self.supabase.table('course_enrollments')\
                    .update({
                        'enrollment_status': 'enrolled',
                        'waitlist_position': None,
                        'notification_sent': False,
                        'updated_at': datetime.now().isoformat()
                    })\
                    .eq('id', candidate['id'])\
                    .execute()
                
                if update_result.data:
                    enrolled_count += 1
                    enrolled_users.append({
                        'user_id': candidate['user_id'],
                        'user_name': f"{candidate['users']['first_name']} {candidate['users']['last_name']}",
                        'email': candidate['users']['email']
                    })
                    
                    # Log the auto-enrollment
                    await self.log_waitlist_action(
                        course_id, candidate['user_id'], 'auto_enrolled',
                        'waitlisted', 'enrolled',
                        f'Auto-enrolled from waitlist due to {trigger_reason}',
                        'system'
                    )
            
            # Update waitlist positions for remaining candidates
            await self.reorder_waitlist_positions(course_id)
            
            return {
                'success': True,
                'enrolled_count': enrolled_count,
                'enrolled_users': enrolled_users,
                'message': f'Auto-enrolled {enrolled_count} candidate(s) from waitlist'
            }
            
        except Exception as e:
            logger.error(f"❌ Error in auto-backfill: {e}")
            return {'success': False, 'message': f'Error: {e}'}
    
    async def reorder_waitlist_positions(self, course_id: str) -> bool:
        """Reorder waitlist positions after enrollment changes"""
        try:
            # Get all waitlisted candidates ordered by priority and date
            candidates = await self.get_waitlist_candidates(course_id)
            
            # Update positions sequentially
            for index, candidate in enumerate(candidates, 1):
                self.supabase.table('course_enrollments')\
                    .update({'waitlist_position': index, 'updated_at': datetime.now().isoformat()})\
                    .eq('id', candidate['id'])\
                    .execute()
            
            return True
        except Exception as e:
            logger.error(f"❌ Error reordering waitlist: {e}")
            return False

    # Audit Logging
    async def log_waitlist_action(self, course_id: str, user_id: str, action: str, 
                                previous_status: str, new_status: str, reason: str,
                                triggered_by: str = 'system', metadata: Dict = None) -> bool:
        """Log waitlist-related actions for audit trail"""
        try:
            log_entry = {
                'course_id': course_id,
                'user_id': user_id,
                'action': action,
                'previous_status': previous_status,
                'new_status': new_status,
                'reason': reason,
                'triggered_by': triggered_by,
                'metadata': json.dumps(metadata or {}),
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('waitlist_audit_log').insert(log_entry).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"❌ Error logging waitlist action: {e}")
            return False
    
    async def get_waitlist_audit_log(self, course_id: str = None, user_id: str = None, 
                                   days: int = 30) -> List[Dict[str, Any]]:
        """Get waitlist audit log with filters"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            query = self.supabase.table('waitlist_audit_log')\
                .select('*, courses(course_name), users(first_name, last_name, email)')\
                .gte('created_at', start_date)
            
            if course_id:
                query = query.eq('course_id', course_id)
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = query.order('created_at', desc=True).execute()
            
            # Parse metadata for each entry
            for entry in result.data:
                if entry.get('metadata'):
                    try:
                        entry['metadata'] = json.loads(entry['metadata'])
                    except:
                        entry['metadata'] = {}
            
            return result.data or []
        except Exception as e:
            logger.error(f"❌ Error getting audit log: {e}")
            return []

    # Notification Management
    async def get_users_needing_notification(self, course_id: str) -> List[Dict[str, Any]]:
        """Get newly enrolled users who need notifications"""
        try:
            result = self.supabase.table('course_enrollments')\
                .select('*, users(*), courses(*)')\
                .eq('course_id', course_id)\
                .eq('enrollment_status', 'enrolled')\
                .eq('notification_sent', False)\
                .execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"❌ Error getting users needing notification: {e}")
            return []
    
    async def mark_notification_sent(self, enrollment_id: str) -> bool:
        """Mark notification as sent for an enrollment"""
        try:
            result = self.supabase.table('course_enrollments')\
                .update({'notification_sent': True, 'updated_at': datetime.now().isoformat()})\
                .eq('id', enrollment_id)\
                .execute()
            
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"❌ Error marking notification sent: {e}")
            return False

    # Analytics and Reporting
    async def get_course_analytics(self, course_id: str = None, days: int = 30) -> Dict[str, Any]:
        """Get course enrollment analytics"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Base query
            query = self.supabase.table('course_enrollments').select('*', count='exact')
            if course_id:
                query = query.eq('course_id', course_id)
            
            # Total enrollments
            total_result = query.gte('created_at', start_date).execute()
            
            # Enrolled count
            enrolled_result = query.eq('enrollment_status', 'enrolled').execute()
            
            # Waitlisted count
            waitlisted_result = query.eq('enrollment_status', 'waitlisted').execute()
            
            # Dropped count
            dropped_result = query.eq('enrollment_status', 'dropped').execute()
            
            # Auto-enrollment stats from audit log
            auto_enroll_query = self.supabase.table('waitlist_audit_log')\
                .select('*', count='exact')\
                .eq('action', 'auto_enrolled')\
                .gte('created_at', start_date)
            
            if course_id:
                auto_enroll_query = auto_enroll_query.eq('course_id', course_id)
            
            auto_enroll_result = auto_enroll_query.execute()
            
            return {
                'period_days': days,
                'total_enrollments': total_result.count or 0,
                'enrolled': enrolled_result.count or 0,
                'waitlisted': waitlisted_result.count or 0,
                'dropped': dropped_result.count or 0,
                'auto_enrolled': auto_enroll_result.count or 0,
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Error getting course analytics: {e}")
            return {}
    
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
            
            # Course data
            courses_result = self.supabase.table('courses').select('*').execute()
            tables['courses'] = pd.DataFrame(courses_result.data)
            
            # Course enrollments
            enrollments_result = self.supabase.table('course_enrollments').select('*').execute()
            tables['course_enrollments'] = pd.DataFrame(enrollments_result.data)
            
            # Waitlist audit log
            audit_result = self.supabase.table('waitlist_audit_log').select('*').execute()
            tables['waitlist_audit_log'] = pd.DataFrame(audit_result.data)
            
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
