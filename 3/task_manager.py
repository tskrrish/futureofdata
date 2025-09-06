"""
Task Assignment Manager with Event-Driven Deadlines
Handles lightweight task management for YMCA volunteer system
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import asyncio
import logging
from database import VolunteerDatabase

logger = logging.getLogger(__name__)

class TaskManager:
    """Manages task assignments with event-driven deadline functionality"""
    
    def __init__(self, database: VolunteerDatabase):
        self.database = database
        self.deadline_monitors = {}  # Active deadline monitoring tasks
        
    async def create_task(
        self,
        title: str,
        description: str = "",
        created_by: str = None,
        assigned_to: str = None,
        priority: int = 2,
        category: str = "",
        project_id: int = None,
        estimated_hours: float = None,
        deadline_type: str = "fixed",
        fixed_deadline: datetime = None,
        event_trigger: str = None,
        deadline_offset_days: int = 0,
        dependencies: List[str] = None,
        tags: List[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new task with optional event-driven deadlines
        
        Args:
            title: Task title
            description: Task description
            created_by: User ID who created the task
            assigned_to: User ID to assign task to
            priority: 1=low, 2=medium, 3=high, 4=urgent
            category: Task category
            project_id: Associated project ID
            estimated_hours: Estimated completion time
            deadline_type: 'fixed', 'event_based', or 'flexible'
            fixed_deadline: Fixed deadline datetime
            event_trigger: Event name that triggers deadline calculation
            deadline_offset_days: Days relative to event trigger
            dependencies: List of task IDs this task depends on
            tags: List of tags for categorization
        """
        try:
            # Validate deadline configuration
            if deadline_type == 'fixed' and not fixed_deadline:
                raise ValueError("Fixed deadline required for deadline_type='fixed'")
            elif deadline_type == 'event_based' and not event_trigger:
                raise ValueError("Event trigger required for deadline_type='event_based'")
            
            # Prepare task data
            task_data = {
                'title': title,
                'description': description,
                'priority': priority,
                'category': category,
                'project_id': project_id,
                'estimated_hours': estimated_hours,
                'created_by': created_by,
                'assigned_to': assigned_to,
                'deadline_type': deadline_type,
                'fixed_deadline': fixed_deadline.isoformat() if fixed_deadline else None,
                'event_trigger': event_trigger,
                'deadline_offset_days': deadline_offset_days,
                'dependencies': json.dumps(dependencies or []),
                'tags': json.dumps(tags or []),
                'task_data': json.dumps(kwargs)
            }
            
            # Create task in database
            task = await self.database.create_task(task_data)
            
            if task:
                logger.info(f"✅ Created task '{title}' with ID {task['id']}")
                
                # Start deadline monitoring if needed
                if deadline_type in ['fixed', 'event_based']:
                    await self._start_deadline_monitoring(task['id'])
                
                return task
            else:
                logger.error(f"❌ Failed to create task '{title}'")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating task: {e}")
            return None
    
    async def assign_task_to_user(self, task_id: str, user_id: str, assigned_by: str = None) -> bool:
        """Assign a task to a specific user"""
        try:
            success = await self.database.assign_task(task_id, user_id, assigned_by)
            
            if success:
                # Get task details for notification
                task = await self.database.get_task_details(task_id)
                if task:
                    await self.database.create_task_notification(
                        task_id, user_id, 'assignment_new',
                        f"You have been assigned task: {task['title']}"
                    )
                
                logger.info(f"✅ Assigned task {task_id} to user {user_id}")
                return True
            else:
                logger.error(f"❌ Failed to assign task {task_id} to user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error assigning task: {e}")
            return False
    
    async def update_task_progress(self, task_id: str, user_id: str, progress: int, 
                                 status: str = None, notes: str = "", time_logged: float = 0.0) -> bool:
        """Update task progress and status"""
        try:
            # Validate progress
            if not 0 <= progress <= 100:
                raise ValueError("Progress must be between 0 and 100")
            
            # Determine status if not provided
            if not status:
                if progress == 100:
                    status = 'completed'
                elif progress > 0:
                    status = 'in_progress'
                else:
                    status = 'pending'
            
            # Update task status
            success = await self.database.update_task_status(task_id, status, user_id, progress)
            
            if success:
                # Update assignment with notes and time logged
                if notes or time_logged > 0:
                    assignment_data = {}
                    if notes:
                        assignment_data['notes'] = notes
                    if time_logged > 0:
                        assignment_data['time_logged'] = time_logged
                    
                    if assignment_data:
                        assignment_data['last_updated'] = datetime.now().isoformat()
                        
                        self.database.supabase.table('task_assignments')\
                            .update(assignment_data)\
                            .eq('task_id', task_id)\
                            .eq('user_id', user_id)\
                            .execute()
                
                # Create notification for status change
                if status == 'completed':
                    task = await self.database.get_task_details(task_id)
                    if task and task.get('created_by'):
                        await self.database.create_task_notification(
                            task_id, task['created_by'], 'status_change',
                            f"Task '{task['title']}' has been completed"
                        )
                
                logger.info(f"✅ Updated task {task_id} progress to {progress}% with status '{status}'")
                return True
            else:
                logger.error(f"❌ Failed to update task {task_id} progress")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating task progress: {e}")
            return False
    
    async def get_user_task_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive task dashboard for a user"""
        try:
            # Get assigned tasks
            assigned_tasks = await self.database.get_user_tasks(user_id, include_created=True)
            
            # Get notifications
            notifications = await self.database.get_user_notifications(user_id, unread_only=True)
            
            # Calculate task statistics
            stats = {
                'total_tasks': len(assigned_tasks),
                'pending_tasks': len([t for t in assigned_tasks if t['status'] == 'pending']),
                'in_progress_tasks': len([t for t in assigned_tasks if t['status'] == 'in_progress']),
                'completed_tasks': len([t for t in assigned_tasks if t['status'] == 'completed']),
                'overdue_tasks': 0,
                'due_soon_tasks': 0  # Due within 24 hours
            }
            
            current_time = datetime.now()
            due_soon_threshold = current_time + timedelta(hours=24)
            
            for task in assigned_tasks:
                deadline = None
                if task['deadline_type'] == 'fixed' and task.get('fixed_deadline'):
                    deadline = datetime.fromisoformat(task['fixed_deadline'].replace('Z', '+00:00'))
                elif task['deadline_type'] == 'event_based' and task.get('deadline_calculated'):
                    deadline = datetime.fromisoformat(task['deadline_calculated'].replace('Z', '+00:00'))
                
                if deadline and task['status'] != 'completed':
                    if deadline < current_time:
                        stats['overdue_tasks'] += 1
                    elif deadline < due_soon_threshold:
                        stats['due_soon_tasks'] += 1
            
            # Group tasks by priority and status
            tasks_by_priority = {}
            tasks_by_category = {}
            
            for task in assigned_tasks:
                priority = task.get('priority', 2)
                priority_name = {1: 'low', 2: 'medium', 3: 'high', 4: 'urgent'}.get(priority, 'medium')
                
                if priority_name not in tasks_by_priority:
                    tasks_by_priority[priority_name] = []
                tasks_by_priority[priority_name].append(task)
                
                category = task.get('category', 'uncategorized')
                if category not in tasks_by_category:
                    tasks_by_category[category] = []
                tasks_by_category[category].append(task)
            
            dashboard = {
                'user_id': user_id,
                'stats': stats,
                'tasks': assigned_tasks,
                'tasks_by_priority': tasks_by_priority,
                'tasks_by_category': tasks_by_category,
                'notifications': notifications,
                'generated_at': current_time.isoformat()
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"❌ Error getting user task dashboard: {e}")
            return {}
    
    async def create_deadline_event(self, event_name: str, event_date: datetime, 
                                  event_data: Dict[str, Any] = None) -> bool:
        """Create or update a deadline trigger event"""
        try:
            success = await self.database.create_deadline_event(event_name, event_date, event_data)
            
            if success:
                logger.info(f"✅ Created/updated deadline event '{event_name}' for {event_date}")
                
                # Notify affected users about deadline changes
                await self._notify_deadline_changes(event_name)
                
                return True
            else:
                logger.error(f"❌ Failed to create deadline event '{event_name}'")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error creating deadline event: {e}")
            return False
    
    async def get_upcoming_deadlines(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get tasks with upcoming deadlines"""
        try:
            future_time = datetime.now() + timedelta(days=days_ahead)
            current_time = datetime.now()
            
            # Query tasks with upcoming fixed deadlines
            fixed_deadline_tasks = self.database.supabase.table('tasks')\
                .select('*, task_assignments(user_id, users(first_name, last_name, email))')\
                .eq('deadline_type', 'fixed')\
                .gte('fixed_deadline', current_time.isoformat())\
                .lte('fixed_deadline', future_time.isoformat())\
                .neq('status', 'completed')\
                .execute()
            
            # Query tasks with upcoming calculated deadlines
            calculated_deadline_tasks = self.database.supabase.table('tasks')\
                .select('*, task_assignments(user_id, users(first_name, last_name, email))')\
                .eq('deadline_type', 'event_based')\
                .gte('deadline_calculated', current_time.isoformat())\
                .lte('deadline_calculated', future_time.isoformat())\
                .neq('status', 'completed')\
                .execute()
            
            # Combine and sort by deadline
            upcoming_tasks = []
            if fixed_deadline_tasks.data:
                for task in fixed_deadline_tasks.data:
                    task['effective_deadline'] = task['fixed_deadline']
                    upcoming_tasks.append(task)
            
            if calculated_deadline_tasks.data:
                for task in calculated_deadline_tasks.data:
                    task['effective_deadline'] = task['deadline_calculated']
                    upcoming_tasks.append(task)
            
            # Sort by effective deadline
            upcoming_tasks.sort(key=lambda x: x['effective_deadline'])
            
            return upcoming_tasks
            
        except Exception as e:
            logger.error(f"❌ Error getting upcoming deadlines: {e}")
            return []
    
    async def check_and_send_deadline_notifications(self):
        """Check for upcoming deadlines and send notifications"""
        try:
            # Get tasks due within 24 hours
            upcoming_tasks = await self.get_upcoming_deadlines(days_ahead=1)
            
            # Get overdue tasks
            overdue_tasks = await self.database.get_overdue_tasks()
            
            # Send notifications for upcoming deadlines
            for task in upcoming_tasks:
                deadline = datetime.fromisoformat(task['effective_deadline'].replace('Z', '+00:00'))
                hours_until_deadline = (deadline - datetime.now()).total_seconds() / 3600
                
                # Send notification if within 24 hours and not already notified recently
                if hours_until_deadline <= 24:
                    for assignment in task.get('task_assignments', []):
                        user_id = assignment['user_id']
                        
                        # Check if we already sent a notification recently
                        recent_notifications = self.database.supabase.table('task_notifications')\
                            .select('id')\
                            .eq('task_id', task['id'])\
                            .eq('user_id', user_id)\
                            .eq('notification_type', 'deadline_approaching')\
                            .gte('sent_at', (datetime.now() - timedelta(hours=12)).isoformat())\
                            .execute()
                        
                        if not recent_notifications.data:
                            hours_text = f"{int(hours_until_deadline)} hours" if hours_until_deadline > 1 else "less than 1 hour"
                            await self.database.create_task_notification(
                                task['id'], user_id, 'deadline_approaching',
                                f"Task '{task['title']}' is due in {hours_text}"
                            )
            
            # Send notifications for overdue tasks
            for task in overdue_tasks:
                for assignment in task.get('task_assignments', []):
                    user_id = assignment['user_id']
                    
                    # Check if we already sent an overdue notification recently
                    recent_notifications = self.database.supabase.table('task_notifications')\
                        .select('id')\
                        .eq('task_id', task['id'])\
                        .eq('user_id', user_id)\
                        .eq('notification_type', 'overdue')\
                        .gte('sent_at', (datetime.now() - timedelta(hours=24)).isoformat())\
                        .execute()
                    
                    if not recent_notifications.data:
                        await self.database.create_task_notification(
                            task['id'], user_id, 'overdue',
                            f"Task '{task['title']}' is overdue"
                        )
            
            logger.info(f"✅ Processed deadline notifications for {len(upcoming_tasks)} upcoming and {len(overdue_tasks)} overdue tasks")
            
        except Exception as e:
            logger.error(f"❌ Error checking deadline notifications: {e}")
    
    async def _start_deadline_monitoring(self, task_id: str):
        """Start monitoring a task's deadline"""
        # This would typically run in a background task scheduler
        # For now, we'll just log that monitoring should be started
        logger.info(f"📅 Started deadline monitoring for task {task_id}")
    
    async def _notify_deadline_changes(self, event_name: str):
        """Notify users about deadline changes due to event updates"""
        try:
            # Get all tasks affected by this event
            affected_tasks = self.database.supabase.table('tasks')\
                .select('id, title, task_assignments(user_id)')\
                .eq('event_trigger', event_name)\
                .eq('deadline_type', 'event_based')\
                .execute()
            
            # Send notifications to assigned users
            for task in affected_tasks.data:
                for assignment in task.get('task_assignments', []):
                    await self.database.create_task_notification(
                        task['id'], assignment['user_id'], 'deadline_change',
                        f"Deadline updated for task '{task['title']}' due to event change"
                    )
            
            logger.info(f"✅ Sent deadline change notifications for {len(affected_tasks.data)} tasks")
            
        except Exception as e:
            logger.error(f"❌ Error notifying deadline changes: {e}")
    
    async def get_task_analytics(self, user_id: str = None, days: int = 30) -> Dict[str, Any]:
        """Get task analytics for system or specific user"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Base query
            base_query = self.database.supabase.table('tasks').select('*')
            if user_id:
                base_query = base_query.eq('created_by', user_id)
            
            # Get tasks created in period
            tasks_in_period = base_query.gte('created_at', start_date).execute()
            
            # Calculate analytics
            analytics = {
                'period_days': days,
                'total_tasks': len(tasks_in_period.data),
                'tasks_by_status': {},
                'tasks_by_priority': {},
                'tasks_by_category': {},
                'completion_rate': 0.0,
                'average_completion_time': 0.0,
                'overdue_count': 0,
                'generated_at': datetime.now().isoformat()
            }
            
            if tasks_in_period.data:
                completed_tasks = []
                completion_times = []
                
                for task in tasks_in_period.data:
                    # Count by status
                    status = task['status']
                    analytics['tasks_by_status'][status] = analytics['tasks_by_status'].get(status, 0) + 1
                    
                    # Count by priority
                    priority = {1: 'low', 2: 'medium', 3: 'high', 4: 'urgent'}.get(task.get('priority', 2), 'medium')
                    analytics['tasks_by_priority'][priority] = analytics['tasks_by_priority'].get(priority, 0) + 1
                    
                    # Count by category
                    category = task.get('category', 'uncategorized')
                    analytics['tasks_by_category'][category] = analytics['tasks_by_category'].get(category, 0) + 1
                    
                    # Track completed tasks
                    if status == 'completed':
                        completed_tasks.append(task)
                        if task.get('created_at') and task.get('completed_at'):
                            created = datetime.fromisoformat(task['created_at'].replace('Z', '+00:00'))
                            completed = datetime.fromisoformat(task['completed_at'].replace('Z', '+00:00'))
                            completion_time = (completed - created).total_seconds() / 3600  # hours
                            completion_times.append(completion_time)
                
                # Calculate completion rate
                analytics['completion_rate'] = len(completed_tasks) / len(tasks_in_period.data)
                
                # Calculate average completion time
                if completion_times:
                    analytics['average_completion_time'] = sum(completion_times) / len(completion_times)
            
            # Get overdue tasks count
            overdue_tasks = await self.database.get_overdue_tasks()
            if user_id:
                # Filter overdue tasks for specific user
                user_overdue = []
                for task in overdue_tasks:
                    if task.get('created_by') == user_id:
                        user_overdue.append(task)
                    elif task.get('task_assignments'):
                        for assignment in task['task_assignments']:
                            if assignment.get('user_id') == user_id:
                                user_overdue.append(task)
                                break
                analytics['overdue_count'] = len(user_overdue)
            else:
                analytics['overdue_count'] = len(overdue_tasks)
            
            return analytics
            
        except Exception as e:
            logger.error(f"❌ Error getting task analytics: {e}")
            return {}


# Background task scheduler (simplified version)
class TaskScheduler:
    """Handles periodic task monitoring and notifications"""
    
    def __init__(self, task_manager: TaskManager):
        self.task_manager = task_manager
        self.running = False
    
    async def start(self):
        """Start the task scheduler"""
        self.running = True
        logger.info("🚀 Starting task scheduler")
        
        # Run deadline notifications every hour
        while self.running:
            try:
                await self.task_manager.check_and_send_deadline_notifications()
                await asyncio.sleep(3600)  # 1 hour
            except Exception as e:
                logger.error(f"❌ Scheduler error: {e}")
                await asyncio.sleep(300)  # 5 minutes on error
    
    def stop(self):
        """Stop the task scheduler"""
        self.running = False
        logger.info("🛑 Stopping task scheduler")