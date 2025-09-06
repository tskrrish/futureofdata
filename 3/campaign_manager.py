"""
Campaign Manager for A/B Testing Message Impact on Volunteer Turnout
Handles campaign creation, message sending, and turnout tracking
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass, asdict
import uuid
from enum import Enum

from ab_test_framework import ABTestFramework, MessageVariant, ScheduleVariant, CampaignMessageManager

logger = logging.getLogger(__name__)

class CampaignStatus(Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

class MessageChannel(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"

@dataclass
class Campaign:
    id: str
    name: str
    description: str
    status: CampaignStatus
    channel: MessageChannel
    test_id: Optional[str]
    target_audience: Dict[str, Any]
    start_date: datetime
    end_date: datetime
    created_by: str
    created_at: datetime
    updated_at: datetime

@dataclass 
class CampaignExecution:
    id: str
    campaign_id: str
    test_id: str
    user_id: str
    variant_id: str
    message_content: Dict[str, Any]
    scheduled_for: datetime
    sent_at: Optional[datetime]
    delivery_status: str
    metadata: Dict[str, Any]

class CampaignManager:
    """High-level campaign management for volunteer messaging"""
    
    def __init__(self, ab_framework: ABTestFramework, database=None):
        self.ab_framework = ab_framework
        self.database = database
        self.campaigns: Dict[str, Campaign] = {}
        self.executions: List[CampaignExecution] = []
        self.message_manager = CampaignMessageManager(ab_framework)
    
    async def create_volunteer_campaign(self, campaign_data: Dict[str, Any]) -> str:
        """Create a new volunteer recruitment campaign with A/B testing"""
        
        campaign_id = str(uuid.uuid4())
        
        # Create the A/B test for this campaign
        test_id = await self._create_campaign_ab_test(campaign_data)
        
        campaign = Campaign(
            id=campaign_id,
            name=campaign_data['name'],
            description=campaign_data['description'],
            status=CampaignStatus.DRAFT,
            channel=MessageChannel(campaign_data.get('channel', 'email')),
            test_id=test_id,
            target_audience=campaign_data.get('target_audience', {}),
            start_date=datetime.fromisoformat(campaign_data['start_date']),
            end_date=datetime.fromisoformat(campaign_data['end_date']),
            created_by=campaign_data['created_by'],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.campaigns[campaign_id] = campaign
        
        if self.database:
            await self._save_campaign_to_db(campaign)
        
        logger.info(f"Created campaign: {campaign.name} (ID: {campaign_id}, Test ID: {test_id})")
        return campaign_id
    
    async def launch_campaign(self, campaign_id: str) -> bool:
        """Launch a campaign and start A/B testing"""
        
        if campaign_id not in self.campaigns:
            logger.error(f"Campaign {campaign_id} not found")
            return False
        
        campaign = self.campaigns[campaign_id]
        
        # Start the associated A/B test
        if campaign.test_id:
            success = await self.ab_framework.start_test(campaign.test_id)
            if not success:
                logger.error(f"Failed to start A/B test for campaign {campaign_id}")
                return False
        
        campaign.status = CampaignStatus.ACTIVE
        campaign.updated_at = datetime.now()
        
        if self.database:
            await self._update_campaign_in_db(campaign)
        
        # Schedule message sends based on target audience
        await self._schedule_campaign_messages(campaign)
        
        logger.info(f"Launched campaign: {campaign.name}")
        return True
    
    async def send_personalized_message(self, campaign_id: str, user_id: str, 
                                      user_profile: Dict[str, Any]) -> bool:
        """Send a personalized message to a user as part of the campaign"""
        
        if campaign_id not in self.campaigns:
            return False
        
        campaign = self.campaigns[campaign_id]
        if not campaign.test_id:
            return False
        
        # Get the appropriate message variant for this user
        message_variant = await self.ab_framework.get_message_for_user(campaign.test_id, user_id)
        if not message_variant:
            return False
        
        # Get schedule variant
        schedule_variant = await self.ab_framework.get_schedule_for_user(campaign.test_id, user_id)
        
        # Personalize the message content
        personalized_content = self._personalize_message(message_variant, user_profile)
        
        # Create execution record
        execution = CampaignExecution(
            id=str(uuid.uuid4()),
            campaign_id=campaign_id,
            test_id=campaign.test_id,
            user_id=user_id,
            variant_id=message_variant.id,
            message_content=personalized_content,
            scheduled_for=datetime.now(),
            sent_at=datetime.now(),
            delivery_status="sent",
            metadata={
                'user_profile': user_profile,
                'schedule_variant_id': schedule_variant.id if schedule_variant else None
            }
        )
        
        self.executions.append(execution)
        
        # Track the message send event
        await self.ab_framework.track_event(
            campaign.test_id, user_id, "message_sent",
            {
                'campaign_id': campaign_id,
                'message_variant_id': message_variant.id,
                'channel': campaign.channel.value,
                'personalized_content': personalized_content
            }
        )
        
        # In production, integrate with actual messaging service (email, SMS, etc.)
        success = await self._deliver_message(execution)
        
        if success:
            execution.delivery_status = "delivered"
            logger.info(f"Sent personalized message to user {user_id} for campaign {campaign_id}")
        else:
            execution.delivery_status = "failed"
            logger.error(f"Failed to send message to user {user_id} for campaign {campaign_id}")
        
        if self.database:
            await self._save_execution_to_db(execution)
        
        return success
    
    async def track_user_engagement(self, campaign_id: str, user_id: str, 
                                  engagement_type: str, metadata: Dict[str, Any] = None):
        """Track user engagement with campaign messages"""
        
        if campaign_id not in self.campaigns:
            return
        
        campaign = self.campaigns[campaign_id]
        if not campaign.test_id:
            return
        
        await self.ab_framework.track_event(
            campaign.test_id, user_id, engagement_type,
            {
                'campaign_id': campaign_id,
                **(metadata or {})
            }
        )
        
        logger.debug(f"Tracked {engagement_type} for user {user_id} in campaign {campaign_id}")
    
    async def track_volunteer_registration(self, campaign_id: str, user_id: str, 
                                         event_details: Dict[str, Any]):
        """Track when a user registers for a volunteer opportunity"""
        
        await self.track_user_engagement(campaign_id, user_id, "registered", {
            'event_details': event_details,
            'registration_timestamp': datetime.now().isoformat()
        })
        
        # Also track in volunteer turnout tracking
        if self.database:
            await self._save_volunteer_registration(campaign_id, user_id, event_details)
    
    async def track_volunteer_attendance(self, campaign_id: str, user_id: str, 
                                       attended: bool, event_details: Dict[str, Any]):
        """Track volunteer attendance at events"""
        
        event_type = "attended" if attended else "no_show"
        
        await self.track_user_engagement(campaign_id, user_id, event_type, {
            'event_details': event_details,
            'attendance_timestamp': datetime.now().isoformat(),
            'hours_contributed': event_details.get('hours', 0)
        })
        
        # Track in volunteer turnout tracking
        if self.database:
            await self._save_volunteer_attendance(campaign_id, user_id, attended, event_details)
    
    async def get_campaign_performance(self, campaign_id: str) -> Dict[str, Any]:
        """Get performance metrics for a campaign"""
        
        if campaign_id not in self.campaigns:
            return {}
        
        campaign = self.campaigns[campaign_id]
        if not campaign.test_id:
            return {}
        
        # Get A/B test results
        results = await self.ab_framework.calculate_results(campaign.test_id)
        
        # Calculate campaign-specific metrics
        campaign_executions = [e for e in self.executions if e.campaign_id == campaign_id]
        
        total_sent = len(campaign_executions)
        delivered = len([e for e in campaign_executions if e.delivery_status == "delivered"])
        
        performance = {
            'campaign_id': campaign_id,
            'campaign_name': campaign.name,
            'status': campaign.status.value,
            'total_messages_sent': total_sent,
            'delivery_rate': delivered / total_sent if total_sent > 0 else 0,
            'ab_test_results': [asdict(r) for r in results],
            'generated_at': datetime.now().isoformat()
        }
        
        return performance
    
    async def get_all_campaigns(self) -> List[Dict[str, Any]]:
        """Get all campaigns with their performance data"""
        campaigns_data = []
        
        for campaign_id, campaign in self.campaigns.items():
            performance = await self.get_campaign_performance(campaign_id)
            campaign_data = asdict(campaign)
            campaign_data['performance'] = performance
            campaigns_data.append(campaign_data)
        
        return campaigns_data
    
    def _personalize_message(self, message_variant: MessageVariant, 
                           user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Personalize message content based on user profile and variant settings"""
        
        content = message_variant.content
        subject = message_variant.subject_line
        
        if message_variant.personalization_level == "basic":
            # Basic personalization - name and location
            if 'first_name' in user_profile:
                content = f"Hi {user_profile['first_name']}, {content}"
                subject = f"{user_profile['first_name']}, {subject}"
            
            if 'city' in user_profile:
                content = content.replace("your community", f"{user_profile['city']}")
        
        elif message_variant.personalization_level == "advanced":
            # Advanced personalization - interests, skills, history
            if 'first_name' in user_profile:
                content = f"Hi {user_profile['first_name']}, {content}"
                subject = f"{user_profile['first_name']}, {subject}"
            
            if 'interests' in user_profile:
                interests = user_profile['interests']
                if interests:
                    content += f" Since you're interested in {interests}, this opportunity might be perfect for you!"
            
            if 'volunteer_history' in user_profile:
                history = user_profile['volunteer_history']
                if history.get('previous_hours', 0) > 0:
                    content += f" Thank you for your {history['previous_hours']} hours of previous volunteer service!"
        
        return {
            'subject_line': subject,
            'content': content,
            'call_to_action': message_variant.call_to_action,
            'tone': message_variant.tone,
            'personalization_applied': message_variant.personalization_level
        }
    
    async def _create_campaign_ab_test(self, campaign_data: Dict[str, Any]) -> str:
        """Create A/B test configuration for the campaign"""
        
        # Use predefined message variants or create custom ones
        if 'message_variants' in campaign_data:
            message_variants = campaign_data['message_variants']
        else:
            # Use default volunteer recruitment message variants
            message_variants = [
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Control - Standard Invitation',
                    'subject_line': 'Volunteer Opportunity Available',
                    'content': 'We have a volunteer opportunity that matches your interests. Your help would make a real difference in our community.',
                    'call_to_action': 'View Opportunity',
                    'tone': 'professional',
                    'personalization_level': 'basic',
                    'message_length': 'medium'
                },
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Urgent - Community Need',
                    'subject_line': 'Your Community Needs You!',
                    'content': 'There\'s an urgent need for volunteers in your area. This is your chance to step up and make a meaningful impact. Every hour counts!',
                    'call_to_action': 'Help Now',
                    'tone': 'urgent',
                    'personalization_level': 'basic',
                    'message_length': 'short'
                },
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Personal - Warm Invitation',
                    'subject_line': 'A Special Volunteer Opportunity Just for You',
                    'content': 'Based on your interests and skills, we\'ve found a volunteer opportunity that seems like a perfect match. We\'d love to have you join our community of changemakers and see the difference you can make.',
                    'call_to_action': 'Explore Match',
                    'tone': 'friendly',
                    'personalization_level': 'advanced',
                    'message_length': 'long'
                }
            ]
        
        # Create schedule variants
        schedule_variants = [
            {
                'id': str(uuid.uuid4()),
                'name': 'Morning Engagement',
                'send_time': '09:00',
                'send_days': ['Tuesday', 'Thursday'],
                'frequency': 'weekly',
                'reminder_schedule': [7, 3, 1]
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Evening Outreach',
                'send_time': '18:30',
                'send_days': ['Wednesday', 'Friday'],
                'frequency': 'weekly',
                'reminder_schedule': [5, 2]
            }
        ]
        
        test_config = {
            'name': f'Campaign A/B Test: {campaign_data["name"]}',
            'description': f'Testing message impact on volunteer turnout for: {campaign_data["description"]}',
            'test_type': 'hybrid',
            'start_date': campaign_data['start_date'],
            'end_date': campaign_data['end_date'],
            'sample_size': campaign_data.get('sample_size', 1000),
            'confidence_level': 0.95,
            'primary_metric': 'turnout_rate',
            'secondary_metrics': ['engagement_rate', 'conversion_rate', 'retention_rate'],
            'message_variants': message_variants,
            'schedule_variants': schedule_variants,
            'target_audience_filters': campaign_data.get('target_audience', {}),
            'created_by': campaign_data['created_by']
        }
        
        return await self.ab_framework.create_test(test_config)
    
    async def _schedule_campaign_messages(self, campaign: Campaign):
        """Schedule messages for all target users in the campaign"""
        
        # In production, this would query the database for users matching target criteria
        # For now, we'll create a placeholder for scheduling logic
        
        logger.info(f"Scheduling messages for campaign {campaign.name}")
        # This would integrate with your user database and scheduling system
        
    async def _deliver_message(self, execution: CampaignExecution) -> bool:
        """Deliver message via appropriate channel (email, SMS, etc.)"""
        
        # In production, integrate with actual messaging services
        # For now, simulate delivery
        
        channel_map = {
            MessageChannel.EMAIL: "email_service",
            MessageChannel.SMS: "sms_service", 
            MessageChannel.PUSH: "push_service",
            MessageChannel.IN_APP: "in_app_service"
        }
        
        logger.info(f"Delivering message via {channel_map.get(MessageChannel.EMAIL, 'unknown')} "
                   f"to user {execution.user_id}")
        
        # Simulate successful delivery
        return True
    
    async def _save_campaign_to_db(self, campaign: Campaign):
        """Save campaign to database"""
        if not self.database:
            return
        
        try:
            campaign_data = asdict(campaign)
            # Convert datetime objects to ISO strings
            campaign_data['start_date'] = campaign.start_date.isoformat()
            campaign_data['end_date'] = campaign.end_date.isoformat()
            campaign_data['created_at'] = campaign.created_at.isoformat()
            campaign_data['updated_at'] = campaign.updated_at.isoformat()
            campaign_data['status'] = campaign.status.value
            campaign_data['channel'] = campaign.channel.value
            
            await self.database.supabase.table('campaigns').insert(campaign_data).execute()
            logger.info(f"Saved campaign {campaign.id} to database")
        except Exception as e:
            logger.error(f"Failed to save campaign to database: {e}")
    
    async def _update_campaign_in_db(self, campaign: Campaign):
        """Update campaign in database"""
        if not self.database:
            return
        
        try:
            update_data = {
                'status': campaign.status.value,
                'updated_at': campaign.updated_at.isoformat()
            }
            
            await self.database.supabase.table('campaigns').update(update_data).eq('id', campaign.id).execute()
            logger.info(f"Updated campaign {campaign.id} in database")
        except Exception as e:
            logger.error(f"Failed to update campaign in database: {e}")
    
    async def _save_execution_to_db(self, execution: CampaignExecution):
        """Save campaign execution to database"""
        if not self.database:
            return
        
        try:
            execution_data = asdict(execution)
            execution_data['scheduled_for'] = execution.scheduled_for.isoformat()
            if execution.sent_at:
                execution_data['sent_at'] = execution.sent_at.isoformat()
            
            await self.database.supabase.table('campaign_executions').insert(execution_data).execute()
            logger.debug(f"Saved execution {execution.id} to database")
        except Exception as e:
            logger.error(f"Failed to save execution to database: {e}")
    
    async def _save_volunteer_registration(self, campaign_id: str, user_id: str, 
                                         event_details: Dict[str, Any]):
        """Save volunteer registration to turnout tracking table"""
        if not self.database:
            return
        
        try:
            campaign = self.campaigns.get(campaign_id)
            if not campaign:
                return
            
            tracking_data = {
                'test_id': campaign.test_id,
                'user_id': user_id,
                'event_id': event_details.get('event_id'),
                'event_name': event_details.get('event_name'),
                'event_date': event_details.get('event_date'),
                'registration_date': datetime.now().isoformat(),
                'metadata': json.dumps(event_details)
            }
            
            await self.database.supabase.table('volunteer_turnout_tracking').insert(tracking_data).execute()
            logger.info(f"Saved volunteer registration for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to save volunteer registration: {e}")
    
    async def _save_volunteer_attendance(self, campaign_id: str, user_id: str, 
                                       attended: bool, event_details: Dict[str, Any]):
        """Save volunteer attendance to turnout tracking table"""
        if not self.database:
            return
        
        try:
            campaign = self.campaigns.get(campaign_id)
            if not campaign:
                return
            
            # Update existing record or create new one
            update_data = {
                'attended': attended,
                'attendance_confirmed_at': datetime.now().isoformat(),
                'hours_contributed': event_details.get('hours', 0),
                'feedback_rating': event_details.get('rating'),
                'metadata': json.dumps(event_details)
            }
            
            result = await self.database.supabase.table('volunteer_turnout_tracking')\
                .update(update_data)\
                .eq('test_id', campaign.test_id)\
                .eq('user_id', user_id)\
                .eq('event_id', event_details.get('event_id'))\
                .execute()
            
            logger.info(f"Saved volunteer attendance for user {user_id}: {attended}")
        except Exception as e:
            logger.error(f"Failed to save volunteer attendance: {e}")

