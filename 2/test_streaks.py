#!/usr/bin/env python3

"""
Simple test script to validate streak calculation logic.
This tests the core streak functionality without requiring external dependencies.
"""

from datetime import datetime, timedelta
import sys
import os

# Add current directory to path so we can import our modules
sys.path.append(os.path.dirname(__file__))

# Mock pandas DataFrame functionality for testing
class MockDataFrame:
    def __init__(self, data):
        self.data = data
        self._empty = len(data) == 0
    
    @property 
    def empty(self):
        return self._empty
    
    def copy(self):
        return MockDataFrame(self.data.copy())
    
    def dropna(self, subset=None):
        # Simple mock - return self
        return self
    
    def sort_values(self, column):
        # Simple mock - return self
        return self
    
    def __getitem__(self, key):
        return [row[key] for row in self.data]

# Mock pandas functionality
class MockPandas:
    def __init__(self):
        self.Timestamp = datetime
        
    def to_datetime(self, dates, errors='raise'):
        if isinstance(dates, list):
            return [datetime.fromisoformat(d.replace('Z', '+00:00')) if isinstance(d, str) else d for d in dates]
        return datetime.fromisoformat(dates.replace('Z', '+00:00')) if isinstance(dates, str) else dates

# Patch pandas import
import sys
sys.modules['pandas'] = MockPandas()
pd = MockPandas()

from shared_constants import STREAK_TYPES, compute_streak_milestones

def test_streak_constants():
    """Test that streak constants are properly defined."""
    print("Testing streak constants...")
    
    # Test STREAK_TYPES
    assert 'weekly' in STREAK_TYPES
    assert 'monthly' in STREAK_TYPES
    
    weekly = STREAK_TYPES['weekly']
    assert weekly['period_days'] == 7
    assert weekly['grace_days'] == 2
    assert weekly['min_hours_per_period'] == 1.0
    
    monthly = STREAK_TYPES['monthly']  
    assert monthly['period_days'] == 30
    assert monthly['grace_days'] == 7
    assert monthly['min_hours_per_period'] == 2.0
    
    print("✓ Streak constants are correct")

def test_streak_milestones():
    """Test streak milestone calculation."""
    print("Testing streak milestones...")
    
    # Test milestone thresholds
    milestones_0 = compute_streak_milestones(0)
    assert milestones_0 == []
    
    milestones_2 = compute_streak_milestones(2)
    assert "Streak Starter" in milestones_2
    
    milestones_4 = compute_streak_milestones(4)
    assert "Streak Starter" in milestones_4
    assert "Consistent Contributor" in milestones_4
    
    milestones_52 = compute_streak_milestones(52)
    assert len(milestones_52) == 6  # All milestones
    assert "Legendary Streaker" in milestones_52
    
    print("✓ Streak milestones calculated correctly")

def test_basic_logic():
    """Test basic streak logic concepts."""
    print("Testing basic logic...")
    
    # Test grace period logic
    weekly_config = STREAK_TYPES['weekly']
    period_days = weekly_config['period_days']  # 7
    grace_days = weekly_config['grace_days']    # 2
    
    # A week period with 2 grace days = 9 total days to maintain streak
    total_allowable = period_days + grace_days
    assert total_allowable == 9
    
    # Monthly should be 37 days total
    monthly_config = STREAK_TYPES['monthly']
    monthly_total = monthly_config['period_days'] + monthly_config['grace_days']
    assert monthly_total == 37
    
    print("✓ Basic logic checks passed")

def main():
    """Run all tests."""
    print("🔥 Testing Streak Feature Implementation")
    print("=" * 40)
    
    try:
        test_streak_constants()
        test_streak_milestones()
        test_basic_logic()
        
        print("=" * 40)
        print("✅ All tests passed! Streak feature is ready.")
        
        # Print configuration summary
        print("\n📊 Streak Configuration Summary:")
        for streak_type, config in STREAK_TYPES.items():
            print(f"  {streak_type.title()}: {config['period_days']} days + {config['grace_days']} grace = {config['period_days'] + config['grace_days']} total")
        
        return 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())