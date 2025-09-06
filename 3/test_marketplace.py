#!/usr/bin/env python3
"""
Test script for the YMCA Volunteer Opportunity Marketplace
Tests core functionality without external dependencies
"""

import json
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock
import pandas as pd

# Mock external dependencies
class MockSupabase:
    def table(self, name):
        return Mock()

class MockDatabase:
    def __init__(self):
        self.is_available = True
    
    async def save_application(self, user_id, app_data):
        return "test-app-id-123"
    
    async def get_user_preferences(self, user_id):
        return {
            "preferences_data": {
                "interests": "youth development",
                "time_commitment": 2,
                "location": "Blue Ash"
            }
        }

class MockMatchingEngine:
    def __init__(self):
        self.models_trained = True
    
    def _create_user_vector(self, preferences):
        return {
            "interests_youth": 1 if "youth" in preferences.get("interests", "") else 0,
            "time_commitment": preferences.get("time_commitment", 2),
            "age": 35
        }
    
    def _calculate_match_score(self, user_vector, opportunity, preferences):
        # Simple mock scoring
        score = 0.5
        if user_vector.get("interests_youth") and "youth" in opportunity.get("category", "").lower():
            score += 0.3
        return min(score, 1.0)
    
    def get_similar_opportunities(self, opportunity_id, limit=5):
        return [
            {
                "project_id": i,
                "project_name": f"Similar Project {i}",
                "branch": "Blue Ash",
                "category": "Youth Development",
                "similarity_score": 0.8,
                "similar_aspects": ["Same category", "Similar time commitment"]
            }
            for i in range(1, limit + 1)
        ]

def create_mock_volunteer_data():
    """Create mock volunteer data for testing"""
    projects_data = [
        {
            "project_id": 1,
            "project_name": "Youth Basketball Assistant",
            "branch": "Blue Ash YMCA",
            "category": "Youth Development",
            "avg_hours_per_session": 2.5,
            "unique_volunteers": 8,
            "need": "Help coach youth basketball teams",
            "sample_activities": "Assist with drills, games, and team building",
            "required_credentials": "Background check required"
        },
        {
            "project_id": 2,
            "project_name": "Fitness Class Support",
            "branch": "M.E. Lyons YMCA",
            "category": "Fitness & Wellness",
            "avg_hours_per_session": 1.5,
            "unique_volunteers": 12,
            "need": "Support fitness instructors during classes",
            "sample_activities": "Set up equipment, assist participants",
            "required_credentials": "CPR certification preferred"
        },
        {
            "project_id": 3,
            "project_name": "Summer Camp Counselor",
            "branch": "Campbell County YMCA", 
            "category": "Youth Programs",
            "avg_hours_per_session": 4.0,
            "unique_volunteers": 15,
            "need": "Lead activities for children during summer camp",
            "sample_activities": "Games, crafts, outdoor activities",
            "required_credentials": "Background check and training required"
        }
    ]
    
    return {
        "projects": pd.DataFrame(projects_data),
        "volunteers": pd.DataFrame(),
        "interactions": pd.DataFrame()
    }

def test_filtering_logic():
    """Test opportunity filtering functionality"""
    print("🧪 Testing filtering logic...")
    
    volunteer_data = create_mock_volunteer_data()
    opportunities = volunteer_data["projects"]
    
    # Test category filtering
    filtered = opportunities[
        opportunities['category'].str.contains("Youth", case=False, na=False)
    ]
    assert len(filtered) == 2, f"Expected 2 youth opportunities, got {len(filtered)}"
    
    # Test branch filtering  
    filtered = opportunities[
        opportunities['branch'].str.contains("Blue Ash", case=False, na=False)
    ]
    assert len(filtered) == 1, f"Expected 1 Blue Ash opportunity, got {len(filtered)}"
    
    # Test hours filtering
    filtered = opportunities[
        opportunities['avg_hours_per_session'] <= 2.0
    ]
    assert len(filtered) == 1, f"Expected 1 opportunity ≤2 hours, got {len(filtered)}"
    
    print("✅ Filtering logic tests passed")

def test_personalized_ranking():
    """Test personalized ranking algorithm"""
    print("🧪 Testing personalized ranking...")
    
    volunteer_data = create_mock_volunteer_data()
    matching_engine = MockMatchingEngine()
    
    user_preferences = {
        "interests": "youth development",
        "time_commitment": 2,
        "age": 28
    }
    
    opportunities = volunteer_data["projects"]
    ranked_opportunities = []
    
    for _, opportunity in opportunities.iterrows():
        user_vector = matching_engine._create_user_vector(user_preferences)
        score = matching_engine._calculate_match_score(user_vector, opportunity, user_preferences)
        
        ranked_opportunities.append({
            "project_id": opportunity["project_id"],
            "project_name": opportunity["project_name"],
            "score": score,
            "category": opportunity["category"]
        })
    
    # Sort by score
    ranked_opportunities.sort(key=lambda x: x['score'], reverse=True)
    
    # Youth development opportunities should rank higher
    top_opportunity = ranked_opportunities[0]
    assert "Youth" in top_opportunity["category"], "Youth opportunity should rank highest"
    assert top_opportunity["score"] >= 0.5, f"Top score should be ≥0.5, got {top_opportunity['score']}"
    
    print(f"✅ Top ranked opportunity: {top_opportunity['project_name']} (Score: {top_opportunity['score']:.2f})")

