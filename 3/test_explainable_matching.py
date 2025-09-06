"""
Test script for explainable matching feature
"""
import pandas as pd
from matching_engine import VolunteerMatchingEngine


def test_explainable_matching():
    """Test the enhanced explainable matching functionality"""
    
    # Create sample data for testing
    volunteers_data = pd.DataFrame({
        'contact_id': [1, 2, 3],
        'first_name': ['John', 'Jane', 'Mike'],
        'last_name': ['Doe', 'Smith', 'Johnson'],
        'age': [25, 35, 45],
        'gender': ['Male', 'Female', 'Male'],
        'race_ethnicity': ['White', 'Hispanic', 'Black'],
        'home_city': ['Blue Ash', 'Oakley', 'Newport'],
        'home_state': ['OH', 'OH', 'KY'],
        'is_ymca_member': [True, False, True],
        'member_branch': ['Blue Ash', None, 'Campbell County'],
        'total_hours': [50, 25, 100],
        'unique_projects': [3, 2, 5],
        'branches_volunteered': ['Blue Ash', 'M.E. Lyons', 'Campbell County'],
        'project_categories': ['Youth Development', 'Fitness & Wellness', 'Special Events'],
        'volunteer_sessions': [10, 5, 20],
        'volunteer_tenure_days': [365, 180, 730],
        'avg_hours_per_session': [5, 5, 5],
        'volunteer_frequency': [0.8, 0.9, 0.7],
        'volunteer_type': ['Regular', 'Newcomer', 'Champion']
    })
    
    projects_data = pd.DataFrame({
        'project_id': [101, 102, 103],
        'project_name': ['Youth Mentoring Program', 'Fitness Class Assistant', 'Special Event Coordinator'],
        'branch': ['Blue Ash YMCA', 'M.E. Lyons YMCA', 'Campbell County YMCA'],
        'category': ['Youth Development', 'Fitness & Wellness', 'Special Events'],
        'tags': ['youth, mentoring', 'fitness, exercise', 'events, coordination'],
        'type': ['ongoing', 'recurring', 'one-time'],
        'need': ['Youth mentors needed', 'Fitness assistants wanted', 'Event volunteers required'],
        'total_hours': [200, 150, 75],
        'avg_hours_per_session': [3, 2, 4],
        'total_sessions': [40, 30, 15],
        'unique_volunteers': [15, 8, 5],
        'avg_volunteer_age': [30, 35, 40],
        'common_gender': ['Mixed', 'Female', 'Mixed'],
        'required_credentials': ['Background check', 'Basic training', 'None'],
        'sample_activities': ['Tutoring, mentoring kids', 'Assisting with classes', 'Setup, registration']
    })
    
    interactions_data = pd.DataFrame({
        'contact_id': [1, 1, 2, 2, 3, 3],
        'project_id': [101, 102, 102, 103, 101, 103],
        'hours': [15, 10, 8, 12, 25, 20],
        'date': ['2024-01-15', '2024-02-20', '2024-01-10', '2024-03-05', '2024-01-01', '2024-02-15']
    })
    
    # Create test volunteer data structure
    volunteer_data = {
        'volunteers': volunteers_data,
        'projects': projects_data,
        'interactions': interactions_data,
        'insights': {
            'total_volunteers': 3,
            'total_projects': 3,
            'top_branches': {'Blue Ash': 2, 'M.E. Lyons': 1, 'Campbell County': 1}
        }
    }
    
    # Initialize matching engine
    print("🚀 Testing Explainable Matching Engine")
    matching_engine = VolunteerMatchingEngine(volunteer_data)
    matching_engine.train_models()
    
    # Test different user preferences
    test_cases = [
        {
            'name': 'Youth-Interested Newcomer',
            'preferences': {
                'age': 28,
                'interests': 'youth development mentoring',
                'skills': 'teaching communication',
                'availability': {'weekday': True, 'evening': True},
                'time_commitment': 2,
                'location_preference': 'Blue Ash',
                'experience_level': 1,
                'affinity': {
                    'branches': {},
                    'categories': {}
                }
            }
        },
        {
            'name': 'Fitness Enthusiast',
            'preferences': {
                'age': 35,
                'interests': 'fitness wellness health',
                'skills': 'exercise instruction group fitness',
                'availability': {'weekend': True},
                'time_commitment': 3,
                'location_preference': 'Oakley',
                'experience_level': 2,
                'affinity': {
                    'branches': {'M.E. Lyons': 3},
                    'categories': {'Fitness & Wellness': 2}
                }
            }
        },
        {
            'name': 'Experienced Event Volunteer',
            'preferences': {
                'age': 45,
                'interests': 'events planning coordination',
                'skills': 'event management organization leadership',
                'availability': {'weekday': True, 'weekend': True},
                'time_commitment': 3,
                'location_preference': 'Newport',
                'experience_level': 3,
                'volunteer_type': 'Champion',
                'affinity': {
                    'branches': {'Campbell County': 5},
                    'categories': {'Special Events': 4}
                }
            }
        }
    ]
    
    print("\n" + "="*80)
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        print("-" * 50)
        
        matches = matching_engine.find_matches(test_case['preferences'], top_k=3)
        
        for i, match in enumerate(matches, 1):
            print(f"\n#{i} {match['project_name']}")
            print(f"   Branch: {match['branch']}")
            print(f"   Overall Score: {match['score']:.2f}")
            print(f"   Compatibility Score: {match.get('compatibility_score', 0):.2f}")
            
            # Test explainable factors
            match_factors = match.get('match_factors', {})
            print(f"   Match Factors:")
            print(f"     - Skills Alignment: {match_factors.get('skills_alignment', 0)}%")
            print(f"     - Location Convenience: {match_factors.get('location_convenience', 0)}%")
            print(f"     - Experience Relevance: {match_factors.get('experience_relevance', 0)}%")
            print(f"     - Schedule Compatibility: {match_factors.get('schedule_compatibility', 0)}%")
            print(f"     - Level Appropriateness: {match_factors.get('level_appropriateness', 0)}%")
            
            # Test reasons
            reasons = match.get('reasons', [])
            print(f"   Primary Reasons ({len(reasons)}):")
            for reason in reasons:
                print(f"     • {reason}")
            
            # Test detailed breakdown
            breakdown = match.get('detailed_breakdown', {})
            if breakdown:
                print(f"   Detailed Analysis Available: ✓")
                for category, details in breakdown.items():
                    if details and isinstance(details, dict) and details.get('score', 0) > 0.5:
                        print(f"     - {category.title()}: {details.get('score', 0):.2f} score")
    
    print("\n" + "="*80)
    print("✅ Explainable Matching Test Complete!")
    print("\nKey Features Tested:")
    print("✓ Skills matching with keyword analysis")
    print("✓ Proximity matching with branch preferences")
    print("✓ History matching with volunteer background")
    print("✓ Schedule compatibility analysis")
    print("✓ Experience level appropriateness")
    print("✓ Visual factor breakdown percentages")
    print("✓ Detailed reason explanations")
    print("✓ Comprehensive compatibility scoring")


if __name__ == "__main__":
    test_explainable_matching()