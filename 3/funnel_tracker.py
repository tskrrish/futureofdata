"""
Interest→Active Funnel Tracking System
Tracks volunteer journey from initial interest through activation
and measures intervention impact on conversion rates
"""
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import json
import pandas as pd
from dataclasses import dataclass
from database import VolunteerDatabase
import logging

logger = logging.getLogger(__name__)

class FunnelStage(Enum):
    """Stages in the volunteer interest→active funnel"""
    INTEREST_EXPRESSED = "interest_expressed"
    PROFILE_CREATED = "profile_created"
    MATCHED_OPPORTUNITIES = "matched_opportunities"
    APPLICATION_STARTED = "application_started"
    APPLICATION_SUBMITTED = "application_submitted"
    SCREENING_COMPLETED = "screening_completed"
    ORIENTATION_SCHEDULED = "orientation_scheduled"
    ORIENTATION_COMPLETED = "orientation_completed"
    FIRST_ASSIGNMENT = "first_assignment"
    ACTIVE_VOLUNTEER = "active_volunteer"

class InterventionType(Enum):
    """Types of interventions that can be applied"""
    EMAIL_REMINDER = "email_reminder"
    PHONE_CALL = "phone_call"
    PERSONALIZED_MATCH = "personalized_match"
    SIMPLIFIED_APPLICATION = "simplified_application"
    QUICK_START_PROGRAM = "quick_start_program"
    PEER_MENTOR = "peer_mentor"
    BRANCH_VISIT = "branch_visit"
    FLEXIBILITY_OPTION = "flexibility_option"

@dataclass
class FunnelEvent:
    """Represents a single event in the volunteer funnel"""
    user_id: str
    stage: FunnelStage
    timestamp: datetime
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    intervention_applied: Optional[InterventionType] = None
    source_system: str = "pathfinder"

@dataclass
class InterventionOutcome:
    """Tracks the outcome of an intervention"""
    intervention_id: str
    user_id: str
    intervention_type: InterventionType
    applied_at: datetime
    target_stage: FunnelStage
    successful: bool
    next_stage_reached_at: Optional[datetime] = None
    time_to_progression: Optional[timedelta] = None
    metadata: Optional[Dict[str, Any]] = None

