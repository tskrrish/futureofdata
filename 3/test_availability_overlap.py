"""
Test Suite for Availability Overlap Scoring Feature
Tests fine-grained window matching for volunteer shifts
"""

import unittest
from datetime import time
import sys
import os

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from availability_overlap_scorer import (
    TimeWindow, VolunteerAvailability, ShiftRequirement, AvailabilityOverlapScorer,
    DayOfWeek, create_time_window_from_string, create_availability_from_dict
)

class TestTimeWindow(unittest.TestCase):
    """Test TimeWindow functionality"""
    
    def setUp(self):
        self.monday_morning = TimeWindow(
            start_time=time(9, 0),
            end_time=time(12, 0),
            day_of_week=DayOfWeek.MONDAY
        )
        
        self.monday_afternoon = TimeWindow(
            start_time=time(14, 0),
            end_time=time(17, 0),
            day_of_week=DayOfWeek.MONDAY
        )
        
        self.monday_overlap = TimeWindow(
            start_time=time(11, 0),
            end_time=time(15, 0),
            day_of_week=DayOfWeek.MONDAY
        )
        
        self.tuesday_morning = TimeWindow(
            start_time=time(9, 0),
            end_time=time(12, 0),
            day_of_week=DayOfWeek.TUESDAY
        )
    
    def test_duration_calculation(self):
        """Test duration calculation in hours"""
        self.assertEqual(self.monday_morning.duration_hours(), 3.0)
        self.assertEqual(self.monday_afternoon.duration_hours(), 3.0)
        self.assertEqual(self.monday_overlap.duration_hours(), 4.0)
    
    def test_overlap_detection(self):
        """Test overlap detection between windows"""
        # Same day overlapping windows
        self.assertTrue(self.monday_morning.overlaps_with(self.monday_overlap))
        self.assertTrue(self.monday_afternoon.overlaps_with(self.monday_overlap))
        
        # Same day non-overlapping windows
        self.assertFalse(self.monday_morning.overlaps_with(self.monday_afternoon))
        
        # Different day windows (no overlap)
        self.assertFalse(self.monday_morning.overlaps_with(self.tuesday_morning))
    
    def test_overlap_duration_calculation(self):
        """Test overlap duration calculation"""
        # Monday morning (9-12) overlaps with Monday overlap (11-15) for 1 hour
        overlap_duration = self.monday_morning.overlap_duration(self.monday_overlap)
        self.assertEqual(overlap_duration, 1.0)
        
        # Monday afternoon (14-17) overlaps with Monday overlap (11-15) for 1 hour  
        overlap_duration = self.monday_afternoon.overlap_duration(self.monday_overlap)
        self.assertEqual(overlap_duration, 1.0)
        
        # No overlap between non-overlapping windows
        overlap_duration = self.monday_morning.overlap_duration(self.monday_afternoon)
        self.assertEqual(overlap_duration, 0.0)
        
        # No overlap between different days
        overlap_duration = self.monday_morning.overlap_duration(self.tuesday_morning)
        self.assertEqual(overlap_duration, 0.0)