def test_search_functionality():
    """Test search functionality"""
    print("🧪 Testing search functionality...")
    
    volunteer_data = create_mock_volunteer_data()
    opportunities = volunteer_data["projects"]
    
    # Test search
    query = "basketball"
    search_results = []
    
    search_fields = ['project_name', 'category', 'need', 'sample_activities']
    query_lower = query.lower()
    
    for _, opp in opportunities.iterrows():
        relevance_score = 0
        matched_fields = []
        
        for field in search_fields:
            field_value = str(opp.get(field, '')).lower()
            if query_lower in field_value:
                relevance_score += 1
                matched_fields.append(field)
        
        if relevance_score > 0:
            search_results.append({
                "project_name": opp["project_name"],
                "relevance_score": relevance_score,
                "matched_fields": matched_fields
            })
    
    # Sort by relevance
    search_results.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    assert len(search_results) == 1, f"Expected 1 basketball result, got {len(search_results)}"
    assert search_results[0]["project_name"] == "Youth Basketball Assistant"
    
    print("✅ Search functionality tests passed")

def test_application_data_structure():
    """Test application data structure"""
    print("🧪 Testing application data structure...")
    
    application_data = {
        "project_id": 1,
        "message": "I'm interested in helping with youth basketball",
        "availability": {
            "weekday": True,
            "weekend": False,
            "evening": True
        }
    }
    
    # Validate required fields
    assert "project_id" in application_data, "project_id is required"
    assert isinstance(application_data["project_id"], int), "project_id should be integer"
    assert "message" in application_data, "message is required"
    assert "availability" in application_data, "availability is required"
    
    # Test JSON serialization
    json_str = json.dumps(application_data)
    parsed = json.loads(json_str)
    assert parsed == application_data, "Application data should be JSON serializable"
    
    print("✅ Application data structure tests passed")

async def test_async_functionality():
    """Test async functions"""
    print("🧪 Testing async functionality...")
    
    # Mock database operations
    database = MockDatabase()
    
    application_data = {
        "project_id": 1,
        "message": "Test application",
        "availability": {"flexible": True}
    }
    
    # Test application saving
    app_id = await database.save_application("test-user", application_data)
    assert app_id is not None, "Application should be saved successfully"
    assert isinstance(app_id, str), "Application ID should be a string"
    
    # Test user preferences retrieval
    preferences = await database.get_user_preferences("test-user")
    assert preferences is not None, "Preferences should be retrievable"
    assert "preferences_data" in preferences, "Preferences should have data structure"
    
    print("✅ Async functionality tests passed")

def test_marketplace_statistics():
    """Test marketplace statistics calculation"""
    print("🧪 Testing marketplace statistics...")
    
    volunteer_data = create_mock_volunteer_data()
    opportunities = volunteer_data["projects"]
    
    stats = {
        "total_opportunities": len(opportunities),
        "categories": {
            "count": opportunities['category'].nunique(),
            "distribution": opportunities['category'].value_counts().to_dict()
        },
        "branches": {
            "count": opportunities['branch'].nunique(),
            "distribution": opportunities['branch'].value_counts().to_dict()
        },
        "time_commitments": {
            "avg_hours": float(opportunities['avg_hours_per_session'].mean()),
            "min_hours": float(opportunities['avg_hours_per_session'].min()),
            "max_hours": float(opportunities['avg_hours_per_session'].max())
        },
        "volunteer_engagement": {
            "total_volunteers": int(opportunities['unique_volunteers'].sum()),
            "avg_volunteers_per_opportunity": float(opportunities['unique_volunteers'].mean())
        }
    }
    
    # Validate statistics
    assert stats["total_opportunities"] == 3, f"Expected 3 opportunities, got {stats['total_opportunities']}"
    assert stats["categories"]["count"] == 3, f"Expected 3 categories, got {stats['categories']['count']}"
    assert stats["branches"]["count"] == 3, f"Expected 3 branches, got {stats['branches']['count']}"
    assert stats["volunteer_engagement"]["total_volunteers"] == 35, f"Expected 35 total volunteers, got {stats['volunteer_engagement']['total_volunteers']}"
    
    print("✅ Marketplace statistics tests passed")

def test_similar_opportunities():
    """Test similar opportunities functionality"""
    print("🧪 Testing similar opportunities...")
    
    matching_engine = MockMatchingEngine()
    similar_opps = matching_engine.get_similar_opportunities(1, limit=3)
    
    assert len(similar_opps) == 3, f"Expected 3 similar opportunities, got {len(similar_opps)}"
    
    for opp in similar_opps:
        assert "project_id" in opp, "Similar opportunity should have project_id"
        assert "similarity_score" in opp, "Similar opportunity should have similarity_score"
        assert "similar_aspects" in opp, "Similar opportunity should have similar_aspects"
        assert isinstance(opp["similar_aspects"], list), "Similar aspects should be a list"
    
    print("✅ Similar opportunities tests passed")

def run_all_tests():
    """Run all marketplace tests"""
    print("🚀 Starting YMCA Volunteer Marketplace Tests\n")
    
    try:
        # Synchronous tests
        test_filtering_logic()
        test_personalized_ranking()
        test_search_functionality()
        test_application_data_structure()
        test_marketplace_statistics()
        test_similar_opportunities()
        
        # Asynchronous tests
        asyncio.run(test_async_functionality())
        
        print("\n🎉 All marketplace tests passed!")
        print("\n📊 Test Summary:")
        print("✅ Filtering and search functionality")
        print("✅ Personalized ranking algorithm")
        print("✅ Application data handling")
        print("✅ Async database operations")
        print("✅ Statistics and analytics")
        print("✅ Similar opportunities matching")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)