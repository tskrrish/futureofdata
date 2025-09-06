"""
Data Retention Policy with Lawful Hold Mechanism
Handles automated archival/deletion of user data with legal hold safeguards
"""
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
import asyncio
import logging
from dataclasses import dataclass, asdict
from supabase import Client

logger = logging.getLogger(__name__)

class RetentionAction(Enum):
    """Actions that can be taken on data"""
    ARCHIVE = "archive"
    DELETE = "delete"
    RETAIN = "retain"

class DataCategory(Enum):
    """Categories of data for retention policies"""
    USER_PROFILES = "user_profiles"
    MESSAGES = "messages"
    ANALYTICS = "analytics"
    FEEDBACK = "feedback"
    MATCHES = "matches"
    CONVERSATIONS = "conversations"
    PREFERENCES = "preferences"

class LegalHoldStatus(Enum):
    """Status of legal holds"""
    ACTIVE = "active"
    PENDING = "pending"
    RELEASED = "released"
    EXPIRED = "expired"

@dataclass
class RetentionPolicy:
    """Data retention policy configuration"""
    id: str
    name: str
    description: str
    data_category: DataCategory
    retention_period_days: int
    archive_after_days: Optional[int] = None
    action: RetentionAction = RetentionAction.DELETE
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class LegalHold:
    """Legal hold configuration"""
    id: str
    case_name: str
    description: str
    data_categories: List[DataCategory]
    user_ids: Optional[List[str]] = None  # Specific users, None = all users
    keywords: Optional[List[str]] = None  # Content keywords to match
    status: LegalHoldStatus = LegalHoldStatus.ACTIVE
    created_by: str = "system"
    created_at: datetime = None
    expires_at: Optional[datetime] = None
    released_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class RetentionEvent:
    """Record of retention actions taken"""
    id: str
    policy_id: str
    table_name: str
    record_id: str
    action_taken: RetentionAction
    records_affected: int
    reason: str
    legal_hold_applied: bool = False
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class DataRetentionManager:
    """Main class for managing data retention policies and lawful holds"""
    
    def __init__(self, database_client: Client):
        self.db = database_client
        self.policies: Dict[str, RetentionPolicy] = {}
        self.legal_holds: Dict[str, LegalHold] = {}
        self.archive_storage_path = "/data/archives"
        
    async def initialize_retention_tables(self):
        """Initialize database tables for retention management"""
        
        retention_policies_sql = """
        CREATE TABLE IF NOT EXISTS retention_policies (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            description TEXT,
            data_category VARCHAR(50) NOT NULL,
            retention_period_days INTEGER NOT NULL,
            archive_after_days INTEGER,
            action VARCHAR(20) NOT NULL DEFAULT 'delete',
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        legal_holds_sql = """
        CREATE TABLE IF NOT EXISTS legal_holds (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            case_name VARCHAR(255) NOT NULL,
            description TEXT,
            data_categories TEXT[] NOT NULL,
            user_ids UUID[],
            keywords TEXT[],
            status VARCHAR(20) DEFAULT 'active',
            created_by VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            expires_at TIMESTAMP WITH TIME ZONE,
            released_at TIMESTAMP WITH TIME ZONE
        );
        """
        
        retention_events_sql = """
        CREATE TABLE IF NOT EXISTS retention_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            policy_id UUID REFERENCES retention_policies(id),
            table_name VARCHAR(100) NOT NULL,
            record_id VARCHAR(255) NOT NULL,
            action_taken VARCHAR(20) NOT NULL,
            records_affected INTEGER DEFAULT 1,
            reason TEXT,
            legal_hold_applied BOOLEAN DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        archived_data_sql = """
        CREATE TABLE IF NOT EXISTS archived_data (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            original_table VARCHAR(100) NOT NULL,
            original_id VARCHAR(255) NOT NULL,
            data_content JSONB NOT NULL,
            archived_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            policy_id UUID REFERENCES retention_policies(id),
            restore_before TIMESTAMP WITH TIME ZONE
        );
        """
        
        # Index for performance
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_retention_policies_active ON retention_policies(is_active);",
            "CREATE INDEX IF NOT EXISTS idx_legal_holds_status ON legal_holds(status);",
            "CREATE INDEX IF NOT EXISTS idx_retention_events_policy ON retention_events(policy_id);",
            "CREATE INDEX IF NOT EXISTS idx_archived_data_table ON archived_data(original_table);",
            "CREATE INDEX IF NOT EXISTS idx_archived_data_restore ON archived_data(restore_before);"
        ]
        
        tables = [retention_policies_sql, legal_holds_sql, retention_events_sql, archived_data_sql] + indexes_sql
        
        logger.info("🗄️ Setting up data retention tables...")
        for sql in tables:
            try:
                logger.info(f"📝 Prepared retention table SQL: {sql.split()[2] if 'CREATE TABLE' in sql else 'INDEX'}")
            except Exception as e:
                logger.warning(f"⚠️ Table setup note: {e}")
        
        logger.info("✅ Data retention schema ready!")
    
    async def create_retention_policy(self, policy: RetentionPolicy) -> bool:
        """Create a new retention policy"""
        try:
            policy_data = {
                'id': policy.id,
                'name': policy.name,
                'description': policy.description,
                'data_category': policy.data_category.value,
                'retention_period_days': policy.retention_period_days,
                'archive_after_days': policy.archive_after_days,
                'action': policy.action.value,
                'is_active': policy.is_active,
                'created_at': policy.created_at.isoformat(),
                'updated_at': policy.updated_at.isoformat()
            }
            
            result = self.db.table('retention_policies').insert(policy_data).execute()
            if result.data:
                self.policies[policy.id] = policy
                logger.info(f"✅ Created retention policy: {policy.name}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error creating retention policy: {e}")
            return False
    
    async def create_legal_hold(self, hold: LegalHold) -> bool:
        """Create a new legal hold"""
        try:
            hold_data = {
                'id': hold.id,
                'case_name': hold.case_name,
                'description': hold.description,
                'data_categories': [cat.value for cat in hold.data_categories],
                'user_ids': hold.user_ids,
                'keywords': hold.keywords,
                'status': hold.status.value,
                'created_by': hold.created_by,
                'created_at': hold.created_at.isoformat(),
                'expires_at': hold.expires_at.isoformat() if hold.expires_at else None,
                'released_at': hold.released_at.isoformat() if hold.released_at else None
            }
            
            result = self.db.table('legal_holds').insert(hold_data).execute()
            if result.data:
                self.legal_holds[hold.id] = hold
                logger.info(f"✅ Created legal hold: {hold.case_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error creating legal hold: {e}")
            return False
    
    async def is_under_legal_hold(self, data_category: DataCategory, record_data: Dict[str, Any], 
                                user_id: str = None) -> List[LegalHold]:
        """Check if data is under any active legal holds"""
        applicable_holds = []
        
        for hold in self.legal_holds.values():
            if hold.status != LegalHoldStatus.ACTIVE:
                continue
                
            # Check if hold has expired
            if hold.expires_at and datetime.now() > hold.expires_at:
                continue
                
            # Check data category match
            if data_category not in hold.data_categories:
                continue
            
            # Check user-specific holds
            if hold.user_ids and user_id and user_id not in hold.user_ids:
                continue
            
            # Check keyword matches in content
            if hold.keywords:
                content_text = str(record_data).lower()
                if not any(keyword.lower() in content_text for keyword in hold.keywords):
                    continue
            
            applicable_holds.append(hold)
        
        return applicable_holds
    
    async def archive_data(self, table_name: str, record_id: str, data: Dict[str, Any], 
                          policy_id: str, restore_before: Optional[datetime] = None) -> bool:
        """Archive data to the archived_data table"""
        try:
            archive_record = {
                'original_table': table_name,
                'original_id': record_id,
                'data_content': json.dumps(data),
                'policy_id': policy_id,
                'restore_before': restore_before.isoformat() if restore_before else None,
                'archived_at': datetime.now().isoformat()
            }
            
            result = self.db.table('archived_data').insert(archive_record).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"❌ Error archiving data: {e}")
            return False
    
    async def apply_retention_policy(self, policy: RetentionPolicy) -> Dict[str, Any]:
        """Apply a retention policy to eligible data"""
        if not policy.is_active:
            return {'skipped': True, 'reason': 'Policy inactive'}
        
        # Map data categories to tables
        table_mapping = {
            DataCategory.USER_PROFILES: 'users',
            DataCategory.MESSAGES: 'messages',
            DataCategory.ANALYTICS: 'analytics_events',
            DataCategory.FEEDBACK: 'volunteer_feedback',
            DataCategory.MATCHES: 'volunteer_matches',
            DataCategory.CONVERSATIONS: 'conversations',
            DataCategory.PREFERENCES: 'user_preferences'
        }
        
        table_name = table_mapping.get(policy.data_category)
        if not table_name:
            return {'error': f'No table mapping for category {policy.data_category}'}
        
        cutoff_date = datetime.now() - timedelta(days=policy.retention_period_days)
        archive_date = None
        if policy.archive_after_days:
            archive_date = datetime.now() - timedelta(days=policy.archive_after_days)
        
        try:
            # Get eligible records
            query = self.db.table(table_name).select('*').lt('created_at', cutoff_date.isoformat())
            result = query.execute()
            
            eligible_records = result.data
            processed_count = 0
            legal_hold_count = 0
            archived_count = 0
            deleted_count = 0
            
            for record in eligible_records:
                user_id = record.get('user_id')
                
                # Check for legal holds
                legal_holds = await self.is_under_legal_hold(
                    policy.data_category, record, user_id
                )
                
                if legal_holds:
                    legal_hold_count += 1
                    # Log the legal hold application
                    event = RetentionEvent(
                        id=str(uuid.uuid4()),
                        policy_id=policy.id,
                        table_name=table_name,
                        record_id=str(record.get('id', '')),
                        action_taken=RetentionAction.RETAIN,
                        records_affected=1,
                        reason=f"Legal hold applied: {', '.join([h.case_name for h in legal_holds])}",
                        legal_hold_applied=True
                    )
                    await self._log_retention_event(event)
                    continue
                
                record_id = str(record.get('id', ''))
                
                if policy.action == RetentionAction.ARCHIVE:
                    # Archive the data
                    restore_date = datetime.now() + timedelta(days=365)  # Keep archives for 1 year
                    archived = await self.archive_data(table_name, record_id, record, policy.id, restore_date)
                    
                    if archived:
                        # Delete from original table
                        delete_result = self.db.table(table_name).delete().eq('id', record['id']).execute()
                        if delete_result.data:
                            archived_count += 1
                
                elif policy.action == RetentionAction.DELETE:
                    # Delete the record
                    delete_result = self.db.table(table_name).delete().eq('id', record['id']).execute()
                    if delete_result.data:
                        deleted_count += 1
                
                processed_count += 1
            
            # Log the retention policy execution
            action_summary = f"Processed: {processed_count}, Archived: {archived_count}, Deleted: {deleted_count}, Legal Holds: {legal_hold_count}"
            
            event = RetentionEvent(
                id=str(uuid.uuid4()),
                policy_id=policy.id,
                table_name=table_name,
                record_id="BATCH",
                action_taken=policy.action,
                records_affected=processed_count,
                reason=f"Retention policy execution: {action_summary}"
            )
            await self._log_retention_event(event)
            
            return {
                'success': True,
                'policy_name': policy.name,
                'table_processed': table_name,
                'total_eligible': len(eligible_records),
                'processed_count': processed_count,
                'archived_count': archived_count,
                'deleted_count': deleted_count,
                'legal_hold_count': legal_hold_count
            }
            
        except Exception as e:
            logger.error(f"❌ Error applying retention policy {policy.name}: {e}")
            return {'error': str(e)}
    
    async def _log_retention_event(self, event: RetentionEvent) -> bool:
        """Log a retention event"""
        try:
            event_data = {
                'id': event.id,
                'policy_id': event.policy_id,
                'table_name': event.table_name,
                'record_id': event.record_id,
                'action_taken': event.action_taken.value,
                'records_affected': event.records_affected,
                'reason': event.reason,
                'legal_hold_applied': event.legal_hold_applied,
                'created_at': event.created_at.isoformat()
            }
            
            result = self.db.table('retention_events').insert(event_data).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"❌ Error logging retention event: {e}")
            return False
    
    async def run_retention_policies(self) -> List[Dict[str, Any]]:
        """Run all active retention policies"""
        results = []
        
        # Load policies from database
        await self.load_policies()
        
        for policy in self.policies.values():
            if policy.is_active:
                logger.info(f"🔄 Running retention policy: {policy.name}")
                result = await self.apply_retention_policy(policy)
                results.append(result)
        
        return results
    
    async def load_policies(self):
        """Load retention policies from database"""
        try:
            result = self.db.table('retention_policies').select('*').eq('is_active', True).execute()
            
            for policy_data in result.data:
                policy = RetentionPolicy(
                    id=policy_data['id'],
                    name=policy_data['name'],
                    description=policy_data['description'],
                    data_category=DataCategory(policy_data['data_category']),
                    retention_period_days=policy_data['retention_period_days'],
                    archive_after_days=policy_data['archive_after_days'],
                    action=RetentionAction(policy_data['action']),
                    is_active=policy_data['is_active'],
                    created_at=datetime.fromisoformat(policy_data['created_at'].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(policy_data['updated_at'].replace('Z', '+00:00'))
                )
                self.policies[policy.id] = policy
        except Exception as e:
            logger.error(f"❌ Error loading policies: {e}")
    
    async def load_legal_holds(self):
        """Load active legal holds from database"""
        try:
            result = self.db.table('legal_holds').select('*').eq('status', 'active').execute()
            
            for hold_data in result.data:
                hold = LegalHold(
                    id=hold_data['id'],
                    case_name=hold_data['case_name'],
                    description=hold_data['description'],
                    data_categories=[DataCategory(cat) for cat in hold_data['data_categories']],
                    user_ids=hold_data['user_ids'],
                    keywords=hold_data['keywords'],
                    status=LegalHoldStatus(hold_data['status']),
                    created_by=hold_data['created_by'],
                    created_at=datetime.fromisoformat(hold_data['created_at'].replace('Z', '+00:00')),
                    expires_at=datetime.fromisoformat(hold_data['expires_at'].replace('Z', '+00:00')) if hold_data['expires_at'] else None,
                    released_at=datetime.fromisoformat(hold_data['released_at'].replace('Z', '+00:00')) if hold_data['released_at'] else None
                )
                self.legal_holds[hold.id] = hold
        except Exception as e:
            logger.error(f"❌ Error loading legal holds: {e}")
    
    async def release_legal_hold(self, hold_id: str, released_by: str) -> bool:
        """Release a legal hold"""
        try:
            update_data = {
                'status': LegalHoldStatus.RELEASED.value,
                'released_at': datetime.now().isoformat()
            }
            
            result = self.db.table('legal_holds').update(update_data).eq('id', hold_id).execute()
            
            if result.data:
                if hold_id in self.legal_holds:
                    self.legal_holds[hold_id].status = LegalHoldStatus.RELEASED
                    self.legal_holds[hold_id].released_at = datetime.now()
                
                logger.info(f"✅ Released legal hold: {hold_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error releasing legal hold: {e}")
            return False
    
    async def get_retention_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate a retention activity report"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get retention events
            events_result = self.db.table('retention_events')\
                .select('*')\
                .gte('created_at', start_date)\
                .execute()
            
            # Get legal holds
            holds_result = self.db.table('legal_holds')\
                .select('*')\
                .gte('created_at', start_date)\
                .execute()
            
            # Aggregate statistics
            events = events_result.data
            total_records_processed = sum(event['records_affected'] for event in events)
            actions_by_type = {}
            
            for event in events:
                action = event['action_taken']
                actions_by_type[action] = actions_by_type.get(action, 0) + event['records_affected']
            
            return {
                'report_period_days': days,
                'total_events': len(events),
                'total_records_processed': total_records_processed,
                'actions_by_type': actions_by_type,
                'legal_holds_created': len(holds_result.data),
                'generated_at': datetime.now().isoformat(),
                'recent_events': events[:10]  # Last 10 events for details
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating retention report: {e}")
            return {'error': str(e)}