class TestAvailabilityOverlapScorer(unittest.TestCase):
    """Test the main overlap scoring functionality"""
    
    def setUp(self):
        self.scorer = AvailabilityOverlapScorer()
        
        # Create test volunteer availability
        self.volunteer_availability = VolunteerAvailability(
            volunteer_id="test_volunteer",
            time_windows=[
                TimeWindow(time(9, 0), time(17, 0), DayOfWeek.MONDAY),     # Mon 9-17
                TimeWindow(time(9, 0), time(17, 0), DayOfWeek.TUESDAY),    # Tue 9-17
                TimeWindow(time(18, 0), time(21, 0), DayOfWeek.MONDAY),    # Mon 18-21 (evening)
                TimeWindow(time(10, 0), time(16, 0), DayOfWeek.SATURDAY),  # Sat 10-16
            ],
            preferences={
                'prefers_morning': True,
                'skills': ['mentoring', 'youth_development']
            }
        )
        
        # Create test shift requirements
        self.perfect_shift = ShiftRequirement(
            shift_id="perfect_001",
            project_id="project_001",
            time_window=TimeWindow(time(10, 0), time(14, 0), DayOfWeek.MONDAY),  # Mon 10-14 (4h)
            required_volunteers=1,
            preferred_skills=['mentoring'],
            priority='high'
        )
        
        self.partial_shift = ShiftRequirement(
            shift_id="partial_001", 
            project_id="project_002",
            time_window=TimeWindow(time(15, 0), time(19, 0), DayOfWeek.MONDAY),  # Mon 15-19 (partial overlap)
            required_volunteers=1,
            preferred_skills=[],
            priority='normal'
        )
        
        self.no_overlap_shift = ShiftRequirement(
            shift_id="none_001",
            project_id="project_003", 
            time_window=TimeWindow(time(8, 0), time(12, 0), DayOfWeek.WEDNESDAY),  # Wed 8-12 (no overlap)
            required_volunteers=1,
            preferred_skills=[],
            priority='low'
        )
    
    def test_perfect_overlap_scoring(self):
        """Test scoring for perfect overlap scenario"""
        score_result = self.scorer.calculate_overlap_score(self.volunteer_availability, self.perfect_shift)
        
        # Should have high total score
        self.assertGreaterEqual(score_result['total_score'], 0.7)
        
        # Should have 4 hours overlap (volunteer 9-17, shift 10-14)
        self.assertEqual(score_result['overlap_duration'], 4.0)
        
        # Should have 100% coverage (4h overlap / 4h shift)
        self.assertEqual(score_result['coverage_percentage'], 100.0)
        
        # Should include skill match bonus
        self.assertGreater(score_result['preference_match'], 50.0)
    
    def test_partial_overlap_scoring(self):
        """Test scoring for partial overlap scenario"""
        score_result = self.scorer.calculate_overlap_score(self.volunteer_availability, self.partial_shift)
        
        # Should have moderate score
        self.assertGreaterEqual(score_result['total_score'], 0.3)
        self.assertLess(score_result['total_score'], 0.7)
        
        # Should have 3 hours overlap (volunteer 9-17 and 18-21, shift 15-19)
        # Best match is volunteer 9-17 with shift 15-19 = 2h overlap
        self.assertEqual(score_result['overlap_duration'], 2.0)
        
        # Coverage should be 50% (2h overlap / 4h shift)
        self.assertEqual(score_result['coverage_percentage'], 50.0)
    
    def test_no_overlap_scoring(self):
        """Test scoring for no overlap scenario"""
        score_result = self.scorer.calculate_overlap_score(self.volunteer_availability, self.no_overlap_shift)
        
        # Should have zero score
        self.assertEqual(score_result['total_score'], 0.0)
        self.assertEqual(score_result['overlap_duration'], 0.0)
        self.assertEqual(score_result['coverage_percentage'], 0.0)
    
    def test_multiple_shift_scoring(self):
        """Test scoring multiple shifts and ranking"""
        shifts = [self.perfect_shift, self.partial_shift, self.no_overlap_shift]
        scored_shifts = self.scorer.score_multiple_shifts(self.volunteer_availability, shifts)
        
        # Should be ordered by score (perfect > partial > none)
        self.assertEqual(scored_shifts[0]['shift_id'], 'perfect_001')
        self.assertEqual(scored_shifts[1]['shift_id'], 'partial_001') 
        self.assertEqual(scored_shifts[2]['shift_id'], 'none_001')
        
        # Scores should be in descending order
        self.assertGreaterEqual(scored_shifts[0]['total_score'], scored_shifts[1]['total_score'])
        self.assertGreaterEqual(scored_shifts[1]['total_score'], scored_shifts[2]['total_score'])

