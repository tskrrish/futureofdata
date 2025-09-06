"""
Availability Overlap Scoring Feature Demonstration
Shows comprehensive fine-grained window matching for volunteer shifts
"""

from datetime import time
from availability_overlap_scorer import (
    AvailabilityOverlapScorer, VolunteerAvailability, ShiftRequirement,
    TimeWindow, DayOfWeek, create_time_window_from_string, create_availability_from_dict
)

def demo_basic_overlap_scoring():
    """Demonstrate basic availability overlap scoring"""
    print("🎯 DEMO: Basic Availability Overlap Scoring")
    print("="*60)
    
    scorer = AvailabilityOverlapScorer()
    
    # Create a volunteer with mixed availability
    volunteer = VolunteerAvailability(
        volunteer_id="sarah_martinez",
        time_windows=[
            TimeWindow(time(9, 0), time(17, 0), DayOfWeek.MONDAY),     # Full weekday
            TimeWindow(time(9, 0), time(17, 0), DayOfWeek.WEDNESDAY),  # Full weekday  
            TimeWindow(time(18, 0), time(21, 0), DayOfWeek.TUESDAY),   # Evening only
            TimeWindow(time(10, 0), time(16, 0), DayOfWeek.SATURDAY),  # Weekend
        ],
        preferences={
            'prefers_morning': True,
            'prefers_weekends': False,
            'skills': ['youth_development', 'mentoring', 'tutoring']
        },
        max_hours_per_week=20,
        min_shift_duration=2.0,
        max_shift_duration=8.0
    )
    
    # Create various test shifts
    shifts = [
        ShiftRequirement(
            shift_id="youth_tutoring_mon",
            project_id="education_001",
            time_window=TimeWindow(time(14, 0), time(17, 0), DayOfWeek.MONDAY),
            required_volunteers=2,
            preferred_skills=['tutoring', 'youth_development'],
            minimum_duration_overlap=2.0,
            priority='high'
        ),
        ShiftRequirement(
            shift_id="evening_mentoring_tue",
            project_id="mentoring_001", 
            time_window=TimeWindow(time(19, 0), time(21, 0), DayOfWeek.TUESDAY),
            required_volunteers=1,
            preferred_skills=['mentoring'],
            minimum_duration_overlap=1.5,
            priority='normal'
        ),
        ShiftRequirement(
            shift_id="weekend_event_sat",
            project_id="events_001",
            time_window=TimeWindow(time(12, 0), time(18, 0), DayOfWeek.SATURDAY),
            required_volunteers=3,
            preferred_skills=['event_planning'],
            minimum_duration_overlap=3.0,
            priority='normal'
        ),
        ShiftRequirement(
            shift_id="early_morning_fri",
            project_id="fitness_001",
            time_window=TimeWindow(time(6, 0), time(9, 0), DayOfWeek.FRIDAY),
            required_volunteers=1,
            preferred_skills=['fitness'],
            minimum_duration_overlap=2.0,
            priority='low'
        )
    ]
    
    # Score all shifts
    scored_shifts = scorer.score_multiple_shifts(volunteer, shifts)
    
    print(f"Volunteer: {volunteer.volunteer_id}")
    print(f"Available Hours/Week: {volunteer.get_total_available_hours()}")
    print(f"Preferences: {volunteer.preferences}")
    print()
    
    print("SHIFT SCORING RESULTS:")
    print("-" * 40)
    
    for i, shift in enumerate(scored_shifts, 1):
        print(f"{i}. {shift['shift_id'].replace('_', ' ').title()}")
        print(f"   📊 Total Score: {shift['total_score']:.3f}")
        print(f"   ⏱️  Overlap Duration: {shift['overlap_duration']} hours")
        print(f"   📈 Coverage: {shift['coverage_percentage']}%")
        print(f"   💡 Recommendation: {shift['recommendation']}")
        print(f"   🎯 Priority: {shifts[scored_shifts.index(shift)].priority}")
        print()
    
    return scored_shifts

