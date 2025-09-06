"""
KPI Email Report Scheduler
Handles automated scheduling and execution of KPI email reports
"""
import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging
from dataclasses import dataclass
import threading
from concurrent.futures import ThreadPoolExecutor

from kpi_email_service import KPIEmailService
from database import VolunteerDatabase
from data_processor import VolunteerDataProcessor
from config import settings

logger = logging.getLogger(__name__)

@dataclass
class ScheduledJob:
    """Represents a scheduled KPI report job"""
    job_id: str
    frequency: str  # daily, weekly, monthly
    time: str  # "09:00" format
    timezone: str = "US/Eastern"
    active: bool = True
    last_run: str = None
    next_run: str = None

class KPIScheduler:
    """Scheduler for automated KPI email reports"""
    
    def __init__(self, email_service: KPIEmailService = None):
        self.email_service = email_service
        self.jobs: List[ScheduledJob] = []
        self.scheduler_thread = None
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.running = False
        self._load_schedule_config()
    
    def _load_schedule_config(self):
        """Load scheduling configuration"""
        # Default scheduling configuration
        default_jobs = [
            {
                "job_id": "daily_morning_report",
                "frequency": "daily", 
                "time": "08:00",
                "timezone": "US/Eastern",
                "active": True
            },
            {
                "job_id": "weekly_monday_report",
                "frequency": "weekly",
                "time": "09:00", 
                "timezone": "US/Eastern",
                "active": True
            },
            {
                "job_id": "monthly_first_report",
                "frequency": "monthly",
                "time": "10:00",
                "timezone": "US/Eastern", 
                "active": True
            }
        ]
        
        self.jobs = [ScheduledJob(**job_config) for job_config in default_jobs]
        logger.info(f"Loaded {len(self.jobs)} scheduled jobs")
    
    def start_scheduler(self):
        """Start the background scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        
        # Initialize email service if not provided
        if not self.email_service:
            database = VolunteerDatabase()
            data_processor = VolunteerDataProcessor(settings.VOLUNTEER_DATA_PATH)
            self.email_service = KPIEmailService(database, data_processor)
        
        # Schedule jobs
        self._schedule_jobs()
        
        # Start scheduler in background thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("KPI scheduler started successfully")
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        if not self.running:
            return
        
        self.running = False
        schedule.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        self.executor.shutdown(wait=True)
        logger.info("KPI scheduler stopped")
    
    def _schedule_jobs(self):
        """Schedule all active jobs"""
        schedule.clear()
        
        for job in self.jobs:
            if not job.active:
                continue
                
            if job.frequency == "daily":
                schedule.every().day.at(job.time).do(
                    self._execute_job_wrapper, job.job_id, job.frequency
                ).tag(job.job_id)
                
            elif job.frequency == "weekly":
                schedule.every().monday.at(job.time).do(
                    self._execute_job_wrapper, job.job_id, job.frequency
                ).tag(job.job_id)
                
            elif job.frequency == "monthly":
                # Schedule for first day of each month
                schedule.every().day.at(job.time).do(
                    self._check_monthly_job, job.job_id, job.frequency
                ).tag(job.job_id)
        
        logger.info(f"Scheduled {len([j for j in self.jobs if j.active])} active jobs")
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        logger.info("Scheduler thread started")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)
        
        logger.info("Scheduler thread stopped")
    
    def _execute_job_wrapper(self, job_id: str, frequency: str):
        """Wrapper for job execution in thread pool"""
        future = self.executor.submit(self._execute_job, job_id, frequency)
        
        # Log result when complete (non-blocking)
        def log_result(fut):
            try:
                result = fut.result()
                logger.info(f"Job {job_id} completed: {result}")
            except Exception as e:
                logger.error(f"Job {job_id} failed: {e}")
        
        future.add_done_callback(log_result)
    
    def _execute_job(self, job_id: str, frequency: str) -> Dict[str, Any]:
        """Execute a scheduled job"""
        start_time = datetime.now()
        
        try:
            logger.info(f"Executing job {job_id} ({frequency})")
            
            # Run the email service
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    self.email_service.send_scheduled_reports(frequency)
                )
                
                # Update job last run time
                self._update_job_run_time(job_id, start_time)
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return {
                    "job_id": job_id,
                    "frequency": frequency,
                    "success": True,
                    "execution_time": execution_time,
                    "reports_sent": result.get("sent", 0),
                    "reports_failed": result.get("failed", 0),
                    "errors": result.get("errors", [])
                }
                
            finally:
                loop.close()
            
        except Exception as e:
            logger.error(f"Job {job_id} execution error: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "job_id": job_id,
                "frequency": frequency,
                "success": False,
                "execution_time": execution_time,
                "error": str(e)
            }
    
    def _check_monthly_job(self, job_id: str, frequency: str):
        """Check if monthly job should run (first day of month)"""
        today = datetime.now()
        
        if today.day == 1:
            self._execute_job_wrapper(job_id, frequency)
    
    def _update_job_run_time(self, job_id: str, run_time: datetime):
        """Update job's last run time"""
        for job in self.jobs:
            if job.job_id == job_id:
                job.last_run = run_time.isoformat()
                # Calculate next run time based on frequency
                if job.frequency == "daily":
                    next_run = run_time + timedelta(days=1)
                elif job.frequency == "weekly":
                    next_run = run_time + timedelta(weeks=1)
                elif job.frequency == "monthly":
                    # Next first day of month
                    if run_time.month == 12:
                        next_run = run_time.replace(year=run_time.year + 1, month=1, day=1)
                    else:
                        next_run = run_time.replace(month=run_time.month + 1, day=1)
                else:
                    next_run = run_time + timedelta(days=1)
                
                job.next_run = next_run.isoformat()
                break
    
    async def run_job_immediately(self, job_id: str) -> Dict[str, Any]:
        """Run a specific job immediately (for testing/manual execution)"""
        job = next((j for j in self.jobs if j.job_id == job_id), None)
        
        if not job:
            return {"success": False, "error": f"Job {job_id} not found"}
        
        if not job.active:
            return {"success": False, "error": f"Job {job_id} is not active"}
        
        # Execute job in thread pool
        future = self.executor.submit(self._execute_job, job.job_id, job.frequency)
        result = future.result()  # Wait for completion
        
        return result
    
    async def run_frequency_immediately(self, frequency: str) -> Dict[str, Any]:
        """Run all jobs of a specific frequency immediately"""
        if not self.email_service:
            return {"success": False, "error": "Email service not initialized"}
        
        result = await self.email_service.send_scheduled_reports(frequency)
        
        return {
            "success": True,
            "frequency": frequency,
            "reports_sent": result.get("sent", 0),
            "reports_failed": result.get("failed", 0),
            "stakeholders": result.get("stakeholders", []),
            "errors": result.get("errors", [])
        }
    
    def get_job_status(self) -> List[Dict[str, Any]]:
        """Get status of all scheduled jobs"""
        return [
            {
                "job_id": job.job_id,
                "frequency": job.frequency,
                "time": job.time,
                "timezone": job.timezone,
                "active": job.active,
                "last_run": job.last_run,
                "next_run": job.next_run
            }
            for job in self.jobs
        ]
    
    def add_job(self, job_config: Dict[str, Any]) -> bool:
        """Add a new scheduled job"""
        try:
            job = ScheduledJob(**job_config)
            
            # Check for duplicate job_id
            if any(j.job_id == job.job_id for j in self.jobs):
                logger.error(f"Job ID {job.job_id} already exists")
                return False
            
            self.jobs.append(job)
            
            # Reschedule if scheduler is running
            if self.running:
                self._schedule_jobs()
            
            logger.info(f"Added new job: {job.job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding job: {e}")
            return False
    
    def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing job"""
        try:
            for i, job in enumerate(self.jobs):
                if job.job_id == job_id:
                    # Update job attributes
                    for key, value in updates.items():
                        if hasattr(job, key):
                            setattr(job, key, value)
                    
                    # Reschedule if scheduler is running
                    if self.running:
                        self._schedule_jobs()
                    
                    logger.info(f"Updated job: {job_id}")
                    return True
            
            logger.error(f"Job {job_id} not found")
            return False
            
        except Exception as e:
            logger.error(f"Error updating job: {e}")
            return False
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a scheduled job"""
        try:
            original_length = len(self.jobs)
            self.jobs = [job for job in self.jobs if job.job_id != job_id]
            
            if len(self.jobs) == original_length:
                logger.error(f"Job {job_id} not found")
                return False
            
            # Remove from scheduler
            if self.running:
                schedule.clear(job_id)
                self._schedule_jobs()
            
            logger.info(f"Deleted job: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting job: {e}")
            return False
    
    def get_next_runs(self) -> List[Dict[str, Any]]:
        """Get upcoming job runs"""
        upcoming = []
        
        for job in self.jobs:
            if job.active and job.next_run:
                try:
                    next_run_dt = datetime.fromisoformat(job.next_run)
                    upcoming.append({
                        "job_id": job.job_id,
                        "frequency": job.frequency,
                        "next_run": job.next_run,
                        "minutes_until": int((next_run_dt - datetime.now()).total_seconds() / 60)
                    })
                except:
                    continue
        
        # Sort by next run time
        upcoming.sort(key=lambda x: x["next_run"])
        return upcoming

# Global scheduler instance
_scheduler_instance = None

def get_scheduler() -> KPIScheduler:
    """Get global scheduler instance"""
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = KPIScheduler()
    
    return _scheduler_instance

def start_kpi_scheduler():
    """Start the global KPI scheduler"""
    scheduler = get_scheduler()
    scheduler.start_scheduler()
    return scheduler

def stop_kpi_scheduler():
    """Stop the global KPI scheduler"""
    scheduler = get_scheduler()
    scheduler.stop_scheduler()