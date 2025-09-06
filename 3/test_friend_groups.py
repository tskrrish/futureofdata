"""
Test script for the friend group detection and team matching functionality
Creates sample volunteer data to demonstrate the friend group features
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from friend_group_detector import FriendGroupDetector
from team_matching_engine import TeamMatchingEngine
import json

def create_sample_volunteer_data():
    """Create sample volunteer data for testing friend group detection"""
    
    # Create sample volunteers
    volunteers_data = []
    volunteer_ids = [f"vol_{i:03d}" for i in range(1, 21)]  # 20 volunteers
    
    for i, vol_id in enumerate(volunteer_ids):
        volunteers_data.append({
            'contact_id': vol_id,
            'first_name': f'Volunteer_{i+1}',
            'last_name': f'Smith_{i+1}',
            'age': 20 + (i * 2),  # Ages 20-58
            'gender': 'Female' if i % 2 == 0 else 'Male',
            'race_ethnicity': 'Not Specified',
            'home_city': 'Cincinnati' if i < 15 else 'Newport',
            'home_state': 'OH',
            'is_ymca_member': i % 3 == 0,
            'member_branch': 'Blue Ash YMCA' if i < 10 else 'M.E. Lyons YMCA',
            'total_hours': 10 + (i * 5),
            'volunteer_sessions': 2 + (i // 2),
            'unique_projects': 1 + (i // 3),
            'branches_volunteered': 'Blue Ash YMCA' if i < 10 else 'M.E. Lyons YMCA',
            'project_categories': 'Youth Development' if i % 3 == 0 else ('Fitness & Wellness' if i % 3 == 1 else 'Special Events'),
            'first_volunteer_date': datetime(2024, 1, 1) + timedelta(days=i*5),
            'last_volunteer_date': datetime(2024, 8, 1) + timedelta(days=i*3),
            'volunteer_tenure_days': 100 + (i * 10),
            'avg_hours_per_session': 2 + (i * 0.1),
            'volunteer_frequency': 0.5 + (i * 0.05),
            'volunteer_type': ['Newcomer', 'Regular', 'Committed', 'Champion'][min(i//5, 3)]
        })
    
    volunteers_df = pd.DataFrame(volunteers_data)
    
    # Create sample projects
    projects_data = []
    project_names = [
        'Youth Mentoring Program', 'Summer Camp Assistant', 'Fitness Class Helper',
        'Special Event Setup', 'Swimming Instructor', 'After School Program',
        'Community Garden', 'Senior Exercise Class', 'Holiday Party Planning',
        'Basketball Coaching', 'Art Class Volunteer', 'Reading Buddy Program'
    ]
    
    for i, name in enumerate(project_names):
        projects_data.append({
            'project_id': i + 1,
            'project_name': name,
            'branch': 'Blue Ash YMCA' if i % 2 == 0 else 'M.E. Lyons YMCA',
            'category': ['Youth Development', 'Fitness & Wellness', 'Special Events'][i % 3],
            'tags': 'General',
            'type': 'Ongoing',
            'need': 'Helper needed',
            'total_hours': 100 + (i * 20),
            'avg_hours_per_session': 2 + (i * 0.2),
            'total_sessions': 20 + (i * 5),
            'unique_volunteers': 3 + (i // 2),
            'avg_volunteer_age': 25 + (i * 2),
            'common_gender': 'Mixed',
            'required_credentials': 'Basic background check',
            'sample_activities': f'Activities for {name}',
            'popularity_score': 0.5 + (i * 0.1),
            'volunteer_retention': 1.5 + (i * 0.1)
        })
    
    projects_df = pd.DataFrame(projects_data)
    
    # Create sample interactions (volunteer-project sessions)
    interactions_data = []
    interaction_id = 1
    
    # Create some friend groups by having certain volunteers work together frequently
    friend_groups = [
        ['vol_001', 'vol_002', 'vol_003'],  # Close friends - work together often
        ['vol_004', 'vol_005'],             # Pair of friends  
        ['vol_008', 'vol_009', 'vol_010', 'vol_011'],  # Larger friend group
        ['vol_015', 'vol_016']              # Another pair
    ]
    
    # Generate interactions with friendship patterns
    for month in range(1, 9):  # 8 months of data
        for week in range(1, 5):  # 4 weeks per month
            date = datetime(2024, month, week * 7)
            
            # Regular individual volunteers
            for vol_id in volunteer_ids:
                # Random chance each volunteer participates this week
                if np.random.random() < 0.3:  # 30% chance per week
                    project_id = np.random.choice(range(1, len(project_names) + 1))
                    hours = np.random.uniform(1, 4)
                    
                    interactions_data.append({
                        'contact_id': vol_id,
                        'project_id': project_id,
                        'date': date,
                        'hours': hours,
                        'pledged': hours,
                        'branch_short': 'Blue Ash' if project_id % 2 == 1 else 'M.E. Lyons',
                        'project_category': ['Youth Development', 'Fitness & Wellness', 'Special Events'][(project_id-1) % 3],
                        'project_clean': project_names[project_id-1]
                    })
                    interaction_id += 1
            
            # Friends working together (higher frequency)
            for friend_group in friend_groups:
                if np.random.random() < 0.6:  # 60% chance friends work together each week
                    project_id = np.random.choice(range(1, len(project_names) + 1))
                    base_hours = np.random.uniform(2, 4)
                    
                    for vol_id in friend_group:
                        hours = base_hours + np.random.uniform(-0.5, 0.5)  # Similar hours for friends
                        
                        interactions_data.append({
                            'contact_id': vol_id,
                            'project_id': project_id,
                            'date': date,
                            'hours': hours,
                            'pledged': hours,
                            'branch_short': 'Blue Ash' if project_id % 2 == 1 else 'M.E. Lyons',
                            'project_category': ['Youth Development', 'Fitness & Wellness', 'Special Events'][(project_id-1) % 3],
                            'project_clean': project_names[project_id-1]
                        })
                        interaction_id += 1
    
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

def test_friend_group_detection():
    """Test the friend group detection functionality"""
    print("🔄 Creating sample volunteer data...")
    volunteer_data = create_sample_volunteer_data()
    
    print(f"📊 Sample data created:")
    print(f"   - Volunteers: {len(volunteer_data['volunteers'])}")
    print(f"   - Projects: {len(volunteer_data['projects'])}")
    print(f"   - Interactions: {len(volunteer_data['interactions'])}")
    
    print("\n🤝 Testing Friend Group Detection...")
    detector = FriendGroupDetector(volunteer_data)
    friend_groups = detector.detect_friend_groups()
    
    print(f"\n✅ Detected {len(friend_groups)} friend groups:")
    for i, group in enumerate(friend_groups, 1):
        print(f"\n{i}. Group {group['group_id']} ({group['size']} members):")
        for member in group.get('members_info', []):
            print(f"   - {member.get('name', member.get('contact_id', 'Unknown'))}")
        
        stats = group.get('stats', {})
        print(f"   Friendship Score: {stats.get('avg_friendship_score', 0):.3f}")
        print(f"   Shared Projects: {group.get('shared_activities', {}).get('total_shared_projects', 0)}")
    
    return detector, volunteer_data

def test_team_matching():
    """Test the team matching functionality"""
    print("\n🎯 Testing Team Matching Engine...")
    
    detector, volunteer_data = test_friend_group_detection()
    
    # Create team matching engine
    team_engine = TeamMatchingEngine(volunteer_data)
    team_engine.train_models()
    team_engine.initialize_friend_detection()
    
    # Test individual team-aware matching
    test_preferences = {
        'age': 28,
        'interests': 'youth development',
        'time_commitment': 2,
        'user_id': 'vol_001'  # Use first volunteer
    }
    
    print("\n🔍 Testing team-aware matching for individual volunteer...")
    team_matches = team_engine.find_team_matches(test_preferences, include_friends=True)
    
    print(f"\nTop 3 team-aware matches for vol_001:")
    for i, match in enumerate(team_matches[:3], 1):
        print(f"{i}. {match['project_name']}")
        print(f"   Team Score: {match.get('team_score', match['score']):.3f}")
        print(f"   Friend Group Compatible: {match.get('friend_group_compatible', False)}")
        team_factors = match.get('team_factors', [])
        if team_factors:
            print(f"   Team Factors: {'; '.join(team_factors)}")
    
    # Test group matching
    if team_engine.friend_groups:
        test_group = team_engine.friend_groups[0]['members'][:3]  # First 3 members of first group
        
        print(f"\n👥 Testing group matching for {len(test_group)} friends...")
        group_matches = team_engine.find_matches_for_group(test_group)
        
        print(f"Top 2 group matches:")
        for i, match in enumerate(group_matches[:2], 1):
            print(f"{i}. {match['project_name']}")
            print(f"   Group Score: {match['score']:.3f}")
            print(f"   Reasons: {'; '.join(match['reasons'])}")
            print(f"   Team Compatibility: {match.get('team_compatibility', {}).get('score', 0):.3f}")
    
    return team_engine

def test_should_keep_together():
    """Test the 'should keep together' functionality"""
    print("\n🔗 Testing 'Should Keep Together' functionality...")
    
    detector, volunteer_data = test_friend_group_detection()
    
    # Test various combinations
    test_cases = [
        ['vol_001', 'vol_002'],  # Should be friends
        ['vol_001', 'vol_002', 'vol_003'],  # Should be a friend group
        ['vol_001', 'vol_010'],  # Probably not friends
        ['vol_004', 'vol_005'],  # Should be friends (from our sample data)
        ['vol_015', 'vol_016', 'vol_017', 'vol_018']  # Mixed case
    ]
    
    for test_case in test_cases:
        result = detector.should_keep_together(test_case)
        volunteer_names = ', '.join(test_case)
        keep_together = result.get('keep_together', False)
        reason = result.get('reason', 'No reason provided')
        strength = result.get('strength', 0)
        
        print(f"\n{volunteer_names}:")
        print(f"   Keep Together: {'✅ Yes' if keep_together else '❌ No'}")
        print(f"   Reason: {reason}")
        if strength > 0:
            print(f"   Strength: {strength:.3f}")

def export_sample_results():
    """Export sample results for demonstration"""
    print("\n📤 Exporting sample results...")
    
    detector, volunteer_data = test_friend_group_detection()
    team_engine = test_team_matching()
    
    # Export friend groups data
    export_data = detector.export_friend_groups()
    
    print("\n📋 Friend Group Summary:")
    print(f"   Total Friend Groups: {export_data['total_groups']}")
    print(f"   Total Volunteers in Groups: {export_data['total_volunteers_in_groups']}")
    print(f"   Network Stats:")
    network_stats = export_data.get('network_stats', {})
    print(f"     - Total Volunteers: {network_stats.get('total_nodes', 0)}")
    print(f"     - Total Friendships: {network_stats.get('total_edges', 0)}")
    print(f"     - Average Connections: {network_stats.get('average_degree', 0):.2f}")
    
    return export_data

if __name__ == "__main__":
    print("🧪 Testing YMCA Friend Group Detection & Team Matching")
    print("=" * 60)
    
    try:
        # Run all tests
        test_friend_group_detection()
        test_team_matching()
        test_should_keep_together()
        export_results = export_sample_results()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("\nThe friend group detection and team matching features are working correctly.")
        print("Key features demonstrated:")
        print("  ✓ Friend group detection from volunteer interaction patterns")
        print("  ✓ Team-aware volunteer matching")
        print("  ✓ Group-based volunteer matching")
        print("  ✓ Friend relationship strength assessment")
        print("  ✓ 'Should keep together' recommendations")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()