def demo_availability_report():
    """Demonstrate comprehensive availability reporting"""
    print("\n📋 DEMO: Comprehensive Availability Report")
    print("="*60)
    
    scorer = AvailabilityOverlapScorer()
    
    # Create volunteer with complex schedule
    volunteer = VolunteerAvailability(
        volunteer_id="alex_johnson",
        time_windows=[
            # Weekday mornings
            TimeWindow(time(7, 0), time(11, 0), DayOfWeek.MONDAY),
            TimeWindow(time(7, 0), time(11, 0), DayOfWeek.WEDNESDAY),
            TimeWindow(time(7, 0), time(11, 0), DayOfWeek.FRIDAY),
            
            # Tuesday and Thursday evenings
            TimeWindow(time(17, 30), time(20, 0), DayOfWeek.TUESDAY),
            TimeWindow(time(17, 30), time(20, 0), DayOfWeek.THURSDAY),
            
            # Weekend flexibility
            TimeWindow(time(9, 0), time(17, 0), DayOfWeek.SATURDAY),
            TimeWindow(time(13, 0), time(18, 0), DayOfWeek.SUNDAY),
        ],
        preferences={
            'prefers_morning': True,
            'prefers_weekends': True,
            'preferred_days': ['saturday', 'sunday'],
            'skills': ['fitness', 'group_instruction', 'swimming']
        },
        max_hours_per_week=25,
        min_shift_duration=1.5,
        max_shift_duration=6.0
    )
    
    report = scorer.generate_availability_report(volunteer)
    
    print(f"AVAILABILITY REPORT FOR: {report['volunteer_id'].upper()}")
    print("-" * 50)
    print(f"📊 Total Available Hours/Week: {report['total_available_hours_per_week']}")
    print()
    
    print("📅 WEEKLY SCHEDULE:")
    days_order = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY']
    for day in days_order:
        if day in report['availability_by_day']:
            windows = report['availability_by_day'][day]
            print(f"  {day}:")
            for window in windows:
                print(f"    🕐 {window['start_time']} - {window['end_time']} ({window['duration_hours']}h)")
        else:
            print(f"  {day}: Not available")
    
    print()
    print("⚙️  CONSTRAINTS:")
    for key, value in report['constraints'].items():
        if value is not None:
            print(f"  • {key.replace('_', ' ').title()}: {value}")
    
    print()
    print("💭 PREFERENCES:")
    for key, value in report['preferences'].items():
        print(f"  • {key.replace('_', ' ').title()}: {value}")
    
    return report