# Usage example
async def example_campaign_usage():
    """Example of how to use the campaign manager"""
    
    # Initialize framework and manager
    ab_framework = ABTestFramework()
    campaign_manager = CampaignManager(ab_framework)
    
    # Create a new volunteer recruitment campaign
    campaign_data = {
        'name': 'Youth Mentorship Drive 2025',
        'description': 'Recruiting volunteers for youth mentorship programs',
        'channel': 'email',
        'start_date': datetime.now().isoformat(),
        'end_date': (datetime.now() + timedelta(days=30)).isoformat(),
        'target_audience': {
            'age': {'min': 18, 'max': 65},
            'interests': ['youth development', 'mentoring', 'education'],
            'location': ['Cincinnati', 'Blue Ash', 'Newport']
        },
        'sample_size': 500,
        'created_by': 'campaign_manager_001'
    }
    
    campaign_id = await campaign_manager.create_volunteer_campaign(campaign_data)
    print(f"Created campaign: {campaign_id}")
    
    # Launch the campaign
    success = await campaign_manager.launch_campaign(campaign_id)
    print(f"Campaign launched: {success}")
    
    # Send personalized message to a user
    user_profile = {
        'first_name': 'Sarah',
        'interests': 'youth development',
        'city': 'Cincinnati',
        'volunteer_history': {'previous_hours': 25}
    }
    
    await campaign_manager.send_personalized_message(campaign_id, 'user_123', user_profile)
    
    # Track user engagement
    await campaign_manager.track_user_engagement(campaign_id, 'user_123', 'message_opened')
    await campaign_manager.track_user_engagement(campaign_id, 'user_123', 'clicked')
    
    # Track registration and attendance
    event_details = {
        'event_id': 'mentorship_training_001',
        'event_name': 'Youth Mentorship Training',
        'event_date': (datetime.now() + timedelta(days=7)).isoformat(),
        'hours': 3
    }
    
    await campaign_manager.track_volunteer_registration(campaign_id, 'user_123', event_details)
    await campaign_manager.track_volunteer_attendance(campaign_id, 'user_123', True, event_details)
    
    # Get campaign performance
    performance = await campaign_manager.get_campaign_performance(campaign_id)
    print(f"Campaign performance: {performance}")

if __name__ == "__main__":
    asyncio.run(example_campaign_usage())