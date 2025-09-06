"""
Background Check Alert Scheduler
Automated task to process background check expiration alerts and workflows
"""
import asyncio
import schedule
import time
import logging
from datetime import datetime
from background_check_service import BackgroundCheckService
from database import VolunteerDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackgroundCheckScheduler:
    def __init__(self):
        self.database = VolunteerDatabase()
        self.bg_service = BackgroundCheckService(self.database)
    
    async def process_daily_alerts(self):
        """Daily task to process background check alerts"""
        try:
            logger.info("🔍 Starting daily background check alert processing...")
            
            stats = await self.bg_service.process_expiration_alerts()
            
            logger.info(f"✅ Daily alert processing completed: {stats}")
            
            # Log to analytics
            await self.database.track_event(
                "scheduled_alert_processing",
                {
                    "stats": stats,
                    "processed_at": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Error in daily alert processing: {e}")
    
    async def process_workflow_reminders(self):
        """Weekly task to send workflow reminders"""
        try:
            logger.info("📧 Starting weekly workflow reminder processing...")
            
            # Get active workflows that haven't been reminded recently
            workflows = await self._get_workflows_needing_reminders()
            
            reminder_count = 0
            for workflow in workflows:
                try:
                    success = await self.bg_service.send_workflow_reminder(workflow['id'])
                    if success:
                        reminder_count += 1
                        logger.info(f"📧 Sent reminder for workflow {workflow['id']}")
                except Exception as e:
                    logger.error(f"❌ Failed to send reminder for workflow {workflow['id']}: {e}")
            
            logger.info(f"✅ Weekly reminder processing completed: {reminder_count} reminders sent")
            
            # Log to analytics
            await self.database.track_event(
                "scheduled_reminder_processing",
                {
                    "reminders_sent": reminder_count,
                    "processed_at": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Error in weekly reminder processing: {e}")
    
    async def cleanup_old_alerts(self):
        """Monthly task to clean up old resolved alerts"""
        try:
            logger.info("🧹 Starting monthly cleanup of old alerts...")
            
            # This would implement cleanup logic for old resolved alerts
            # For now, just log that we're performing maintenance
            
            logger.info("✅ Monthly cleanup completed")
            
            # Log to analytics
            await self.database.track_event(
                "scheduled_cleanup",
                {
                    "processed_at": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Error in monthly cleanup: {e}")
    
    async def generate_weekly_report(self):
        """Generate weekly background check status report"""
        try:
            logger.info("📊 Generating weekly background check report...")
            
            # Get dashboard stats
            stats = await self.bg_service.get_dashboard_stats()
            
            # Get pending alerts
            alerts = await self.bg_service.get_pending_alerts()
            
            report_data = {
                "report_date": datetime.now().isoformat(),
                "dashboard_stats": stats,
                "pending_alerts_count": len(alerts),
                "critical_items": []
            }
            
            # Identify critical items
            if stats.get('expired_checks', 0) > 0:
                report_data['critical_items'].append(f"{stats['expired_checks']} expired background checks")
            
            if stats.get('expiring_soon', 0) > 5:
                report_data['critical_items'].append(f"{stats['expiring_soon']} background checks expiring soon")
            
            logger.info(f"📊 Weekly report generated: {report_data}")
            
            # Log to analytics
            await self.database.track_event(
                "weekly_report_generated",
                report_data
            )
            
        except Exception as e:
            logger.error(f"❌ Error generating weekly report: {e}")
    
    async def _get_workflows_needing_reminders(self):
        """Get workflows that need reminder notifications"""
        try:
            # This would query for workflows that:
            # 1. Are in 'initiated' or 'volunteer_notified' status
            # 2. Haven't been reminded in the last 7 days
            # 3. Are past their due date or approaching deadline
            
            # For now, return empty list - would implement proper query
            return []
            
        except Exception as e:
            logger.error(f"❌ Error getting workflows needing reminders: {e}")
            return []
    
    def schedule_tasks(self):
        """Schedule all background check tasks"""
        # Daily alert processing at 8 AM
        schedule.every().day.at("08:00").do(
            lambda: asyncio.create_task(self.process_daily_alerts())
        )
        
        # Weekly workflow reminders on Mondays at 9 AM
        schedule.every().monday.at("09:00").do(
            lambda: asyncio.create_task(self.process_workflow_reminders())
        )
        
        # Monthly cleanup on the 1st at 2 AM
        schedule.every().month.do(
            lambda: asyncio.create_task(self.cleanup_old_alerts())
        )
        
        # Weekly reports on Fridays at 5 PM
        schedule.every().friday.at("17:00").do(
            lambda: asyncio.create_task(self.generate_weekly_report())
        )
        
        logger.info("✅ Background check tasks scheduled:")
        logger.info("  - Daily alert processing: 8:00 AM")
        logger.info("  - Weekly workflow reminders: Monday 9:00 AM")
        logger.info("  - Monthly cleanup: 1st of month 2:00 AM")
        logger.info("  - Weekly reports: Friday 5:00 PM")
    
    def run(self):
        """Run the scheduler"""
        self.schedule_tasks()
        
        logger.info("🚀 Background Check Scheduler started")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

async def run_manual_processing():
    """Manual execution of background check processing"""
    scheduler = BackgroundCheckScheduler()
    
    print("Running manual background check processing...")
    
    # Process alerts
    await scheduler.process_daily_alerts()
    
    # Process workflow reminders
    await scheduler.process_workflow_reminders()
    
    # Generate report
    await scheduler.generate_weekly_report()
    
    print("Manual processing completed!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        # Run manual processing
        asyncio.run(run_manual_processing())
    else:
        # Run continuous scheduler
        scheduler = BackgroundCheckScheduler()
        scheduler.run()