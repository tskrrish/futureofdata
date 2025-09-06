"""
Examples of how to use the Volunteer Churn Risk Model

This file provides examples of how to interact with the churn risk model
both programmatically and through the API endpoints.
"""

import requests
import json
from datetime import datetime

class ChurnRiskAPIExamples:
    """Examples of using the churn risk API endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def get_individual_risk_analysis(self, contact_id: int):
        """Example: Get churn risk analysis for a specific volunteer"""
        url = f"{self.base_url}/api/churn/volunteer/{contact_id}"
        
        try:
            response = requests.get(url)
            
            if response.status_code == 200:
                risk_data = response.json()
                
                print(f"Churn Risk Analysis for Volunteer {contact_id}")
                print("=" * 50)
                print(f"Risk Score: {risk_data['risk_score']}/100")
                print(f"Risk Category: {risk_data['risk_category'].title()}")
                print(f"Churn Probability: {risk_data['churn_probability']:.1%}")
                
                print("\nTop Risk Factors:")
                for i, factor in enumerate(risk_data['top_risk_factors'][:3], 1):
                    print(f"  {i}. {factor['factor']}: {factor['description']}")
                
                print("\nRecommended Interventions:")
                for i, intervention in enumerate(risk_data['intervention_recommendations'][:3], 1):
                    print(f"  {i}. {intervention['intervention']} (Priority: {intervention['priority']})")
                
                return risk_data
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
                
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None
    
    def get_high_risk_volunteers(self, threshold: int = 70, limit: int = 10):
        """Example: Get list of high-risk volunteers"""
        url = f"{self.base_url}/api/churn/high-risk"
        params = {"threshold": threshold, "limit": limit}
        
        try:
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"High-Risk Volunteers (Risk >= {threshold})")
                print("=" * 50)
                print(f"Found: {data['total_found']} volunteers")
                
                for i, volunteer in enumerate(data['high_risk_volunteers'][:5], 1):
                    summary = volunteer['volunteer_summary']
                    print(f"\n{i}. Contact {volunteer['contact_id']}")
                    print(f"   Risk Score: {volunteer['risk_score']}/100")
                    print(f"   Total Hours: {summary['total_hours']:.1f}")
                    print(f"   Last Activity: {summary['last_activity_days_ago']} days ago")
                    
                    if volunteer['top_risk_factors']:
                        print(f"   Main Risk: {volunteer['top_risk_factors'][0]['factor']}")
                
                return data
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
                
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None
    
    def batch_risk_analysis(self, contact_ids: list):
        """Example: Batch risk analysis for multiple volunteers"""
        url = f"{self.base_url}/api/churn/batch"
        
        try:
            response = requests.post(
                url,
                json=contact_ids,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"Batch Risk Analysis Results")
                print("=" * 50)
                
                summary = data['summary']
                print(f"Analyzed: {summary['total_analyzed']} volunteers")
                print(f"Average Risk Score: {summary.get('avg_risk_score', 0):.1f}")
                print(f"High Risk: {summary.get('high_risk_count', 0)}")
                print(f"Medium Risk: {summary.get('medium_risk_count', 0)}")
                print(f"Low Risk: {summary.get('low_risk_count', 0)}")
                
                # Show top 3 highest risk
                results = sorted(data['results'], key=lambda x: x['risk_score'], reverse=True)
                print(f"\nTop 3 Highest Risk Volunteers:")
                for i, result in enumerate(results[:3], 1):
                    print(f"  {i}. Contact {result['contact_id']}: {result['risk_score']}/100")
                
                return data
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
                
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None
    
    def get_model_insights(self):
        """Example: Get churn model insights and performance metrics"""
        url = f"{self.base_url}/api/churn/insights"
        
        try:
            response = requests.get(url)
            
            if response.status_code == 200:
                insights = response.json()
                
                print("Churn Risk Model Insights")
                print("=" * 50)
                print(f"Model Trained: {insights['model_trained']}")
                print(f"Total Volunteers: {insights['total_volunteers']}")
                print(f"Churn Rate: {insights['churn_rate']:.1%}")
                
                print("\nTop Predictive Features:")
                for i, (feature, importance) in enumerate(insights['top_predictive_features'][:5], 1):
                    print(f"  {i}. {feature}: {importance:.3f}")
                
                print(f"\nRisk Categories:")
                for category, (min_val, max_val) in insights['risk_categories'].items():
                    print(f"  {category.title()}: {min_val}-{max_val}")
                
                return insights
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
                
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None
    
    def record_intervention(self, contact_id: int, intervention: str, notes: str = None):
        """Example: Record that an intervention was taken for a volunteer"""
        url = f"{self.base_url}/api/churn/intervention"
        
        data = {
            "contact_id": contact_id,
            "intervention_taken": intervention,
            "notes": notes
        }
        
        try:
            response = requests.post(
                url,
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"Intervention Recorded")
                print("=" * 30)
                print(f"Volunteer: {contact_id}")
                print(f"Intervention: {intervention}")
                print(f"Current Risk Score: {result['current_risk_analysis']['risk_score']}/100")
                print(f"Recorded At: {result['intervention_recorded']['performed_at']}")
                
                return result
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
                
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None

def usage_examples():
    """Demo usage of the churn risk API"""
    api = ChurnRiskAPIExamples()
    
    print("🎯 Volunteer Churn Risk Model - Usage Examples")
    print("=" * 60)
    
    # Example 1: Individual risk analysis
    print("\n1. Individual Risk Analysis")
    print("-" * 30)
    # api.get_individual_risk_analysis(contact_id=1001)
    print("Usage: GET /api/churn/volunteer/{contact_id}")
    print("Returns: Risk score, factors, interventions for specific volunteer")
    
    # Example 2: High-risk volunteers
    print("\n2. High-Risk Volunteers")
    print("-" * 30) 
    # api.get_high_risk_volunteers(threshold=70, limit=5)
    print("Usage: GET /api/churn/high-risk?threshold=70&limit=10")
    print("Returns: List of volunteers above risk threshold")
    
    # Example 3: Batch analysis
    print("\n3. Batch Risk Analysis")
    print("-" * 30)
    # api.batch_risk_analysis([1001, 1002, 1003, 1004])
    print("Usage: POST /api/churn/batch with JSON body: [contact_id1, contact_id2, ...]")
    print("Returns: Risk analysis for multiple volunteers with summary stats")
    
    # Example 4: Model insights
    print("\n4. Model Insights")
    print("-" * 30)
    # api.get_model_insights()
    print("Usage: GET /api/churn/insights")
    print("Returns: Model performance, feature importance, statistics")
    
    # Example 5: Record intervention
    print("\n5. Record Intervention")
    print("-" * 30)
    # api.record_intervention(1001, "Called volunteer for check-in", "Volunteer was receptive")
    print("Usage: POST /api/churn/intervention")
    print("Body: {contact_id, intervention_taken, notes}")
    print("Returns: Confirmation and current risk status")

# Sample data structures for reference
SAMPLE_RISK_RESPONSE = {
    "contact_id": 1001,
    "risk_score": 75,
    "risk_category": "high",
    "churn_probability": 0.75,
    "top_risk_factors": [
        {
            "factor": "Recent Inactivity",
            "description": "No activity in 95 days",
            "severity": "high",
            "impact_score": 0.8
        }
    ],
    "intervention_recommendations": [
        {
            "risk_factor": "Recent Inactivity",
            "intervention": "Schedule a check-in call to understand their experience",
            "category": "low_engagement",
            "priority": "high",
            "expected_impact": 0.8
        }
    ],
    "volunteer_summary": {
        "name": "Volunteer 1001",
        "total_hours": 45.5,
        "volunteer_sessions": 8,
        "unique_projects": 3,
        "tenure_days": 180,
        "last_activity_days_ago": 95
    }
}

SAMPLE_HIGH_RISK_RESPONSE = {
    "high_risk_volunteers": [
        # List of volunteers with risk_score >= threshold
    ],
    "threshold": 70,
    "total_found": 12,
    "generated_at": "2025-09-06T20:30:00Z"
}

if __name__ == "__main__":
    usage_examples()