"""
Friend Group Detection System for YMCA Volunteer Matching
Identifies groups of volunteers who regularly work together and should be kept together when possible
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Set, Any, Optional
from collections import defaultdict, Counter
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import networkx as nx
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class FriendGroupDetector:
    def __init__(self, volunteer_data: Dict[str, Any]):
        self.volunteer_data = volunteer_data
        self.volunteers_df = volunteer_data.get('volunteers')
        self.projects_df = volunteer_data.get('projects')
        self.interactions_df = volunteer_data.get('interactions')
        
        # Friendship detection parameters
        self.min_shared_sessions = 2  # Minimum sessions together to be considered friends
        self.min_friendship_score = 0.3  # Minimum friendship score (0-1)
        self.max_friend_group_size = 6  # Maximum size of a friend group
        
        # Detected friend groups and relationships
        self.friendship_graph = nx.Graph()
        self.friend_groups = []
        self.volunteer_friendships = defaultdict(list)
        
    def detect_friend_groups(self) -> List[Dict[str, Any]]:
        """Main method to detect friend groups from volunteer data"""
        if self.interactions_df is None or len(self.interactions_df) == 0:
            logger.warning("No interaction data available for friend group detection")
            return []
        
        print("🤝 Detecting friend groups from volunteer interactions...")
        
        # Step 1: Calculate volunteer pair interactions
        pair_interactions = self._calculate_pair_interactions()
        
        # Step 2: Build friendship network
        self._build_friendship_network(pair_interactions)
        
        # Step 3: Detect friend groups using community detection
        self._detect_communities()
        
        # Step 4: Validate and enrich friend groups
        self._validate_and_enrich_groups()
        
        print(f"✅ Detected {len(self.friend_groups)} friend groups")
        return self.friend_groups
    
    def _calculate_pair_interactions(self) -> Dict[Tuple[str, str], Dict[str, Any]]:
        """Calculate interaction metrics between all pairs of volunteers"""
        print("  📊 Calculating volunteer pair interactions...")
        
        pair_interactions = defaultdict(lambda: {
            'shared_sessions': 0,
            'shared_projects': set(),
            'shared_branches': set(),
            'shared_dates': set(),
            'total_hours_together': 0,
            'first_interaction': None,
            'last_interaction': None,
            'interaction_frequency': 0
        })
        
        # Group interactions by project and date to find co-volunteers
        project_date_groups = self.interactions_df.groupby(['project_id', 'date'])
        
        for (project_id, date), group in project_date_groups:
            volunteers_in_session = group['contact_id'].unique()
            
            # Skip if only one volunteer (no pairs possible)
            if len(volunteers_in_session) < 2:
                continue
                
            # Calculate interactions for all pairs in this session
            for i, vol1 in enumerate(volunteers_in_session):
                for vol2 in volunteers_in_session[i+1:]:
                    # Create ordered pair key (smaller ID first for consistency)
                    pair_key = tuple(sorted([vol1, vol2]))
                    
                    # Update interaction metrics
                    pair_data = pair_interactions[pair_key]
                    pair_data['shared_sessions'] += 1
                    pair_data['shared_projects'].add(project_id)
                    pair_data['shared_dates'].add(date)
                    
                    # Add hours (sum of both volunteers' hours in this session)
                    vol1_hours = group[group['contact_id'] == vol1]['hours'].sum()
                    vol2_hours = group[group['contact_id'] == vol2]['hours'].sum()
                    pair_data['total_hours_together'] += min(vol1_hours, vol2_hours)  # Use minimum as actual shared time
                    
                    # Track branch information
                    if 'branch_short' in group.columns:
                        pair_data['shared_branches'].update(group['branch_short'].unique())
                    
                    # Update date range
                    if pair_data['first_interaction'] is None or date < pair_data['first_interaction']:
                        pair_data['first_interaction'] = date
                    if pair_data['last_interaction'] is None or date > pair_data['last_interaction']:
                        pair_data['last_interaction'] = date
        
        # Calculate interaction frequency (sessions per month)
        for pair_key, data in pair_interactions.items():
            if data['first_interaction'] and data['last_interaction']:
                days_span = (data['last_interaction'] - data['first_interaction']).days + 1
                data['interaction_frequency'] = (data['shared_sessions'] / max(days_span, 1)) * 30
        
        print(f"  📈 Calculated interactions for {len(pair_interactions)} volunteer pairs")
        return dict(pair_interactions)
    
    def _build_friendship_network(self, pair_interactions: Dict[Tuple[str, str], Dict[str, Any]]):
        """Build a friendship network graph from pair interactions"""
        print("  🕸️ Building friendship network...")
        
        for pair_key, interactions in pair_interactions.items():
            vol1, vol2 = pair_key
            
            # Calculate friendship score based on multiple factors
            friendship_score = self._calculate_friendship_score(interactions)
            
            # Add edge if friendship score meets threshold
            if (friendship_score >= self.min_friendship_score and 
                interactions['shared_sessions'] >= self.min_shared_sessions):
                
                self.friendship_graph.add_edge(
                    vol1, vol2, 
                    weight=friendship_score,
                    shared_sessions=interactions['shared_sessions'],
                    shared_projects=len(interactions['shared_projects']),
                    total_hours=interactions['total_hours_together'],
                    frequency=interactions['interaction_frequency']
                )
                
                # Store friendship info for quick lookup
                self.volunteer_friendships[vol1].append({
                    'friend_id': vol2,
                    'score': friendship_score,
                    'shared_sessions': interactions['shared_sessions']
                })
                self.volunteer_friendships[vol2].append({
                    'friend_id': vol1,
                    'score': friendship_score,
                    'shared_sessions': interactions['shared_sessions']
                })
        
        print(f"  🤝 Built network with {self.friendship_graph.number_of_nodes()} volunteers and {self.friendship_graph.number_of_edges()} friendships")
    
    def _calculate_friendship_score(self, interactions: Dict[str, Any]) -> float:
        """Calculate a friendship score (0-1) based on interaction patterns"""
        score = 0.0
        
        # Base score from shared sessions (40% weight)
        session_score = min(1.0, interactions['shared_sessions'] / 10.0)  # Normalize to 10 sessions = 1.0
        score += session_score * 0.4
        
        # Project diversity score (20% weight) - friends work on multiple projects together
        project_diversity = min(1.0, len(interactions['shared_projects']) / 3.0)  # 3+ projects = 1.0
        score += project_diversity * 0.2
        
        # Consistency/frequency score (20% weight)
        frequency_score = min(1.0, interactions['interaction_frequency'] / 2.0)  # 2+ times per month = 1.0
        score += frequency_score * 0.2
        
        # Duration score (10% weight) - long-term friendships
        if interactions['first_interaction'] and interactions['last_interaction']:
            duration_days = (interactions['last_interaction'] - interactions['first_interaction']).days
            duration_score = min(1.0, duration_days / 180.0)  # 6 months = 1.0
            score += duration_score * 0.1
        
        # Hours together score (10% weight)
        hours_score = min(1.0, interactions['total_hours_together'] / 20.0)  # 20+ hours = 1.0
        score += hours_score * 0.1
        
        return min(score, 1.0)
    
    def _detect_communities(self):
        """Detect friend group communities using network analysis"""
        print("  👥 Detecting friend group communities...")
        
        if self.friendship_graph.number_of_nodes() == 0:
            print("  ⚠️  No friendship connections found")
            return
        
        # Use different community detection algorithms based on graph size
        if self.friendship_graph.number_of_nodes() < 100:
            # For smaller graphs, use Louvain algorithm
            try:
                import community as community_louvain
                communities = community_louvain.best_partition(self.friendship_graph)
            except ImportError:
                # Fallback to simple connected components
                communities = {}
                for i, component in enumerate(nx.connected_components(self.friendship_graph)):
                    for node in component:
                        communities[node] = i
        else:
            # For larger graphs, use connected components to avoid performance issues
            communities = {}
            for i, component in enumerate(nx.connected_components(self.friendship_graph)):
                for node in component:
                    communities[node] = i
        
        # Group volunteers by community
        community_groups = defaultdict(list)
        for volunteer_id, community_id in communities.items():
            community_groups[community_id].append(volunteer_id)
        
        # Filter and process communities into friend groups
        for community_id, member_ids in community_groups.items():
            if len(member_ids) >= 2:  # At least 2 people for a group
                # If group is too large, break it into smaller subgroups
                if len(member_ids) > self.max_friend_group_size:
                    subgroups = self._split_large_group(member_ids)
                    for subgroup in subgroups:
                        if len(subgroup) >= 2:
                            self.friend_groups.append({
                                'group_id': f"fg_{len(self.friend_groups)}",
                                'members': subgroup,
                                'size': len(subgroup),
                                'type': 'large_split'
                            })
                else:
                    self.friend_groups.append({
                        'group_id': f"fg_{len(self.friend_groups)}",
                        'members': member_ids,
                        'size': len(member_ids),
                        'type': 'community'
                    })
    
    def _split_large_group(self, member_ids: List[str]) -> List[List[str]]:
        """Split a large friend group into smaller cohesive subgroups"""
        if len(member_ids) <= self.max_friend_group_size:
            return [member_ids]
        
        # Create subgraph of this large group
        subgraph = self.friendship_graph.subgraph(member_ids)
        
        # Find the strongest connections and build smaller groups
        subgroups = []
        remaining_members = set(member_ids)
        
        while len(remaining_members) >= 2:
            # Start with the member who has the most connections in remaining set
            start_member = max(remaining_members, 
                             key=lambda x: sum(1 for neighbor in subgraph.neighbors(x) 
                                             if neighbor in remaining_members))
            
            # Build subgroup starting from this member
            current_subgroup = [start_member]
            remaining_members.remove(start_member)
            
            # Add closest friends up to max group size
            while len(current_subgroup) < self.max_friend_group_size and remaining_members:
                # Find the member with strongest average connection to current subgroup
                best_candidate = None
                best_score = 0
                
                for candidate in remaining_members:
                    if candidate in subgraph:
                        # Calculate average friendship score with current subgroup members
                        scores = []
                        for member in current_subgroup:
                            if subgraph.has_edge(candidate, member):
                                scores.append(subgraph[candidate][member]['weight'])
                        
                        if scores:
                            avg_score = sum(scores) / len(scores)
                            if avg_score > best_score:
                                best_score = avg_score
                                best_candidate = candidate
                
                if best_candidate and best_score > self.min_friendship_score:
                    current_subgroup.append(best_candidate)
                    remaining_members.remove(best_candidate)
                else:
                    break
            
            if len(current_subgroup) >= 2:
                subgroups.append(current_subgroup)
            elif len(current_subgroup) == 1:
                # Single member left, try to add to an existing subgroup
                added = False
                for subgroup in subgroups:
                    if len(subgroup) < self.max_friend_group_size:
                        # Check if this member has connections to the subgroup
                        connections = sum(1 for member in subgroup 
                                        if subgraph.has_edge(current_subgroup[0], member))
                        if connections > 0:
                            subgroup.append(current_subgroup[0])
                            added = True
                            break
                
                if not added and len(subgroups) > 0:
                    # Add to largest existing subgroup if no connections found
                    largest_subgroup = max(subgroups, key=len)
                    if len(largest_subgroup) < self.max_friend_group_size:
                        largest_subgroup.append(current_subgroup[0])
        
        return subgroups
    
    def _validate_and_enrich_groups(self):
        """Validate friend groups and add demographic/preference information"""
        print("  ✅ Validating and enriching friend groups...")
        
        validated_groups = []
        
        for group in self.friend_groups:
            # Get member information from volunteer profiles
            member_info = []
            if self.volunteers_df is not None:
                for member_id in group['members']:
                    member_data = self.volunteers_df[self.volunteers_df['contact_id'] == member_id]
                    if not member_data.empty:
                        member_info.append({
                            'contact_id': member_id,
                            'name': f"{member_data.iloc[0].get('first_name', '')} {member_data.iloc[0].get('last_name', '')}".strip(),
                            'age': member_data.iloc[0].get('age'),
                            'total_hours': member_data.iloc[0].get('total_hours', 0),
                            'volunteer_type': member_data.iloc[0].get('volunteer_type'),
                            'home_city': member_data.iloc[0].get('home_city'),
                            'member_branch': member_data.iloc[0].get('member_branch')
                        })
            
            if len(member_info) >= 2:  # Only keep groups with at least 2 members with profile data
                # Calculate group statistics
                ages = [info['age'] for info in member_info if info['age']]
                hours = [info['total_hours'] for info in member_info if info['total_hours']]
                cities = [info['home_city'] for info in member_info if info['home_city']]
                branches = [info['member_branch'] for info in member_info if info['member_branch']]
                
                # Calculate friendship strength (average pairwise friendship scores)
                friendship_scores = []
                for i, member1 in enumerate(group['members']):
                    for member2 in group['members'][i+1:]:
                        if self.friendship_graph.has_edge(member1, member2):
                            friendship_scores.append(self.friendship_graph[member1][member2]['weight'])
                
                enriched_group = {
                    **group,
                    'members_info': member_info,
                    'stats': {
                        'avg_age': sum(ages) / len(ages) if ages else None,
                        'age_range': f"{min(ages)}-{max(ages)}" if ages else None,
                        'total_group_hours': sum(hours),
                        'avg_member_hours': sum(hours) / len(hours) if hours else 0,
                        'common_cities': Counter(cities).most_common(3) if cities else [],
                        'common_branches': Counter(branches).most_common(3) if branches else [],
                        'avg_friendship_score': sum(friendship_scores) / len(friendship_scores) if friendship_scores else 0,
                        'group_cohesion': min(friendship_scores) if friendship_scores else 0  # Weakest link
                    },
                    'shared_activities': self._get_shared_activities(group['members']),
                    'recommended_together': True
                }
                
                validated_groups.append(enriched_group)
        
        self.friend_groups = validated_groups
        print(f"  ✨ Validated {len(self.friend_groups)} friend groups with enriched data")
    
    def _get_shared_activities(self, member_ids: List[str]) -> Dict[str, Any]:
        """Get shared activities/projects for a friend group"""
        if not self.interactions_df is not None:
            return {}
        
        # Find interactions involving any group member
        group_interactions = self.interactions_df[
            self.interactions_df['contact_id'].isin(member_ids)
        ]
        
        # Find projects/activities where multiple group members participated
        project_participation = defaultdict(set)
        for _, row in group_interactions.iterrows():
            project_participation[row['project_id']].add(row['contact_id'])
        
        # Filter for activities with multiple group members
        shared_projects = {}
        for project_id, participants in project_participation.items():
            if len(participants) >= 2:  # At least 2 group members participated
                project_info = self.projects_df[
                    self.projects_df['project_id'] == project_id
                ] if self.projects_df is not None else pd.DataFrame()
                
                shared_projects[project_id] = {
                    'project_name': project_info.iloc[0]['project_name'] if not project_info.empty else f'Project {project_id}',
                    'participants': list(participants),
                    'participant_count': len(participants),
                    'branch': project_info.iloc[0].get('branch', 'Unknown') if not project_info.empty else 'Unknown',
                    'category': project_info.iloc[0].get('category', 'General') if not project_info.empty else 'General'
                }
        
        return {
            'shared_projects': shared_projects,
            'total_shared_projects': len(shared_projects),
            'most_common_categories': Counter([
                proj['category'] for proj in shared_projects.values()
            ]).most_common(3)
        }
    
    def get_friend_group_for_volunteer(self, volunteer_id: str) -> Optional[Dict[str, Any]]:
        """Get the friend group that contains a specific volunteer"""
        for group in self.friend_groups:
            if volunteer_id in group['members']:
                return group
        return None
    
    def get_volunteer_friends(self, volunteer_id: str) -> List[Dict[str, Any]]:
        """Get direct friends for a specific volunteer"""
        return self.volunteer_friendships.get(volunteer_id, [])
    
    def should_keep_together(self, volunteer_ids: List[str]) -> Dict[str, Any]:
        """Check if a set of volunteers should be kept together and why"""
        if len(volunteer_ids) < 2:
            return {'keep_together': False, 'reason': 'Not enough volunteers'}
        
        # Check if all volunteers are in the same friend group
        groups = []
        for vol_id in volunteer_ids:
            group = self.get_friend_group_for_volunteer(vol_id)
            if group:
                groups.append(group['group_id'])
        
        if len(set(groups)) == 1 and len(groups) == len(volunteer_ids):
            # All volunteers are in the same friend group
            group = self.get_friend_group_for_volunteer(volunteer_ids[0])
            return {
                'keep_together': True,
                'reason': 'All volunteers are in the same friend group',
                'group_info': group,
                'strength': group['stats']['avg_friendship_score']
            }
        
        # Check for partial friend group overlap
        friendship_scores = []
        for i, vol1 in enumerate(volunteer_ids):
            for vol2 in volunteer_ids[i+1:]:
                if self.friendship_graph.has_edge(vol1, vol2):
                    friendship_scores.append(self.friendship_graph[vol1][vol2]['weight'])
        
        if friendship_scores:
            avg_score = sum(friendship_scores) / len(friendship_scores)
            if avg_score >= self.min_friendship_score:
                return {
                    'keep_together': True,
                    'reason': 'Strong friendship connections detected',
                    'strength': avg_score,
                    'connected_pairs': len(friendship_scores)
                }
        
        return {'keep_together': False, 'reason': 'No strong friendship connections found'}
    
    def export_friend_groups(self) -> Dict[str, Any]:
        """Export friend groups data for use in other systems"""
        return {
            'friend_groups': self.friend_groups,
            'total_groups': len(self.friend_groups),
            'total_volunteers_in_groups': sum(group['size'] for group in self.friend_groups),
            'network_stats': {
                'total_nodes': self.friendship_graph.number_of_nodes(),
                'total_edges': self.friendship_graph.number_of_edges(),
                'average_degree': sum(dict(self.friendship_graph.degree()).values()) / max(self.friendship_graph.number_of_nodes(), 1)
            },
            'generated_at': datetime.now().isoformat()
        }

# Example usage
if __name__ == "__main__":
    from data_processor import VolunteerDataProcessor
    
    # Load volunteer data
    processor = VolunteerDataProcessor("Y Volunteer Raw Data - Jan- August 2025.xlsx")
    volunteer_data = processor.get_volunteer_recommendations_data()
    
    # Detect friend groups
    detector = FriendGroupDetector(volunteer_data)
    friend_groups = detector.detect_friend_groups()
    
    # Print results
    print(f"\n🎯 DETECTED {len(friend_groups)} FRIEND GROUPS:")
    for group in friend_groups:
        print(f"\nGroup {group['group_id']} ({group['size']} members):")
        for member in group['members_info']:
            print(f"  - {member['name']} ({member['volunteer_type']})")
        print(f"  Avg Friendship Score: {group['stats']['avg_friendship_score']:.3f}")
        print(f"  Shared Projects: {group['shared_activities']['total_shared_projects']}")
    
    # Export data
    export_data = detector.export_friend_groups()
    print(f"\n📊 Total volunteers in friend groups: {export_data['total_volunteers_in_groups']}")