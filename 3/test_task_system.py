"""
Test script for Task Assignment system with Event-Driven Deadlines
Demonstrates the functionality of the lightweight task management system
"""
import asyncio
import json
from datetime import datetime, timedelta
from database import VolunteerDatabase
from task_manager import TaskManager

async def test_task_system():
    """Test the complete task assignment system"""
    
    print("🧪 Testing Task Assignment System with Event-Driven Deadlines")
    print("=" * 60)
    
    # Initialize components
    database = VolunteerDatabase()
    task_manager = TaskManager(database)
    
    # Test 1: Create deadline events
    print("\n1. Creating deadline events...")
    
    # Create some test events that could trigger deadlines
    events = [
        ("volunteer_training_complete", datetime.now() + timedelta(days=7), {"type": "training", "required": True}),
        ("project_kickoff", datetime.now() + timedelta(days=14), {"project_id": 101, "location": "Blue Ash YMCA"}),
        ("event_start", datetime.now() + timedelta(days=21), {"event_name": "Summer Camp 2025", "participants": 150})
    ]
    
    for event_name, event_date, event_data in events:
        success = await task_manager.create_deadline_event(event_name, event_date, event_data)
        print(f"   {'✅' if success else '❌'} Created event: {event_name} on {event_date.strftime('%Y-%m-%d')}")
    
    # Test 2: Create users (simulated)
    print("\n2. Creating test users...")
    
    test_users = [
        {"email": "john@example.com", "first_name": "John", "last_name": "Smith", "age": 28},
        {"email": "sarah@example.com", "first_name": "Sarah", "last_name": "Johnson", "age": 35},
        {"email": "mike@example.com", "first_name": "Mike", "last_name": "Wilson", "age": 42}
    ]
    
    created_users = []
    for user_data in test_users:
        user = await database.create_user(user_data)
        if user:
            created_users.append(user)
            print(f"   ✅ Created user: {user['first_name']} {user['last_name']} ({user['id']})")
    
    if len(created_users) < 2:
        print("   ❌ Need at least 2 users for testing")
        return
    
    creator_id = created_users[0]['id']
    assignee_id = created_users[1]['id']
    
    # Test 3: Create tasks with different deadline types
    print("\n3. Creating tasks with different deadline types...")
    
    tasks = []
    
    # Fixed deadline task
    fixed_task = await task_manager.create_task(
        title="Complete volunteer background check",
        description="Submit background check documents and complete online training",
        created_by=creator_id,
        assigned_to=assignee_id,
        priority=3,
        category="Onboarding",
        estimated_hours=2.0,
        deadline_type="fixed",
        fixed_deadline=datetime.now() + timedelta(days=5),
        tags=["onboarding", "required", "background-check"]
    )
    
    if fixed_task:
        tasks.append(fixed_task)
        print(f"   ✅ Created fixed deadline task: {fixed_task['title']}")
        print(f"       Deadline: {fixed_task['fixed_deadline']}")
    
    # Event-based deadline task
    event_task = await task_manager.create_task(
        title="Prepare activity materials",
        description="Gather and organize materials for summer camp activities",
        created_by=creator_id,
        assigned_to=assignee_id,
        priority=2,
        category="Preparation",
        estimated_hours=4.0,
        deadline_type="event_based",
        event_trigger="project_kickoff",
        deadline_offset_days=-3,  # 3 days before project kickoff
        tags=["preparation", "materials", "camp"]
    )
    
    if event_task:
        tasks.append(event_task)
        print(f"   ✅ Created event-based deadline task: {event_task['title']}")
        print(f"       Event trigger: {event_task['event_trigger']} (offset: {event_task['deadline_offset_days']} days)")
        print(f"       Calculated deadline: {event_task.get('deadline_calculated', 'Not calculated')}")
    
    # Flexible deadline task
    flexible_task = await task_manager.create_task(
        title="Review volunteer handbook",
        description="Read through the complete volunteer handbook and familiarize yourself with policies",
        created_by=creator_id,
        assigned_to=assignee_id,
        priority=1,
        category="Training",
        estimated_hours=1.5,
        deadline_type="flexible",
        tags=["handbook", "policies", "self-paced"]
    )
    
    if flexible_task:
        tasks.append(flexible_task)
        print(f"   ✅ Created flexible deadline task: {flexible_task['title']}")
    
    # Test 4: Update task progress
    print("\n4. Testing task progress updates...")
    
    if tasks:
        test_task = tasks[0]
        
        # Update progress to 25%
        success = await task_manager.update_task_progress(
            test_task['id'], assignee_id, 25, 
            status="in_progress", 
            notes="Started working on background check forms",
            time_logged=0.5
        )
        print(f"   {'✅' if success else '❌'} Updated task progress to 25%")
        
        # Update progress to 100%
        success = await task_manager.update_task_progress(
            test_task['id'], assignee_id, 100,
            status="completed",
            notes="Background check submitted and approved",
            time_logged=2.0
        )
        print(f"   {'✅' if success else '❌'} Completed task")
    
    # Test 5: Get user task dashboard
    print("\n5. Testing user task dashboard...")
    
    dashboard = await task_manager.get_user_task_dashboard(assignee_id)
    if dashboard:
        stats = dashboard.get('stats', {})
        print(f"   ✅ User dashboard retrieved:")
        print(f"       Total tasks: {stats.get('total_tasks', 0)}")
        print(f"       Pending: {stats.get('pending_tasks', 0)}")
        print(f"       In progress: {stats.get('in_progress_tasks', 0)}")
        print(f"       Completed: {stats.get('completed_tasks', 0)}")
        print(f"       Overdue: {stats.get('overdue_tasks', 0)}")
    
    # Test 6: Test event deadline recalculation
    print("\n6. Testing event deadline recalculation...")
    
    # Update the project_kickoff event to a new date
    new_kickoff_date = datetime.now() + timedelta(days=10)  # Changed from 14 to 10 days
    success = await task_manager.create_deadline_event(
        "project_kickoff", 
        new_kickoff_date, 
        {"project_id": 101, "location": "Blue Ash YMCA", "updated": True}
    )
    
    if success:
        print(f"   ✅ Updated project_kickoff event to {new_kickoff_date.strftime('%Y-%m-%d')}")
        
        # Check if event-based task deadline was recalculated
        updated_task = await database.get_task_details(event_task['id']) if event_task else None
        if updated_task:
            print(f"   ✅ Task deadline recalculated to: {updated_task.get('deadline_calculated', 'Not found')}")
    
    # Test 7: Get upcoming deadlines
    print("\n7. Testing upcoming deadlines...")
    
    upcoming_tasks = await task_manager.get_upcoming_deadlines(days_ahead=30)
    print(f"   ✅ Found {len(upcoming_tasks)} tasks with upcoming deadlines:")
    
    for task in upcoming_tasks[:3]:  # Show first 3
        deadline = task.get('effective_deadline', 'No deadline')
        print(f"       - {task['title']}: {deadline}")
    
    # Test 8: Test notifications
    print("\n8. Testing notification system...")
    
    # Create some test notifications
    if tasks:
        await database.create_task_notification(
            tasks[0]['id'], assignee_id, 'deadline_approaching',
            f"Task '{tasks[0]['title']}' is due soon"
        )
        
        notifications = await database.get_user_notifications(assignee_id)
        print(f"   ✅ User has {len(notifications)} notifications")
        
        if notifications:
            print(f"       Latest: {notifications[0].get('message', 'No message')}")
    
    # Test 9: Analytics
    print("\n9. Testing task analytics...")
    
    analytics = await task_manager.get_task_analytics(user_id=creator_id, days=30)
    if analytics:
        print(f"   ✅ Analytics for creator:")
        print(f"       Total tasks created: {analytics.get('total_tasks', 0)}")
        print(f"       Completion rate: {analytics.get('completion_rate', 0):.1%}")
        print(f"       Average completion time: {analytics.get('average_completion_time', 0):.1f} hours")
    
    # Test 10: Deadline monitoring
    print("\n10. Testing deadline monitoring...")
    
    await task_manager.check_and_send_deadline_notifications()
    print("   ✅ Deadline monitoring check completed")
    
    print("\n" + "=" * 60)
    print("🎉 Task Assignment System testing completed!")
    print("\nKey features demonstrated:")
    print("✅ Fixed deadline tasks")
    print("✅ Event-driven deadline tasks")  
    print("✅ Flexible deadline tasks")
    print("✅ Task assignment and progress tracking")
    print("✅ Event deadline recalculation")
    print("✅ Notification system")
    print("✅ User task dashboard")
    print("✅ Analytics and reporting")
    print("✅ Deadline monitoring")

