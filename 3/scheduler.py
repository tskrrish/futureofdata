"""
Background scheduler for automated tasks
Handles shift reminders, notifications, and other periodic tasks
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import schedule
import threading
import time

from config import settings
from shift_service import shift_service
from slack_integration import slack_integration

logger = logging.getLogger(__name__)

class TaskScheduler:
    def __init__(self):
        self.running = False
        self.scheduler_thread = None
        
    def start(self):
        """Start the background scheduler"""
        if self.running:
            logger.warning("Scheduler already running")
            return
            
        logger.info("Starting task scheduler...")
        
        # Schedule periodic tasks
        self._schedule_tasks()
        
        # Start scheduler in background thread
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Task scheduler started")
    
    def stop(self):
        """Stop the background scheduler"""
        logger.info("Stopping task scheduler...")
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        schedule.clear()
        logger.info("Task scheduler stopped")
    
    def _schedule_tasks(self):
        """Set up scheduled tasks"""
        
        # Send shift reminders every day at 9 AM
        schedule.every().day.at("09:00").do(self._send_daily_reminders)
        
        # Send 24-hour reminders
        schedule.every().hour.do(self._send_24_hour_reminders)
        
        # Send 2-hour reminders
        schedule.every(30).minutes.do(self._send_2_hour_reminders)
        
        # Clean up old data weekly
        schedule.every().sunday.at("02:00").do(self._cleanup_old_data)
        
        logger.info("Scheduled tasks configured")
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)
    
    def _send_daily_reminders(self):
        """Send daily shift reminders"""
        try:
            logger.info("Sending daily shift reminders")
            
            # Run in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Send reminders for shifts in next 24 hours
            reminders_sent = loop.run_until_complete(
                shift_service.send_shift_reminders(hours_before=24)
            )
            
            logger.info(f"Sent {reminders_sent} daily reminders")
            
        except Exception as e:
            logger.error(f"Error sending daily reminders: {e}")
        finally:
            loop.close()
    
    def _send_24_hour_reminders(self):
        """Send 24-hour advance reminders"""
        try:
            logger.debug("Checking for 24-hour reminders")
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            reminders_sent = loop.run_until_complete(
                shift_service.send_shift_reminders(hours_before=24)
            )
            
            if reminders_sent > 0:
                logger.info(f"Sent {reminders_sent} 24-hour reminders")
                
        except Exception as e:
            logger.error(f"Error sending 24-hour reminders: {e}")
        finally:
            loop.close()
    
    def _send_2_hour_reminders(self):
        """Send 2-hour advance reminders"""
        try:
            logger.debug("Checking for 2-hour reminders")
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            reminders_sent = loop.run_until_complete(
                shift_service.send_shift_reminders(hours_before=2)
            )
            
            if reminders_sent > 0:
                logger.info(f"Sent {reminders_sent} 2-hour reminders")
                
        except Exception as e:
            logger.error(f"Error sending 2-hour reminders: {e}")
        finally:
            loop.close()
    
    def _cleanup_old_data(self):
        """Clean up old shift data and logs"""
        try:
            logger.info("Running weekly cleanup")
            
            # This would implement cleanup logic for old shifts, logs, etc.
            # Placeholder implementation
            cutoff_date = datetime.now() - timedelta(days=90)
            logger.info(f"Cleaning up data older than {cutoff_date}")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Create scheduler instance
task_scheduler = TaskScheduler()

# Auto-start scheduler if enabled
if settings.SLACK_ENABLED:
    task_scheduler.start()
    logger.info("Background scheduler started for Slack integration")
else:
    logger.info("Slack integration disabled, scheduler not started")