def demo_real_world_scenarios():
    """Demonstrate real-world volunteer matching scenarios"""
    print("\n🌍 DEMO: Real-World Matching Scenarios")
    print("="*60)
    
    scorer = AvailabilityOverlapScorer()
    
    # Scenario 1: Working parent with limited evening availability
    print("SCENARIO 1: Working Parent (Limited Evening Availability)")
    print("-" * 55)
    
    working_parent = VolunteerAvailability(
        volunteer_id="jamie_working_parent",
        time_windows=[
            # Only Tuesday and Thursday evenings after kids' bedtime
            TimeWindow(time(19, 30), time(21, 30), DayOfWeek.TUESDAY),
            TimeWindow(time(19, 30), time(21, 30), DayOfWeek.THURSDAY),
            # Saturday mornings when partner can watch kids
            TimeWindow(time(8, 0), time(12, 0), DayOfWeek.SATURDAY),
        ],
        preferences={
            'prefers_evening': True,
            'skills': ['admin', 'data_entry', 'phone_calls'],
            'preferred_days': ['tuesday', 'thursday', 'saturday']
        },
        max_hours_per_week=8
    )
    
    parent_shifts = [
        ShiftRequirement(
            "admin_support_tue", "admin_001",
            TimeWindow(time(19, 0), time(21, 0), DayOfWeek.TUESDAY),
            1, ['admin'], 1.5, 'normal'
        ),
        ShiftRequirement(
            "data_entry_sat", "data_001",
            TimeWindow(time(9, 0), time(11, 0), DayOfWeek.SATURDAY), 
            1, ['data_entry'], 2.0, 'high'
        ),
        ShiftRequirement(
            "weekday_morning", "morning_001",
            TimeWindow(time(9, 0), time(12, 0), DayOfWeek.WEDNESDAY),
            2, [], 3.0, 'normal'
        )
    ]
    
    parent_matches = scorer.score_multiple_shifts(working_parent, parent_shifts)
    
    for match in parent_matches:
        if match['total_score'] > 0:
            print(f"✅ {match['shift_id']}: Score {match['total_score']:.3f} - {match['recommendation']}")
        else:
            print(f"❌ {match['shift_id']}: No overlap available")
    
    print()
    
    # Scenario 2: College student with class schedule
    print("SCENARIO 2: College Student (Class Schedule Constraints)")
    print("-" * 55)
    
    college_student = VolunteerAvailability(
        volunteer_id="taylor_college_student",
        time_windows=[
            # Between classes on MWF
            TimeWindow(time(11, 0), time(13, 0), DayOfWeek.MONDAY),
            TimeWindow(time(11, 0), time(13, 0), DayOfWeek.WEDNESDAY),
            TimeWindow(time(11, 0), time(13, 0), DayOfWeek.FRIDAY),
            # Free afternoons on T/Th
            TimeWindow(time(14, 0), time(18, 0), DayOfWeek.TUESDAY),
            TimeWindow(time(14, 0), time(18, 0), DayOfWeek.THURSDAY),
            # Weekend availability
            TimeWindow(time(10, 0), time(16, 0), DayOfWeek.SUNDAY),
        ],
        preferences={
            'prefers_afternoon': True,
            'skills': ['tutoring', 'youth_development', 'sports'],
            'preferred_days': ['tuesday', 'thursday', 'sunday']
        },
        max_hours_per_week=15
    )
    
    student_shifts = [
        ShiftRequirement(
            "youth_tutoring_thu", "tutoring_001",
            TimeWindow(time(15, 0), time(17, 0), DayOfWeek.THURSDAY),
            2, ['tutoring'], 2.0, 'high'
        ),
        ShiftRequirement(
            "sports_program_sun", "sports_001", 
            TimeWindow(time(13, 0), time(16, 0), DayOfWeek.SUNDAY),
            1, ['sports'], 2.5, 'normal'
        ),
        ShiftRequirement(
            "lunch_program_wed", "lunch_001",
            TimeWindow(time(11, 30), time(12, 30), DayOfWeek.WEDNESDAY),
            3, [], 1.0, 'normal'
        )
    ]
    
    student_matches = scorer.score_multiple_shifts(college_student, student_shifts)
    
    for match in student_matches:
        if match['total_score'] > 0:
            print(f"✅ {match['shift_id']}: Score {match['total_score']:.3f} - {match['recommendation']}")
        else:
            print(f"❌ {match['shift_id']}: No overlap available")
    
    print()
    
    # Scenario 3: Retiree with full flexibility
    print("SCENARIO 3: Retiree (Full Flexibility)")
    print("-" * 40)
    
    retiree = VolunteerAvailability(
        volunteer_id="pat_retiree",
        time_windows=[
            # Available most weekdays
            TimeWindow(time(8, 0), time(17, 0), DayOfWeek.MONDAY),
            TimeWindow(time(8, 0), time(17, 0), DayOfWeek.TUESDAY),
            TimeWindow(time(8, 0), time(17, 0), DayOfWeek.WEDNESDAY),
            TimeWindow(time(8, 0), time(17, 0), DayOfWeek.THURSDAY),
            # Partial Friday (doctor appointments)
            TimeWindow(time(8, 0), time(12, 0), DayOfWeek.FRIDAY),
        ],
        preferences={
            'prefers_morning': True,
            'skills': ['mentoring', 'life_skills', 'career_counseling'],
            'experience_level': 'high'
        },
        max_hours_per_week=30
    )
    
    retiree_shifts = [
        ShiftRequirement(
            "mentoring_program", "mentor_001",
            TimeWindow(time(10, 0), time(12, 0), DayOfWeek.TUESDAY),
            1, ['mentoring'], 2.0, 'high'
        ),
        ShiftRequirement(
            "career_workshop", "career_001",
            TimeWindow(time(14, 0), time(16, 0), DayOfWeek.THURSDAY),
            2, ['career_counseling'], 2.0, 'normal'  
        ),
        ShiftRequirement(
            "weekend_intensive", "intensive_001",
            TimeWindow(time(9, 0), time(17, 0), DayOfWeek.SATURDAY),
            1, [], 6.0, 'low'
        )
    ]
    
    retiree_matches = scorer.score_multiple_shifts(retiree, retiree_shifts)
    
    for match in retiree_matches:
        if match['total_score'] > 0:
            print(f"✅ {match['shift_id']}: Score {match['total_score']:.3f} - {match['recommendation']}")
        else:
            print(f"❌ {match['shift_id']}: No overlap available")

