"""
Retention Policy Scheduler
Handles automated execution of data retention policies on a schedule
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from data_retention import DataRetentionManager

logger = logging.getLogger(__name__)

class RetentionScheduler:
    """Scheduler for automated retention policy execution"""
    
    def __init__(self, retention_manager: DataRetentionManager):
        self.retention_manager = retention_manager
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
    async def start(self):
        """Start the retention scheduler"""
        if self.is_running:
            logger.warning("Retention scheduler is already running")
            return
            
        try:
            # Schedule daily retention policy execution at 2:00 AM
            self.scheduler.add_job(
                self.run_daily_retention,
                CronTrigger(hour=2, minute=0),
                id='daily_retention',
                name='Daily Retention Policy Execution',
                misfire_grace_time=3600,  # 1 hour grace period
                replace_existing=True
            )
            
            # Schedule weekly retention report at Sunday 6:00 AM
            self.scheduler.add_job(
                self.generate_weekly_report,
                CronTrigger(day_of_week=6, hour=6, minute=0),  # Sunday
                id='weekly_report',
                name='Weekly Retention Report',
                misfire_grace_time=7200,  # 2 hour grace period
                replace_existing=True
            )
            
            # Schedule legal hold expiration check every 6 hours
            self.scheduler.add_job(
                self.check_legal_hold_expirations,
                CronTrigger(hour='*/6'),
                id='legal_hold_check',
                name='Legal Hold Expiration Check',
                misfire_grace_time=1800,  # 30 minute grace period
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            logger.info("✅ Retention scheduler started")
            
        except Exception as e:
            logger.error(f"❌ Failed to start retention scheduler: {e}")
    
    async def stop(self):
        """Stop the retention scheduler"""
        if not self.is_running:
            return
            
        try:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("✅ Retention scheduler stopped")
        except Exception as e:
            logger.error(f"❌ Failed to stop retention scheduler: {e}")
    
    async def run_daily_retention(self):
        """Execute all active retention policies"""
        logger.info("🔄 Starting daily retention policy execution")
        
        try:
            # Load current policies and legal holds
            await self.retention_manager.load_policies()
            await self.retention_manager.load_legal_holds()
            
            # Execute retention policies
            results = await self.retention_manager.run_retention_policies()
            
            # Log summary
            total_processed = sum(r.get('processed_count', 0) for r in results if 'processed_count' in r)
            total_archived = sum(r.get('archived_count', 0) for r in results if 'archived_count' in r)
            total_deleted = sum(r.get('deleted_count', 0) for r in results if 'deleted_count' in r)
            total_legal_holds = sum(r.get('legal_hold_count', 0) for r in results if 'legal_hold_count' in r)
            
            logger.info(f"✅ Daily retention completed: {total_processed} records processed, "
                       f"{total_archived} archived, {total_deleted} deleted, "
                       f"{total_legal_holds} protected by legal holds")
            
            return {
                'execution_time': datetime.now().isoformat(),
                'policies_executed': len(results),
                'total_processed': total_processed,
                'total_archived': total_archived,
                'total_deleted': total_deleted,
                'legal_hold_protections': total_legal_holds,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"❌ Daily retention execution failed: {e}")
            return {'error': str(e), 'execution_time': datetime.now().isoformat()}
    
    async def generate_weekly_report(self):
        """Generate weekly retention activity report"""
        logger.info("📊 Generating weekly retention report")
        
        try:
            report = await self.retention_manager.get_retention_report(days=7)
            
            logger.info(f"📊 Weekly report generated: {report.get('total_events', 0)} events, "
                       f"{report.get('total_records_processed', 0)} records processed")
            
            # In a production environment, you might want to:
            # - Email this report to administrators
            # - Store it in a reporting database
            # - Send it to a monitoring system
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Weekly report generation failed: {e}")
            return {'error': str(e), 'generation_time': datetime.now().isoformat()}
    
    async def check_legal_hold_expirations(self):
        """Check for expired legal holds and update their status"""
        logger.info("⚖️ Checking for expired legal holds")
        
        try:
            await self.retention_manager.load_legal_holds()
            
            expired_count = 0
            current_time = datetime.now()
            
            for hold_id, hold in self.retention_manager.legal_holds.items():
                if (hold.expires_at and 
                    current_time > hold.expires_at and 
                    hold.status.value == 'active'):
                    
                    # Update hold status to expired
                    success = await self.retention_manager.db.table('legal_holds')\
                        .update({'status': 'expired'})\
                        .eq('id', hold_id)\
                        .execute()
                    
                    if success.data:
                        expired_count += 1
                        logger.info(f"⚖️ Expired legal hold: {hold.case_name} ({hold_id})")
            
            logger.info(f"✅ Legal hold check completed: {expired_count} holds expired")
            
            return {
                'check_time': current_time.isoformat(),
                'expired_holds': expired_count
            }
            
        except Exception as e:
            logger.error(f"❌ Legal hold expiration check failed: {e}")
            return {'error': str(e), 'check_time': datetime.now().isoformat()}
    
    async def run_manual_retention(self, policy_id: str = None) -> Dict[str, Any]:
        """Manually trigger retention policy execution"""
        logger.info(f"🔄 Manual retention execution triggered for policy: {policy_id or 'all'}")
        
        try:
            await self.retention_manager.load_policies()
            
            if policy_id:
                # Run specific policy
                if policy_id in self.retention_manager.policies:
                    policy = self.retention_manager.policies[policy_id]
                    result = await self.retention_manager.apply_retention_policy(policy)
                    return {'results': [result]}
                else:
                    return {'error': f'Policy {policy_id} not found'}
            else:
                # Run all policies
                results = await self.retention_manager.run_retention_policies()
                return {'results': results}
                
        except Exception as e:
            logger.error(f"❌ Manual retention execution failed: {e}")
            return {'error': str(e)}
    
    def get_scheduled_jobs(self) -> Dict[str, Any]:
        """Get information about scheduled jobs"""
        if not self.is_running:
            return {'scheduler_running': False, 'jobs': []}
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return {
            'scheduler_running': True,
            'jobs': jobs
        }

# Utility functions for setting up default retention policies
async def setup_default_retention_policies(retention_manager: DataRetentionManager):
    """Set up default retention policies for the YMCA system"""
    from data_retention import RetentionPolicy, DataCategory, RetentionAction
    import uuid
    
    default_policies = [
        {
            'name': 'Analytics Data Retention',
            'description': 'Automatically delete analytics events older than 2 years',
            'data_category': DataCategory.ANALYTICS,
            'retention_period_days': 730,  # 2 years
            'action': RetentionAction.DELETE
        },
        {
            'name': 'Message Archive Policy',
            'description': 'Archive conversation messages older than 1 year, delete after 3 years',
            'data_category': DataCategory.MESSAGES,
            'retention_period_days': 1095,  # 3 years
            'archive_after_days': 365,  # 1 year
            'action': RetentionAction.ARCHIVE
        },
        {
            'name': 'Feedback Retention Policy',
            'description': 'Archive feedback older than 6 months, delete after 2 years',
            'data_category': DataCategory.FEEDBACK,
            'retention_period_days': 730,  # 2 years
            'archive_after_days': 180,  # 6 months
            'action': RetentionAction.ARCHIVE
        },
        {
            'name': 'Inactive User Cleanup',
            'description': 'Archive user profiles inactive for 3 years, delete after 7 years',
            'data_category': DataCategory.USER_PROFILES,
            'retention_period_days': 2555,  # 7 years
            'archive_after_days': 1095,  # 3 years
            'action': RetentionAction.ARCHIVE
        },
        {
            'name': 'Old Match Data Cleanup',
            'description': 'Delete volunteer match data older than 1 year',
            'data_category': DataCategory.MATCHES,
            'retention_period_days': 365,  # 1 year
            'action': RetentionAction.DELETE
        }
    ]
    
    created_count = 0
    for policy_data in default_policies:
        policy = RetentionPolicy(
            id=str(uuid.uuid4()),
            name=policy_data['name'],
            description=policy_data['description'],
            data_category=policy_data['data_category'],
            retention_period_days=policy_data['retention_period_days'],
            archive_after_days=policy_data.get('archive_after_days'),
            action=policy_data['action']
        )
        
        success = await retention_manager.create_retention_policy(policy)
        if success:
            created_count += 1
            logger.info(f"✅ Created default policy: {policy.name}")
    
    logger.info(f"✅ Set up {created_count} default retention policies")
    return created_count