# Task Assignment System with Event-Driven Deadlines

## Overview

This system provides lightweight task management functionality tied to events and deadlines for the YMCA Volunteer PathFinder application. It allows for creating, assigning, and tracking tasks with flexible deadline management based on real-world events.

## Key Features

### 🎯 **Lightweight Task Management**
- Create and assign tasks to volunteers
- Track progress and completion status
- Support for task priorities, categories, and tagging
- Time logging and notes for tasks

### ⏰ **Event-Driven Deadlines**
- **Fixed Deadlines**: Traditional date/time deadlines
- **Event-Based Deadlines**: Deadlines calculated from event triggers
- **Flexible Deadlines**: Tasks without strict deadlines
- Automatic recalculation when events change

### 🔔 **Smart Notifications**
- Deadline approaching alerts (24 hours before)
- Overdue task notifications
- Assignment notifications
- Status change notifications

### 📊 **Analytics & Reporting**
- Task completion rates
- Time tracking analysis
- User task dashboards
- Overdue task monitoring

## Database Schema

The system adds 6 new tables to the existing database:

### 1. `tasks` - Main task information
```sql
- id (UUID, Primary Key)
- title, description, priority, status
- deadline_type ('fixed', 'event_based', 'flexible')
- fixed_deadline, event_trigger, deadline_offset_days
- deadline_calculated (computed from events)
- dependencies, tags, task_data (JSONB)
```

### 2. `task_assignments` - User-task relationships
```sql
- task_id, user_id (composite key)
- status ('assigned', 'accepted', 'declined', 'completed')
- progress_percentage, time_logged, notes
```

### 3. `deadline_events` - Event triggers
```sql
- event_name (unique)
- event_date, event_data, is_active
```

### 4. `task_deadline_history` - Deadline change tracking
```sql
- task_id, old_deadline, new_deadline
- change_reason, changed_by, changed_at
```

### 5. `task_notifications` - User notifications
```sql
- task_id, user_id, notification_type
- message, is_read, sent_at, read_at
```

## API Endpoints

### Task Management
```http
POST   /api/tasks                    # Create new task
GET    /api/tasks/{task_id}         # Get task details
PUT    /api/tasks/{task_id}         # Update task progress
POST   /api/tasks/{task_id}/assign  # Assign task to user
```

### User Interface
```http
GET    /api/users/{user_id}/tasks   # User task dashboard
GET    /api/users/{user_id}/notifications  # User notifications
PUT    /api/notifications/{id}/read # Mark notification as read
```

### Deadline Management
```http
POST   /api/deadline-events         # Create/update deadline event
GET    /api/deadlines/upcoming      # Get upcoming deadlines
GET    /api/deadlines/overdue       # Get overdue tasks
POST   /api/tasks/check-deadlines   # Trigger deadline check
```

### Analytics
```http
GET    /api/tasks/analytics         # Get task analytics
```

## Usage Examples

### Creating Tasks

#### 1. Fixed Deadline Task
```python
task_data = {
    "title": "Complete volunteer background check",
    "description": "Submit required documents",
    "priority": 3,  # 1=low, 2=medium, 3=high, 4=urgent
    "category": "Onboarding",
    "deadline_type": "fixed",
    "fixed_deadline": "2025-01-15T10:00:00Z",
    "estimated_hours": 2.0,
    "tags": ["background-check", "required"]
}
# POST /api/tasks
```

#### 2. Event-Based Deadline Task
```python
task_data = {
    "title": "Set up event registration booth",
    "description": "Prepare registration materials and booth setup",
    "priority": 2,
    "category": "Event Preparation", 
    "deadline_type": "event_based",
    "event_trigger": "community_fair_start",
    "deadline_offset_days": -1,  # 1 day before event
    "estimated_hours": 3.0,
    "tags": ["setup", "registration"]
}
```

#### 3. Flexible Deadline Task
```python
task_data = {
    "title": "Review volunteer handbook",
    "description": "Familiarize yourself with policies and procedures",
    "priority": 1,
    "category": "Training",
    "deadline_type": "flexible",  # No strict deadline
    "estimated_hours": 1.5,
    "tags": ["handbook", "self-paced"]
}
```

### Creating Deadline Events
```python
event_data = {
    "event_name": "summer_camp_2025",
    "event_date": "2025-06-15T08:00:00Z",
    "event_data": {
        "location": "Blue Ash YMCA",
        "participants": 150,
        "duration_weeks": 8
    }
}
# POST /api/deadline-events
```

When this event is created/updated, all tasks with `event_trigger="summer_camp_2025"` will have their deadlines automatically recalculated.

### Updating Task Progress
```python
progress_data = {
    "progress": 75,
    "status": "in_progress", 
    "notes": "Background check submitted, awaiting approval",
    "time_logged": 1.5
}
# PUT /api/tasks/{task_id}
```

## Event-Driven Deadline System

### How It Works
1. **Event Creation**: Define events that can trigger deadlines
   ```python
   # Event: Project kickoff meeting
   event_date = "2025-02-01T09:00:00Z"
   ```

