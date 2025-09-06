"""
Test script for the Recurring Role Matching system
Demonstrates the functionality of the new recurring role matching feature
"""
import asyncio
import json
from datetime import date, datetime, timedelta
import sys
import os

# Add the current directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from recurring_role_manager import RecurringRoleManager
from data_processor import VolunteerDataProcessor
from database import VolunteerDatabase

async def test_recurring_role_system():
    """Test the recurring role matching system"""
    print("🧪 Testing Recurring Role Matching System")
    print("=" * 50)
    
    # Initialize test data
    try:
        # Try to load real volunteer data if available
        if os.path.exists("Y Volunteer Raw Data - Jan- August 2025.xlsx"):
            print("📊 Loading real volunteer data...")
            processor = VolunteerDataProcessor("Y Volunteer Raw Data - Jan- August 2025.xlsx")
            volunteer_data = processor.get_volunteer_recommendations_data()
        else:
            print("📊 Creating mock volunteer data for testing...")
            volunteer_data = create_mock_volunteer_data()
        
        # Initialize database
        database = VolunteerDatabase()
        
        # Initialize recurring role manager
        role_manager = RecurringRoleManager(volunteer_data, database)
        
        print(f"✅ Initialized with {len(volunteer_data.get('volunteers', []))} volunteers")
        
        # Test 1: Create recurring shifts
        print("\n🔧 Test 1: Creating recurring shifts...")
        
        test_shifts = [
            {
                'name': 'Youth Development - Monday Morning',
                'description': 'Help with after-school programs',
                'branch': 'Blue Ash',
                'category': 'Youth Development',
                'day_of_week': 0,  # Monday
                'start_time': '09:00',
                'end_time': '12:00',
                'required_volunteers': 2,
                'required_skills': ['youth mentoring', 'communication'],
                'recurrence_pattern': 'weekly',
                'start_date': date.today()
            },
            {
                'name': 'Fitness Classes - Wednesday Evening',
                'description': 'Assist with group fitness classes',
                'branch': 'M.E. Lyons',
                'category': 'Fitness & Wellness',
                'day_of_week': 2,  # Wednesday
                'start_time': '18:00',
                'end_time': '20:00',
                'required_volunteers': 1,
                'required_skills': ['fitness instruction'],
                'recurrence_pattern': 'weekly',
                'start_date': date.today()
            },
            {
                'name': 'Special Events - Saturday',
                'description': 'Help with community events',
                'branch': 'Campbell County',
                'category': 'Special Events',
                'day_of_week': 5,  # Saturday
                'start_time': '10:00',
                'end_time': '16:00',
                'required_volunteers': 3,
                'required_skills': [],
                'recurrence_pattern': 'biweekly',
                'start_date': date.today()
            }
        ]
        
        shift_ids = []
        for shift_data in test_shifts:
            shift_id = role_manager.create_recurring_shift(shift_data)
            shift_ids.append(shift_id)
            print(f"  ✅ Created shift: {shift_data['name']} (ID: {shift_id[:8]}...)")
        
        # Test 2: Add volunteer availability
        print("\n🔧 Test 2: Adding volunteer availability...")
        
        # Get some test volunteer IDs from the data
        volunteers_df = volunteer_data.get('volunteers')
        if volunteers_df is not None and len(volunteers_df) > 0:
            test_volunteer_ids = volunteers_df['contact_id'].head(5).tolist()
            
            for i, volunteer_id in enumerate(test_volunteer_ids):
                # Create varied availability patterns
                availability = []
                
                if i % 3 == 0:  # Available Monday-Friday
                    for day in range(5):
                        availability.append({
                            'day_of_week': day,
                            'start_time': '09:00',
                            'end_time': '17:00',
                            'preferred': day in [0, 2]  # Prefer Monday and Wednesday
                        })
                elif i % 3 == 1:  # Available evenings and weekends
                    for day in range(7):
                        if day < 5:  # Weekday evenings
                            availability.append({
                                'day_of_week': day,
                                'start_time': '17:00',
                                'end_time': '21:00',
                                'preferred': day == 2  # Prefer Wednesday
                            })
                        else:  # Weekends
                            availability.append({
                                'day_of_week': day,
                                'start_time': '08:00',
                                'end_time': '18:00',
                                'preferred': True
                            })
                else:  # Available weekends only
                    for day in [5, 6]:  # Saturday and Sunday
                        availability.append({
                            'day_of_week': day,
                            'start_time': '10:00',
                            'end_time': '16:00',
                            'preferred': True
                        })
                
                role_manager.add_volunteer_availability(str(volunteer_id), availability)
                print(f"  ✅ Added availability for volunteer {volunteer_id}")
        
        # Test 3: Generate shift assignments
        print("\n🔧 Test 3: Generating shift assignments...")
        
        assignments = role_manager.generate_shift_assignments(weeks_ahead=2)
        
        total_assignments = sum(len(shift_assigns) for shift_assigns in assignments.values())
        print(f"  ✅ Generated {total_assignments} total assignments")
        
        for shift_id, shift_assignments in assignments.items():
            shift = role_manager.recurring_shifts.get(shift_id)
            if shift:
                print(f"    📋 {shift.name}: {len(shift_assignments)} assignments")
                for assignment in shift_assignments[:3]:  # Show first 3
                    print(f"      - Volunteer {assignment.volunteer_id} on {assignment.assignment_date} (confidence: {assignment.confidence_score:.2f})")
        
        # Test 4: Check for conflicts
        print("\n🔧 Test 4: Analyzing conflicts...")
        
        total_conflicts = sum(len(conflicts) for conflicts in role_manager.conflicts.values())
        print(f"  ⚠️  Found {total_conflicts} conflicts")
        
        if total_conflicts > 0:
            for conflict_key, conflicts in role_manager.conflicts.items():
                if conflicts:
                    print(f"    🚨 Conflicts for {conflict_key}:")
                    for conflict in conflicts[:2]:  # Show first 2
                        print(f"      - {conflict.type.value}: {conflict.description}")
                        print(f"        Suggestions: {conflict.resolution_suggestions[0] if conflict.resolution_suggestions else 'None'}")
        
        # Test 5: Get assignment summary
        print("\n🔧 Test 5: Assignment summary...")
        
        summary = role_manager.get_assignment_summary(weeks_ahead=2)
        
        print(f"  📊 Total shifts: {summary['total_shifts']}")
        print(f"  📊 Total assignments: {summary['total_assignments']}")
        print(f"  📊 Expected assignments: {summary['expected_assignments']}")
        print(f"  📊 Fill rate: {summary['fill_rate']:.1%}")
        print(f"  📊 Total conflicts: {summary['total_conflicts']}")
        
        # Test 6: Export data structure
        print("\n🔧 Test 6: Exporting assignment data...")
        
        export_data = role_manager.export_assignments_to_dict()
        
        print(f"  📤 Exported {len(export_data['shifts'])} shifts")
        print(f"  📤 Exported {len(export_data['assignments'])} assignments")
        print(f"  📤 Exported {len(export_data['conflicts'])} conflict groups")
        
        # Save export data to file for inspection
        with open('test_assignments_export.json', 'w') as f:
            # Convert date objects to strings for JSON serialization
            json_data = json.dumps(export_data, indent=2, default=str)
            f.write(json_data)
        print("  ✅ Saved export data to test_assignments_export.json")
        
        print("\n🎉 All tests completed successfully!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_mock_volunteer_data():
    """Create mock volunteer data for testing"""
    import pandas as pd
    
    # Mock volunteers data
    volunteers_data = []
    for i in range(20):
        volunteers_data.append({
            'contact_id': 1000 + i,
            'first_name': f'Volunteer{i}',
            'last_name': 'Test',
            'total_hours': 20 + (i * 5),
            'volunteer_sessions': 5 + (i % 10),
            'unique_projects': 2 + (i % 5),
            'project_categories': 'Youth Development, Fitness & Wellness' if i % 2 == 0 else 'Special Events',
            'member_branch': ['Blue Ash', 'M.E. Lyons', 'Campbell County'][i % 3],
            'volunteer_type': ['Regular', 'Committed', 'Explorer'][i % 3]
        })
    
    volunteers_df = pd.DataFrame(volunteers_data)
    
    # Mock projects data
    projects_data = []
    for i in range(10):
        projects_data.append({
            'project_id': 2000 + i,
            'project_name': f'Test Project {i}',
            'branch': ['Blue Ash', 'M.E. Lyons', 'Campbell County'][i % 3],
            'category': ['Youth Development', 'Fitness & Wellness', 'Special Events'][i % 3],
            'unique_volunteers': 5 + (i * 2)
        })
    
    projects_df = pd.DataFrame(projects_data)
    
    # Mock interactions data
    interactions_data = []
    for i in range(100):
        volunteer_id = 1000 + (i % 20)
        project_id = 2000 + (i % 10)
        interactions_data.append({
            'contact_id': volunteer_id,
            'project_id': project_id,
            'hours': 2 + (i % 5),
            'date': datetime.now() - timedelta(days=i * 7)
        })
    
    interactions_df = pd.DataFrame(interactions_data)
    
    return {
        'volunteers': volunteers_df,
        'projects': projects_df,
        'interactions': interactions_df,
        'insights': {
            'total_volunteers': 20,
            'total_projects': 10
        }
    }

if __name__ == "__main__":
    print("🚀 Starting Recurring Role Matching Tests...")
    
    # Run the async test
    success = asyncio.run(test_recurring_role_system())
    
    if success:
        print("✅ All tests passed!")
        exit(0)
    else:
        print("❌ Tests failed!")
        exit(1)