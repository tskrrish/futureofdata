"""
Background scheduler for BI connector refresh operations
Handles periodic data exports and refresh triggers
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import signal
import sys

try:
    from croniter import croniter
    CRONITER_AVAILABLE = True
except ImportError:
    CRONITER_AVAILABLE = False
    logging.warning("croniter not available, using simplified scheduling")

from bi_connectors import bi_connector_manager

# Configure logging
logger = logging.getLogger(__name__)

class BIConnectorScheduler:
    """Background scheduler for BI connector operations"""
    
    def __init__(self, check_interval_seconds: int = 300):  # Check every 5 minutes
        self.check_interval = check_interval_seconds
        self.running = False
        self.task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the background scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._scheduler_loop())
        logger.info(f"BI Connector scheduler started (check interval: {self.check_interval}s)")
    
    async def stop(self):
        """Stop the background scheduler"""
        if not self.running:
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("BI Connector scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                await self._check_and_execute_scheduled_jobs()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_and_execute_scheduled_jobs(self):
        """Check for due scheduled jobs and execute them"""
        try:
            current_time = datetime.now()
            schedules = bi_connector_manager.get_refresh_schedules()
            
            for schedule in schedules:
                if not schedule.enabled:
                    continue
                
                # Check if it's time to run
                should_run = False
                
                if CRONITER_AVAILABLE:
                    # Use croniter for proper cron expression parsing
                    try:
                        cron = croniter(schedule.cron_expression, schedule.last_run or current_time)
                        next_run_time = cron.get_next(datetime)
                        should_run = current_time >= next_run_time
                    except Exception as e:
                        logger.error(f"Error parsing cron expression '{schedule.cron_expression}': {e}")
                        continue
                else:
                    # Fallback simple scheduling
                    if schedule.next_run and current_time >= schedule.next_run:
                        should_run = True
                
                if should_run:
                    try:
                        logger.info(f"Executing scheduled refresh for connector: {schedule.connector_name}")
                        result = await bi_connector_manager.refresh_connector_dataset(schedule.connector_name)
                        
                        # Update schedule times
                        schedule.last_run = current_time
                        
                        if CRONITER_AVAILABLE:
                            cron = croniter(schedule.cron_expression, current_time)
                            schedule.next_run = cron.get_next(datetime)
                        else:
                            # Simple fallback: add 6 hours
                            schedule.next_run = current_time + timedelta(hours=6)
                        
                        if result.get("success"):
                            logger.info(f"Scheduled refresh successful for {schedule.connector_name}")
                        else:
                            logger.error(f"Scheduled refresh failed for {schedule.connector_name}: {result.get('error')}")
                        
                    except Exception as e:
                        logger.error(f"Error executing scheduled refresh for {schedule.connector_name}: {e}")
                        
        except Exception as e:
            logger.error(f"Error in scheduled job execution: {e}")

# Global scheduler instance
scheduler = BIConnectorScheduler()

async def start_scheduler():
    """Start the global scheduler"""
    await scheduler.start()

async def stop_scheduler():
    """Stop the global scheduler"""
    await scheduler.stop()

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down scheduler...")
        asyncio.create_task(stop_scheduler())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    # Run scheduler standalone
    setup_signal_handlers()
    
    async def main():
        await start_scheduler()
        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await stop_scheduler()
    
    asyncio.run(main())