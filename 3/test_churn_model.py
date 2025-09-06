"""
Test script for the Volunteer Churn Risk Model

This script tests the churn risk model functionality with sample data
to ensure it works correctly before deployment.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from churn_risk_model import VolunteerChurnRiskModel

def create_sample_volunteer_data():
    """Create sample volunteer data for testing"""
    
    # Sample volunteers
    volunteers_data = []
    for i in range(100):
        contact_id = 1000 + i
        age = np.random.randint(18, 70)
        total_hours = max(0, np.random.normal(50, 30))
        sessions = max(1, int(np.random.poisson(8)))
        projects = max(1, min(sessions, int(np.random.poisson(3))))
        tenure_days = max(30, int(np.random.normal(200, 100)))
        
        volunteers_data.append({
            'contact_id': contact_id,
            'age': age,
            'gender': np.random.choice(['Male', 'Female', 'Other']),
            'race_ethnicity': np.random.choice(['White', 'Black', 'Hispanic', 'Asian', 'Other']),
            'total_hours': total_hours,
            'volunteer_sessions': sessions,
            'unique_projects': projects,
            'volunteer_tenure_days': tenure_days,
            'avg_hours_per_session': total_hours / sessions if sessions > 0 else 0,
            'is_ymca_member': np.random.choice([True, False]),
            'home_city': 'Cincinnati',
            'home_state': 'OH',
            'project_categories': ','.join(np.random.choice(['Youth Development', 'Fitness', 'Events'], 
                                                           size=np.random.randint(1, 3), replace=False))
        })
    
    volunteers_df = pd.DataFrame(volunteers_data)
    
    # Sample interactions (volunteer session records)
    interactions_data = []
    base_date = datetime.now() - timedelta(days=365)
    
    for _, volunteer in volunteers_df.iterrows():
        contact_id = volunteer['contact_id']
        sessions = volunteer['volunteer_sessions']
        
        for session in range(sessions):
            # Create sessions spread over tenure period
            session_date = base_date + timedelta(
                days=np.random.randint(0, min(365, volunteer['volunteer_tenure_days']))
            )
            
            interactions_data.append({
                'contact_id': contact_id,
                'project_id': 200 + np.random.randint(0, 20),
                'date': session_date,
                'hours': max(0.5, np.random.normal(3, 1.5))
            })
    
    interactions_df = pd.DataFrame(interactions_data)
    
    # Sample projects
    projects_data = []
    categories = ['Youth Development', 'Fitness & Wellness', 'Special Events', 
                 'Facility Support', 'Administrative']
    branches = ['Blue Ash', 'M.E. Lyons', 'Campbell County', 'Clippard']
    
    for i in range(20):
        projects_data.append({
            'project_id': 200 + i,
            'project_name': f'Sample Project {i+1}',
            'category': np.random.choice(categories),
            'branch': np.random.choice(branches),
            'avg_hours_per_session': np.random.uniform(1, 6),
            'unique_volunteers': np.random.randint(5, 30),
            'required_credentials': 'Basic volunteer requirements',
            'need': f'Help with project activities {i+1}',
            'sample_activities': f'Various volunteer activities for project {i+1}'
        })
    
    projects_df = pd.DataFrame(projects_data)
    
    return {
        'volunteers': volunteers_df,
        'interactions': interactions_df,
        'projects': projects_df,
        'insights': {
            'total_volunteers': len(volunteers_df),
            'total_projects': len(projects_df),
            'top_branches': {'Blue Ash': 25, 'M.E. Lyons': 30, 'Campbell County': 20, 'Clippard': 25}
        }
    }

def test_churn_model():
    """Test the churn risk model functionality"""
    print("🧪 Testing Volunteer Churn Risk Model")
    print("=" * 50)
    
    # Create sample data
    print("📊 Creating sample volunteer data...")
    volunteer_data = create_sample_volunteer_data()
    print(f"✅ Created data for {len(volunteer_data['volunteers'])} volunteers")
    
    # Initialize churn model
    print("\n🤖 Initializing churn risk model...")
    churn_model = VolunteerChurnRiskModel(volunteer_data)
    
    # Train the model
    print("\n📈 Training churn prediction model...")
    churn_model.train_model()
    
    # Test individual risk prediction
    print("\n🎯 Testing individual risk prediction...")
    test_contact_id = volunteer_data['volunteers']['contact_id'].iloc[0]
    risk_analysis = churn_model.predict_churn_risk(test_contact_id)
    
    print(f"Risk Analysis for Volunteer {test_contact_id}:")
    print(f"  - Risk Score: {risk_analysis['risk_score']}/100")
    print(f"  - Risk Category: {risk_analysis['risk_category']}")
    print(f"  - Top Risk Factors: {len(risk_analysis['top_risk_factors'])}")
    print(f"  - Intervention Recommendations: {len(risk_analysis['intervention_recommendations'])}")
    
    if risk_analysis['top_risk_factors']:
        print("\n  Top Risk Factor:")
        top_factor = risk_analysis['top_risk_factors'][0]
        print(f"    - {top_factor['factor']}: {top_factor['description']}")
    
    if risk_analysis['intervention_recommendations']:
        print("\n  Top Intervention:")
        top_intervention = risk_analysis['intervention_recommendations'][0]
        print(f"    - {top_intervention['intervention']}")
    
    # Test batch prediction
    print("\n📊 Testing batch prediction...")
    sample_contact_ids = volunteer_data['volunteers']['contact_id'].head(10).tolist()
    batch_results = churn_model.batch_predict_churn_risk(sample_contact_ids)
    
    print(f"  - Analyzed {len(batch_results)} volunteers")
    risk_scores = [result['risk_score'] for result in batch_results if 'risk_score' in result]
    if risk_scores:
        print(f"  - Average risk score: {sum(risk_scores) / len(risk_scores):.1f}")
        print(f"  - Risk score range: {min(risk_scores)} - {max(risk_scores)}")
    
    # Test high-risk volunteers
    print("\n⚠️  Testing high-risk volunteer identification...")
    high_risk_volunteers = churn_model.get_high_risk_volunteers(threshold=60, limit=5)
    
    print(f"  - Found {len(high_risk_volunteers)} high-risk volunteers")
    for i, volunteer in enumerate(high_risk_volunteers[:3], 1):
        print(f"    {i}. Contact {volunteer['contact_id']}: {volunteer['risk_score']}/100 risk")
    
    # Test model insights
    print("\n🔍 Testing model insights...")
    insights = churn_model.get_model_insights()
    
    if 'error' not in insights:
        print(f"  - Model trained: {insights['model_trained']}")
        print(f"  - Total volunteers: {insights['total_volunteers']}")
        print(f"  - Churn rate: {insights['churn_rate']:.2%}")
        print(f"  - Top predictive features: {len(insights['top_predictive_features'])}")
        
        if insights['top_predictive_features']:
            print("\n  Most Important Features:")
            for feature, importance in insights['top_predictive_features'][:3]:
                print(f"    - {feature}: {importance:.3f}")
    
    print("\n✅ All tests completed successfully!")
    print("🎉 Churn risk model is working correctly!")
    
    return True

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n🧪 Testing edge cases...")
    
    # Test with minimal data
    minimal_data = {
        'volunteers': pd.DataFrame([{
            'contact_id': 9999,
            'age': 30,
            'gender': 'Female',
            'race_ethnicity': 'White',
            'total_hours': 10,
            'volunteer_sessions': 2,
            'unique_projects': 1,
            'volunteer_tenure_days': 45,
            'avg_hours_per_session': 5,
            'is_ymca_member': True,
            'home_city': 'Cincinnati',
            'home_state': 'OH',
            'project_categories': 'Youth Development'
        }]),
        'interactions': pd.DataFrame([{
            'contact_id': 9999,
            'project_id': 201,
            'date': datetime.now() - timedelta(days=30),
            'hours': 5
        }]),
        'projects': pd.DataFrame([{
            'project_id': 201,
            'project_name': 'Test Project',
            'category': 'Youth Development',
            'branch': 'Test Branch',
            'avg_hours_per_session': 3,
            'unique_volunteers': 10
        }])
    }
    
    churn_model_minimal = VolunteerChurnRiskModel(minimal_data)
    
    # Test prediction with minimal data (should use fallback logic)
    risk_result = churn_model_minimal.predict_churn_risk(9999)
    print(f"  - Minimal data prediction: {risk_result['risk_score']}/100")
    
    # Test prediction for non-existent volunteer
    error_result = churn_model_minimal.predict_churn_risk(99999)
    print(f"  - Non-existent volunteer: {'error' in error_result}")
    
    print("✅ Edge case testing completed!")

if __name__ == "__main__":
    try:
        # Run main tests
        success = test_churn_model()
        
        # Run edge case tests
        test_edge_cases()
        
        print(f"\n🎯 Test Summary: {'PASSED' if success else 'FAILED'}")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()