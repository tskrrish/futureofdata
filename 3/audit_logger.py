"""
Audit Logger for Volunteer PathFinder
Provides comprehensive change tracking with diffs and export functionality
"""
from typing import Dict, List, Optional, Any, Union
import json
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import difflib
import logging
from supabase import Client
from database import VolunteerDatabase
import pandas as pd
import csv
import io

logger = logging.getLogger(__name__)

class AuditAction(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    EXPORT = "export"
    LOGIN = "login"
    LOGOUT = "logout"

class AuditResource(Enum):
    USER = "user"
    USER_PREFERENCES = "user_preferences"
    CONVERSATION = "conversation"
    MESSAGE = "message"
    VOLUNTEER_MATCH = "volunteer_match"
    FEEDBACK = "feedback"
    ANALYTICS_EVENT = "analytics_event"
    SYSTEM = "system"

@dataclass
class AuditEntry:
    id: str
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    action: AuditAction
    resource: AuditResource
    resource_id: Optional[str]
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    changes: Optional[Dict[str, Any]]
    diff_text: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    metadata: Optional[Dict[str, Any]]

class AuditLogger:
    def __init__(self, database: VolunteerDatabase):
        self.database = database
        self._setup_audit_tables()
    
    def _setup_audit_tables(self):
        """Setup audit log tables in the database"""
        # This would be executed in Supabase SQL editor
        audit_logs_sql = """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            user_id UUID,
            session_id VARCHAR(100),
            action VARCHAR(50) NOT NULL,
            resource VARCHAR(50) NOT NULL,
            resource_id VARCHAR(100),
            old_values JSONB,
            new_values JSONB,
            changes JSONB,
            diff_text TEXT,
            ip_address INET,
            user_agent TEXT,
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_id ON audit_logs(resource_id);
        """
        
        logger.info("Audit tables schema prepared. Execute in Supabase SQL editor.")
    
    async def log_audit_entry(
        self,
        action: AuditAction,
        resource: AuditResource,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log an audit entry with change tracking and diff generation"""
        
        audit_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        # Calculate changes and generate diff
        changes = self._calculate_changes(old_values, new_values)
        diff_text = self._generate_diff_text(old_values, new_values, resource.value)
        
        audit_entry = AuditEntry(
            id=audit_id,
            timestamp=timestamp,
            user_id=user_id,
            session_id=session_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            changes=changes,
            diff_text=diff_text,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata
        )
        
        # Save to database
        try:
            if self.database._is_available():
                audit_data = {
                    'id': audit_id,
                    'timestamp': timestamp.isoformat(),
                    'user_id': user_id,
                    'session_id': session_id,
                    'action': action.value,
                    'resource': resource.value,
                    'resource_id': resource_id,
                    'old_values': json.dumps(old_values) if old_values else None,
                    'new_values': json.dumps(new_values) if new_values else None,
                    'changes': json.dumps(changes) if changes else None,
                    'diff_text': diff_text,
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'metadata': json.dumps(metadata) if metadata else None,
                    'created_at': timestamp.isoformat()
                }
                
                result = self.database.supabase.table('audit_logs').insert(audit_data).execute()
                
                if result.data:
                    logger.info(f"✅ Audit entry logged: {action.value} on {resource.value} by user {user_id}")
                else:
                    logger.error(f"❌ Failed to log audit entry: {result}")
                    
        except Exception as e:
            logger.error(f"❌ Error logging audit entry: {e}")
            # Consider falling back to file logging or other persistence method
        
        return audit_id
    
    def _calculate_changes(self, old_values: Optional[Dict], new_values: Optional[Dict]) -> Optional[Dict]:
        """Calculate what fields changed between old and new values"""
        if not old_values and not new_values:
            return None
        
        if not old_values:
            # Creation - all new values are changes
            return {"added": new_values}
        
        if not new_values:
            # Deletion - all old values are removed
            return {"removed": old_values}
        
        # Update - calculate differences
        changes = {"modified": {}, "added": {}, "removed": {}}
        
        # Find modified and removed fields
        for key, old_val in old_values.items():
            if key not in new_values:
                changes["removed"][key] = old_val
            elif new_values[key] != old_val:
                changes["modified"][key] = {"old": old_val, "new": new_values[key]}
        
        # Find added fields
        for key, new_val in new_values.items():
            if key not in old_values:
                changes["added"][key] = new_val
        
        # Clean up empty categories
        changes = {k: v for k, v in changes.items() if v}
        
        return changes if changes else None
    
    def _generate_diff_text(self, old_values: Optional[Dict], new_values: Optional[Dict], resource_name: str) -> Optional[str]:
        """Generate human-readable diff text"""
        if not old_values and not new_values:
            return None
        
        if not old_values:
            return f"Created {resource_name} with values:\n" + json.dumps(new_values, indent=2)
        
        if not new_values:
            return f"Deleted {resource_name} with values:\n" + json.dumps(old_values, indent=2)
        
        # Generate unified diff
        old_json = json.dumps(old_values, indent=2, sort_keys=True).splitlines()
        new_json = json.dumps(new_values, indent=2, sort_keys=True).splitlines()
        
        diff = list(difflib.unified_diff(
            old_json,
            new_json,
            fromfile=f"{resource_name}_before",
            tofile=f"{resource_name}_after",
            lineterm=""
        ))
        
        return "\n".join(diff) if diff else None
    
    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        resource: Optional[AuditResource] = None,
        resource_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Retrieve audit logs with filtering options"""
        
        try:
            if not self.database._is_available():
                logger.warning("Database not available")
                return []
            
            query = self.database.supabase.table('audit_logs').select('*')
            
            # Apply filters
            if user_id:
                query = query.eq('user_id', user_id)
            if resource:
                query = query.eq('resource', resource.value)
            if resource_id:
                query = query.eq('resource_id', resource_id)
            if action:
                query = query.eq('action', action.value)
            if start_date:
                query = query.gte('timestamp', start_date.isoformat())
            if end_date:
                query = query.lte('timestamp', end_date.isoformat())
            
            # Apply pagination and ordering
            result = query.order('timestamp', desc=True).range(offset, offset + limit - 1).execute()
            
            # Parse JSON fields
            logs = []
            for log in result.data:
                if log.get('old_values'):
                    log['old_values'] = json.loads(log['old_values'])
                if log.get('new_values'):
                    log['new_values'] = json.loads(log['new_values'])
                if log.get('changes'):
                    log['changes'] = json.loads(log['changes'])
                if log.get('metadata'):
                    log['metadata'] = json.loads(log['metadata'])
                logs.append(log)
            
            return logs
            
        except Exception as e:
            logger.error(f"❌ Error retrieving audit logs: {e}")
            return []
    
    async def get_resource_history(self, resource: AuditResource, resource_id: str) -> List[Dict[str, Any]]:
        """Get the complete history of changes for a specific resource"""
        return await self.get_audit_logs(
            resource=resource,
            resource_id=resource_id,
            limit=1000
        )
    
    async def get_user_activity(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get all audit activity for a specific user"""
        start_date = datetime.utcnow() - timedelta(days=days)
        return await self.get_audit_logs(
            user_id=user_id,
            start_date=start_date,
            limit=1000
        )
    
    async def export_audit_logs(
        self,
        format_type: str = "csv",
        user_id: Optional[str] = None,
        resource: Optional[AuditResource] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Union[str, bytes]:
        """Export audit logs to various formats (CSV, JSON, Excel)"""
        
        # Get all matching logs
        logs = await self.get_audit_logs(
            user_id=user_id,
            resource=resource,
            start_date=start_date,
            end_date=end_date,
            limit=10000  # Large limit for export
        )
        
        if format_type.lower() == "json":
            return json.dumps(logs, indent=2, default=str)
        
        elif format_type.lower() == "csv":
            if not logs:
                return "No audit logs found for the specified criteria."
            
            # Flatten the logs for CSV export
            flattened_logs = []
            for log in logs:
                flat_log = {
                    'id': log.get('id'),
                    'timestamp': log.get('timestamp'),
                    'user_id': log.get('user_id'),
                    'session_id': log.get('session_id'),
                    'action': log.get('action'),
                    'resource': log.get('resource'),
                    'resource_id': log.get('resource_id'),
                    'ip_address': log.get('ip_address'),
                    'user_agent': log.get('user_agent'),
                    'changes_summary': self._summarize_changes(log.get('changes')),
                    'diff_text': log.get('diff_text')
                }
                flattened_logs.append(flat_log)
            
            # Convert to CSV
            output = io.StringIO()
            if flattened_logs:
                writer = csv.DictWriter(output, fieldnames=flattened_logs[0].keys())
                writer.writeheader()
                writer.writerows(flattened_logs)
            
            return output.getvalue()
        
        elif format_type.lower() == "excel":
            # Convert to Excel using pandas
            df = pd.DataFrame(logs)
            
            # Flatten complex JSON fields
            if not df.empty:
                df['changes_summary'] = df['changes'].apply(self._summarize_changes)
                df = df.drop(['old_values', 'new_values', 'changes', 'metadata'], axis=1, errors='ignore')
            
            # Create Excel file in memory
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Audit_Logs', index=False)
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def _summarize_changes(self, changes: Optional[Dict]) -> str:
        """Create a human-readable summary of changes"""
        if not changes:
            return "No changes"
        
        summary_parts = []
        
        if "added" in changes and changes["added"]:
            added_fields = list(changes["added"].keys())
            summary_parts.append(f"Added: {', '.join(added_fields)}")
        
        if "modified" in changes and changes["modified"]:
            modified_fields = list(changes["modified"].keys())
            summary_parts.append(f"Modified: {', '.join(modified_fields)}")
        
        if "removed" in changes and changes["removed"]:
            removed_fields = list(changes["removed"].keys())
            summary_parts.append(f"Removed: {', '.join(removed_fields)}")
        
        return "; ".join(summary_parts) if summary_parts else "No changes"
    
    async def get_audit_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get audit log statistics and insights"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            logs = await self.get_audit_logs(start_date=start_date, limit=10000)
            
            if not logs:
                return {"message": "No audit logs found for the specified period"}
            
            # Calculate statistics
            total_activities = len(logs)
            unique_users = len(set(log['user_id'] for log in logs if log.get('user_id')))
            
            # Activity by action
            actions = {}
            for log in logs:
                action = log.get('action', 'unknown')
                actions[action] = actions.get(action, 0) + 1
            
            # Activity by resource
            resources = {}
            for log in logs:
                resource = log.get('resource', 'unknown')
                resources[resource] = resources.get(resource, 0) + 1
            
            # Daily activity
            daily_activity = {}
            for log in logs:
                if log.get('timestamp'):
                    date_str = log['timestamp'][:10]  # Extract date part
                    daily_activity[date_str] = daily_activity.get(date_str, 0) + 1
            
            # Top users by activity
            user_activity = {}
            for log in logs:
                user_id = log.get('user_id')
                if user_id:
                    user_activity[user_id] = user_activity.get(user_id, 0) + 1
            
            top_users = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                "period_days": days,
                "total_activities": total_activities,
                "unique_users": unique_users,
                "activity_by_action": actions,
                "activity_by_resource": resources,
                "daily_activity": daily_activity,
                "top_users": [{"user_id": user_id, "activity_count": count} for user_id, count in top_users],
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting audit statistics: {e}")
            return {"error": str(e)}

# Decorators for automatic audit logging
def audit_log(action: AuditAction, resource: AuditResource):
    """Decorator to automatically log audit entries for function calls"""
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            # Extract audit information from function parameters
            user_id = kwargs.get('user_id') or (args[0] if args and isinstance(args[0], str) else None)
            
            # Get old values if this is an update
            old_values = None
            if hasattr(self, 'audit_logger') and action == AuditAction.UPDATE:
                # This would need to be implemented based on the specific function
                pass
            
            # Execute the original function
            result = await func(self, *args, **kwargs)
            
            # Log the audit entry
            if hasattr(self, 'audit_logger'):
                await self.audit_logger.log_audit_entry(
                    action=action,
                    resource=resource,
                    user_id=user_id,
                    new_values=kwargs if kwargs else None,
                    metadata={'function': func.__name__, 'args_count': len(args)}
                )
            
            return result
        return wrapper
    return decorator