def demo_scoring_components():
    """Demonstrate detailed scoring component breakdown"""
    print("\n🔬 DEMO: Detailed Scoring Analysis")
    print("="*60)
    
    scorer = AvailabilityOverlapScorer()
    
    volunteer = VolunteerAvailability(
        volunteer_id="analysis_volunteer",
        time_windows=[
            TimeWindow(time(9, 0), time(17, 0), DayOfWeek.MONDAY),
        ],
        preferences={
            'prefers_morning': True,
            'skills': ['youth_development', 'mentoring']
        }
    )
    
    # Different overlap scenarios for analysis
    scenarios = [
        ("Perfect Match", ShiftRequirement(
            "perfect", "proj1",
            TimeWindow(time(10, 0), time(14, 0), DayOfWeek.MONDAY),
            1, ['mentoring'], 2.0, 'high'
        )),
        ("Partial Match", ShiftRequirement(
            "partial", "proj2", 
            TimeWindow(time(15, 0), time(19, 0), DayOfWeek.MONDAY),
            1, [], 2.0, 'normal'
        )),
        ("Skill Mismatch", ShiftRequirement(
            "mismatch", "proj3",
            TimeWindow(time(11, 0), time(15, 0), DayOfWeek.MONDAY),
            1, ['fitness'], 2.0, 'normal'
        )),
        ("Low Priority", ShiftRequirement(
            "low_pri", "proj4",
            TimeWindow(time(12, 0), time(16, 0), DayOfWeek.MONDAY),
            1, ['mentoring'], 2.0, 'low'
        ))
    ]
    
    print("DETAILED SCORING BREAKDOWN:")
    print("-" * 40)
    
    for scenario_name, shift in scenarios:
        score_result = scorer.calculate_overlap_score(volunteer, shift)
        breakdown = score_result['detailed_breakdown']
        
        print(f"\n{scenario_name.upper()}:")
        print(f"  Total Score: {score_result['total_score']:.3f}")
        print(f"  Components:")
        print(f"    • Overlap Duration: {breakdown['overlap_duration_score']:.3f} (weight: {breakdown['weights_used']['overlap_duration']})")
        print(f"    • Coverage %: {breakdown['coverage_percentage_score']:.3f} (weight: {breakdown['weights_used']['coverage_percentage']})")
        print(f"    • Utilization: {breakdown['volunteer_utilization_score']:.3f} (weight: {breakdown['weights_used']['volunteer_utilization']})")
        print(f"    • Preferences: {breakdown['preference_match_score']:.3f} (weight: {breakdown['weights_used']['preference_match']})")
        print(f"    • Priority: {breakdown['shift_priority_bonus']:.3f} (weight: {breakdown['weights_used']['shift_priority']})")
        print(f"  Overlap: {score_result['overlap_duration']}h ({score_result['coverage_percentage']}% coverage)")

def main():
    """Run comprehensive demonstration"""
    print("🎉 AVAILABILITY OVERLAP SCORING FEATURE DEMONSTRATION")
    print("="*80)
    print("This demo showcases the fine-grained window matching capabilities")
    print("for volunteer shift scheduling with comprehensive scoring algorithms.")
    print()
    
    # Run all demonstrations
    demo_basic_overlap_scoring()
    demo_availability_report() 
    demo_real_world_scenarios()
    demo_scoring_components()
    
    print("\n" + "="*80)
    print("🏆 DEMONSTRATION COMPLETE!")
    print("\nKey Features Demonstrated:")
    print("✅ Fine-grained time window overlap detection")
    print("✅ Multi-dimensional scoring (duration, coverage, utilization, preferences)")
    print("✅ Comprehensive availability reporting")
    print("✅ Real-world scenario handling (working parents, students, retirees)")
    print("✅ Detailed scoring component analysis")
    print("✅ Flexible preference and skill matching")
    print("✅ Priority-based shift ranking")
    print("\nThe availability overlap scoring feature is ready for production use! 🚀")

if __name__ == "__main__":
    main()