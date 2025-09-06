"""
Background Check Service for Volunteer PathFinder
Handles background check tracking, expiration alerts, and re-check workflows
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from supabase import Client
from database import VolunteerDatabase
import json
import uuid
import logging

logger = logging.getLogger(__name__)

class BackgroundCheckService:
    def __init__(self, database: VolunteerDatabase):
        self.db = database
        self.supabase = database.supabase
    
    async def create_background_check(self, check_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new background check record"""
        try:
            # Calculate expiration date based on requirements
            if not check_data.get('expiration_date'):
                requirement = await self._get_requirement(
                    check_data.get('volunteer_type', 'general'),
                    check_data.get('check_type')
                )
                if requirement:
                    validity_months = requirement.get('validity_months', 24)
                    submission_date = datetime.fromisoformat(check_data['submission_date'])
                    check_data['expiration_date'] = (
                        submission_date + timedelta(days=validity_months * 30)
                    ).isoformat()
            
            check_data['created_at'] = datetime.now().isoformat()
            check_data['updated_at'] = datetime.now().isoformat()
            
            result = self.supabase.table('background_checks').insert(check_data).execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"✅ Created background check: {result.data[0]['id']}")
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"❌ Error creating background check: {e}")
            return None
    
    async def get_user_background_checks(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all background checks for a user"""
        try:
            result = self.supabase.table('background_checks')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"❌ Error getting background checks: {e}")
            return []
    
    async def get_expiring_checks(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get background checks expiring within specified days"""
        try:
            expiration_threshold = (datetime.now() + timedelta(days=days_ahead)).isoformat()
            
            result = self.supabase.table('background_checks')\
                .select('*, users(email, first_name, last_name)')\
                .eq('status', 'completed')\
                .eq('result', 'clear')\
                .lte('expiration_date', expiration_threshold)\
                .gte('expiration_date', datetime.now().isoformat())\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"❌ Error getting expiring checks: {e}")
            return []
    
    async def get_expired_checks(self) -> List[Dict[str, Any]]:
        """Get expired background checks"""
        try:
            result = self.supabase.table('background_checks')\
                .select('*, users(email, first_name, last_name)')\
                .lt('expiration_date', datetime.now().isoformat())\
                .neq('status', 'expired')\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"❌ Error getting expired checks: {e}")
            return []
    
    async def update_check_status(self, check_id: str, status: str, result: str = None, completion_date: str = None) -> bool:
        """Update background check status and result"""
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            if result:
                update_data['result'] = result
            
            if completion_date:
                update_data['completion_date'] = completion_date
            
            result = self.supabase.table('background_checks')\
                .update(update_data)\
                .eq('id', check_id)\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"❌ Error updating check status: {e}")
            return False
    
    async def create_alert(self, background_check_id: str, alert_type: str, notes: str = None) -> Optional[Dict[str, Any]]:
        """Create a background check alert"""
        try:
            # Check if alert already exists
            existing = self.supabase.table('background_check_alerts')\
                .select('*')\
                .eq('background_check_id', background_check_id)\
                .eq('alert_type', alert_type)\
                .eq('resolved', False)\
                .execute()
            
            if existing.data:
                logger.info(f"Alert already exists for check {background_check_id}")
                return existing.data[0]
            
            alert_data = {
                'background_check_id': background_check_id,
                'alert_type': alert_type,
                'alert_date': datetime.now().isoformat(),
                'notes': notes,
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('background_check_alerts').insert(alert_data).execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"✅ Created alert: {alert_type} for check {background_check_id}")
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"❌ Error creating alert: {e}")
            return None
    
    async def get_pending_alerts(self, resolved: bool = False) -> List[Dict[str, Any]]:
        """Get pending or resolved alerts"""
        try:
            result = self.supabase.table('background_check_alerts')\
                .select('*, background_checks(*, users(email, first_name, last_name))')\
                .eq('resolved', resolved)\
                .order('alert_date', desc=True)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"❌ Error getting alerts: {e}")
            return []
    
    async def resolve_alert(self, alert_id: str, notes: str = None) -> bool:
        """Mark an alert as resolved"""
        try:
            update_data = {
                'resolved': True,
                'resolved_date': datetime.now().isoformat()
            }
            
            if notes:
                update_data['notes'] = notes
            
            result = self.supabase.table('background_check_alerts')\
                .update(update_data)\
                .eq('id', alert_id)\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"❌ Error resolving alert: {e}")
            return False
    
    async def initiate_recheck_workflow(self, user_id: str, original_check_id: str, initiated_by: str = 'system_automatic') -> Optional[Dict[str, Any]]:
        """Initiate a background check renewal workflow"""
        try:
            # Get the original check to determine requirements
            original_check = await self._get_background_check(original_check_id)
            if not original_check:
                return None
            
            # Calculate due date based on requirements
            requirement = await self._get_requirement(
                original_check.get('volunteer_type', 'general'),
                original_check.get('check_type')
            )
            
            advance_days = requirement.get('advance_warning_days', 30) if requirement else 30
            due_date = datetime.now() + timedelta(days=advance_days)
            completion_deadline = datetime.now() + timedelta(days=advance_days * 2)
            
            workflow_data = {
                'user_id': user_id,
                'original_check_id': original_check_id,
                'workflow_status': 'initiated',
                'initiated_by': initiated_by,
                'due_date': due_date.isoformat(),
                'completion_deadline': completion_deadline.isoformat(),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('recheck_workflows').insert(workflow_data).execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"✅ Initiated recheck workflow for user {user_id}")
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"❌ Error initiating recheck workflow: {e}")
            return None
    
    async def get_user_recheck_workflows(self, user_id: str, status: str = None) -> List[Dict[str, Any]]:
        """Get recheck workflows for a user"""
        try:
            query = self.supabase.table('recheck_workflows')\
                .select('*, background_checks!original_check_id(*)')\
                .eq('user_id', user_id)
            
            if status:
                query = query.eq('workflow_status', status)
            
            result = query.order('created_at', desc=True).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"❌ Error getting recheck workflows: {e}")
            return []
    
    async def update_workflow_status(self, workflow_id: str, status: str, notes: str = None) -> bool:
        """Update workflow status"""
        try:
            update_data = {
                'workflow_status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            if notes:
                update_data['notes'] = notes
            
            result = self.supabase.table('recheck_workflows')\
                .update(update_data)\
                .eq('id', workflow_id)\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"❌ Error updating workflow status: {e}")
            return False
    
    async def send_workflow_reminder(self, workflow_id: str) -> bool:
        """Send reminder for recheck workflow and update reminder count"""
        try:
            # Get current workflow
            workflow = await self._get_workflow(workflow_id)
            if not workflow:
                return False
            
            reminder_count = workflow.get('reminder_count', 0) + 1
            
            update_data = {
                'reminder_count': reminder_count,
                'last_reminder_date': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('recheck_workflows')\
                .update(update_data)\
                .eq('id', workflow_id)\
                .execute()
            
            logger.info(f"✅ Sent reminder #{reminder_count} for workflow {workflow_id}")
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"❌ Error sending workflow reminder: {e}")
            return False
    
    async def process_expiration_alerts(self) -> Dict[str, int]:
        """Process and create expiration alerts for background checks"""
        try:
            stats = {
                'expiring_soon_created': 0,
                'expired_marked': 0,
                'workflows_initiated': 0
            }
            
            # Get expiring checks
            expiring_checks = await self.get_expiring_checks()
            
            for check in expiring_checks:
                # Create expiring soon alert
                await self.create_alert(
                    check['id'],
                    'expiring_soon',
                    f"Background check expires on {check['expiration_date'][:10]}"
                )
                stats['expiring_soon_created'] += 1
                
                # Initiate renewal workflow if not already exists
                existing_workflows = await self.get_user_recheck_workflows(
                    check['user_id'],
                    status='initiated'
                )
                
                if not existing_workflows:
                    await self.initiate_recheck_workflow(check['user_id'], check['id'])
                    stats['workflows_initiated'] += 1
            
            # Get expired checks
            expired_checks = await self.get_expired_checks()
            
            for check in expired_checks:
                # Mark as expired
                await self.update_check_status(check['id'], 'expired')
                stats['expired_marked'] += 1
                
                # Create expired alert
                await self.create_alert(
                    check['id'],
                    'expired',
                    f"Background check expired on {check['expiration_date'][:10]}"
                )
            
            logger.info(f"✅ Processed expiration alerts: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error processing expiration alerts: {e}")
            return {}
    
    async def get_dashboard_stats(self, user_id: str = None) -> Dict[str, Any]:
        """Get dashboard statistics for background checks"""
        try:
            stats = {
                'total_checks': 0,
                'pending_checks': 0,
                'completed_checks': 0,
                'expired_checks': 0,
                'expiring_soon': 0,
                'active_workflows': 0,
                'pending_alerts': 0
            }
            
            base_query = self.supabase.table('background_checks').select('*', count='exact')
            
            if user_id:
                base_query = base_query.eq('user_id', user_id)
            
            # Total checks
            total_result = base_query.execute()
            stats['total_checks'] = total_result.count or 0
            
            # Pending checks
            pending_result = base_query.eq('status', 'pending').execute()
            stats['pending_checks'] = pending_result.count or 0
            
            # Completed checks
            completed_result = base_query.eq('status', 'completed').execute()
            stats['completed_checks'] = completed_result.count or 0
            
            # Expired checks
            expired_result = base_query.eq('status', 'expired').execute()
            stats['expired_checks'] = expired_result.count or 0
            
            # Expiring soon (30 days)
            expiring_threshold = (datetime.now() + timedelta(days=30)).isoformat()
            expiring_result = base_query.eq('status', 'completed')\
                .lte('expiration_date', expiring_threshold)\
                .gte('expiration_date', datetime.now().isoformat())\
                .execute()
            stats['expiring_soon'] = expiring_result.count or 0
            
            # Active workflows
            workflow_query = self.supabase.table('recheck_workflows').select('*', count='exact')
            if user_id:
                workflow_query = workflow_query.eq('user_id', user_id)
            
            active_workflows_result = workflow_query.in_('workflow_status', ['initiated', 'volunteer_notified', 'in_progress']).execute()
            stats['active_workflows'] = active_workflows_result.count or 0
            
            # Pending alerts
            alert_query = self.supabase.table('background_check_alerts')\
                .select('*', count='exact')\
                .eq('resolved', False)
            
            if user_id:
                alert_query = alert_query.eq('background_checks.user_id', user_id)
            
            pending_alerts_result = alert_query.execute()
            stats['pending_alerts'] = pending_alerts_result.count or 0
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting dashboard stats: {e}")
            return {}
    
    # Helper methods
    async def _get_background_check(self, check_id: str) -> Optional[Dict[str, Any]]:
        """Get a single background check by ID"""
        try:
            result = self.supabase.table('background_checks')\
                .select('*')\
                .eq('id', check_id)\
                .execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"❌ Error getting background check: {e}")
            return None
    
    async def _get_requirement(self, volunteer_type: str, check_type: str) -> Optional[Dict[str, Any]]:
        """Get background check requirement"""
        try:
            result = self.supabase.table('background_check_requirements')\
                .select('*')\
                .eq('volunteer_type', volunteer_type)\
                .eq('check_type', check_type)\
                .execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"❌ Error getting requirement: {e}")
            return None
    
    async def _get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get a single workflow by ID"""
        try:
            result = self.supabase.table('recheck_workflows')\
                .select('*')\
                .eq('id', workflow_id)\
                .execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"❌ Error getting workflow: {e}")
            return None