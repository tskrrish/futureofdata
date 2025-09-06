"""
Simple Integration Test for Availability Overlap Feature
Tests the integration without requiring external data files
"""

import sys
import os
from datetime import time

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from availability_overlap_scorer import (
        TimeWindow, VolunteerAvailability, ShiftRequirement, 
        AvailabilityOverlapScorer, DayOfWeek
    )
    print("✅ Successfully imported availability overlap scorer")
except ImportError as e:
    print(f"❌ Failed to import availability overlap scorer: {e}")
    sys.exit(1)

def test_basic_functionality():
    """Test basic availability overlap scoring functionality"""
    print("\n=== TESTING BASIC FUNCTIONALITY ===")
    
    scorer = AvailabilityOverlapScorer()
    
    # Create a volunteer with weekday availability
    volunteer = VolunteerAvailability(
        volunteer_id="test_volunteer_001",
        time_windows=[
            TimeWindow(time(9, 0), time(17, 0), DayOfWeek.MONDAY),    # Mon 9-17
            TimeWindow(time(9, 0), time(17, 0), DayOfWeek.TUESDAY),   # Tue 9-17  
            TimeWindow(time(18, 0), time(21, 0), DayOfWeek.WEDNESDAY), # Wed 18-21
        ],
        preferences={
            'prefers_morning': True,
            'skills': ['youth_development', 'mentoring']
        }
    )
    
    # Create test shifts
    shifts = [
        ShiftRequirement(
            shift_id="morning_shift",
            project_id="youth_program",
            time_window=TimeWindow(time(10, 0), time(14, 0), DayOfWeek.MONDAY),  # Mon 10-14
            required_volunteers=1,
            preferred_skills=['mentoring'],
            priority='high'
        ),
        ShiftRequirement(
            shift_id="evening_shift", 
            project_id="evening_program",
            time_window=TimeWindow(time(19, 0), time(21, 0), DayOfWeek.WEDNESDAY),  # Wed 19-21
            required_volunteers=1,
            preferred_skills=['youth_development'],
            priority='normal'
        ),
        ShiftRequirement(
            shift_id="weekend_shift",
            project_id="weekend_program", 
            time_window=TimeWindow(time(10, 0), time(14, 0), DayOfWeek.SATURDAY),  # Sat 10-14
            required_volunteers=2,
            preferred_skills=[],
            priority='low'
        )
    ]
    
    # Score the shifts
    scored_shifts = scorer.score_multiple_shifts(volunteer, shifts)
    
    print("Shift Scoring Results:")
    for i, shift in enumerate(scored_shifts, 1):
        print(f"{i}. {shift['shift_id']}:")
        print(f"   Total Score: {shift['total_score']:.3f}")
        print(f"   Overlap Duration: {shift['overlap_duration']} hours")
        print(f"   Coverage: {shift['coverage_percentage']}%")
        print(f"   Recommendation: {shift['recommendation']}")
        print()
    
    # Verify expected results
    assert scored_shifts[0]['shift_id'] == 'morning_shift', "Morning shift should rank highest"
    assert scored_shifts[0]['overlap_duration'] == 4.0, "Morning shift should have 4h overlap"
    assert scored_shifts[0]['coverage_percentage'] == 100.0, "Morning shift should have 100% coverage"
    
    # Evening shift should have some overlap
    evening_result = next((s for s in scored_shifts if s['shift_id'] == 'evening_shift'), None)
    assert evening_result is not None, "Evening shift should be scored"
    assert evening_result['overlap_duration'] == 2.0, "Evening shift should have 2h overlap"
    
    # Weekend shift should have no overlap
    weekend_result = next((s for s in scored_shifts if s['shift_id'] == 'weekend_shift'), None)
    assert weekend_result is not None, "Weekend shift should be scored"
    assert weekend_result['overlap_duration'] == 0.0, "Weekend shift should have no overlap"
    
    print("✅ Basic functionality test passed!")

def test_availability_report():
    """Test availability report generation"""
    print("\n=== TESTING AVAILABILITY REPORT ===")
    
    scorer = AvailabilityOverlapScorer()
    
    volunteer = VolunteerAvailability(
        volunteer_id="report_test_volunteer",
        time_windows=[
            TimeWindow(time(9, 0), time(12, 0), DayOfWeek.MONDAY),     # Mon 9-12 (3h)
            TimeWindow(time(14, 0), time(18, 0), DayOfWeek.MONDAY),    # Mon 14-18 (4h)
            TimeWindow(time(10, 0), time(16, 0), DayOfWeek.SATURDAY),  # Sat 10-16 (6h)
        ],
        preferences={'prefers_flexible': True},
        max_hours_per_week=20,
        min_shift_duration=2.0
    )
    
    report = scorer.generate_availability_report(volunteer)
    
    print("Availability Report:")
    print(f"Volunteer ID: {report['volunteer_id']}")
    print(f"Total Available Hours/Week: {report['total_available_hours_per_week']}")
    print("Availability by Day:")
    for day, windows in report['availability_by_day'].items():
        print(f"  {day}:")
        for window in windows:
            print(f"    {window['start_time']} - {window['end_time']} ({window['duration_hours']}h)")
    
    print(f"Constraints: {report['constraints']}")
    print(f"Preferences: {report['preferences']}")
    
    # Verify report data
    assert report['volunteer_id'] == 'report_test_volunteer', "Volunteer ID should match"
    assert report['total_available_hours_per_week'] == 13.0, "Total hours should be 3+4+6=13"
    assert 'MONDAY' in report['availability_by_day'], "Should have Monday availability"
    assert 'SATURDAY' in report['availability_by_day'], "Should have Saturday availability"
    assert len(report['availability_by_day']['MONDAY']) == 2, "Should have 2 Monday windows"
    assert report['constraints']['max_hours_per_week'] == 20, "Max hours constraint should match"
    
    print("✅ Availability report test passed!")