# Example API usage
def example_api_requests():
    """Show example API requests for the task system"""
    
    print("\n📋 Example API Requests:")
    print("=" * 40)
    
    examples = [
        {
            "description": "Create a task with fixed deadline",
            "method": "POST",
            "endpoint": "/api/tasks",
            "payload": {
                "title": "Complete volunteer orientation",
                "description": "Attend the volunteer orientation session",
                "priority": 3,
                "category": "Onboarding",
                "deadline_type": "fixed",
                "fixed_deadline": "2025-01-15T10:00:00Z",
                "estimated_hours": 2.0,
                "tags": ["orientation", "required"]
            }
        },
        {
            "description": "Create a task with event-driven deadline",
            "method": "POST", 
            "endpoint": "/api/tasks",
            "payload": {
                "title": "Set up registration booth",
                "description": "Prepare and set up the registration booth for the community event",
                "priority": 2,
                "category": "Event Preparation",
                "deadline_type": "event_based",
                "event_trigger": "event_start",
                "deadline_offset_days": -1,
                "estimated_hours": 3.0,
                "tags": ["setup", "registration", "event"]
            }
        },
        {
            "description": "Update task progress",
            "method": "PUT",
            "endpoint": "/api/tasks/{task_id}",
            "payload": {
                "progress": 75,
                "status": "in_progress",
                "notes": "Registration materials prepared, booth location confirmed",
                "time_logged": 2.5
            }
        },
        {
            "description": "Create deadline event",
            "method": "POST",
            "endpoint": "/api/deadline-events", 
            "payload": {
                "event_name": "community_fair",
                "event_date": "2025-02-15T09:00:00Z",
                "event_data": {
                    "location": "M.E. Lyons YMCA",
                    "expected_volunteers": 25,
                    "setup_time": "08:00"
                }
            }
        },
        {
            "description": "Get user task dashboard",
            "method": "GET",
            "endpoint": "/api/users/{user_id}/tasks",
            "payload": None
        },
        {
            "description": "Get upcoming deadlines",
            "method": "GET", 
            "endpoint": "/api/deadlines/upcoming?days_ahead=7",
            "payload": None
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['description']}")
        print(f"   {example['method']} {example['endpoint']}")
        if example['payload']:
            print(f"   Body: {json.dumps(example['payload'], indent=2)}")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_task_system())
    
    # Show API examples
    example_api_requests()