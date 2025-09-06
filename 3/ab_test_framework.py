"""
A/B Test Framework for Campaign Message Impact on Volunteer Turnout
Measures the effectiveness of different messages and schedules on volunteer engagement
"""
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np
from scipy import stats
import asyncio
import logging

logger = logging.getLogger(__name__)

class TestStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class VariantType(Enum):
    MESSAGE = "message"
    SCHEDULE = "schedule"
    HYBRID = "hybrid"

class MetricType(Enum):
    TURNOUT_RATE = "turnout_rate"
    ENGAGEMENT_RATE = "engagement_rate"
    RETENTION_RATE = "retention_rate"
    CONVERSION_RATE = "conversion_rate"

@dataclass
class MessageVariant:
    id: str
    name: str
    subject_line: str
    content: str
    call_to_action: str
    tone: str  # "urgent", "friendly", "professional", "casual"
    personalization_level: str  # "none", "basic", "advanced"
    message_length: str  # "short", "medium", "long"

@dataclass
class ScheduleVariant:
    id: str
    name: str
    send_time: str  # "09:00", "12:00", "17:00", etc.
    send_days: List[str]  # ["Monday", "Wednesday", "Friday"]
    frequency: str  # "once", "weekly", "bi-weekly"
    reminder_schedule: List[int]  # Days before event to send reminders [7, 3, 1]

@dataclass
class TestConfiguration:
    test_id: str
    name: str
    description: str
    test_type: VariantType
    status: TestStatus
    start_date: datetime
    end_date: datetime
    sample_size: int
    confidence_level: float
    primary_metric: MetricType
    secondary_metrics: List[MetricType]
    message_variants: List[MessageVariant]
    schedule_variants: List[ScheduleVariant]
    target_audience_filters: Dict[str, Any]
    created_by: str
    created_at: datetime
    updated_at: datetime

@dataclass
class ParticipantAssignment:
    user_id: str
    test_id: str
    variant_id: str
    variant_type: VariantType
    assigned_at: datetime
    metadata: Dict[str, Any]

@dataclass
class TestEvent:
    event_id: str
    test_id: str
    user_id: str
    variant_id: str
    event_type: str  # "message_sent", "message_opened", "clicked", "registered", "attended"
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class TestResults:
    test_id: str
    variant_id: str
    variant_name: str
    sample_size: int
    primary_metric_value: float
    secondary_metrics: Dict[str, float]
    confidence_interval: Tuple[float, float]
    p_value: float
    is_statistically_significant: bool
    lift_percentage: float
    calculated_at: datetime