class VolunteerFunnelTracker:
    """Main class for tracking volunteer funnel progression and interventions"""
    
    def __init__(self, database: VolunteerDatabase):
        self.database = database
        self.stage_order = list(FunnelStage)
    
    async def initialize_tracking_tables(self):
        """Initialize database tables for funnel tracking"""
        
        funnel_events_sql = """
        CREATE TABLE IF NOT EXISTS funnel_events (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            stage VARCHAR(50) NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            session_id VARCHAR(100),
            metadata JSONB,
            intervention_applied VARCHAR(50),
            source_system VARCHAR(50) DEFAULT 'pathfinder',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        interventions_sql = """
        CREATE TABLE IF NOT EXISTS funnel_interventions (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            intervention_type VARCHAR(50) NOT NULL,
            applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            target_stage VARCHAR(50) NOT NULL,
            successful BOOLEAN DEFAULT FALSE,
            next_stage_reached_at TIMESTAMP WITH TIME ZONE,
            time_to_progression_hours INTEGER,
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        funnel_cohorts_sql = """
        CREATE TABLE IF NOT EXISTS funnel_cohorts (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            cohort_name VARCHAR(100),
            entry_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            entry_stage VARCHAR(50) DEFAULT 'interest_expressed',
            current_stage VARCHAR(50) DEFAULT 'interest_expressed',
            is_control_group BOOLEAN DEFAULT FALSE,
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        logger.info("Funnel tracking tables SQL prepared")
        return [funnel_events_sql, interventions_sql, funnel_cohorts_sql]
    
    async def track_stage_progression(self, event: FunnelEvent) -> bool:
        """Track a user's progression through funnel stages"""
        try:
            event_data = {
                'user_id': event.user_id,
                'stage': event.stage.value,
                'timestamp': event.timestamp.isoformat(),
                'session_id': event.session_id,
                'metadata': json.dumps(event.metadata or {}),
                'intervention_applied': event.intervention_applied.value if event.intervention_applied else None,
                'source_system': event.source_system
            }
            
            # Insert funnel event
            result = self.database.supabase.table('funnel_events').insert(event_data).execute()
            
            # Update user's current stage in cohorts table
            await self._update_user_current_stage(event.user_id, event.stage)
            
            # Check if this progression was due to an intervention
            if event.intervention_applied:
                await self._mark_intervention_successful(event.user_id, event.intervention_applied, event.timestamp)
            
            logger.info(f"Tracked stage progression: {event.user_id} → {event.stage.value}")
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error tracking stage progression: {e}")
            return False
    
    async def apply_intervention(self, user_id: str, intervention_type: InterventionType, 
                               target_stage: FunnelStage, metadata: Dict[str, Any] = None) -> str:
        """Apply an intervention to help user progress to target stage"""
        try:
            intervention_data = {
                'user_id': user_id,
                'intervention_type': intervention_type.value,
                'applied_at': datetime.now().isoformat(),
                'target_stage': target_stage.value,
                'metadata': json.dumps(metadata or {})
            }
            
            result = self.database.supabase.table('funnel_interventions').insert(intervention_data).execute()
            intervention_id = result.data[0]['id'] if result.data else None
            
            # Track intervention application as analytics event
            await self.database.track_event(
                'intervention_applied',
                {
                    'intervention_type': intervention_type.value,
                    'target_stage': target_stage.value,
                    'metadata': metadata
                },
                user_id
            )
            
            logger.info(f"Applied intervention: {intervention_type.value} for user {user_id}")
            return intervention_id
            
        except Exception as e:
            logger.error(f"Error applying intervention: {e}")
            return None
    
    async def get_funnel_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive funnel analytics"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Stage distribution
            stage_dist_result = self.database.supabase.rpc(
                'get_stage_distribution',
                {'start_date': start_date}
            ).execute()
            
            # Conversion rates between stages
            conversions = await self._calculate_stage_conversions(days)
            
            # Drop-off analysis
            dropoffs = await self._analyze_stage_dropoffs(days)
            
            # Intervention effectiveness
            intervention_stats = await self._get_intervention_effectiveness(days)
            
            # Time to progression analysis
            progression_times = await self._analyze_progression_times(days)
            
            # Cohort analysis
            cohort_performance = await self._analyze_cohort_performance(days)
            
            return {
                'period_days': days,
                'stage_distribution': stage_dist_result.data if stage_dist_result.data else {},
                'conversion_rates': conversions,
                'dropoff_analysis': dropoffs,
                'intervention_effectiveness': intervention_stats,
                'progression_times': progression_times,
                'cohort_performance': cohort_performance,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting funnel analytics: {e}")
            return {'error': str(e)}
    
    async def identify_at_risk_users(self, hours_threshold: int = 48) -> List[Dict[str, Any]]:
        """Identify users at risk of dropping off based on time since last activity"""
        try:
            cutoff_time = (datetime.now() - timedelta(hours=hours_threshold)).isoformat()
            
            # Find users stuck in early stages
            at_risk_query = """
            SELECT DISTINCT ON (user_id) 
                user_id, stage, timestamp, metadata
            FROM funnel_events 
            WHERE timestamp < %s 
                AND stage IN ('interest_expressed', 'profile_created', 'matched_opportunities')
            ORDER BY user_id, timestamp DESC
            """
            
            # Get recent funnel events to identify stagnant users
            recent_events = self.database.supabase.table('funnel_events')\
                .select('*')\
                .lt('timestamp', cutoff_time)\
                .in_('stage', ['interest_expressed', 'profile_created', 'matched_opportunities'])\
                .order('timestamp', desc=True)\
                .execute()
            
            at_risk_users = []
            processed_users = set()
            
            for event in recent_events.data:
                user_id = event['user_id']
                if user_id in processed_users:
                    continue
                
                # Check if user has progressed beyond this stage recently
                recent_progress = self.database.supabase.table('funnel_events')\
                    .select('stage')\
                    .eq('user_id', user_id)\
                    .gt('timestamp', cutoff_time)\
                    .execute()
                
                if not recent_progress.data:
                    at_risk_users.append({
                        'user_id': user_id,
                        'stuck_stage': event['stage'],
                        'last_activity': event['timestamp'],
                        'hours_since_activity': (datetime.now() - datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))).total_seconds() / 3600,
                        'suggested_interventions': self._suggest_interventions(event['stage'])
                    })
                    processed_users.add(user_id)
            
            logger.info(f"Identified {len(at_risk_users)} at-risk users")
            return at_risk_users
            
        except Exception as e:
            logger.error(f"Error identifying at-risk users: {e}")
            return []
    
    async def create_user_cohort(self, user_ids: List[str], cohort_name: str, 
                               is_control_group: bool = False, metadata: Dict[str, Any] = None) -> bool:
        """Create a cohort for A/B testing interventions"""
        try:
            cohort_records = []
            for user_id in user_ids:
                cohort_records.append({
                    'user_id': user_id,
                    'cohort_name': cohort_name,
                    'is_control_group': is_control_group,
                    'metadata': json.dumps(metadata or {}),
                    'entry_date': datetime.now().isoformat()
                })
            
            result = self.database.supabase.table('funnel_cohorts').insert(cohort_records).execute()
            
            logger.info(f"Created cohort '{cohort_name}' with {len(user_ids)} users")
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error creating cohort: {e}")
            return False
    
    def _suggest_interventions(self, current_stage: str) -> List[str]:
        """Suggest appropriate interventions based on current stage"""
        suggestions = {
            'interest_expressed': [
                InterventionType.EMAIL_REMINDER.value,
                InterventionType.PERSONALIZED_MATCH.value,
                InterventionType.SIMPLIFIED_APPLICATION.value
            ],
            'profile_created': [
                InterventionType.PERSONALIZED_MATCH.value,
                InterventionType.PHONE_CALL.value,
                InterventionType.QUICK_START_PROGRAM.value
            ],
            'matched_opportunities': [
                InterventionType.EMAIL_REMINDER.value,
                InterventionType.SIMPLIFIED_APPLICATION.value,
                InterventionType.PEER_MENTOR.value
            ],
            'application_started': [
                InterventionType.EMAIL_REMINDER.value,
                InterventionType.PHONE_CALL.value,
                InterventionType.SIMPLIFIED_APPLICATION.value
            ]
        }
        
        return suggestions.get(current_stage, [])
    
    async def _update_user_current_stage(self, user_id: str, stage: FunnelStage):
        """Update user's current stage in cohorts table"""
        try:
            # Check if user exists in cohorts
            existing = self.database.supabase.table('funnel_cohorts')\
                .select('id')\
                .eq('user_id', user_id)\
                .execute()
            
            if existing.data:
                # Update existing record
                self.database.supabase.table('funnel_cohorts')\
                    .update({'current_stage': stage.value})\
                    .eq('user_id', user_id)\
                    .execute()
            else:
                # Create new cohort entry
                self.database.supabase.table('funnel_cohorts').insert({
                    'user_id': user_id,
                    'cohort_name': 'default',
                    'current_stage': stage.value
                }).execute()
                
        except Exception as e:
            logger.error(f"Error updating user current stage: {e}")
    
    async def _mark_intervention_successful(self, user_id: str, intervention_type: InterventionType, 
                                          progression_time: datetime):
        """Mark an intervention as successful when user progresses"""
        try:
            # Find the most recent intervention of this type for this user
            recent_intervention = self.database.supabase.table('funnel_interventions')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('intervention_type', intervention_type.value)\
                .eq('successful', False)\
                .order('applied_at', desc=True)\
                .limit(1)\
                .execute()
            
            if recent_intervention.data:
                intervention = recent_intervention.data[0]
                applied_at = datetime.fromisoformat(intervention['applied_at'].replace('Z', '+00:00'))
                time_diff = progression_time - applied_at
                
                # Update intervention as successful
                self.database.supabase.table('funnel_interventions')\
                    .update({
                        'successful': True,
                        'next_stage_reached_at': progression_time.isoformat(),
                        'time_to_progression_hours': int(time_diff.total_seconds() / 3600)
                    })\
                    .eq('id', intervention['id'])\
                    .execute()
                
        except Exception as e:
            logger.error(f"Error marking intervention successful: {e}")
    
    async def _calculate_stage_conversions(self, days: int) -> Dict[str, float]:
        """Calculate conversion rates between stages"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            conversions = {}
            for i in range(len(self.stage_order) - 1):
                current_stage = self.stage_order[i]
                next_stage = self.stage_order[i + 1]
                
                # Users who reached current stage
                current_users = self.database.supabase.table('funnel_events')\
                    .select('user_id')\
                    .eq('stage', current_stage.value)\
                    .gte('timestamp', start_date)\
                    .execute()
                
                # Users who reached next stage
                next_users = self.database.supabase.table('funnel_events')\
                    .select('user_id')\
                    .eq('stage', next_stage.value)\
                    .gte('timestamp', start_date)\
                    .execute()
                
                current_count = len(set(u['user_id'] for u in current_users.data))
                next_count = len(set(u['user_id'] for u in next_users.data))
                
                conversion_rate = (next_count / current_count * 100) if current_count > 0 else 0
                conversions[f"{current_stage.value}_to_{next_stage.value}"] = round(conversion_rate, 2)
            
            return conversions
            
        except Exception as e:
            logger.error(f"Error calculating conversions: {e}")
            return {}
    
    async def _analyze_stage_dropoffs(self, days: int) -> Dict[str, Any]:
        """Analyze where users drop off in the funnel"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get last stage for each user
            user_stages = self.database.supabase.table('funnel_events')\
                .select('user_id, stage')\
                .gte('timestamp', start_date)\
                .order('timestamp', desc=True)\
                .execute()
            
            # Count dropoffs by stage
            last_stages = {}
            processed_users = set()
            
            for event in user_stages.data:
                user_id = event['user_id']
                if user_id not in processed_users:
                    stage = event['stage']
                    last_stages[stage] = last_stages.get(stage, 0) + 1
                    processed_users.add(user_id)
            
            total_users = len(processed_users)
            dropoff_percentages = {
                stage: round(count / total_users * 100, 2) 
                for stage, count in last_stages.items()
            }
            
            return {
                'total_users_in_period': total_users,
                'dropoff_by_stage': last_stages,
                'dropoff_percentages': dropoff_percentages
            }
            
        except Exception as e:
            logger.error(f"Error analyzing dropoffs: {e}")
            return {}
    
    async def _get_intervention_effectiveness(self, days: int) -> Dict[str, Any]:
        """Analyze effectiveness of different interventions"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            interventions = self.database.supabase.table('funnel_interventions')\
                .select('*')\
                .gte('applied_at', start_date)\
                .execute()
            
            effectiveness = {}
            for intervention in interventions.data:
                int_type = intervention['intervention_type']
                if int_type not in effectiveness:
                    effectiveness[int_type] = {
                        'total_applied': 0,
                        'successful': 0,
                        'success_rate': 0,
                        'avg_time_to_progression': 0
                    }
                
                effectiveness[int_type]['total_applied'] += 1
                if intervention['successful']:
                    effectiveness[int_type]['successful'] += 1
                    if intervention['time_to_progression_hours']:
                        current_avg = effectiveness[int_type]['avg_time_to_progression']
                        new_avg = (current_avg + intervention['time_to_progression_hours']) / 2
                        effectiveness[int_type]['avg_time_to_progression'] = round(new_avg, 1)
            
            # Calculate success rates
            for int_type in effectiveness:
                stats = effectiveness[int_type]
                if stats['total_applied'] > 0:
                    stats['success_rate'] = round(stats['successful'] / stats['total_applied'] * 100, 2)
            
            return effectiveness
            
        except Exception as e:
            logger.error(f"Error analyzing intervention effectiveness: {e}")
            return {}
    
    async def _analyze_progression_times(self, days: int) -> Dict[str, float]:
        """Analyze time taken to progress between stages"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get all events ordered by user and time
            events = self.database.supabase.table('funnel_events')\
                .select('*')\
                .gte('timestamp', start_date)\
                .order('user_id, timestamp')\
                .execute()
            
            progression_times = {}
            user_events = {}
            
            # Group events by user
            for event in events.data:
                user_id = event['user_id']
                if user_id not in user_events:
                    user_events[user_id] = []
                user_events[user_id].append(event)
            
            # Calculate progression times
            for user_id, user_event_list in user_events.items():
                for i in range(len(user_event_list) - 1):
                    current_event = user_event_list[i]
                    next_event = user_event_list[i + 1]
                    
                    current_time = datetime.fromisoformat(current_event['timestamp'].replace('Z', '+00:00'))
                    next_time = datetime.fromisoformat(next_event['timestamp'].replace('Z', '+00:00'))
                    
                    time_diff = (next_time - current_time).total_seconds() / 3600  # hours
                    
                    transition = f"{current_event['stage']}_to_{next_event['stage']}"
                    if transition not in progression_times:
                        progression_times[transition] = []
                    progression_times[transition].append(time_diff)
            
            # Calculate averages
            avg_times = {}
            for transition, times in progression_times.items():
                if times:
                    avg_times[transition] = round(sum(times) / len(times), 2)
            
            return avg_times
            
        except Exception as e:
            logger.error(f"Error analyzing progression times: {e}")
            return {}
    
    async def _analyze_cohort_performance(self, days: int) -> Dict[str, Any]:
        """Analyze performance differences between cohorts"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get cohort data
            cohorts = self.database.supabase.table('funnel_cohorts')\
                .select('*')\
                .gte('entry_date', start_date)\
                .execute()
            
            cohort_performance = {}
            
            for cohort in cohorts.data:
                cohort_name = cohort['cohort_name']
                user_id = cohort['user_id']
                
                if cohort_name not in cohort_performance:
                    cohort_performance[cohort_name] = {
                        'total_users': 0,
                        'active_users': 0,
                        'is_control': cohort['is_control_group'],
                        'stage_distribution': {}
                    }
                
                cohort_performance[cohort_name]['total_users'] += 1
                
                # Check current stage
                current_stage = cohort['current_stage']
                stage_dist = cohort_performance[cohort_name]['stage_distribution']
                stage_dist[current_stage] = stage_dist.get(current_stage, 0) + 1
                
                # Check if user is active (reached active_volunteer stage)
                if current_stage == 'active_volunteer':
                    cohort_performance[cohort_name]['active_users'] += 1
            
            # Calculate activation rates
            for cohort_name in cohort_performance:
                stats = cohort_performance[cohort_name]
                if stats['total_users'] > 0:
                    stats['activation_rate'] = round(stats['active_users'] / stats['total_users'] * 100, 2)
                else:
                    stats['activation_rate'] = 0
            
            return cohort_performance
            
        except Exception as e:
            logger.error(f"Error analyzing cohort performance: {e}")
            return {}

# Convenience functions for easy integration
async def track_user_interest(user_id: str, source: str = "web", metadata: Dict[str, Any] = None):
    """Track when a user expresses interest in volunteering"""
    from database import VolunteerDatabase
    
    db = VolunteerDatabase()
    tracker = VolunteerFunnelTracker(db)
    
    event = FunnelEvent(
        user_id=user_id,
        stage=FunnelStage.INTEREST_EXPRESSED,
        timestamp=datetime.now(),
        metadata={'source': source, **(metadata or {})}
    )
    
    return await tracker.track_stage_progression(event)

async def track_profile_creation(user_id: str, session_id: str = None):
    """Track when a user creates their profile"""
    from database import VolunteerDatabase
    
    db = VolunteerDatabase()
    tracker = VolunteerFunnelTracker(db)
    
    event = FunnelEvent(
        user_id=user_id,
        stage=FunnelStage.PROFILE_CREATED,
        timestamp=datetime.now(),
        session_id=session_id
    )
    
    return await tracker.track_stage_progression(event)

async def track_volunteer_activation(user_id: str, first_activity: Dict[str, Any] = None):
    """Track when a volunteer becomes active"""
    from database import VolunteerDatabase
    
    db = VolunteerDatabase()
    tracker = VolunteerFunnelTracker(db)
    
    event = FunnelEvent(
        user_id=user_id,
        stage=FunnelStage.ACTIVE_VOLUNTEER,
        timestamp=datetime.now(),
        metadata={'first_activity': first_activity or {}}
    )
    
    return await tracker.track_stage_progression(event)