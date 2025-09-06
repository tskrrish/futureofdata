"""
Email Campaign System with Dynamic Audience Segmentation
Supports both Mailchimp and SendGrid integrations for targeted volunteer campaigns
"""
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    # Mock pandas DataFrame for basic testing
    class MockDataFrame:
        def __init__(self, data=None):
            self.data = data or []
        def __len__(self):
            return len(self.data)
        def empty(self):
            return len(self.data) == 0
        def iterrows(self):
            for i, row in enumerate(self.data):
                yield i, row
        def merge(self, *args, **kwargs):
            return MockDataFrame()
        def fillna(self, value):
            return self
        def copy(self):
            return MockDataFrame(self.data.copy() if self.data else [])
    pd = type('MockPandas', (), {'DataFrame': MockDataFrame})()

import asyncio
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class CampaignStatus(Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class SegmentationType(Enum):
    ENGAGEMENT_LEVEL = "engagement_level"
    VOLUNTEER_EXPERIENCE = "volunteer_experience" 
    BRANCH_AFFINITY = "branch_affinity"
    CATEGORY_INTEREST = "category_interest"
    TIME_SINCE_LAST_ACTIVITY = "time_since_last_activity"
    DEMOGRAPHIC = "demographic"
    CUSTOM = "custom"

@dataclass
class SegmentCriteria:
    """Defines criteria for audience segmentation"""
    type: SegmentationType
    field: str
    operator: str  # eq, gt, lt, gte, lte, in, contains, between
    value: Union[str, int, float, List[Any]]
    description: str = ""

@dataclass
class Campaign:
    """Email campaign definition"""
    id: str
    name: str
    description: str
    subject_line: str
    email_content: str
    sender_name: str
    sender_email: str
    segments: List[SegmentCriteria]
    status: CampaignStatus
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    recipient_count: int = 0
    open_rate: float = 0.0
    click_rate: float = 0.0
    metadata: Dict[str, Any] = None

    def to_dict(self):
        return {
            **asdict(self),
            'status': self.status.value,
            'segments': [asdict(s) for s in self.segments],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None
        }

class AudienceSegmentationEngine:
    """Engine for creating dynamic audience segments from volunteer data"""
    
    def __init__(self, volunteer_data: Dict[str, Any]):
        self.volunteer_data = volunteer_data
        self.volunteers_df = pd.DataFrame(volunteer_data.get('volunteers', []))
        self.interactions_df = pd.DataFrame(volunteer_data.get('interactions', []))
        
    def create_segment(self, criteria: List[SegmentCriteria]) -> pd.DataFrame:
        """Create audience segment based on criteria"""
        try:
            # Start with all volunteers
            segment_df = self.volunteers_df.copy()
            
            for criterion in criteria:
                segment_df = self._apply_criterion(segment_df, criterion)
                
            return segment_df
            
        except Exception as e:
            logger.error(f"Error creating segment: {e}")
            return pd.DataFrame()
    
    def _apply_criterion(self, df: pd.DataFrame, criterion: SegmentCriteria) -> pd.DataFrame:
        """Apply a single criterion to the dataframe"""
        try:
            if criterion.type == SegmentationType.ENGAGEMENT_LEVEL:
                return self._filter_by_engagement(df, criterion)
            elif criterion.type == SegmentationType.VOLUNTEER_EXPERIENCE:
                return self._filter_by_experience(df, criterion)
            elif criterion.type == SegmentationType.BRANCH_AFFINITY:
                return self._filter_by_branch(df, criterion)
            elif criterion.type == SegmentationType.CATEGORY_INTEREST:
                return self._filter_by_category(df, criterion)
            elif criterion.type == SegmentationType.TIME_SINCE_LAST_ACTIVITY:
                return self._filter_by_last_activity(df, criterion)
            elif criterion.type == SegmentationType.DEMOGRAPHIC:
                return self._filter_by_demographic(df, criterion)
            elif criterion.type == SegmentationType.CUSTOM:
                return self._filter_by_custom(df, criterion)
            else:
                return df
                
        except Exception as e:
            logger.error(f"Error applying criterion {criterion.type}: {e}")
            return df
    
    def _filter_by_engagement(self, df: pd.DataFrame, criterion: SegmentCriteria) -> pd.DataFrame:
        """Filter by engagement level (hours, sessions, etc.)"""
        if 'contact_id' not in df.columns:
            return df
            
        # Calculate engagement metrics from interactions
        engagement_stats = self.interactions_df.groupby('contact_id').agg({
            'hours': 'sum',
            'date': 'count',  # sessions
            'project_id': 'nunique'  # unique projects
        }).reset_index()
        engagement_stats.columns = ['contact_id', 'total_hours', 'total_sessions', 'unique_projects']
        
        # Merge with volunteers
        df_with_engagement = df.merge(engagement_stats, on='contact_id', how='left').fillna(0)
        
        # Apply filter based on criterion
        field_map = {
            'hours': 'total_hours',
            'sessions': 'total_sessions', 
            'projects': 'unique_projects'
        }
        
        field = field_map.get(criterion.field, criterion.field)
        return self._apply_numeric_filter(df_with_engagement, field, criterion.operator, criterion.value)
    
    def _filter_by_experience(self, df: pd.DataFrame, criterion: SegmentCriteria) -> pd.DataFrame:
        """Filter by volunteer experience level"""
        if criterion.field == 'experience_level' and 'experience_level' in df.columns:
            return self._apply_filter(df, 'experience_level', criterion.operator, criterion.value)
        return df
    
    def _filter_by_branch(self, df: pd.DataFrame, criterion: SegmentCriteria) -> pd.DataFrame:
        """Filter by branch affinity"""
        if 'contact_id' not in df.columns:
            return df
            
        # Get branch preferences from interactions
        branch_stats = self.interactions_df.groupby('contact_id')['branch_short'].apply(
            lambda x: x.value_counts().index[0] if len(x) > 0 else None
        ).reset_index()
        branch_stats.columns = ['contact_id', 'preferred_branch']
        
        df_with_branch = df.merge(branch_stats, on='contact_id', how='left')
        return self._apply_filter(df_with_branch, 'preferred_branch', criterion.operator, criterion.value)
    
    def _filter_by_category(self, df: pd.DataFrame, criterion: SegmentCriteria) -> pd.DataFrame:
        """Filter by category interest"""
        if 'contact_id' not in df.columns:
            return df
            
        # Get category preferences from interactions
        category_stats = self.interactions_df.groupby('contact_id')['project_category'].apply(
            lambda x: x.value_counts().index[0] if len(x) > 0 else None
        ).reset_index()
        category_stats.columns = ['contact_id', 'preferred_category']
        
        df_with_category = df.merge(category_stats, on='contact_id', how='left')
        return self._apply_filter(df_with_category, 'preferred_category', criterion.operator, criterion.value)
    
    def _filter_by_last_activity(self, df: pd.DataFrame, criterion: SegmentCriteria) -> pd.DataFrame:
        """Filter by time since last activity"""
        if 'contact_id' not in df.columns:
            return df
            
        # Get last activity date
        last_activity = self.interactions_df.groupby('contact_id')['date'].max().reset_index()
        last_activity.columns = ['contact_id', 'last_activity_date']
        
        df_with_activity = df.merge(last_activity, on='contact_id', how='left')
        
        # Calculate days since last activity
        df_with_activity['days_since_last_activity'] = (
            datetime.now() - pd.to_datetime(df_with_activity['last_activity_date'])
        ).dt.days
        
        return self._apply_numeric_filter(df_with_activity, 'days_since_last_activity', 
                                        criterion.operator, criterion.value)
    
    def _filter_by_demographic(self, df: pd.DataFrame, criterion: SegmentCriteria) -> pd.DataFrame:
        """Filter by demographic data"""
        if criterion.field in df.columns:
            return self._apply_filter(df, criterion.field, criterion.operator, criterion.value)
        return df
    
    def _filter_by_custom(self, df: pd.DataFrame, criterion: SegmentCriteria) -> pd.DataFrame:
        """Apply custom filter logic"""
        if criterion.field in df.columns:
            return self._apply_filter(df, criterion.field, criterion.operator, criterion.value)
        return df
    
    def _apply_filter(self, df: pd.DataFrame, field: str, operator: str, value: Any) -> pd.DataFrame:
        """Apply generic filter to dataframe"""
        if field not in df.columns:
            return df
            
        if operator == 'eq':
            return df[df[field] == value]
        elif operator == 'in':
            return df[df[field].isin(value)]
        elif operator == 'contains':
            return df[df[field].str.contains(str(value), na=False)]
        else:
            return self._apply_numeric_filter(df, field, operator, value)
    
    def _apply_numeric_filter(self, df: pd.DataFrame, field: str, operator: str, value: Any) -> pd.DataFrame:
        """Apply numeric filter operations"""
        if field not in df.columns:
            return df
            
        try:
            if operator == 'gt':
                return df[df[field] > value]
            elif operator == 'lt':
                return df[df[field] < value]
            elif operator == 'gte':
                return df[df[field] >= value]
            elif operator == 'lte':
                return df[df[field] <= value]
            elif operator == 'between' and isinstance(value, list) and len(value) == 2:
                return df[(df[field] >= value[0]) & (df[field] <= value[1])]
            else:
                return df
        except Exception:
            return df

class EmailProvider(ABC):
    """Abstract base class for email providers"""
    
    @abstractmethod
    async def send_campaign(self, campaign: Campaign, recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def create_list(self, name: str, recipients: List[Dict[str, Any]]) -> str:
        pass
    
    @abstractmethod
    async def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        pass

class MailchimpProvider(EmailProvider):
    """Mailchimp email provider implementation"""
    
    def __init__(self, api_key: str, server_prefix: str):
        self.api_key = api_key
        self.server_prefix = server_prefix
        self.base_url = f"https://{server_prefix}.api.mailchimp.com/3.0"
        
    async def send_campaign(self, campaign: Campaign, recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send campaign via Mailchimp"""
        try:
            # Create audience list
            list_id = await self.create_list(f"{campaign.name}_audience", recipients)
            
            # Create campaign
            campaign_data = {
                "type": "regular",
                "recipients": {"list_id": list_id},
                "settings": {
                    "subject_line": campaign.subject_line,
                    "from_name": campaign.sender_name,
                    "reply_to": campaign.sender_email,
                    "title": campaign.name
                }
            }
            
            # Mock API call - in production, use mailchimp3 library
            logger.info(f"Would create Mailchimp campaign: {campaign.name}")
            logger.info(f"Recipients: {len(recipients)}")
            
            return {
                "success": True,
                "campaign_id": f"mc_{campaign.id}",
                "list_id": list_id,
                "recipient_count": len(recipients)
            }
            
        except Exception as e:
            logger.error(f"Mailchimp campaign send error: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_list(self, name: str, recipients: List[Dict[str, Any]]) -> str:
        """Create audience list in Mailchimp"""
        try:
            # Mock implementation - in production, use Mailchimp API
            list_id = f"mc_list_{uuid.uuid4().hex[:8]}"
            logger.info(f"Would create Mailchimp list '{name}' with {len(recipients)} recipients")
            return list_id
            
        except Exception as e:
            logger.error(f"Mailchimp list creation error: {e}")
            return ""
    
    async def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign statistics from Mailchimp"""
        try:
            # Mock stats - in production, fetch from Mailchimp API
            return {
                "opens": {"opens_total": 150, "unique_opens": 120, "open_rate": 0.24},
                "clicks": {"clicks_total": 45, "unique_clicks": 38, "click_rate": 0.076},
                "emails_sent": 500
            }
        except Exception as e:
            logger.error(f"Mailchimp stats error: {e}")
            return {}

class SendGridProvider(EmailProvider):
    """SendGrid email provider implementation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    async def send_campaign(self, campaign: Campaign, recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send campaign via SendGrid"""
        try:
            # Create contact list
            list_id = await self.create_list(f"{campaign.name}_contacts", recipients)
            
            # Create single send campaign
            campaign_data = {
                "name": campaign.name,
                "send_to": {"list_ids": [list_id]},
                "email_config": {
                    "subject": campaign.subject_line,
                    "html_content": campaign.email_content,
                    "sender_id": 1,  # Would be actual sender ID
                    "suppression_group_id": 1
                }
            }
            
            # Mock API call - in production, use sendgrid library
            logger.info(f"Would create SendGrid campaign: {campaign.name}")
            logger.info(f"Recipients: {len(recipients)}")
            
            return {
                "success": True,
                "campaign_id": f"sg_{campaign.id}",
                "list_id": list_id,
                "recipient_count": len(recipients)
            }
            
        except Exception as e:
            logger.error(f"SendGrid campaign send error: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_list(self, name: str, recipients: List[Dict[str, Any]]) -> str:
        """Create contact list in SendGrid"""
        try:
            # Mock implementation - in production, use SendGrid API
            list_id = f"sg_list_{uuid.uuid4().hex[:8]}"
            logger.info(f"Would create SendGrid list '{name}' with {len(recipients)} recipients")
            return list_id
            
        except Exception as e:
            logger.error(f"SendGrid list creation error: {e}")
            return ""
    
    async def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign statistics from SendGrid"""
        try:
            # Mock stats - in production, fetch from SendGrid API
            return {
                "unique_opens": 135,
                "unique_clicks": 42,
                "delivered": 485,
                "bounces": 5,
                "spam_reports": 1
            }
        except Exception as e:
            logger.error(f"SendGrid stats error: {e}")
            return {}

class EmailCampaignManager:
    """Main campaign management system"""
    
    def __init__(self, volunteer_data: Dict[str, Any], database=None):
        self.volunteer_data = volunteer_data
        self.database = database
        self.segmentation_engine = AudienceSegmentationEngine(volunteer_data)
        self.providers = {}
        self.campaigns = {}
        
    def add_provider(self, name: str, provider: EmailProvider):
        """Add email provider"""
        self.providers[name] = provider
    
    async def create_campaign(self, 
                            name: str,
                            description: str,
                            subject_line: str,
                            email_content: str,
                            sender_name: str,
                            sender_email: str,
                            segments: List[SegmentCriteria],
                            scheduled_at: Optional[datetime] = None) -> Campaign:
        """Create a new campaign"""
        
        campaign = Campaign(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            subject_line=subject_line,
            email_content=email_content,
            sender_name=sender_name,
            sender_email=sender_email,
            segments=segments,
            status=CampaignStatus.DRAFT,
            created_at=datetime.now(),
            scheduled_at=scheduled_at,
            metadata={}
        )
        
        self.campaigns[campaign.id] = campaign
        
        # Save to database if available
        if self.database:
            await self._save_campaign_to_db(campaign)
        
        logger.info(f"Created campaign: {campaign.name} ({campaign.id})")
        return campaign
    
    async def get_campaign_audience(self, campaign_id: str) -> List[Dict[str, Any]]:
        """Get the target audience for a campaign"""
        if campaign_id not in self.campaigns:
            return []
            
        campaign = self.campaigns[campaign_id]
        
        # Create segment based on criteria
        segment_df = self.segmentation_engine.create_segment(campaign.segments)
        
        # Convert to recipient format
        recipients = []
        for _, volunteer in segment_df.iterrows():
            recipient = {
                "email": volunteer.get('email', ''),
                "first_name": volunteer.get('first_name', ''),
                "last_name": volunteer.get('last_name', ''),
                "contact_id": volunteer.get('contact_id'),
                "merge_fields": {
                    "FNAME": volunteer.get('first_name', ''),
                    "LNAME": volunteer.get('last_name', ''),
                    "BRANCH": volunteer.get('member_branch', ''),
                    "EXPERIENCE": volunteer.get('experience_level', 1)
                }
            }
            
            if recipient["email"]:  # Only include if email exists
                recipients.append(recipient)
        
        # Update recipient count
        campaign.recipient_count = len(recipients)
        
        return recipients
    
    async def send_campaign(self, campaign_id: str, provider_name: str = "mailchimp") -> Dict[str, Any]:
        """Send a campaign using specified provider"""
        if campaign_id not in self.campaigns:
            return {"success": False, "error": "Campaign not found"}
            
        if provider_name not in self.providers:
            return {"success": False, "error": f"Provider {provider_name} not configured"}
        
        campaign = self.campaigns[campaign_id]
        provider = self.providers[provider_name]
        
        # Get target audience
        recipients = await self.get_campaign_audience(campaign_id)
        
        if not recipients:
            return {"success": False, "error": "No recipients found for campaign"}
        
        # Send via provider
        result = await provider.send_campaign(campaign, recipients)
        
        if result.get("success"):
            campaign.status = CampaignStatus.ACTIVE
            campaign.sent_at = datetime.now()
            campaign.recipient_count = len(recipients)
            
            # Update in database
            if self.database:
                await self._save_campaign_to_db(campaign)
        
        return result
    
    async def get_campaign_analytics(self, campaign_id: str, provider_name: str = "mailchimp") -> Dict[str, Any]:
        """Get campaign analytics"""
        if campaign_id not in self.campaigns:
            return {}
            
        if provider_name not in self.providers:
            return {}
        
        campaign = self.campaigns[campaign_id]
        provider = self.providers[provider_name]
        
        # Get stats from provider
        stats = await provider.get_campaign_stats(f"{provider_name[0:2]}_{campaign_id}")
        
        # Update campaign stats
        if "open_rate" in stats or "opens" in stats:
            if "opens" in stats:
                campaign.open_rate = stats["opens"].get("open_rate", 0)
            else:
                campaign.open_rate = stats.get("open_rate", 0)
                
        if "click_rate" in stats or "clicks" in stats:
            if "clicks" in stats:
                campaign.click_rate = stats["clicks"].get("click_rate", 0)
            else:
                campaign.click_rate = stats.get("click_rate", 0)
        
        return {
            "campaign": campaign.to_dict(),
            "provider_stats": stats
        }
    
    def list_campaigns(self, status: Optional[CampaignStatus] = None) -> List[Campaign]:
        """List campaigns with optional status filter"""
        campaigns = list(self.campaigns.values())
        
        if status:
            campaigns = [c for c in campaigns if c.status == status]
            
        return sorted(campaigns, key=lambda x: x.created_at, reverse=True)
    
    async def _save_campaign_to_db(self, campaign: Campaign):
        """Save campaign to database"""
        try:
            if not self.database or not hasattr(self.database, 'supabase'):
                return
                
            campaign_data = {
                'id': campaign.id,
                'name': campaign.name,
                'description': campaign.description,
                'subject_line': campaign.subject_line,
                'email_content': campaign.email_content,
                'sender_name': campaign.sender_name,
                'sender_email': campaign.sender_email,
                'segments': json.dumps([asdict(s) for s in campaign.segments]),
                'status': campaign.status.value,
                'recipient_count': campaign.recipient_count,
                'open_rate': campaign.open_rate,
                'click_rate': campaign.click_rate,
                'created_at': campaign.created_at.isoformat(),
                'scheduled_at': campaign.scheduled_at.isoformat() if campaign.scheduled_at else None,
                'sent_at': campaign.sent_at.isoformat() if campaign.sent_at else None,
                'metadata': json.dumps(campaign.metadata or {})
            }
            
            # Try to create campaigns table and insert
            result = self.database.supabase.table('email_campaigns').upsert(campaign_data).execute()
            
        except Exception as e:
            logger.error(f"Error saving campaign to database: {e}")

# Pre-defined segment templates
class SegmentTemplates:
    """Pre-defined segment templates for common use cases"""
    
    @staticmethod
    def high_engagement_volunteers() -> List[SegmentCriteria]:
        """Volunteers with high engagement (20+ hours)"""
        return [
            SegmentCriteria(
                type=SegmentationType.ENGAGEMENT_LEVEL,
                field="hours",
                operator="gte",
                value=20,
                description="Volunteers with 20+ hours of service"
            )
        ]
    
    @staticmethod
    def inactive_volunteers(days: int = 90) -> List[SegmentCriteria]:
        """Volunteers inactive for specified days"""
        return [
            SegmentCriteria(
                type=SegmentationType.TIME_SINCE_LAST_ACTIVITY,
                field="days_since_last_activity",
                operator="gte",
                value=days,
                description=f"Volunteers inactive for {days}+ days"
            )
        ]
    
    @staticmethod
    def new_volunteers(days: int = 30) -> List[SegmentCriteria]:
        """Recently joined volunteers"""
        return [
            SegmentCriteria(
                type=SegmentationType.TIME_SINCE_LAST_ACTIVITY,
                field="days_since_last_activity",
                operator="lte",
                value=days,
                description=f"Volunteers active within {days} days"
            )
        ]
    
    @staticmethod
    def branch_specific(branch: str) -> List[SegmentCriteria]:
        """Volunteers affiliated with specific branch"""
        return [
            SegmentCriteria(
                type=SegmentationType.BRANCH_AFFINITY,
                field="preferred_branch",
                operator="eq",
                value=branch,
                description=f"Volunteers affiliated with {branch}"
            )
        ]
    
    @staticmethod
    def category_interested(category: str) -> List[SegmentCriteria]:
        """Volunteers interested in specific category"""
        return [
            SegmentCriteria(
                type=SegmentationType.CATEGORY_INTEREST,
                field="preferred_category",
                operator="eq",
                value=category,
                description=f"Volunteers interested in {category}"
            )
        ]
    
    @staticmethod
    def youth_demographic(max_age: int = 35) -> List[SegmentCriteria]:
        """Young volunteers"""
        return [
            SegmentCriteria(
                type=SegmentationType.DEMOGRAPHIC,
                field="age",
                operator="lte",
                value=max_age,
                description=f"Volunteers aged {max_age} and under"
            )
        ]