2. **Task Creation**: Create tasks with event-based deadlines
   ```python
   # Task: Prepare meeting materials
   # Due 2 days BEFORE project kickoff
   deadline_offset_days = -2
   ```

3. **Automatic Calculation**: System calculates actual deadline
   ```
   Event Date: 2025-02-01T09:00:00Z
   Offset: -2 days
   Calculated Deadline: 2025-01-30T09:00:00Z
   ```

4. **Event Updates**: If event date changes, all related task deadlines update automatically
   ```python
   # Event moved to Feb 5th
   # Task deadline automatically becomes Jan 3rd
   ```

### Common Event Types
- `volunteer_training_complete` - After training completion
- `project_kickoff` - Project start dates
- `event_start` - Community events, camps, programs
- `registration_deadline` - Registration cutoffs
- `facility_booking` - Facility reservation dates

## Notification System

### Notification Types
- `deadline_approaching` - 24 hours before deadline
- `overdue` - Task past deadline
- `assignment_new` - New task assigned
- `status_change` - Task status updated
- `deadline_change` - Event caused deadline change

### Automatic Notifications
The system automatically sends notifications for:
- Tasks due within 24 hours
- Overdue tasks (daily reminders)
- New task assignments
- Deadline changes from event updates

## Task Dashboard

Each user gets a comprehensive dashboard showing:

```json
{
  "user_id": "user-uuid",
  "stats": {
    "total_tasks": 12,
    "pending_tasks": 3,
    "in_progress_tasks": 5,
    "completed_tasks": 4,
    "overdue_tasks": 1,
    "due_soon_tasks": 2
  },
  "tasks": [...], // Full task list
  "tasks_by_priority": {
    "urgent": [...],
    "high": [...],
    "medium": [...],
    "low": [...]
  },
  "notifications": [...] // Unread notifications
}
```

## Analytics

### System Analytics
```json
{
  "total_tasks": 156,
  "completion_rate": 0.73,
  "average_completion_time": 2.4,
  "tasks_by_status": {
    "completed": 114,
    "in_progress": 28,
    "pending": 14
  },
  "overdue_count": 8
}
```

### User Analytics
Track individual volunteer performance and engagement.

## Integration with YMCA System

The task system integrates seamlessly with existing volunteer management:

### 1. Volunteer Onboarding
```python
# Create onboarding tasks automatically when volunteer signs up
tasks = [
    "Complete background check",
    "Attend orientation session", 
    "Review safety procedures",
    "Complete required training"
]
```

### 2. Event Preparation
```python
# Create event-based tasks tied to camp/program dates
# Tasks automatically get proper deadlines
```

### 3. Ongoing Volunteer Management
```python
# Regular tasks for active volunteers
# Deadline monitoring ensures nothing falls through cracks
```

## Testing

Run the comprehensive test script:
```bash
python test_task_system.py
```

This demonstrates:
- Task creation with different deadline types
- Event-driven deadline recalculation
- Progress tracking and notifications
- User dashboard functionality
- Analytics reporting

## Production Deployment

### 1. Database Setup
Run the SQL commands from `database.py` to create the required tables in your Supabase instance.

### 2. Environment Variables
Ensure these are configured:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_service_key
```

### 3. Task Scheduler
In production, run the deadline monitoring in a separate process:
```python
# Background task scheduler
task_scheduler = TaskScheduler(task_manager)
asyncio.create_task(task_scheduler.start())
```

### 4. API Integration
The task management endpoints are automatically included when you start the FastAPI application.

## Best Practices

### 1. Event Naming
Use consistent, descriptive event names:
- `summer_camp_2025_start`
- `volunteer_training_march_completion`
- `facility_maintenance_window`

### 2. Task Categories
Organize tasks with clear categories:
- "Onboarding"
- "Training" 
- "Event Preparation"
- "Maintenance"
- "Documentation"

### 3. Priority Levels
- **Urgent (4)**: Safety-critical or time-sensitive
- **High (3)**: Important deadlines, required tasks
- **Medium (2)**: Regular tasks, moderate importance
- **Low (1)**: Nice-to-have, flexible timing

### 4. Deadline Offsets
Plan appropriate lead times:
- Training completion: -7 days before event
- Material preparation: -3 days before event  
- Setup tasks: -1 day before event

## Troubleshooting

### Common Issues

1. **Tasks not getting calculated deadlines**
   - Ensure event exists with matching `event_name`
   - Check event `is_active = true`
   - Verify `deadline_type = 'event_based'`

2. **Notifications not sending**
   - Check task has assigned users
   - Verify deadline is within notification window
   - Ensure user has valid user_id

3. **Dashboard not loading**
   - Confirm user exists in users table
   - Check task assignments are properly linked

### Debug Endpoints
- `GET /health` - System health check
- `POST /api/tasks/check-deadlines` - Manual deadline check
- `GET /api/tasks/analytics` - System analytics

---

## Summary

This lightweight task assignment system provides powerful, event-driven task management specifically designed for volunteer organizations like the YMCA. It handles the complexity of coordinating tasks around real-world events while providing clear visibility and automated notifications to keep everyone on track.

The system is production-ready and integrates seamlessly with the existing volunteer management infrastructure.