def test_utility_functions():
    """Test utility functions for creating objects from common formats"""
    print("\n=== TESTING UTILITY FUNCTIONS ===")
    
    from availability_overlap_scorer import create_time_window_from_string, create_availability_from_dict
    
    # Test time window creation
    window = create_time_window_from_string("tuesday", "14:30-18:45")
    assert window.day_of_week == DayOfWeek.TUESDAY, "Should be Tuesday"
    assert window.start_time == time(14, 30), "Start time should match"
    assert window.end_time == time(18, 45), "End time should match"
    assert abs(window.duration_hours() - 4.25) < 0.01, "Duration should be 4.25 hours"
    
    # Test availability creation from dict
    availability_dict = {
        'windows': [
            {'day': 'monday', 'start': '09:00', 'end': '17:00'},
            {'day': 'friday', 'start': '13:00', 'end': '17:00'}
        ],
        'preferences': {
            'prefers_morning': False,
            'skills': ['admin', 'data_entry']
        },
        'max_hours_per_week': 15
    }
    
    availability = create_availability_from_dict('util_test_vol', availability_dict)
    assert availability.volunteer_id == 'util_test_vol', "Volunteer ID should match"
    assert len(availability.time_windows) == 2, "Should have 2 time windows"
    assert availability.max_hours_per_week == 15, "Max hours should match"
    assert 'admin' in availability.preferences['skills'], "Should have admin skill"
    
    print("✅ Utility functions test passed!")

def test_edge_cases():
    """Test edge cases and boundary conditions"""
    print("\n=== TESTING EDGE CASES ===")
    
    scorer = AvailabilityOverlapScorer()
    
    # Test overnight shift
    overnight_volunteer = VolunteerAvailability(
        volunteer_id="overnight_vol",
        time_windows=[
            TimeWindow(time(22, 0), time(6, 0), DayOfWeek.FRIDAY),  # Fri 22:00 - Sat 06:00
        ],
        preferences={}
    )
    
    overnight_shift = ShiftRequirement(
        shift_id="overnight_security",
        project_id="security",
        time_window=TimeWindow(time(23, 0), time(5, 0), DayOfWeek.FRIDAY),  # Fri 23:00 - Sat 05:00
        required_volunteers=1,
        preferred_skills=[],
        priority='normal'
    )
    
    score_result = scorer.calculate_overlap_score(overnight_volunteer, overnight_shift)
    print(f"Overnight shift overlap: {score_result['overlap_duration']} hours")
    print(f"Overnight shift score: {score_result['total_score']:.3f}")
    
    # Should have significant overlap
    assert score_result['overlap_duration'] > 0, "Should have some overnight overlap"
    
    # Test zero duration window (should not crash)
    zero_volunteer = VolunteerAvailability(
        volunteer_id="zero_vol",
        time_windows=[
            TimeWindow(time(12, 0), time(12, 0), DayOfWeek.MONDAY),  # Zero duration
        ],
        preferences={}
    )
    
    normal_shift = ShiftRequirement(
        shift_id="normal",
        project_id="normal",
        time_window=TimeWindow(time(10, 0), time(14, 0), DayOfWeek.MONDAY),
        required_volunteers=1,
        preferred_skills=[],
        priority='normal'
    )
    
    score_result = scorer.calculate_overlap_score(zero_volunteer, normal_shift)
    assert score_result['total_score'] == 0.0, "Zero duration should result in zero score"
    
    print("✅ Edge cases test passed!")

def main():
    """Run all tests"""
    print("🚀 Starting Availability Overlap Scoring Integration Tests")
    
    try:
        test_basic_functionality()
        test_availability_report()
        test_utility_functions()
        test_edge_cases()
        
        print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
        print("\n=== FEATURE SUMMARY ===")
        print("✅ Fine-grained time window matching implemented")
        print("✅ Availability overlap scoring algorithm working")
        print("✅ Multi-dimensional scoring (duration, coverage, utilization, preferences)")
        print("✅ Comprehensive availability reporting")
        print("✅ Utility functions for easy integration")
        print("✅ Edge case handling (overnight shifts, zero duration, etc.)")
        print("✅ Integration ready for volunteer matching system")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)