class ABTestFramework:
    def __init__(self, database=None):
        self.database = database
        self.active_tests: Dict[str, TestConfiguration] = {}
        self.participant_assignments: Dict[str, List[ParticipantAssignment]] = {}
        self.test_events: List[TestEvent] = []
        
    async def create_test(self, test_config: Dict[str, Any]) -> str:
        """Create a new A/B test configuration"""
        test_id = str(uuid.uuid4())
        
        # Convert dict to TestConfiguration
        message_variants = [
            MessageVariant(**variant) for variant in test_config.get('message_variants', [])
        ]
        schedule_variants = [
            ScheduleVariant(**variant) for variant in test_config.get('schedule_variants', [])
        ]
        
        test = TestConfiguration(
            test_id=test_id,
            name=test_config['name'],
            description=test_config['description'],
            test_type=VariantType(test_config['test_type']),
            status=TestStatus.DRAFT,
            start_date=datetime.fromisoformat(test_config['start_date']),
            end_date=datetime.fromisoformat(test_config['end_date']),
            sample_size=test_config['sample_size'],
            confidence_level=test_config.get('confidence_level', 0.95),
            primary_metric=MetricType(test_config['primary_metric']),
            secondary_metrics=[MetricType(m) for m in test_config.get('secondary_metrics', [])],
            message_variants=message_variants,
            schedule_variants=schedule_variants,
            target_audience_filters=test_config.get('target_audience_filters', {}),
            created_by=test_config['created_by'],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Save to database if available
        if self.database:
            await self._save_test_to_db(test)
        
        self.active_tests[test_id] = test
        logger.info(f"Created A/B test: {test.name} (ID: {test_id})")
        return test_id
    
    async def start_test(self, test_id: str) -> bool:
        """Start an A/B test"""
        if test_id not in self.active_tests:
            logger.error(f"Test {test_id} not found")
            return False
        
        test = self.active_tests[test_id]
        if test.status != TestStatus.DRAFT:
            logger.error(f"Test {test_id} cannot be started (status: {test.status})")
            return False
        
        # Validate test configuration
        if not self._validate_test_config(test):
            return False
        
        test.status = TestStatus.ACTIVE
        test.updated_at = datetime.now()
        
        # Initialize participant assignment tracking
        self.participant_assignments[test_id] = []
        
        if self.database:
            await self._update_test_in_db(test)
        
        logger.info(f"Started A/B test: {test.name}")
        return True
    
    def assign_participant(self, test_id: str, user_id: str, user_profile: Dict[str, Any] = None) -> Optional[str]:
        """Assign a user to a test variant"""
        if test_id not in self.active_tests:
            return None
        
        test = self.active_tests[test_id]
        if test.status != TestStatus.ACTIVE:
            return None
        
        # Check if user already assigned
        existing_assignments = self.participant_assignments.get(test_id, [])
        for assignment in existing_assignments:
            if assignment.user_id == user_id:
                return assignment.variant_id
        
        # Check if user meets target audience criteria
        if not self._user_matches_criteria(user_profile or {}, test.target_audience_filters):
            return None
        
        # Assign variant using hash-based assignment for consistency
        variant_id = self._assign_variant(test, user_id)
        
        assignment = ParticipantAssignment(
            user_id=user_id,
            test_id=test_id,
            variant_id=variant_id,
            variant_type=test.test_type,
            assigned_at=datetime.now(),
            metadata=user_profile or {}
        )
        
        if test_id not in self.participant_assignments:
            self.participant_assignments[test_id] = []
        self.participant_assignments[test_id].append(assignment)
        
        logger.info(f"Assigned user {user_id} to variant {variant_id} in test {test_id}")
        return variant_id
    
    async def track_event(self, test_id: str, user_id: str, event_type: str, metadata: Dict[str, Any] = None):
        """Track an event for A/B test analysis"""
        if test_id not in self.active_tests:
            return
        
        # Find user's variant assignment
        variant_id = None
        assignments = self.participant_assignments.get(test_id, [])
        for assignment in assignments:
            if assignment.user_id == user_id:
                variant_id = assignment.variant_id
                break
        
        if not variant_id:
            return
        
        event = TestEvent(
            event_id=str(uuid.uuid4()),
            test_id=test_id,
            user_id=user_id,
            variant_id=variant_id,
            event_type=event_type,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        self.test_events.append(event)
        
        if self.database:
            await self._save_event_to_db(event)
        
        logger.debug(f"Tracked event {event_type} for user {user_id} in test {test_id}")
    
    async def calculate_results(self, test_id: str) -> List[TestResults]:
        """Calculate statistical results for an A/B test"""
        if test_id not in self.active_tests:
            return []
        
        test = self.active_tests[test_id]
        assignments = self.participant_assignments.get(test_id, [])
        
        # Get all variants
        all_variants = []
        if test.test_type in [VariantType.MESSAGE, VariantType.HYBRID]:
            all_variants.extend([(v.id, v.name) for v in test.message_variants])
        if test.test_type in [VariantType.SCHEDULE, VariantType.HYBRID]:
            all_variants.extend([(v.id, v.name) for v in test.schedule_variants])
        
        results = []
        
        for variant_id, variant_name in all_variants:
            # Get participants for this variant
            variant_participants = [a for a in assignments if a.variant_id == variant_id]
            variant_user_ids = [p.user_id for p in variant_participants]
            
            # Get events for this variant
            variant_events = [e for e in self.test_events 
                            if e.test_id == test_id and e.user_id in variant_user_ids]
            
            # Calculate primary metric
            primary_value = self._calculate_metric(
                test.primary_metric, variant_user_ids, variant_events
            )
            
            # Calculate secondary metrics
            secondary_values = {}
            for metric in test.secondary_metrics:
                secondary_values[metric.value] = self._calculate_metric(
                    metric, variant_user_ids, variant_events
                )
            
            # Calculate statistical significance (vs. control variant)
            p_value, confidence_interval, lift = self._calculate_significance(
                test, variant_id, variant_user_ids, variant_events, primary_value
            )
            
            result = TestResults(
                test_id=test_id,
                variant_id=variant_id,
                variant_name=variant_name,
                sample_size=len(variant_participants),
                primary_metric_value=primary_value,
                secondary_metrics=secondary_values,
                confidence_interval=confidence_interval,
                p_value=p_value,
                is_statistically_significant=p_value < (1 - test.confidence_level),
                lift_percentage=lift,
                calculated_at=datetime.now()
            )
            
            results.append(result)
        
        return results
    
    async def get_message_for_user(self, test_id: str, user_id: str) -> Optional[MessageVariant]:
        """Get the appropriate message variant for a user"""
        variant_id = self.assign_participant(test_id, user_id)
        if not variant_id:
            return None
        
        test = self.active_tests[test_id]
        for variant in test.message_variants:
            if variant.id == variant_id:
                return variant
        
        return None
    
    async def get_schedule_for_user(self, test_id: str, user_id: str) -> Optional[ScheduleVariant]:
        """Get the appropriate schedule variant for a user"""
        variant_id = self.assign_participant(test_id, user_id)
        if not variant_id:
            return None
        
        test = self.active_tests[test_id]
        for variant in test.schedule_variants:
            if variant.id == variant_id:
                return variant
        
        return None
    
    def _assign_variant(self, test: TestConfiguration, user_id: str) -> str:
        """Assign variant using hash-based consistent assignment"""
        # Get all possible variants
        all_variants = []
        if test.test_type in [VariantType.MESSAGE, VariantType.HYBRID]:
            all_variants.extend([v.id for v in test.message_variants])
        if test.test_type in [VariantType.SCHEDULE, VariantType.HYBRID]:
            all_variants.extend([v.id for v in test.schedule_variants])
        
        if not all_variants:
            return ""
        
        # Use hash of user_id + test_id for consistent assignment
        hash_input = f"{user_id}_{test.test_id}"
        hash_value = hash(hash_input) % len(all_variants)
        return all_variants[hash_value]
    
    def _user_matches_criteria(self, user_profile: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if user matches target audience criteria"""
        if not filters:
            return True
        
        for key, value in filters.items():
            if key not in user_profile:
                continue
            
            user_value = user_profile[key]
            
            if isinstance(value, list):
                if user_value not in value:
                    return False
            elif isinstance(value, dict):
                if 'min' in value and user_value < value['min']:
                    return False
                if 'max' in value and user_value > value['max']:
                    return False
            elif user_value != value:
                return False
        
        return True
    
    def _calculate_metric(self, metric: MetricType, user_ids: List[str], events: List[TestEvent]) -> float:
        """Calculate a specific metric value"""
        if not user_ids:
            return 0.0
        
        if metric == MetricType.TURNOUT_RATE:
            # Percentage of users who attended events
            attended_users = set()
            for event in events:
                if event.event_type == "attended" and event.user_id in user_ids:
                    attended_users.add(event.user_id)
            return len(attended_users) / len(user_ids)
        
        elif metric == MetricType.ENGAGEMENT_RATE:
            # Percentage of users who opened messages or clicked links
            engaged_users = set()
            for event in events:
                if event.event_type in ["message_opened", "clicked"] and event.user_id in user_ids:
                    engaged_users.add(event.user_id)
            return len(engaged_users) / len(user_ids)
        
        elif metric == MetricType.RETENTION_RATE:
            # Percentage of users who attended multiple events
            user_attendance = {}
            for event in events:
                if event.event_type == "attended" and event.user_id in user_ids:
                    user_attendance[event.user_id] = user_attendance.get(event.user_id, 0) + 1
            
            retained_users = sum(1 for count in user_attendance.values() if count > 1)
            return retained_users / len(user_ids)
        
        elif metric == MetricType.CONVERSION_RATE:
            # Percentage of users who registered after receiving message
            converted_users = set()
            for event in events:
                if event.event_type == "registered" and event.user_id in user_ids:
                    converted_users.add(event.user_id)
            return len(converted_users) / len(user_ids)
        
        return 0.0
    
    def _calculate_significance(self, test: TestConfiguration, variant_id: str, 
                              variant_users: List[str], variant_events: List[TestEvent],
                              variant_value: float) -> Tuple[float, Tuple[float, float], float]:
        """Calculate statistical significance vs control"""
        # For now, return placeholder values
        # In production, implement proper statistical tests (t-test, chi-square, etc.)
        p_value = 0.05
        confidence_interval = (variant_value * 0.9, variant_value * 1.1)
        lift_percentage = 0.0
        
        return p_value, confidence_interval, lift_percentage
    
    def _validate_test_config(self, test: TestConfiguration) -> bool:
        """Validate test configuration before starting"""
        if not test.message_variants and not test.schedule_variants:
            logger.error("Test must have at least one variant")
            return False
        
        if test.sample_size <= 0:
            logger.error("Sample size must be positive")
            return False
        
        if test.end_date <= test.start_date:
            logger.error("End date must be after start date")
            return False
        
        return True
    
    async def _save_test_to_db(self, test: TestConfiguration):
        """Save test configuration to database"""
        if not self.database:
            return
        
        try:
            test_data = {
                'id': test.test_id,
                'name': test.name,
                'description': test.description,
                'test_type': test.test_type.value,
                'status': test.status.value,
                'start_date': test.start_date.isoformat(),
                'end_date': test.end_date.isoformat(),
                'sample_size': test.sample_size,
                'confidence_level': test.confidence_level,
                'primary_metric': test.primary_metric.value,
                'secondary_metrics': [m.value for m in test.secondary_metrics],
                'message_variants': [asdict(v) for v in test.message_variants],
                'schedule_variants': [asdict(v) for v in test.schedule_variants],
                'target_audience_filters': test.target_audience_filters,
                'created_by': test.created_by,
                'created_at': test.created_at.isoformat(),
                'updated_at': test.updated_at.isoformat()
            }
            
            await self.database.supabase.table('ab_tests').insert(test_data).execute()
            logger.info(f"Saved test {test.test_id} to database")
        except Exception as e:
            logger.error(f"Failed to save test to database: {e}")
    
    async def _update_test_in_db(self, test: TestConfiguration):
        """Update test configuration in database"""
        if not self.database:
            return
        
        try:
            update_data = {
                'status': test.status.value,
                'updated_at': test.updated_at.isoformat()
            }
            
            await self.database.supabase.table('ab_tests').update(update_data).eq('id', test.test_id).execute()
            logger.info(f"Updated test {test.test_id} in database")
        except Exception as e:
            logger.error(f"Failed to update test in database: {e}")
    
    async def _save_event_to_db(self, event: TestEvent):
        """Save event to database"""
        if not self.database:
            return
        
        try:
            event_data = {
                'id': event.event_id,
                'test_id': event.test_id,
                'user_id': event.user_id,
                'variant_id': event.variant_id,
                'event_type': event.event_type,
                'timestamp': event.timestamp.isoformat(),
                'metadata': json.dumps(event.metadata)
            }
            
            await self.database.supabase.table('ab_test_events').insert(event_data).execute()
        except Exception as e:
            logger.error(f"Failed to save event to database: {e}")

# Usage example and helper functions
class CampaignMessageManager:
    """High-level manager for campaign message A/B testing"""
    
    def __init__(self, ab_framework: ABTestFramework):
        self.ab_framework = ab_framework
    
    async def create_message_impact_test(self, campaign_name: str, created_by: str) -> str:
        """Create a standard message impact test"""
        
        # Define standard message variants
        message_variants = [
            {
                'id': str(uuid.uuid4()),
                'name': 'Control - Standard',
                'subject_line': 'Volunteer Opportunity Available',
                'content': 'We have a volunteer opportunity that matches your interests. Would you like to participate?',
                'call_to_action': 'Sign Up Now',
                'tone': 'professional',
                'personalization_level': 'basic',
                'message_length': 'medium'
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Urgent - High Impact',
                'subject_line': 'URGENT: Volunteers Needed for Community Impact',
                'content': 'Your community needs you! This volunteer opportunity will make a real difference in people\'s lives. Don\'t miss your chance to help!',
                'call_to_action': 'Join the Mission',
                'tone': 'urgent',
                'personalization_level': 'basic',
                'message_length': 'medium'
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Personal - Warm',
                'subject_line': 'A Perfect Volunteer Match Just for You',
                'content': 'Hi there! Based on your interests and skills, we found a volunteer opportunity that seems like a perfect fit. We\'d love to have you join our community of changemakers.',
                'call_to_action': 'Explore Opportunity',
                'tone': 'friendly',
                'personalization_level': 'advanced',
                'message_length': 'medium'
            }
        ]
        
        # Define standard schedule variants
        schedule_variants = [
            {
                'id': str(uuid.uuid4()),
                'name': 'Morning Outreach',
                'send_time': '09:00',
                'send_days': ['Tuesday', 'Thursday'],
                'frequency': 'weekly',
                'reminder_schedule': [7, 3, 1]
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Evening Engagement',
                'send_time': '18:00',
                'send_days': ['Wednesday', 'Friday'],
                'frequency': 'weekly',
                'reminder_schedule': [5, 2]
            }
        ]
        
        test_config = {
            'name': f'Campaign Message Impact: {campaign_name}',
            'description': f'A/B test to measure the impact of different message styles and schedules on volunteer turnout for {campaign_name}',
            'test_type': 'hybrid',
            'start_date': datetime.now().isoformat(),
            'end_date': (datetime.now() + timedelta(days=30)).isoformat(),
            'sample_size': 1000,
            'confidence_level': 0.95,
            'primary_metric': 'turnout_rate',
            'secondary_metrics': ['engagement_rate', 'conversion_rate'],
            'message_variants': message_variants,
            'schedule_variants': schedule_variants,
            'target_audience_filters': {
                'is_ymca_member': [True, False],
                'age': {'min': 18, 'max': 80}
            },
            'created_by': created_by
        }
        
        return await self.ab_framework.create_test(test_config)
    
    async def send_campaign_message(self, test_id: str, user_id: str, user_profile: Dict[str, Any]) -> bool:
        """Send personalized campaign message based on A/B test assignment"""
        
        # Get message variant for user
        message_variant = await self.ab_framework.get_message_for_user(test_id, user_id)
        if not message_variant:
            return False
        
        # Get schedule variant for user
        schedule_variant = await self.ab_framework.get_schedule_for_user(test_id, user_id)
        
        # Track message sent event
        await self.ab_framework.track_event(
            test_id, user_id, "message_sent",
            {
                'message_variant_id': message_variant.id,
                'schedule_variant_id': schedule_variant.id if schedule_variant else None,
                'subject_line': message_variant.subject_line
            }
        )
        
        # In production, integrate with actual email/SMS service
        logger.info(f"Sent message '{message_variant.name}' to user {user_id}")
        return True
    
    async def track_volunteer_turnout(self, test_id: str, user_id: str, attended: bool, event_metadata: Dict[str, Any] = None):
        """Track whether a volunteer showed up to an event"""
        event_type = "attended" if attended else "no_show"
        await self.ab_framework.track_event(test_id, user_id, event_type, event_metadata)