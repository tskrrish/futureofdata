"""
Sync manager with error handling, retry logic, and background tasks
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import traceback

from sync_service import CollaborationSyncService, SyncConfig, SyncDirection, SyncStatus
from config import settings

logger = logging.getLogger(__name__)

class RetryStrategy(Enum):
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIXED = "fixed"

@dataclass
class RetryConfig:
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    backoff_factor: float = 2.0

@dataclass
class SyncTask:
    id: str
    table_types: List[str]
    scheduled_time: datetime
    retry_count: int = 0
    status: SyncStatus = SyncStatus.PENDING
    error_message: Optional[str] = None
    result: Optional[Dict] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class SyncManager:
    def __init__(self):
        self.sync_service: Optional[CollaborationSyncService] = None
        self.retry_config = RetryConfig()
        self.background_task: Optional[asyncio.Task] = None
        self.is_running = False
        self.sync_queue: List[SyncTask] = []
        self.sync_history: List[SyncTask] = []
        self.error_handlers: Dict[str, callable] = {}
        
    def initialize(self) -> bool:
        """Initialize the sync manager with configuration"""
        try:
            if not all([
                settings.AIRTABLE_API_KEY,
                settings.AIRTABLE_BASE_ID,
                settings.NOTION_API_KEY,
                settings.NOTION_VOLUNTEER_DB_ID,
                settings.NOTION_PROJECT_DB_ID
            ]):
                logger.warning("Sync manager not initialized: Missing required configuration")
                return False

            sync_config = SyncConfig(
                airtable_api_key=settings.AIRTABLE_API_KEY,
                airtable_base_id=settings.AIRTABLE_BASE_ID,
                notion_api_key=settings.NOTION_API_KEY,
                volunteer_table_name=settings.AIRTABLE_VOLUNTEER_TABLE,
                project_table_name=settings.AIRTABLE_PROJECT_TABLE,
                notion_volunteer_db_id=settings.NOTION_VOLUNTEER_DB_ID,
                notion_project_db_id=settings.NOTION_PROJECT_DB_ID,
                sync_direction=SyncDirection(settings.SYNC_DIRECTION),
                sync_interval_minutes=settings.SYNC_INTERVAL_MINUTES,
                conflict_resolution=settings.CONFLICT_RESOLUTION
            )

            self.sync_service = CollaborationSyncService(sync_config)
            
            # Register default error handlers
            self.register_error_handler("connection_error", self._handle_connection_error)
            self.register_error_handler("rate_limit_error", self._handle_rate_limit_error)
            self.register_error_handler("auth_error", self._handle_auth_error)
            self.register_error_handler("validation_error", self._handle_validation_error)
            
            logger.info("Sync manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize sync manager: {e}")
            return False

    async def start_background_sync(self):
        """Start background sync process"""
        if not self.sync_service or not settings.SYNC_ENABLED:
            logger.info("Background sync not started: service not initialized or disabled")
            return

        if self.is_running:
            logger.warning("Background sync already running")
            return

        self.is_running = True
        self.background_task = asyncio.create_task(self._background_sync_loop())
        logger.info(f"Background sync started with {settings.SYNC_INTERVAL_MINUTES} minute intervals")

    async def stop_background_sync(self):
        """Stop background sync process"""
        self.is_running = False
        if self.background_task:
            self.background_task.cancel()
            try:
                await self.background_task
            except asyncio.CancelledError:
                pass
        logger.info("Background sync stopped")

    async def _background_sync_loop(self):
        """Main background sync loop"""
        while self.is_running:
            try:
                # Process queued tasks
                await self._process_sync_queue()
                
                # Schedule next automatic sync if none pending
                if not self._has_pending_sync():
                    await self.schedule_sync(['volunteers', 'projects'])
                
                # Wait for next interval
                await asyncio.sleep(settings.SYNC_INTERVAL_MINUTES * 60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background sync loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def schedule_sync(self, table_types: List[str], 
                           scheduled_time: Optional[datetime] = None) -> str:
        """Schedule a sync task"""
        if scheduled_time is None:
            scheduled_time = datetime.now()

        task = SyncTask(
            id=f"sync_{datetime.now().timestamp()}",
            table_types=table_types,
            scheduled_time=scheduled_time
        )

        self.sync_queue.append(task)
        logger.info(f"Sync task scheduled: {task.id} for {table_types}")
        return task.id

    async def _process_sync_queue(self):
        """Process all pending sync tasks"""
        current_time = datetime.now()
        
        for task in self.sync_queue[:]:  # Create a copy to iterate over
            if task.scheduled_time <= current_time and task.status == SyncStatus.PENDING:
                await self._execute_sync_task(task)

    async def _execute_sync_task(self, task: SyncTask):
        """Execute a single sync task with retry logic"""
        task.status = SyncStatus.IN_PROGRESS
        
        try:
            logger.info(f"Executing sync task: {task.id}")
            result = await self.sync_service.start_sync_process(task.table_types)
            
            if "error" in result:
                raise Exception(result.get("message", "Sync failed"))
            
            task.status = SyncStatus.COMPLETED
            task.result = result
            logger.info(f"Sync task completed successfully: {task.id}")
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Sync task failed: {task.id} - {error_message}")
            
            # Determine error type and handle accordingly
            error_type = self._classify_error(e)
            should_retry = await self._handle_error(task, error_type, error_message)
            
            if should_retry and task.retry_count < self.retry_config.max_retries:
                await self._schedule_retry(task, error_type)
            else:
                task.status = SyncStatus.FAILED
                task.error_message = error_message
                
        finally:
            # Move completed/failed tasks to history
            if task.status in [SyncStatus.COMPLETED, SyncStatus.FAILED]:
                self.sync_queue.remove(task)
                self.sync_history.append(task)
                
                # Keep only last 100 history entries
                if len(self.sync_history) > 100:
                    self.sync_history = self.sync_history[-100:]

    def _classify_error(self, error: Exception) -> str:
        """Classify error type for appropriate handling"""
        error_message = str(error).lower()
        
        if "connection" in error_message or "timeout" in error_message:
            return "connection_error"
        elif "rate limit" in error_message or "429" in error_message:
            return "rate_limit_error"
        elif "unauthorized" in error_message or "401" in error_message:
            return "auth_error"
        elif "validation" in error_message or "400" in error_message:
            return "validation_error"
        else:
            return "unknown_error"

    async def _handle_error(self, task: SyncTask, error_type: str, error_message: str) -> bool:
        """Handle specific error types and return whether to retry"""
        handler = self.error_handlers.get(error_type)
        if handler:
            return await handler(task, error_message)
        
        # Default handling
        logger.error(f"Unhandled error type {error_type} for task {task.id}: {error_message}")
        return True  # Retry by default

    async def _schedule_retry(self, task: SyncTask, error_type: str):
        """Schedule a retry for a failed task"""
        task.retry_count += 1
        delay = self._calculate_retry_delay(task.retry_count, error_type)
        task.scheduled_time = datetime.now() + timedelta(seconds=delay)
        task.status = SyncStatus.PENDING
        
        logger.info(f"Scheduled retry {task.retry_count} for task {task.id} "
                   f"in {delay} seconds")

    def _calculate_retry_delay(self, retry_count: int, error_type: str) -> float:
        """Calculate retry delay based on strategy and error type"""
        base_delay = self.retry_config.initial_delay
        
        # Longer delays for rate limit errors
        if error_type == "rate_limit_error":
            base_delay *= 5
        
        if self.retry_config.strategy == RetryStrategy.LINEAR:
            delay = base_delay * retry_count
        elif self.retry_config.strategy == RetryStrategy.EXPONENTIAL:
            delay = base_delay * (self.retry_config.backoff_factor ** (retry_count - 1))
        else:  # FIXED
            delay = base_delay
        
        return min(delay, self.retry_config.max_delay)

    def register_error_handler(self, error_type: str, handler: callable):
        """Register a custom error handler"""
        self.error_handlers[error_type] = handler

    async def _handle_connection_error(self, task: SyncTask, error_message: str) -> bool:
        """Handle connection errors"""
        logger.warning(f"Connection error for task {task.id}: {error_message}")
        return True  # Always retry connection errors

    async def _handle_rate_limit_error(self, task: SyncTask, error_message: str) -> bool:
        """Handle rate limit errors"""
        logger.warning(f"Rate limit error for task {task.id}: {error_message}")
        return True  # Always retry rate limit errors with longer delay

    async def _handle_auth_error(self, task: SyncTask, error_message: str) -> bool:
        """Handle authentication errors"""
        logger.error(f"Authentication error for task {task.id}: {error_message}")
        return False  # Don't retry auth errors

    async def _handle_validation_error(self, task: SyncTask, error_message: str) -> bool:
        """Handle validation errors"""
        logger.error(f"Validation error for task {task.id}: {error_message}")
        return False  # Don't retry validation errors

    def _has_pending_sync(self) -> bool:
        """Check if there are pending sync tasks"""
        return any(task.status == SyncStatus.PENDING for task in self.sync_queue)

    async def get_sync_status(self) -> Dict[str, Any]:
        """Get comprehensive sync status"""
        base_status = {}
        if self.sync_service:
            base_status = await self.sync_service.get_sync_status()
        
        return {
            **base_status,
            "manager_status": {
                "is_running": self.is_running,
                "sync_enabled": settings.SYNC_ENABLED,
                "queue_size": len(self.sync_queue),
                "history_size": len(self.sync_history),
                "retry_config": asdict(self.retry_config)
            },
            "queued_tasks": [asdict(task) for task in self.sync_queue],
            "recent_history": [asdict(task) for task in self.sync_history[-10:]]
        }

    async def get_task_details(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific task"""
        # Check queue
        for task in self.sync_queue:
            if task.id == task_id:
                return asdict(task)
        
        # Check history
        for task in self.sync_history:
            if task.id == task_id:
                return asdict(task)
        
        return None

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        for task in self.sync_queue:
            if task.id == task_id and task.status == SyncStatus.PENDING:
                self.sync_queue.remove(task)
                logger.info(f"Task cancelled: {task_id}")
                return True
        return False

    async def force_sync(self, table_types: List[str]) -> str:
        """Force immediate sync bypassing queue"""
        task_id = await self.schedule_sync(table_types, datetime.now())
        
        # Find and execute the task immediately
        for task in self.sync_queue:
            if task.id == task_id:
                await self._execute_sync_task(task)
                break
                
        return task_id

# Global sync manager instance
sync_manager = SyncManager()