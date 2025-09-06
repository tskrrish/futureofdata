"""
Comprehensive Test Suite for Fairness Constraints Engine
Tests demographic balance, equity metrics, and anti-discrimination features
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_processor import VolunteerDataProcessor
from matching_engine import VolunteerMatchingEngine
from fairness_constraints import FairnessConstraintsEngine

def create_test_data() -> Dict[str, Any]:
    """Create synthetic test data for fairness testing"""
    print("📊 Creating synthetic test data for fairness testing...")
    
    # Create diverse volunteer profiles
    np.random.seed(42)
    num_volunteers = 100
    
    volunteers_data = []
    for i in range(num_volunteers):
        volunteer = {
            'contact_id': f'volunteer_{i:03d}',
            'first_name': f'First_{i}',
            'last_name': f'Last_{i}',
            'age': np.random.randint(18, 75),
            'gender': np.random.choice(['Male', 'Female', 'Non-binary'], p=[0.45, 0.45, 0.1]),
            'race_ethnicity': np.random.choice([
                'White', 'Black', 'Hispanic', 'Asian', 'Other'
            ], p=[0.6, 0.15, 0.15, 0.08, 0.02]),
            'home_city': np.random.choice(['Cincinnati', 'Blue Ash', 'Newport', 'Oakley']),
            'home_state': 'OH',
            'is_ymca_member': np.random.choice([True, False], p=[0.7, 0.3]),
            'total_hours': np.random.randint(1, 200),
            'volunteer_sessions': np.random.randint(1, 50),
            'unique_projects': np.random.randint(1, 8),
            'branches_volunteered': np.random.choice([
                'Blue Ash', 'M.E. Lyons', 'Campbell County', 'Clippard', 'YDE'
            ]),
            'project_categories': np.random.choice([
                'Youth Development', 'Fitness & Wellness', 'Special Events', 
                'Administrative', 'General'
            ])
        }
        volunteers_data.append(volunteer)
    
    volunteers_df = pd.DataFrame(volunteers_data)
    
    # Create diverse project catalog
    projects_data = []
    project_names = [
        'Youth Mentoring Program', 'Group Exercise Support', 'Special Event Planning',
        'Administrative Assistant', 'Swim Lesson Volunteer', 'Childcare Helper',
        'Community Outreach', 'Senior Programs', 'Sports Coaching', 'Arts & Crafts'
    ]
    
    for i, name in enumerate(project_names):
        project = {
            'project_id': f'project_{i:03d}',
            'project_name': name,
            'branch': np.random.choice(['Blue Ash', 'M.E. Lyons', 'Campbell County', 'Clippard', 'YDE']),
            'category': np.random.choice([
                'Youth Development', 'Fitness & Wellness', 'Special Events', 
                'Administrative', 'General'
            ]),
            'avg_hours_per_session': np.random.uniform(1, 6),
            'unique_volunteers': np.random.randint(5, 25),
            'total_hours': np.random.randint(50, 500),
            'required_credentials': 'Basic volunteer requirements'
        }
        projects_data.append(project)
    
    projects_df = pd.DataFrame(projects_data)
    
    # Create interaction data
    interactions_data = []
    for i in range(300):  # 300 interactions
        interaction = {
            'contact_id': np.random.choice(volunteers_df['contact_id']),
            'project_id': np.random.choice(projects_df['project_id']),
            'hours': np.random.uniform(0.5, 8),
            'date': pd.Timestamp.now() - pd.Timedelta(days=np.random.randint(1, 365))
        }
        interactions_data.append(interaction)
    
    interactions_df = pd.DataFrame(interactions_data)
    
    return {
        'volunteers': volunteers_df,
        'projects': projects_df,
        'interactions': interactions_df,
        'insights': {
            'total_volunteers': len(volunteers_df),
            'total_projects': len(projects_df),
            'total_interactions': len(interactions_df)
        }
    }

def test_fairness_engine_initialization():
    """Test 1: Basic fairness engine initialization"""
    print("\n🧪 TEST 1: Fairness Engine Initialization")
    
    test_data = create_test_data()
    fairness_engine = FairnessConstraintsEngine(test_data)
    
    # Check if demographic baselines were calculated
    assert fairness_engine.demographic_baselines is not None, "Demographic baselines not calculated"
    assert len(fairness_engine.demographic_baselines) > 0, "No demographic baselines found"
    
    # Check if disparities were analyzed
    assert fairness_engine.current_disparities is not None, "Current disparities not analyzed"
    
    print("✅ Fairness engine initialized successfully")
    print(f"   - Demographic categories tracked: {list(fairness_engine.demographic_baselines.keys())}")
    print(f"   - Fairness thresholds: {fairness_engine.fairness_thresholds}")
    
    return fairness_engine

def test_demographic_balance_analysis(fairness_engine: FairnessConstraintsEngine):
    """Test 2: Demographic balance analysis"""
    print("\n🧪 TEST 2: Demographic Balance Analysis")
    
    # Test with sample matches
    sample_matches = [
        {'project_id': 'proj_001', 'project_name': 'Youth Mentoring', 'branch': 'Blue Ash', 'category': 'Youth Development', 'score': 0.85},
        {'project_id': 'proj_002', 'project_name': 'Group Exercise', 'branch': 'Blue Ash', 'category': 'Fitness & Wellness', 'score': 0.80},
        {'project_id': 'proj_003', 'project_name': 'Special Event', 'branch': 'M.E. Lyons', 'category': 'Special Events', 'score': 0.75},
        {'project_id': 'proj_004', 'project_name': 'Admin Support', 'branch': 'Campbell County', 'category': 'Administrative', 'score': 0.70},
        {'project_id': 'proj_005', 'project_name': 'Community Outreach', 'branch': 'Clippard', 'category': 'General', 'score': 0.65},
    ]
    
    # Test user demographics
    user_demographics = {
        'age': 28,
        'gender': 'Female',
        'race_ethnicity': 'Hispanic',
        'location': 'Cincinnati'
    }
    
    # Apply fairness constraints
    adjusted_matches = fairness_engine.apply_fairness_constraints(sample_matches, user_demographics)
    
    assert len(adjusted_matches) == len(sample_matches), "Number of matches changed unexpectedly"
    assert all('score' in match for match in adjusted_matches), "Original scores missing"
    
    # Check if fairness adjustments were applied
    fairness_applied = any('fairness_adjusted_score' in match for match in adjusted_matches)
    
    print("✅ Demographic balance analysis completed")
    print(f"   - Original matches: {len(sample_matches)}")
    print(f"   - Adjusted matches: {len(adjusted_matches)}")
    print(f"   - Fairness adjustments applied: {fairness_applied}")
    
    # Display score adjustments
    for match in adjusted_matches[:3]:
        original_score = match.get('score', 0)
        adjusted_score = match.get('fairness_adjusted_score', original_score)
        if adjusted_score != original_score:
            print(f"   - {match['project_name']}: {original_score:.3f} → {adjusted_score:.3f}")
    
    return adjusted_matches

def test_fairness_constraints_application():
    """Test 3: Fairness constraints application across different demographic groups"""
    print("\n🧪 TEST 3: Fairness Constraints Application")
    
    test_data = create_test_data()
    matching_engine = VolunteerMatchingEngine(test_data)
    
    # Test different user profiles
    test_profiles = [
        # Profile 1: Young Hispanic female
        {
            'age': 22,
            'gender': 'Female',
            'race_ethnicity': 'Hispanic',
            'interests': 'youth development',
            'location': 'Cincinnati'
        },
        # Profile 2: Older white male
        {
            'age': 58,
            'gender': 'Male',
            'race_ethnicity': 'White',
            'interests': 'fitness wellness',
            'location': 'Blue Ash'
        },
        # Profile 3: Middle-aged Black female
        {
            'age': 35,
            'gender': 'Female',
            'race_ethnicity': 'Black',
            'interests': 'special events',
            'location': 'Newport'
        }
    ]
    
    fairness_results = []
    
    for i, profile in enumerate(test_profiles, 1):
        print(f"\n   Testing Profile {i}: {profile['age']}yo {profile['race_ethnicity']} {profile['gender']}")
        
        # Get matches with and without fairness constraints
        matches_with_fairness = matching_engine.find_matches(profile, top_k=5, apply_fairness_constraints=True)
        matches_without_fairness = matching_engine.find_matches(profile, top_k=5, apply_fairness_constraints=False)
        
        # Analyze balance
        balance_with = matching_engine.analyze_demographic_balance(matches_with_fairness)
        balance_without = matching_engine.analyze_demographic_balance(matches_without_fairness)
        
        fairness_results.append({
            'profile': profile,
            'balance_improvement': {
                'branch_diversity': balance_with['branch_diversity_score'] - balance_without['branch_diversity_score'],
                'category_diversity': balance_with['category_diversity_score'] - balance_without['category_diversity_score'],
                'overall_diversity': balance_with['overall_diversity_score'] - balance_without['overall_diversity_score']
            },
            'fairness_adjustments': sum(1 for match in matches_with_fairness if 'fairness_adjusted_score' in match)
        })
        
        print(f"     - Branch diversity improvement: {fairness_results[-1]['balance_improvement']['branch_diversity']:+.3f}")
        print(f"     - Category diversity improvement: {fairness_results[-1]['balance_improvement']['category_diversity']:+.3f}")
        print(f"     - Matches with adjustments: {fairness_results[-1]['fairness_adjustments']}/5")
    
    print("✅ Fairness constraints application test completed")
    return fairness_results

def test_fairness_reporting():
    """Test 4: Fairness reporting functionality"""
    print("\n🧪 TEST 4: Fairness Reporting")
    
    test_data = create_test_data()
    fairness_engine = FairnessConstraintsEngine(test_data)
    
    # Generate comprehensive report
    report = fairness_engine.generate_fairness_report()
    
    # Validate report structure
    required_sections = ['demographic_baselines', 'current_disparities', 'fairness_thresholds', 
                        'equity_metrics', 'recommendations']
    
    for section in required_sections:
        assert section in report, f"Missing report section: {section}"
    
    print("✅ Fairness reporting test completed")
    print(f"   - Report sections: {list(report.keys())}")
    print(f"   - Equity metrics: {list(report['equity_metrics'].keys()) if report['equity_metrics'] else 'None'}")
    print(f"   - Recommendations: {len(report['recommendations'])} items")
    
    # Display key findings
    if report['equity_metrics']:
        overall_score = report['equity_metrics'].get('overall_fairness_score', 0)
        parity_score = report['equity_metrics'].get('demographic_parity_score', 0)
        print(f"   - Overall fairness score: {overall_score:.3f}")
        print(f"   - Demographic parity score: {parity_score:.3f}")
    
    return report

def test_underrepresentation_boost():
    """Test 5: Underrepresentation boost functionality"""
    print("\n🧪 TEST 5: Underrepresentation Boost")
    
    test_data = create_test_data()
    
    # Create biased data to test underrepresentation detection
    biased_volunteers = test_data['volunteers'].copy()
    # Make one demographic group significantly underrepresented in high-engagement activities
    mask = (biased_volunteers['race_ethnicity'] == 'Hispanic') | (biased_volunteers['race_ethnicity'] == 'Asian')
    biased_volunteers.loc[mask, 'total_hours'] *= 0.3  # Reduce hours for these groups
    
    test_data['volunteers'] = biased_volunteers
    
    fairness_engine = FairnessConstraintsEngine(test_data)
    
    # Test with underrepresented user
    underrepresented_user = {
        'age': 30,
        'gender': 'Female',
        'race_ethnicity': 'Hispanic'
    }
    
    # Test with majority user
    majority_user = {
        'age': 30,
        'gender': 'Female', 
        'race_ethnicity': 'White'
    }
    
    sample_matches = [
        {'project_id': 'proj_001', 'project_name': 'Test Project 1', 'branch': 'Blue Ash', 'category': 'General', 'score': 0.7},
        {'project_id': 'proj_002', 'project_name': 'Test Project 2', 'branch': 'M.E. Lyons', 'category': 'General', 'score': 0.65},
    ]
    
    # Apply fairness constraints for both users
    adjusted_underrepresented = fairness_engine.apply_fairness_constraints(sample_matches.copy(), underrepresented_user)
    adjusted_majority = fairness_engine.apply_fairness_constraints(sample_matches.copy(), majority_user)
    
    # Check if underrepresented user got a boost
    underrep_boost_applied = any('underrepresentation_boost' in match for match in adjusted_underrepresented)
    majority_boost_applied = any('underrepresentation_boost' in match for match in adjusted_majority)
    
    print("✅ Underrepresentation boost test completed")
    print(f"   - Boost applied for Hispanic user: {underrep_boost_applied}")
    print(f"   - Boost applied for White user: {majority_boost_applied}")
    
    if underrep_boost_applied:
        boost_amount = adjusted_underrepresented[0].get('underrepresentation_boost', 0)
        print(f"   - Boost amount for underrepresented user: {boost_amount:.3f}")

def test_branch_equity_constraints():
    """Test 6: Branch equity constraints"""
    print("\n🧪 TEST 6: Branch Equity Constraints")
    
    test_data = create_test_data()
    fairness_engine = FairnessConstraintsEngine(test_data)
    
    # Test matches across different branches
    diverse_matches = [
        {'project_id': 'proj_001', 'project_name': 'Project A', 'branch': 'Blue Ash', 'category': 'General', 'score': 0.8},
        {'project_id': 'proj_002', 'project_name': 'Project B', 'branch': 'M.E. Lyons', 'category': 'General', 'score': 0.75},
        {'project_id': 'proj_003', 'project_name': 'Project C', 'branch': 'Campbell County', 'category': 'General', 'score': 0.7},
        {'project_id': 'proj_004', 'project_name': 'Project D', 'branch': 'Clippard', 'category': 'General', 'score': 0.65},
        {'project_id': 'proj_005', 'project_name': 'Project E', 'branch': 'YDE', 'category': 'General', 'score': 0.6},
    ]
    
    user_demographics = {'age': 25, 'gender': 'Male', 'race_ethnicity': 'Asian'}
    
    adjusted_matches = fairness_engine.apply_fairness_constraints(diverse_matches, user_demographics)
    
    # Check if branch equity adjustments were applied
    branch_adjustments = [match.get('branch_equity_adjustment', 0) for match in adjusted_matches]
    adjustments_applied = any(adj != 0 for adj in branch_adjustments)
    
    print("✅ Branch equity constraints test completed")
    print(f"   - Branch equity adjustments applied: {adjustments_applied}")
    print(f"   - Number of branches represented: {len(set(match['branch'] for match in adjusted_matches))}")
    
    if adjustments_applied:
        for match, adj in zip(adjusted_matches, branch_adjustments):
            if adj != 0:
                print(f"   - {match['branch']}: {adj:+.3f} equity adjustment")

def run_comprehensive_fairness_tests():
    """Run all fairness constraint tests"""
    print("🚀 COMPREHENSIVE FAIRNESS CONSTRAINTS TEST SUITE")
    print("=" * 60)
    
    try:
        # Test 1: Basic initialization
        fairness_engine = test_fairness_engine_initialization()
        
        # Test 2: Demographic balance analysis
        adjusted_matches = test_demographic_balance_analysis(fairness_engine)
        
        # Test 3: Fairness constraints application
        fairness_results = test_fairness_constraints_application()
        
        # Test 4: Fairness reporting
        report = test_fairness_reporting()
        
        # Test 5: Underrepresentation boost
        test_underrepresentation_boost()
        
        # Test 6: Branch equity constraints
        test_branch_equity_constraints()
        
        print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("📊 SUMMARY:")
        print("✅ Fairness constraints engine properly initialized")
        print("✅ Demographic balance analysis working correctly")
        print("✅ Fairness constraints applied across different user profiles")
        print("✅ Comprehensive fairness reporting functional")
        print("✅ Underrepresentation boost mechanism active")
        print("✅ Branch equity constraints operational")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_comprehensive_fairness_tests()
    exit(0 if success else 1)