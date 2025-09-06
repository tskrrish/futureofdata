"""
Volunteer Routing Optimizer for Enhanced Coverage
Provides better fit swap suggestions and optimized volunteer routing
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
import itertools
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

@dataclass
class VolunteerAssignment:
    """Represents a volunteer assignment"""
    volunteer_id: str
    project_id: str
    branch: str
    fit_score: float
    commitment_level: float
    skills_match: float
    availability_match: float

@dataclass
class SwapSuggestion:
    """Represents a swap suggestion between volunteers"""
    volunteer_1_id: str
    volunteer_2_id: str
    project_1_id: str
    project_2_id: str
    current_total_score: float
    proposed_total_score: float
    improvement_score: float
    swap_reasons: List[str]
    volunteer_1_improvement: float
    volunteer_2_improvement: float

class VolunteerRoutingOptimizer:
    def __init__(self, volunteer_data: Dict[str, Any]):
        self.volunteer_data = volunteer_data
        self.volunteers_df = volunteer_data.get('volunteers')
        self.projects_df = volunteer_data.get('projects')
        self.interactions_df = volunteer_data.get('interactions')
        self.insights = volunteer_data.get('insights', {})
        
        # Optimization parameters
        self.scaler = StandardScaler()
        self.optimization_weights = {
            'skill_match': 0.35,
            'availability_match': 0.25,
            'location_preference': 0.20,
            'experience_level': 0.15,
            'volunteer_retention': 0.05
        }
        
        # Prepare optimization data
        self._prepare_optimization_data()
    
    def _prepare_optimization_data(self):
        """Prepare data structures for optimization algorithms"""
        if self.volunteers_df is None or self.projects_df is None:
            print("⚠️  Warning: Missing volunteer or project data for optimization")
            return
        
        print("🔧 Preparing optimization data...")
        
        # Create volunteer feature matrices
        self.volunteer_features = self._create_volunteer_feature_matrix()
        self.project_features = self._create_project_feature_matrix()
        
        # Create compatibility matrix
        self.compatibility_matrix = self._calculate_compatibility_matrix()
        
        print("✅ Optimization data preparation complete!")
    
    def _create_volunteer_feature_matrix(self) -> pd.DataFrame:
        """Create standardized feature matrix for volunteers"""
        features = self.volunteers_df.copy()
        
        # Numerical features
        numerical_features = ['age', 'total_hours', 'volunteer_sessions', 'unique_projects',
                            'volunteer_tenure_days', 'avg_hours_per_session', 'volunteer_frequency']
        
        for feature in numerical_features:
            if feature in features.columns:
                features[feature] = features[feature].fillna(features[feature].median())
        
        # Categorical encoding for skills/interests
        features['skills_youth'] = features['project_categories'].str.contains('Youth', na=False).astype(int)
        features['skills_fitness'] = features['project_categories'].str.contains('Fitness', na=False).astype(int)
        features['skills_events'] = features['project_categories'].str.contains('Events', na=False).astype(int)
        features['skills_admin'] = features['project_categories'].str.contains('Administrative', na=False).astype(int)
        
        # Experience level encoding
        experience_mapping = {'Newcomer': 1, 'Explorer': 2, 'Regular': 3, 'Committed': 4, 'Champion': 5}
        features['experience_level'] = features['volunteer_type'].map(experience_mapping).fillna(2)
        
        # Location preference (based on previous branches)
        features['prefers_blue_ash'] = features['branches_volunteered'].str.contains('Blue Ash', na=False).astype(int)
        features['prefers_lyons'] = features['branches_volunteered'].str.contains('Lyons', na=False).astype(int)
        features['prefers_campbell'] = features['branches_volunteered'].str.contains('Campbell', na=False).astype(int)
        features['prefers_clippard'] = features['branches_volunteered'].str.contains('Clippard', na=False).astype(int)
        
        # Commitment level (based on engagement patterns)
        features['commitment_level'] = np.where(
            features['avg_hours_per_session'] >= 4, 3,
            np.where(features['avg_hours_per_session'] >= 2, 2, 1)
        )
        
        return features
    
    def _create_project_feature_matrix(self) -> pd.DataFrame:
        """Create standardized feature matrix for projects"""
        features = self.projects_df.copy()
        
        # Project requirements encoding
        features['requires_youth_skills'] = features['category'].str.contains('Youth', na=False).astype(int)
        features['requires_fitness_skills'] = features['category'].str.contains('Fitness', na=False).astype(int)
        features['requires_event_skills'] = features['category'].str.contains('Events', na=False).astype(int)
        features['requires_admin_skills'] = features['category'].str.contains('Administrative', na=False).astype(int)
        
        # Time commitment requirements
        features['time_commitment_required'] = np.where(
            features['avg_hours_per_session'] >= 4, 3,
            np.where(features['avg_hours_per_session'] >= 2, 2, 1)
        )
        
        # Experience requirements (based on project complexity)
        features['experience_required'] = np.where(
            features['required_credentials'].str.contains('background|training|certification', na=False, case=False), 3,
            np.where(features['unique_volunteers'] <= 5, 1, 2)  # New projects need less experience
        )
        
        # Branch encoding
        features['at_blue_ash'] = features['branch'].str.contains('Blue Ash', na=False).astype(int)
        features['at_lyons'] = features['branch'].str.contains('Lyons', na=False).astype(int)
        features['at_campbell'] = features['branch'].str.contains('Campbell', na=False).astype(int)
        features['at_clippard'] = features['branch'].str.contains('Clippard', na=False).astype(int)
        
        # Project urgency/priority (based on volunteer gaps)
        median_volunteers = features['unique_volunteers'].median()
        features['priority_score'] = np.where(
            features['unique_volunteers'] < median_volunteers * 0.5, 3,
            np.where(features['unique_volunteers'] < median_volunteers, 2, 1)
        )
        
        return features
    
    def _calculate_compatibility_matrix(self) -> pd.DataFrame:
        """Calculate compatibility scores between volunteers and projects"""
        if self.volunteer_features.empty or self.project_features.empty:
            return pd.DataFrame()
        
        compatibility_scores = []
        
        for _, volunteer in self.volunteer_features.iterrows():
            volunteer_scores = []
            
            for _, project in self.project_features.iterrows():
                score = self._calculate_volunteer_project_compatibility(volunteer, project)
                volunteer_scores.append(score)
            
            compatibility_scores.append(volunteer_scores)
        
        compatibility_matrix = pd.DataFrame(
            compatibility_scores,
            index=self.volunteer_features['contact_id'],
            columns=self.project_features['project_id']
        )
        
        return compatibility_matrix
    
    def _calculate_volunteer_project_compatibility(self, volunteer: pd.Series, project: pd.Series) -> float:
        """Calculate compatibility score between a volunteer and project"""
        score = 0.0
        
        # Skill matching
        skill_match = (
            volunteer['skills_youth'] * project['requires_youth_skills'] +
            volunteer['skills_fitness'] * project['requires_fitness_skills'] +
            volunteer['skills_events'] * project['requires_event_skills'] +
            volunteer['skills_admin'] * project['requires_admin_skills']
        )
        score += skill_match * self.optimization_weights['skill_match']
        
        # Time commitment matching
        time_diff = abs(volunteer['commitment_level'] - project['time_commitment_required'])
        time_score = max(0, 1 - (time_diff / 3))  # Normalize to 0-1
        score += time_score * self.optimization_weights['availability_match']
        
        # Location preference matching
        location_match = (
            volunteer['prefers_blue_ash'] * project['at_blue_ash'] +
            volunteer['prefers_lyons'] * project['at_lyons'] +
            volunteer['prefers_campbell'] * project['at_campbell'] +
            volunteer['prefers_clippard'] * project['at_clippard']
        )
        # If no location preference, give neutral score
        if volunteer[['prefers_blue_ash', 'prefers_lyons', 'prefers_campbell', 'prefers_clippard']].sum() == 0:
            location_match = 0.5
        score += location_match * self.optimization_weights['location_preference']
        
        # Experience level matching
        exp_diff = abs(volunteer['experience_level'] - project['experience_required'])
        exp_score = max(0, 1 - (exp_diff / 4))  # Normalize to 0-1
        score += exp_score * self.optimization_weights['experience_level']
        
        # Project priority bonus (higher priority projects get slight preference)
        priority_bonus = project['priority_score'] / 10  # Small bonus
        score += priority_bonus * self.optimization_weights['volunteer_retention']
        
        return min(score, 1.0)  # Cap at 1.0
    
    def get_current_assignments(self) -> List[VolunteerAssignment]:
        """Get current volunteer assignments based on interaction data"""
        if self.interactions_df is None:
            return []
        
        # Get most recent assignments for each volunteer
        current_assignments = []
        latest_interactions = self.interactions_df.sort_values('date').groupby('contact_id').tail(1)
        
        for _, interaction in latest_interactions.iterrows():
            volunteer_id = interaction['contact_id']
            project_id = interaction['project_id']
            
            # Calculate fit score for current assignment
            if volunteer_id in self.compatibility_matrix.index and project_id in self.compatibility_matrix.columns:
                fit_score = self.compatibility_matrix.loc[volunteer_id, project_id]
            else:
                fit_score = 0.5  # Default neutral score
            
            assignment = VolunteerAssignment(
                volunteer_id=volunteer_id,
                project_id=project_id,
                branch=interaction.get('branch_short', 'Unknown'),
                fit_score=fit_score,
                commitment_level=interaction.get('hours', 2),
                skills_match=fit_score * 0.7,  # Approximate
                availability_match=fit_score * 0.3  # Approximate
            )
            current_assignments.append(assignment)
        
        return current_assignments
    
    def generate_swap_suggestions(self, top_k: int = 10) -> List[SwapSuggestion]:
        """Generate better fit swap suggestions between volunteers"""
        print(f"🔄 Generating top {top_k} swap suggestions...")
        
        current_assignments = self.get_current_assignments()
        if len(current_assignments) < 2:
            return []
        
        swap_suggestions = []
        
        # Compare all pairs of volunteers for potential swaps
        for i, assignment1 in enumerate(current_assignments):
            for j, assignment2 in enumerate(current_assignments[i+1:], i+1):
                if assignment1.volunteer_id == assignment2.volunteer_id:
                    continue
                
                suggestion = self._evaluate_swap(assignment1, assignment2)
                if suggestion and suggestion.improvement_score > 0.05:  # Only suggest meaningful improvements
                    swap_suggestions.append(suggestion)
        
        # Sort by improvement score and return top suggestions
        swap_suggestions.sort(key=lambda x: x.improvement_score, reverse=True)
        
        print(f"✅ Generated {len(swap_suggestions[:top_k])} swap suggestions")
        return swap_suggestions[:top_k]
    
    def _evaluate_swap(self, assignment1: VolunteerAssignment, assignment2: VolunteerAssignment) -> Optional[SwapSuggestion]:
        """Evaluate if swapping two volunteers would improve overall fit"""
        v1_id = assignment1.volunteer_id
        v2_id = assignment2.volunteer_id
        p1_id = assignment1.project_id
        p2_id = assignment2.project_id
        
        # Check if we have compatibility data for all combinations
        if (v1_id not in self.compatibility_matrix.index or 
            v2_id not in self.compatibility_matrix.index or
            p1_id not in self.compatibility_matrix.columns or
            p2_id not in self.compatibility_matrix.columns):
            return None
        
        # Current scores
        current_v1_p1 = self.compatibility_matrix.loc[v1_id, p1_id]
        current_v2_p2 = self.compatibility_matrix.loc[v2_id, p2_id]
        current_total = current_v1_p1 + current_v2_p2
        
        # Proposed scores (after swap)
        proposed_v1_p2 = self.compatibility_matrix.loc[v1_id, p2_id]
        proposed_v2_p1 = self.compatibility_matrix.loc[v2_id, p1_id]
        proposed_total = proposed_v1_p2 + proposed_v2_p1
        
        improvement = proposed_total - current_total
        
        if improvement <= 0:
            return None
        
        # Generate reasons for the swap
        reasons = self._generate_swap_reasons(v1_id, v2_id, p1_id, p2_id, 
                                            current_v1_p1, current_v2_p2,
                                            proposed_v1_p2, proposed_v2_p1)
        
        return SwapSuggestion(
            volunteer_1_id=v1_id,
            volunteer_2_id=v2_id,
            project_1_id=p1_id,
            project_2_id=p2_id,
            current_total_score=current_total,
            proposed_total_score=proposed_total,
            improvement_score=improvement,
            swap_reasons=reasons,
            volunteer_1_improvement=proposed_v1_p2 - current_v1_p1,
            volunteer_2_improvement=proposed_v2_p1 - current_v2_p2
        )
    
    def _generate_swap_reasons(self, v1_id: str, v2_id: str, p1_id: str, p2_id: str,
                             current_v1_p1: float, current_v2_p2: float,
                             proposed_v1_p2: float, proposed_v2_p1: float) -> List[str]:
        """Generate human-readable reasons for a swap suggestion"""
        reasons = []
        
        # Get volunteer and project details
        v1_data = self.volunteer_features[self.volunteer_features['contact_id'] == v1_id].iloc[0]
        v2_data = self.volunteer_features[self.volunteer_features['contact_id'] == v2_id].iloc[0]
        p1_data = self.project_features[self.project_features['project_id'] == p1_id].iloc[0]
        p2_data = self.project_features[self.project_features['project_id'] == p2_id].iloc[0]
        
        v1_name = f"{v1_data['first_name']} {v1_data['last_name']}"
        v2_name = f"{v2_data['first_name']} {v2_data['last_name']}"
        p1_name = p1_data['project_name']
        p2_name = p2_data['project_name']
        
        # Skill-based reasons
        if (v1_data['skills_youth'] and p2_data['requires_youth_skills'] and 
            not v2_data['skills_youth'] and p1_data['requires_youth_skills']):
            reasons.append(f"{v1_name} has youth development experience better suited for {p2_name}")
        
        if (v1_data['skills_fitness'] and p2_data['requires_fitness_skills'] and
            not v2_data['skills_fitness'] and p1_data['requires_fitness_skills']):
            reasons.append(f"{v1_name} has fitness background better suited for {p2_name}")
        
        if (v1_data['skills_admin'] and p2_data['requires_admin_skills'] and
            not v2_data['skills_admin'] and p1_data['requires_admin_skills']):
            reasons.append(f"{v1_name} has administrative skills better suited for {p2_name}")
        
        # Experience level reasons
        if abs(v1_data['experience_level'] - p2_data['experience_required']) < abs(v1_data['experience_level'] - p1_data['experience_required']):
            exp_labels = {1: 'beginner', 2: 'some', 3: 'intermediate', 4: 'experienced', 5: 'expert'}
            v1_exp = exp_labels.get(v1_data['experience_level'], 'some')
            reasons.append(f"{v1_name}'s {v1_exp} experience level is better matched to {p2_name}")
        
        # Time commitment reasons
        if abs(v1_data['commitment_level'] - p2_data['time_commitment_required']) < abs(v1_data['commitment_level'] - p1_data['time_commitment_required']):
            reasons.append(f"{v1_name}'s availability better matches {p2_name}'s time requirements")
        
        # Location preference reasons
        v1_prefers_p2_location = any([
            v1_data['prefers_blue_ash'] and p2_data['at_blue_ash'],
            v1_data['prefers_lyons'] and p2_data['at_lyons'],
            v1_data['prefers_campbell'] and p2_data['at_campbell'],
            v1_data['prefers_clippard'] and p2_data['at_clippard']
        ])
        if v1_prefers_p2_location:
            reasons.append(f"{v1_name} has previously volunteered at {p2_data['branch']} branch")
        
        # Overall improvement reason
        if proposed_v1_p2 > current_v1_p1 and proposed_v2_p1 > current_v2_p2:
            reasons.append("Both volunteers would be better matched to their new assignments")
        elif proposed_v1_p2 > current_v1_p1:
            reasons.append(f"{v1_name} would be significantly better matched")
        elif proposed_v2_p1 > current_v2_p2:
            reasons.append(f"{v2_name} would be significantly better matched")
        
        # Default reason if no specific reasons found
        if not reasons:
            improvement = (proposed_v1_p2 + proposed_v2_p1) - (current_v1_p1 + current_v2_p2)
            reasons.append(f"Overall compatibility would improve by {improvement:.1%}")
        
        return reasons[:3]  # Return top 3 reasons
    
    def optimize_coverage_for_branch(self, branch_name: str, target_coverage: float = 0.8) -> Dict[str, Any]:
        """Optimize volunteer coverage for a specific branch"""
        print(f"🎯 Optimizing coverage for {branch_name} branch...")
        
        # Filter projects for the branch
        branch_projects = self.project_features[
            self.project_features['branch'].str.contains(branch_name, na=False)
        ]
        
        if branch_projects.empty:
            return {"error": f"No projects found for {branch_name} branch"}
        
        # Calculate current coverage
        current_assignments = self.get_current_assignments()
        branch_assignments = [a for a in current_assignments if branch_name.lower() in a.branch.lower()]
        
        coverage_analysis = {
            'branch': branch_name,
            'total_projects': len(branch_projects),
            'current_assignments': len(branch_assignments),
            'coverage_ratio': len(branch_assignments) / len(branch_projects) if len(branch_projects) > 0 else 0,
            'target_coverage': target_coverage,
            'recommendations': []
        }
        
        # Find underserved projects
        assigned_projects = {a.project_id for a in branch_assignments}
        underserved_projects = branch_projects[~branch_projects['project_id'].isin(assigned_projects)]
        
        # Find best volunteers for underserved projects
        for _, project in underserved_projects.iterrows():
            project_id = project['project_id']
            
            if project_id in self.compatibility_matrix.columns:
                # Get compatibility scores for this project
                project_scores = self.compatibility_matrix[project_id].sort_values(ascending=False)
                
                # Find top unassigned volunteers
                assigned_volunteers = {a.volunteer_id for a in current_assignments}
                
                for volunteer_id in project_scores.index[:5]:  # Top 5 candidates
                    if volunteer_id not in assigned_volunteers:
                        score = project_scores[volunteer_id]
                        volunteer_data = self.volunteer_features[
                            self.volunteer_features['contact_id'] == volunteer_id
                        ].iloc[0]
                        
                        coverage_analysis['recommendations'].append({
                            'action': 'assign',
                            'volunteer_id': volunteer_id,
                            'volunteer_name': f"{volunteer_data['first_name']} {volunteer_data['last_name']}",
                            'project_id': project_id,
                            'project_name': project['project_name'],
                            'compatibility_score': float(score),
                            'reason': f"High compatibility ({score:.2f}) for underserved project"
                        })
                        break
        
        return coverage_analysis
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get a summary of optimization opportunities"""
        current_assignments = self.get_current_assignments()
        swap_suggestions = self.generate_swap_suggestions(top_k=5)
        
        # Calculate average fit scores
        avg_current_fit = np.mean([a.fit_score for a in current_assignments]) if current_assignments else 0
        
        # Identify volunteers with low fit scores
        low_fit_volunteers = [a for a in current_assignments if a.fit_score < 0.4]
        
        # Branch coverage analysis
        branch_coverage = {}
        for branch in self.insights.get('top_branches', {}).keys():
            coverage = self.optimize_coverage_for_branch(branch)
            if 'error' not in coverage:
                branch_coverage[branch] = coverage
        
        return {
            'total_assignments': len(current_assignments),
            'average_fit_score': avg_current_fit,
            'low_fit_assignments': len(low_fit_volunteers),
            'swap_opportunities': len(swap_suggestions),
            'top_swap_suggestions': swap_suggestions,
            'branch_coverage_analysis': branch_coverage,
            'optimization_potential': {
                'total_possible_improvement': sum(s.improvement_score for s in swap_suggestions),
                'volunteers_needing_reassignment': len(low_fit_volunteers),
                'highest_impact_swap': swap_suggestions[0] if swap_suggestions else None
            }
        }

# Example usage
if __name__ == "__main__":
    from data_processor import VolunteerDataProcessor
    
    # Load and process data
    processor = VolunteerDataProcessor("Y Volunteer Raw Data - Jan- August 2025.xlsx")
    volunteer_data = processor.get_volunteer_recommendations_data()
    
    # Create optimizer
    optimizer = VolunteerRoutingOptimizer(volunteer_data)
    
    # Generate optimization summary
    summary = optimizer.get_optimization_summary()
    
    print("\n🎯 VOLUNTEER ROUTING OPTIMIZATION SUMMARY:")
    print(f"Total assignments: {summary['total_assignments']}")
    print(f"Average fit score: {summary['average_fit_score']:.2f}")
    print(f"Swap opportunities: {summary['swap_opportunities']}")
    
    if summary['top_swap_suggestions']:
        print("\n🔄 TOP SWAP SUGGESTIONS:")
        for i, swap in enumerate(summary['top_swap_suggestions'], 1):
            print(f"{i}. Improvement: {swap.improvement_score:.2f}")
            print(f"   Reasons: {', '.join(swap.swap_reasons[:2])}")