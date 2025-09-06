"""
Enhanced Team Matching Engine for YMCA Volunteers
Extends the base matching engine to keep friend groups together when possible
"""
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np
from matching_engine import VolunteerMatchingEngine
from friend_group_detector import FriendGroupDetector
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class TeamMatchingEngine(VolunteerMatchingEngine):
    def __init__(self, volunteer_data: Dict[str, Any]):
        super().__init__(volunteer_data)
        
        # Initialize friend group detection
        self.friend_detector = FriendGroupDetector(volunteer_data)
        self.friend_groups = []
        self.friend_group_index = {}  # volunteer_id -> group_id mapping
        self.team_preferences = {}  # Store team matching preferences
        
        # Team matching parameters
        self.friend_group_bonus = 0.15  # Score bonus for keeping friends together
        self.max_team_size = 8  # Maximum team size for projects
        self.min_team_size = 2  # Minimum team size for team-based projects
        
        print("🤝 Initializing Team Matching Engine with friend group detection...")
        
    def initialize_friend_detection(self):
        """Initialize and run friend group detection"""
        try:
            self.friend_groups = self.friend_detector.detect_friend_groups()
            
            # Build index for quick lookup
            for group in self.friend_groups:
                for member_id in group['members']:
                    self.friend_group_index[member_id] = group['group_id']
            
            print(f"✅ Initialized with {len(self.friend_groups)} friend groups")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize friend detection: {e}")
            return False
    
    def find_team_matches(self, user_preferences: Dict[str, Any], 
                         include_friends: bool = True, 
                         team_size_preference: str = 'any',
                         top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find volunteer matches with team/friend group awareness
        
        Args:
            user_preferences: User's volunteer preferences
            include_friends: Whether to prioritize keeping friend groups together
            team_size_preference: 'small' (2-4), 'medium' (4-6), 'large' (6+), or 'any'
            top_k: Number of recommendations to return
        """
        # Initialize friend groups if not already done
        if not self.friend_groups:
            self.initialize_friend_detection()
        
        # Get base matches from parent class
        base_matches = super().find_matches(user_preferences, top_k * 2)  # Get more to allow for team filtering
        
        if not include_friends:
            return base_matches[:top_k]
        
        # Enhance matches with team/friend group information
        enhanced_matches = []
        
        for match in base_matches:
            enhanced_match = match.copy()
            
            # Add team matching information
            team_info = self._calculate_team_compatibility(
                user_preferences, match, team_size_preference
            )
            enhanced_match.update(team_info)
            
            enhanced_matches.append(enhanced_match)
        
        # Sort by enhanced score that includes team factors
        enhanced_matches.sort(key=lambda x: x.get('team_score', x.get('score', 0)), reverse=True)
        
        return enhanced_matches[:top_k]
    
    def find_matches_for_group(self, group_members: List[str], 
                              shared_preferences: Dict[str, Any] = None,
                              top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find matches for an entire friend group trying to volunteer together
        
        Args:
            group_members: List of volunteer IDs in the friend group
            shared_preferences: Common preferences for the group
            top_k: Number of project recommendations
        """
        if not group_members or len(group_members) < 2:
            return []
        
        print(f"🎯 Finding matches for friend group of {len(group_members)} volunteers...")
        
        # If no shared preferences provided, derive from group member history
        if not shared_preferences:
            shared_preferences = self._derive_group_preferences(group_members)
        
        # Get individual preferences for each group member
        individual_prefs = []
        for member_id in group_members:
            member_prefs = self._get_member_preferences_from_history(member_id)
            individual_prefs.append(member_prefs)
        
        # Find projects that can accommodate the group size
        suitable_projects = self._filter_projects_by_group_size(len(group_members))
        
        # Score each suitable project for the group
        group_matches = []
        for _, project in suitable_projects.iterrows():
            group_score = self._calculate_group_project_score(
                group_members, individual_prefs, shared_preferences, project
            )
            
            if group_score > 0:
                match_info = {
                    'project_id': project['project_id'],
                    'project_name': project['project_name'],
                    'branch': project['branch'],
                    'category': project['category'],
                    'score': group_score,
                    'group_size': len(group_members),
                    'group_members': group_members,
                    'reasons': self._explain_group_match(shared_preferences, project, group_members),
                    'team_compatibility': self._assess_team_compatibility(group_members, project),
                    'requirements': project.get('required_credentials', 'Basic volunteer requirements'),
                    'time_commitment': self._describe_time_commitment(project),
                    'volunteer_count': project.get('unique_volunteers', 0),
                    'avg_hours': project.get('avg_hours_per_session', 0),
                    'group_benefits': self._describe_group_benefits(len(group_members), project)
                }
                group_matches.append(match_info)
        
        # Sort and return top matches
        group_matches.sort(key=lambda x: x['score'], reverse=True)
        return group_matches[:top_k]
    
    def _calculate_team_compatibility(self, user_preferences: Dict[str, Any], 
                                    project: Dict[str, Any], 
                                    team_size_preference: str) -> Dict[str, Any]:
        """Calculate team compatibility factors for a project match"""
        team_score = project.get('score', 0)
        team_factors = []
        
        # Check if user has friends who might join
        user_id = user_preferences.get('user_id')  # Assume user_id is passed in preferences
        if user_id and user_id in self.friend_group_index:
            group_id = self.friend_group_index[user_id]
            friend_group = next((g for g in self.friend_groups if g['group_id'] == group_id), None)
            
            if friend_group:
                group_size = friend_group['size']
                
                # Check if project can accommodate the friend group
                project_capacity = self._estimate_project_capacity(project)
                if project_capacity >= group_size:
                    team_score += self.friend_group_bonus
                    team_factors.append(f"Can accommodate your friend group of {group_size}")
                    
                    # Additional bonus for well-matched team size preference
                    if team_size_preference == 'small' and group_size <= 4:
                        team_score += 0.05
                    elif team_size_preference == 'medium' and 4 <= group_size <= 6:
                        team_score += 0.05
                    elif team_size_preference == 'large' and group_size >= 6:
                        team_score += 0.05
                
                # Add information about friends' interests
                friend_interests = self._get_group_interests(friend_group['members'])
                if friend_interests:
                    common_interests = self._find_common_interests(
                        user_preferences.get('interests', ''), friend_interests
                    )
                    if common_interests:
                        team_factors.append(f"Shared interests with friends: {', '.join(common_interests)}")
        
        # Check project's team-friendliness
        avg_volunteers = project.get('unique_volunteers', 1)
        if avg_volunteers > 1:
            team_factors.append(f"Popular with teams (avg {avg_volunteers} volunteers)")
            team_score += 0.02
        
        # Look for team-oriented language in project description
        project_name = str(project.get('project_name', '')).lower()
        team_keywords = ['team', 'group', 'together', 'collaborative', 'crew', 'squad']
        if any(keyword in project_name for keyword in team_keywords):
            team_factors.append("Team-oriented project")
            team_score += 0.03
        
        return {
            'team_score': min(team_score, 1.0),
            'team_factors': team_factors,
            'friend_group_compatible': len(team_factors) > 0,
            'estimated_team_size': self._estimate_project_team_size(project)
        }
    
    def _derive_group_preferences(self, group_members: List[str]) -> Dict[str, Any]:
        """Derive shared preferences for a friend group based on their history"""
        if not self.interactions_df is not None:
            return {'interests': 'general', 'time_commitment': 2}
        
        # Get interactions for all group members
        group_interactions = self.interactions_df[
            self.interactions_df['contact_id'].isin(group_members)
        ]
        
        if group_interactions.empty:
            return {'interests': 'general', 'time_commitment': 2}
        
        # Find common preferences
        common_categories = group_interactions['project_category'].value_counts()
        common_branches = group_interactions.get('branch_short', pd.Series()).value_counts()
        
        # Calculate average time commitment
        avg_hours = group_interactions['hours'].mean()
        time_commitment = 1 if avg_hours < 2 else (3 if avg_hours > 4 else 2)
        
        # Determine experience level based on collective sessions
        total_sessions = group_interactions.shape[0]
        experience_level = min(3, max(1, total_sessions // 10))
        
        return {
            'interests': ', '.join(common_categories.head(3).index.tolist()),
            'time_commitment': time_commitment,
            'location_preference': common_branches.index[0] if not common_branches.empty else 'any',
            'experience_level': experience_level,
            'group_size': len(group_members)
        }
    
    def _get_member_preferences_from_history(self, member_id: str) -> Dict[str, Any]:
        """Get individual member preferences from their volunteer history"""
        if self.interactions_df is None:
            return {}
        
        member_interactions = self.interactions_df[
            self.interactions_df['contact_id'] == member_id
        ]
        
        if member_interactions.empty:
            return {}
        
        return {
            'favorite_categories': member_interactions['project_category'].value_counts().head(3).to_dict(),
            'preferred_branches': member_interactions.get('branch_short', pd.Series()).value_counts().head(2).to_dict(),
            'avg_hours_per_session': member_interactions['hours'].mean(),
            'total_sessions': len(member_interactions)
        }
    
    def _filter_projects_by_group_size(self, group_size: int) -> pd.DataFrame:
        """Filter projects that can accommodate the given group size"""
        if self.project_features.empty:
            return pd.DataFrame()
        
        # Look for projects that historically had group participation
        suitable_projects = self.project_features[
            self.project_features['unique_volunteers'] >= group_size * 0.5  # Projects that had at least half the group size
        ].copy()
        
        # Add capacity estimation
        suitable_projects['estimated_capacity'] = suitable_projects.apply(
            self._estimate_project_capacity, axis=1
        )
        
        # Filter by estimated capacity
        return suitable_projects[suitable_projects['estimated_capacity'] >= group_size]
    
    def _calculate_group_project_score(self, group_members: List[str], 
                                     individual_prefs: List[Dict[str, Any]], 
                                     shared_preferences: Dict[str, Any], 
                                     project: pd.Series) -> float:
        """Calculate how well a project matches a friend group"""
        base_score = 0.0
        
        # Calculate average individual match scores
        individual_scores = []
        for member_prefs in individual_prefs:
            if member_prefs:
                member_score = self._calculate_member_project_match(member_prefs, project)
                individual_scores.append(member_score)
        
        if individual_scores:
            base_score = sum(individual_scores) / len(individual_scores)
        
        # Apply group-specific bonuses
        group_bonuses = 0.0
        
        # Project capacity bonus
        project_capacity = self._estimate_project_capacity(project)
        if project_capacity >= len(group_members):
            group_bonuses += 0.1
        
        # Historical group participation bonus
        if project.get('unique_volunteers', 0) > len(group_members):
            group_bonuses += 0.05
        
        # Category alignment bonus
        project_category = project.get('category', '').lower()
        shared_interests = shared_preferences.get('interests', '').lower()
        if project_category in shared_interests:
            group_bonuses += 0.08
        
        # Time commitment alignment
        project_hours = project.get('avg_hours_per_session', 2)
        preferred_time = shared_preferences.get('time_commitment', 2)
        time_diff = abs(project_hours - preferred_time)
        if time_diff <= 1:
            group_bonuses += 0.05
        
        # Friends working together bonus
        group_bonuses += self.friend_group_bonus
        
        return min(base_score + group_bonuses, 1.0)
    
    def _calculate_member_project_match(self, member_prefs: Dict[str, Any], 
                                      project: pd.Series) -> float:
        """Calculate how well a project matches an individual member"""
        score = 0.5  # Base score
        
        # Category matching
        favorite_categories = member_prefs.get('favorite_categories', {})
        project_category = project.get('category', '')
        if project_category in favorite_categories:
            score += 0.3 * (favorite_categories[project_category] / sum(favorite_categories.values()))
        
        # Branch matching
        preferred_branches = member_prefs.get('preferred_branches', {})
        project_branch = project.get('branch', '')
        if project_branch in preferred_branches:
            score += 0.2 * (preferred_branches[project_branch] / sum(preferred_branches.values()))
        
        return min(score, 1.0)
    
    def _explain_group_match(self, shared_preferences: Dict[str, Any], 
                           project: pd.Series, group_members: List[str]) -> List[str]:
        """Generate explanations for why a project is good for a friend group"""
        reasons = []
        
        # Group size compatibility
        project_capacity = self._estimate_project_capacity(project)
        if project_capacity >= len(group_members):
            reasons.append(f"Can accommodate your group of {len(group_members)} friends")
        
        # Shared interests
        shared_interests = shared_preferences.get('interests', '')
        project_category = project.get('category', '')
        if project_category.lower() in shared_interests.lower():
            reasons.append(f"Matches your group's interest in {project_category.lower()}")
        
        # Historical success
        unique_volunteers = project.get('unique_volunteers', 0)
        if unique_volunteers > len(group_members):
            reasons.append("Popular with volunteer groups")
        
        # Team-friendly project
        project_name = str(project.get('project_name', '')).lower()
        if any(word in project_name for word in ['team', 'group', 'together']):
            reasons.append("Designed for team participation")
        
        # Location convenience
        project_branch = project.get('branch', '')
        if shared_preferences.get('location_preference') == project_branch:
            reasons.append(f"Convenient location at {project_branch}")
        
        if not reasons:
            reasons.append("Good fit for volunteering with friends")
            
        return reasons[:4]  # Return top 4 reasons
    
    def _assess_team_compatibility(self, group_members: List[str], 
                                 project: pd.Series) -> Dict[str, Any]:
        """Assess how well the team will work together on this project"""
        compatibility = {
            'score': 0.7,  # Base compatibility
            'factors': [],
            'potential_challenges': []
        }
        
        # Check friend group strength
        if len(group_members) >= 2:
            group = self.friend_detector.get_friend_group_for_volunteer(group_members[0])
            if group:
                avg_friendship = group['stats'].get('avg_friendship_score', 0)
                compatibility['score'] = min(1.0, 0.5 + avg_friendship * 0.5)
                compatibility['factors'].append(f"Strong friend group (score: {avg_friendship:.2f})")
                
                if avg_friendship < 0.5:
                    compatibility['potential_challenges'].append("Some members may not know each other well")
        
        # Check experience levels
        experience_levels = []
        for member_id in group_members:
            if self.volunteers_df is not None:
                member_data = self.volunteers_df[self.volunteers_df['contact_id'] == member_id]
                if not member_data.empty:
                    volunteer_type = member_data.iloc[0].get('volunteer_type', 'Newcomer')
                    experience_levels.append(volunteer_type)
        
        if experience_levels:
            unique_levels = len(set(experience_levels))
            if unique_levels == 1:
                compatibility['factors'].append("Similar experience levels")
            elif unique_levels <= 2:
                compatibility['factors'].append("Complementary experience levels")
            else:
                compatibility['potential_challenges'].append("Very diverse experience levels")
        
        return compatibility
    
    def _estimate_project_capacity(self, project: pd.Series) -> int:
        """Estimate how many volunteers a project can accommodate"""
        # Use historical data to estimate capacity
        unique_volunteers = project.get('unique_volunteers', 1)
        avg_hours_per_session = project.get('avg_hours_per_session', 2)
        
        # Projects with more volunteers historically can likely take more
        base_capacity = max(2, unique_volunteers)
        
        # Longer session projects might accommodate more volunteers
        if avg_hours_per_session > 4:
            base_capacity = int(base_capacity * 1.2)
        
        # Check project type for capacity hints
        project_name = str(project.get('project_name', '')).lower()
        category = str(project.get('category', '')).lower()
        
        # Some project types naturally accommodate more volunteers
        if any(word in project_name + ' ' + category for word in ['event', 'festival', 'cleanup', 'drive']):
            base_capacity = max(base_capacity, 8)
        elif any(word in project_name + ' ' + category for word in ['mentoring', 'tutoring', 'coaching']):
            base_capacity = min(base_capacity, 4)  # More personal projects
        
        return min(base_capacity, self.max_team_size)
    
    def _estimate_project_team_size(self, project: Dict[str, Any]) -> str:
        """Estimate the typical team size for a project"""
        capacity = self._estimate_project_capacity(project)
        
        if capacity <= 2:
            return "Individual/Pair (1-2 people)"
        elif capacity <= 4:
            return "Small team (2-4 people)"
        elif capacity <= 6:
            return "Medium team (4-6 people)"
        else:
            return "Large team (6+ people)"
    
    def _get_group_interests(self, member_ids: List[str]) -> List[str]:
        """Get common interests for a friend group"""
        if not self.interactions_df is not None:
            return []
        
        group_interactions = self.interactions_df[
            self.interactions_df['contact_id'].isin(member_ids)
        ]
        
        if group_interactions.empty:
            return []
        
        return group_interactions['project_category'].value_counts().head(3).index.tolist()
    
    def _find_common_interests(self, user_interests: str, friend_interests: List[str]) -> List[str]:
        """Find common interests between user and their friends"""
        user_keywords = [word.strip().lower() for word in user_interests.split(',')]
        friend_keywords = [interest.lower() for interest in friend_interests]
        
        common = []
        for user_keyword in user_keywords:
            for friend_keyword in friend_keywords:
                if user_keyword in friend_keyword or friend_keyword in user_keyword:
                    common.append(friend_keyword)
        
        return list(set(common))
    
    def _describe_group_benefits(self, group_size: int, project: pd.Series) -> List[str]:
        """Describe the benefits of volunteering as a group for this project"""
        benefits = []
        
        if group_size >= 2:
            benefits.append("Share the experience with friends")
            benefits.append("Mutual support and encouragement")
        
        if group_size >= 4:
            benefits.append("Can take on larger project components")
            benefits.append("More diverse skills and perspectives")
        
        # Project-specific benefits
        category = project.get('category', '').lower()
        if 'event' in category:
            benefits.append("More fun with friends at events")
        elif 'youth' in category:
            benefits.append("Provide better mentorship as a team")
        elif 'fitness' in category:
            benefits.append("Motivate each other during activities")
        
        return benefits[:3]  # Return top 3 benefits
    
    def get_team_recommendations_for_project(self, project_id: int, 
                                           existing_volunteers: List[str] = None) -> Dict[str, Any]:
        """Get team recommendations for a specific project"""
        if not self.projects_df is not None:
            return {}
        
        project_data = self.projects_df[self.projects_df['project_id'] == project_id]
        if project_data.empty:
            return {}
        
        project = project_data.iloc[0]
        existing_volunteers = existing_volunteers or []
        
        recommendations = {
            'project_id': project_id,
            'project_name': project.get('project_name', ''),
            'optimal_team_size': self._calculate_optimal_team_size(project),
            'current_volunteers': len(existing_volunteers),
            'friend_group_opportunities': [],
            'individual_recommendations': []
        }
        
        # Look for friend groups that would fit well
        for group in self.friend_groups:
            if group['size'] <= recommendations['optimal_team_size'] - len(existing_volunteers):
                group_score = self._calculate_group_project_score(
                    group['members'], [], {}, project
                )
                
                if group_score > 0.6:  # Good match threshold
                    recommendations['friend_group_opportunities'].append({
                        'group_id': group['group_id'],
                        'group_size': group['size'],
                        'members': group['members_info'],
                        'compatibility_score': group_score,
                        'reasons': self._explain_group_match({}, project, group['members'])
                    })
        
        return recommendations
    
    def _calculate_optimal_team_size(self, project: pd.Series) -> int:
        """Calculate optimal team size for a project"""
        base_size = project.get('unique_volunteers', 2)
        project_hours = project.get('avg_hours_per_session', 2)
        
        # Adjust based on project characteristics
        if project_hours > 4:  # Longer projects can use more volunteers
            optimal_size = min(base_size + 2, self.max_team_size)
        else:
            optimal_size = base_size
        
        return max(self.min_team_size, min(optimal_size, self.max_team_size))

# Example usage
if __name__ == "__main__":
    from data_processor import VolunteerDataProcessor
    
    # Load volunteer data
    processor = VolunteerDataProcessor("Y Volunteer Raw Data - Jan- August 2025.xlsx")
    volunteer_data = processor.get_volunteer_recommendations_data()
    
    # Create team matching engine
    team_engine = TeamMatchingEngine(volunteer_data)
    team_engine.initialize_friend_detection()
    
    # Test team matching
    test_preferences = {
        'age': 28,
        'interests': 'youth development',
        'time_commitment': 2,
        'user_id': list(volunteer_data['volunteers']['contact_id'])[0]  # Use first volunteer as test
    }
    
    # Find team-aware matches
    team_matches = team_engine.find_team_matches(test_preferences, include_friends=True)
    
    print("🎯 TEAM-AWARE MATCHES:")
    for i, match in enumerate(team_matches[:3], 1):
        print(f"\n{i}. {match['project_name']}")
        print(f"   Score: {match.get('team_score', match['score']):.3f}")
        print(f"   Team Factors: {', '.join(match.get('team_factors', ['None']))}")
        print(f"   Friend Group Compatible: {match.get('friend_group_compatible', False)}")
    
    # Test group matching
    if team_engine.friend_groups:
        test_group = team_engine.friend_groups[0]['members']
        group_matches = team_engine.find_matches_for_group(test_group[:3])  # Test with first 3 members
        
        print(f"\n🤝 GROUP MATCHES FOR {len(test_group[:3])} FRIENDS:")
        for i, match in enumerate(group_matches[:2], 1):
            print(f"\n{i}. {match['project_name']}")
            print(f"   Score: {match['score']:.3f}")
            print(f"   Reasons: {', '.join(match['reasons'])}")
            print(f"   Team Compatibility: {match['team_compatibility']['score']:.3f}")