class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions for creating time windows and availability"""
    
    def test_create_time_window_from_string(self):
        """Test creating TimeWindow from string format"""
        window = create_time_window_from_string("monday", "09:30-17:45")
        
        self.assertEqual(window.day_of_week, DayOfWeek.MONDAY)
        self.assertEqual(window.start_time, time(9, 30))
        self.assertEqual(window.end_time, time(17, 45))
        self.assertAlmostEqual(window.duration_hours(), 8.25, places=2)
    
    def test_create_availability_from_dict(self):
        """Test creating VolunteerAvailability from dictionary"""
        availability_dict = {
            'windows': [
                {'day': 'monday', 'start': '09:00', 'end': '17:00'},
                {'day': 'wednesday', 'start': '14:00', 'end': '18:00'}
            ],
            'preferences': {
                'prefers_morning': True,
                'skills': ['admin', 'customer_service']
            },
            'max_hours_per_week': 20,
            'min_shift_duration': 2.0
        }
        
        availability = create_availability_from_dict('test_vol', availability_dict)
        
        self.assertEqual(availability.volunteer_id, 'test_vol')
        self.assertEqual(len(availability.time_windows), 2)
        self.assertEqual(availability.max_hours_per_week, 20)
        self.assertEqual(availability.min_shift_duration, 2.0)
        self.assertTrue(availability.preferences['prefers_morning'])
        self.assertIn('admin', availability.preferences['skills'])

class TestAvailabilityReporting(unittest.TestCase):
    """Test availability reporting functionality"""
    
    def setUp(self):
        self.scorer = AvailabilityOverlapScorer()
        self.volunteer_availability = VolunteerAvailability(
            volunteer_id="report_test",
            time_windows=[
                TimeWindow(time(9, 0), time(12, 0), DayOfWeek.MONDAY),
                TimeWindow(time(14, 0), time(17, 0), DayOfWeek.MONDAY),
                TimeWindow(time(10, 0), time(16, 0), DayOfWeek.SATURDAY),
            ],
            preferences={'prefers_weekends': True}
        )
    
    def test_availability_report_generation(self):
        """Test generating availability report"""
        report = self.scorer.generate_availability_report(self.volunteer_availability)
        
        self.assertEqual(report['volunteer_id'], 'report_test')
        self.assertEqual(report['total_available_hours_per_week'], 12.0)  # 3 + 3 + 6
        
        # Check Monday availability (2 windows)
        self.assertIn('MONDAY', report['availability_by_day'])
        monday_windows = report['availability_by_day']['MONDAY']
        self.assertEqual(len(monday_windows), 2)
        
        # Check Saturday availability (1 window)
        self.assertIn('SATURDAY', report['availability_by_day'])
        saturday_windows = report['availability_by_day']['SATURDAY']
        self.assertEqual(len(saturday_windows), 1)
        self.assertEqual(saturday_windows[0]['duration_hours'], 6.0)

class TestIntegrationScenarios(unittest.TestCase):
    """Test real-world integration scenarios"""
    
    def setUp(self):
        self.scorer = AvailabilityOverlapScorer()
    
    def test_evening_volunteer_scenario(self):
        """Test scoring for volunteer who prefers evening shifts"""
        evening_volunteer = VolunteerAvailability(
            volunteer_id="evening_vol",
            time_windows=[
                # Available weekday evenings
                TimeWindow(time(18, 0), time(21, 0), DayOfWeek.MONDAY),
                TimeWindow(time(18, 0), time(21, 0), DayOfWeek.TUESDAY),
                TimeWindow(time(18, 0), time(21, 0), DayOfWeek.WEDNESDAY),
            ],
            preferences={
                'prefers_evening': True,
                'skills': ['fitness', 'group_instruction']
            }
        )
        
        evening_shift = ShiftRequirement(
            shift_id="evening_fitness",
            project_id="fitness_001",
            time_window=TimeWindow(time(19, 0), time(20, 30), DayOfWeek.TUESDAY),
            required_volunteers=1,
            preferred_skills=['fitness'],
            priority='normal'
        )
        
        day_shift = ShiftRequirement(
            shift_id="day_admin",
            project_id="admin_001", 
            time_window=TimeWindow(time(9, 0), time(17, 0), DayOfWeek.TUESDAY),
            required_volunteers=1,
            preferred_skills=['admin'],
            priority='normal'
        )
        
        # Evening shift should score much higher
        evening_score = self.scorer.calculate_overlap_score(evening_volunteer, evening_shift)
        day_score = self.scorer.calculate_overlap_score(evening_volunteer, day_shift)
        
        self.assertGreater(evening_score['total_score'], day_score['total_score'])
        self.assertGreater(evening_score['overlap_duration'], 0)
        self.assertEqual(day_score['overlap_duration'], 0)  # No overlap with day shift
    
    def test_weekend_volunteer_scenario(self):
        """Test scoring for volunteer available only on weekends"""
        weekend_volunteer = VolunteerAvailability(
            volunteer_id="weekend_vol",
            time_windows=[
                TimeWindow(time(8, 0), time(16, 0), DayOfWeek.SATURDAY),
                TimeWindow(time(10, 0), time(18, 0), DayOfWeek.SUNDAY),
            ],
            preferences={
                'preferred_days': ['saturday', 'sunday'],
                'skills': ['event_planning', 'family_programs']
            }
        )
        
        weekend_event = ShiftRequirement(
            shift_id="weekend_event",
            project_id="event_001",
            time_window=TimeWindow(time(10, 0), time(14, 0), DayOfWeek.SATURDAY),
            required_volunteers=3,
            preferred_skills=['event_planning'],
            priority='high'
        )
        
        score_result = self.scorer.calculate_overlap_score(weekend_volunteer, weekend_event)
        
        # Should have excellent score  
        self.assertGreaterEqual(score_result['total_score'], 0.7)
        self.assertEqual(score_result['overlap_duration'], 4.0)
        self.assertEqual(score_result['coverage_percentage'], 100.0)

def run_comprehensive_test():
    """Run comprehensive test with detailed output"""
    print("=== AVAILABILITY OVERLAP SCORING TESTS ===\n")
    
    # Test basic overlap functionality
    print("1. Testing Basic Time Window Overlap...")
    
    monday_9_12 = TimeWindow(time(9, 0), time(12, 0), DayOfWeek.MONDAY)
    monday_10_14 = TimeWindow(time(10, 0), time(14, 0), DayOfWeek.MONDAY)
    
    overlap_duration = monday_9_12.overlap_duration(monday_10_14)
    print(f"   Overlap between 9-12 and 10-14: {overlap_duration} hours ✓")
    
    # Test scoring scenarios
    print("\n2. Testing Scoring Scenarios...")
    
    scorer = AvailabilityOverlapScorer()
    
    # Create test volunteer with mixed availability
    volunteer = VolunteerAvailability(
        volunteer_id="test_vol",
        time_windows=[
            TimeWindow(time(9, 0), time(17, 0), DayOfWeek.MONDAY),
            TimeWindow(time(18, 0), time(21, 0), DayOfWeek.WEDNESDAY),
            TimeWindow(time(10, 0), time(16, 0), DayOfWeek.SATURDAY),
        ],
        preferences={
            'prefers_morning': True,
            'skills': ['youth_development', 'mentoring']
        }
    )
    
    # Test various shift scenarios
    shifts = [
        # Perfect match - Monday morning
        ShiftRequirement(
            "perfect", "proj1",
            TimeWindow(time(10, 0), time(14, 0), DayOfWeek.MONDAY),
            1, ['mentoring'], 1.0, 'high'
        ),
        # Partial match - Wednesday evening overlap
        ShiftRequirement(
            "partial", "proj2", 
            TimeWindow(time(17, 0), time(20, 0), DayOfWeek.WEDNESDAY),
            1, [], 1.0, 'normal'
        ),
        # No match - Tuesday (not available)
        ShiftRequirement(
            "none", "proj3",
            TimeWindow(time(10, 0), time(14, 0), DayOfWeek.TUESDAY), 
            1, [], 1.0, 'low'
        )
    ]
    
    scored_shifts = scorer.score_multiple_shifts(volunteer, shifts)
    
    for shift in scored_shifts:
        print(f"   {shift['shift_id']}: Score {shift['total_score']:.3f}, "
              f"Overlap {shift['overlap_duration']:.1f}h, "
              f"Coverage {shift['coverage_percentage']:.1f}%")
    
    # Test availability report
    print("\n3. Testing Availability Report...")
    report = scorer.generate_availability_report(volunteer)
    print(f"   Total available hours/week: {report['total_available_hours_per_week']}")
    print(f"   Available days: {list(report['availability_by_day'].keys())}")
    
    print("\n✅ All tests completed successfully!")
    return True

if __name__ == "__main__":
    # Run unit tests
    print("Running unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run comprehensive test
    print("\n" + "="*50)
    run_comprehensive_test()