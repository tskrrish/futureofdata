"""
Fairness Constraints Engine for YMCA Volunteer Matching
Ensures demographic balance and equitable opportunity distribution across branches
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict, Counter
from sklearn.metrics import pairwise_distances
import warnings
warnings.filterwarnings('ignore')

class FairnessConstraintsEngine:
    """
    Implements fairness constraints to balance opportunities across demographics and branches.
    
    Key Features:
    - Demographic parity enforcement (gender, race/ethnicity, age groups)
    - Geographic equity across branches
    - Opportunity distribution balancing
    - Anti-discrimination safeguards
    - Diversity monitoring and reporting
    """
    
    def __init__(self, volunteer_data: Dict[str, Any]):
        self.volunteer_data = volunteer_data
        self.volunteers_df = volunteer_data.get('volunteers')
        self.projects_df = volunteer_data.get('projects')
        self.interactions_df = volunteer_data.get('interactions')
        
        # Fairness thresholds (configurable)
        self.fairness_thresholds = {
            'demographic_parity_tolerance': 0.15,  # ±15% demographic representation
            'branch_equity_tolerance': 0.20,       # ±20% branch distribution
            'minimum_diversity_score': 0.7,        # Minimum diversity score (0-1)
            'protected_groups_boost': 0.1          # Boost for underrepresented groups
        }
        
        # Demographic categories for fairness tracking
        self.demographic_categories = {
            'gender': ['Male', 'Female', 'Non-binary', 'Unknown'],
            'age_group': ['Under 25', '25-34', '35-49', '50-64', '65+'],
            'race_ethnicity': ['White', 'Black', 'Hispanic', 'Asian', 'Other', 'Not Specified']
        }
        
        # Branch categories
        self.branches = ['Blue Ash', 'M.E. Lyons', 'Campbell County', 'Clippard', 'YDE', 'Other']
        
        # Initialize demographic statistics
        self._calculate_demographic_baselines()
        self._analyze_current_disparities()
    
    def _calculate_demographic_baselines(self):
        """Calculate baseline demographic distributions from volunteer population"""
        if self.volunteers_df is None or len(self.volunteers_df) == 0:
            print("⚠️  Warning: No volunteer data available for baseline calculations")
            self.demographic_baselines = {}
            return
        
        print("📊 Calculating demographic baselines...")
        
        self.demographic_baselines = {}
        
        # Gender distribution
        if 'gender' in self.volunteers_df.columns:
            gender_dist = self.volunteers_df['gender'].fillna('Unknown').value_counts(normalize=True)
            self.demographic_baselines['gender'] = gender_dist.to_dict()
        
        # Age group distribution
        if 'age' in self.volunteers_df.columns:
            age_bins = [0, 25, 35, 50, 65, 100]
            age_labels = ['Under 25', '25-34', '35-49', '50-64', '65+']
            age_groups = pd.cut(self.volunteers_df['age'].fillna(35), bins=age_bins, labels=age_labels)
            age_dist = age_groups.value_counts(normalize=True)
            self.demographic_baselines['age_group'] = age_dist.to_dict()
        
        # Race/ethnicity distribution
        if 'race_ethnicity' in self.volunteers_df.columns:
            race_dist = self.volunteers_df['race_ethnicity'].fillna('Not Specified').value_counts(normalize=True)
            self.demographic_baselines['race_ethnicity'] = race_dist.to_dict()
        
        # Branch distribution
        if 'branches_volunteered' in self.volunteers_df.columns:
            # Extract primary branch for each volunteer
            primary_branches = []
            for branches_str in self.volunteers_df['branches_volunteered'].fillna(''):
                branches_list = str(branches_str).split(', ')
                primary_branch = branches_list[0] if branches_list and branches_list[0] else 'Other'
                primary_branches.append(primary_branch)
            
            branch_dist = pd.Series(primary_branches).value_counts(normalize=True)
            self.demographic_baselines['branch'] = branch_dist.to_dict()
        
        print(f"✅ Baseline calculations complete for {len(self.demographic_baselines)} categories")
    
    def _analyze_current_disparities(self):
        """Analyze current disparities in opportunity distribution"""
        if self.interactions_df is None or len(self.interactions_df) == 0:
            print("⚠️  Warning: No interaction data available for disparity analysis")
            self.current_disparities = {}
            return
        
        print("🔍 Analyzing current demographic disparities...")
        
        # Merge volunteer demographics with interactions
        if self.volunteers_df is not None:
            enriched_interactions = self.interactions_df.merge(
                self.volunteers_df[['contact_id', 'gender', 'age', 'race_ethnicity', 'branches_volunteered']], 
                on='contact_id', 
                how='left'
            )
        else:
            enriched_interactions = self.interactions_df.copy()
        
        self.current_disparities = {}
        
        # Calculate hours distribution by demographic groups
        if 'gender' in enriched_interactions.columns:
            gender_hours = enriched_interactions.groupby('gender')['hours'].sum()
            total_hours = gender_hours.sum()
            gender_distribution = (gender_hours / total_hours).to_dict()
            
            # Compare with baseline
            baseline_gender = self.demographic_baselines.get('gender', {})
            gender_disparities = {}
            for gender in baseline_gender.keys():
                actual = gender_distribution.get(gender, 0)
                expected = baseline_gender.get(gender, 0)
                disparity = actual - expected if expected > 0 else 0
                gender_disparities[gender] = disparity
            
            self.current_disparities['gender'] = gender_disparities
        
        # Calculate opportunity access by age groups
        if 'age' in enriched_interactions.columns:
            age_bins = [0, 25, 35, 50, 65, 100]
            age_labels = ['Under 25', '25-34', '35-49', '50-64', '65+']
            enriched_interactions['age_group'] = pd.cut(
                enriched_interactions['age'].fillna(35), 
                bins=age_bins, 
                labels=age_labels
            )
            
            age_opportunities = enriched_interactions.groupby('age_group')['project_id'].nunique()
            total_opportunities = enriched_interactions['project_id'].nunique()
            age_access = (age_opportunities / total_opportunities).to_dict()
            
            baseline_age = self.demographic_baselines.get('age_group', {})
            age_disparities = {}
            for age_group in baseline_age.keys():
                actual = age_access.get(age_group, 0)
                expected = baseline_age.get(age_group, 0)
                disparity = actual - expected if expected > 0 else 0
                age_disparities[age_group] = disparity
            
            self.current_disparities['age_group'] = age_disparities
        
        print(f"📈 Disparity analysis complete: {len(self.current_disparities)} categories analyzed")
    
    def apply_fairness_constraints(self, matches: List[Dict[str, Any]], 
                                 user_demographics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply fairness constraints to volunteer matches to promote demographic balance.
        
        Args:
            matches: List of volunteer opportunity matches
            user_demographics: Demographic information about the user
            
        Returns:
            Adjusted matches with fairness constraints applied
        """
        print("⚖️  Applying fairness constraints to matches...")
        
        if not matches:
            return matches
        
        # Create a copy to avoid modifying original matches
        adjusted_matches = [match.copy() for match in matches]
        
        # Apply demographic parity adjustments
        adjusted_matches = self._apply_demographic_parity(adjusted_matches, user_demographics)
        
        # Apply branch equity adjustments
        adjusted_matches = self._apply_branch_equity(adjusted_matches, user_demographics)
        
        # Apply underrepresentation boost
        adjusted_matches = self._apply_underrepresentation_boost(adjusted_matches, user_demographics)
        
        # Ensure diversity in recommendations
        adjusted_matches = self._ensure_recommendation_diversity(adjusted_matches)
        
        # Re-sort by adjusted scores
        adjusted_matches.sort(key=lambda x: x.get('fairness_adjusted_score', x.get('score', 0)), reverse=True)
        
        print(f"✅ Fairness constraints applied to {len(adjusted_matches)} matches")
        return adjusted_matches
    
    def _apply_demographic_parity(self, matches: List[Dict[str, Any]], 
                                user_demographics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply demographic parity constraints to match scoring"""
        if not matches or not self.projects_df is not None:
            return matches
        
        # Get project demographic distributions
        project_demographics = self._get_project_demographics()
        
        for match in matches:
            project_id = match.get('project_id')
            if project_id not in project_demographics:
                continue
            
            project_demo = project_demographics[project_id]
            parity_adjustment = 0
            
            # Check gender parity
            user_gender = user_demographics.get('gender', 'Unknown')
            project_gender_dist = project_demo.get('gender', {})
            
            if user_gender in project_gender_dist:
                current_representation = project_gender_dist[user_gender]
                expected_representation = self.demographic_baselines.get('gender', {}).get(user_gender, 0.25)
                
                # If user's demographic is underrepresented in this project, boost the score
                if current_representation < expected_representation - self.fairness_thresholds['demographic_parity_tolerance']:
                    parity_adjustment += 0.15
                elif current_representation > expected_representation + self.fairness_thresholds['demographic_parity_tolerance']:
                    parity_adjustment -= 0.1
            
            # Check age group parity
            user_age = user_demographics.get('age', 35)
            user_age_group = self._get_age_group(user_age)
            project_age_dist = project_demo.get('age_group', {})
            
            if user_age_group in project_age_dist:
                current_representation = project_age_dist[user_age_group]
                expected_representation = self.demographic_baselines.get('age_group', {}).get(user_age_group, 0.2)
                
                if current_representation < expected_representation - self.fairness_thresholds['demographic_parity_tolerance']:
                    parity_adjustment += 0.1
            
            # Apply adjustment to score
            original_score = match.get('score', 0)
            match['demographic_parity_adjustment'] = parity_adjustment
            match['fairness_adjusted_score'] = max(0, min(1, original_score + parity_adjustment))
        
        return matches
    
    def _apply_branch_equity(self, matches: List[Dict[str, Any]], 
                           user_demographics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply branch equity constraints to ensure fair geographic distribution"""
        if not matches:
            return matches
        
        # Get branch volunteer distributions
        branch_distributions = self._get_branch_distributions()
        
        for match in matches:
            branch = match.get('branch', 'Other')
            branch_adjustment = 0
            
            # Check if this branch needs more volunteers from user's demographic
            if branch in branch_distributions:
                branch_demo = branch_distributions[branch]
                user_gender = user_demographics.get('gender', 'Unknown')
                
                if user_gender in branch_demo.get('gender', {}):
                    current_representation = branch_demo['gender'][user_gender]
                    expected_representation = self.demographic_baselines.get('gender', {}).get(user_gender, 0.25)
                    
                    # Boost branches that need more diversity
                    if current_representation < expected_representation - self.fairness_thresholds['branch_equity_tolerance']:
                        branch_adjustment += 0.12
            
            # Apply branch equity adjustment
            current_score = match.get('fairness_adjusted_score', match.get('score', 0))
            match['branch_equity_adjustment'] = branch_adjustment
            match['fairness_adjusted_score'] = max(0, min(1, current_score + branch_adjustment))
        
        return matches
    
    def _apply_underrepresentation_boost(self, matches: List[Dict[str, Any]], 
                                       user_demographics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply boost for underrepresented demographic groups"""
        if not matches or not self.current_disparities:
            return matches
        
        boost_amount = 0
        
        # Check if user belongs to underrepresented groups
        user_gender = user_demographics.get('gender', 'Unknown')
        if user_gender in self.current_disparities.get('gender', {}):
            disparity = self.current_disparities['gender'][user_gender]
            if disparity < -0.05:  # Underrepresented by more than 5%
                boost_amount += self.fairness_thresholds['protected_groups_boost']
        
        user_age = user_demographics.get('age', 35)
        user_age_group = self._get_age_group(user_age)
        if user_age_group in self.current_disparities.get('age_group', {}):
            disparity = self.current_disparities['age_group'][user_age_group]
            if disparity < -0.05:  # Underrepresented by more than 5%
                boost_amount += self.fairness_thresholds['protected_groups_boost'] * 0.5
        
        # Apply boost to all matches if user is from underrepresented group
        if boost_amount > 0:
            for match in matches:
                current_score = match.get('fairness_adjusted_score', match.get('score', 0))
                match['underrepresentation_boost'] = boost_amount
                match['fairness_adjusted_score'] = max(0, min(1, current_score + boost_amount))
        
        return matches
    
    def _ensure_recommendation_diversity(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure diversity in the final set of recommendations"""
        if len(matches) <= 5:
            return matches
        
        # Group matches by branch and category for diversity
        branch_counts = Counter()
        category_counts = Counter()
        
        for i, match in enumerate(matches):
            branch = match.get('branch', 'Other')
            category = match.get('category', 'General')
            
            # Apply diversity penalty if too many matches from same branch/category
            diversity_penalty = 0
            
            if branch_counts[branch] >= 2:
                diversity_penalty += 0.05
            if category_counts[category] >= 3:
                diversity_penalty += 0.03
            
            # Apply penalty
            if diversity_penalty > 0:
                current_score = match.get('fairness_adjusted_score', match.get('score', 0))
                match['diversity_penalty'] = diversity_penalty
                match['fairness_adjusted_score'] = max(0, current_score - diversity_penalty)
            
            branch_counts[branch] += 1
            category_counts[category] += 1
        
        return matches
    
    def _get_project_demographics(self) -> Dict[str, Dict[str, Any]]:
        """Get demographic distributions for each project"""
        if self.interactions_df is None or self.volunteers_df is None:
            return {}
        
        # Merge interactions with volunteer demographics
        enriched = self.interactions_df.merge(
            self.volunteers_df[['contact_id', 'gender', 'age', 'race_ethnicity']], 
            on='contact_id', 
            how='left'
        )
        
        project_demographics = {}
        
        for project_id in enriched['project_id'].unique():
            project_data = enriched[enriched['project_id'] == project_id]
            
            demographics = {}
            
            # Gender distribution
            if 'gender' in project_data.columns:
                gender_dist = project_data['gender'].fillna('Unknown').value_counts(normalize=True)
                demographics['gender'] = gender_dist.to_dict()
            
            # Age group distribution
            if 'age' in project_data.columns:
                age_groups = pd.cut(project_data['age'].fillna(35), 
                                  bins=[0, 25, 35, 50, 65, 100], 
                                  labels=['Under 25', '25-34', '35-49', '50-64', '65+'])
                age_dist = age_groups.value_counts(normalize=True)
                demographics['age_group'] = age_dist.to_dict()
            
            project_demographics[project_id] = demographics
        
        return project_demographics
    
    def _get_branch_distributions(self) -> Dict[str, Dict[str, Any]]:
        """Get demographic distributions for each branch"""
        if self.interactions_df is None or self.volunteers_df is None:
            return {}
        
        # Get branch information from projects
        branch_project_map = {}
        if self.projects_df is not None:
            for _, project in self.projects_df.iterrows():
                branch_project_map[project['project_id']] = project.get('branch', 'Other')
        
        # Merge interactions with volunteer demographics and branch info
        enriched = self.interactions_df.merge(
            self.volunteers_df[['contact_id', 'gender', 'age', 'race_ethnicity']], 
            on='contact_id', 
            how='left'
        )
        
        enriched['branch'] = enriched['project_id'].map(branch_project_map).fillna('Other')
        
        branch_demographics = {}
        
        for branch in enriched['branch'].unique():
            branch_data = enriched[enriched['branch'] == branch]
            
            demographics = {}
            
            # Gender distribution
            if 'gender' in branch_data.columns:
                gender_dist = branch_data['gender'].fillna('Unknown').value_counts(normalize=True)
                demographics['gender'] = gender_dist.to_dict()
            
            branch_demographics[branch] = demographics
        
        return branch_demographics
    
    def _get_age_group(self, age: float) -> str:
        """Convert age to age group category"""
        if pd.isna(age):
            return '25-34'  # Default
        
        if age < 25:
            return 'Under 25'
        elif age < 35:
            return '25-34'
        elif age < 50:
            return '35-49'
        elif age < 65:
            return '50-64'
        else:
            return '65+'
    
    def generate_fairness_report(self) -> Dict[str, Any]:
        """Generate comprehensive fairness and equity report"""
        print("📋 Generating fairness report...")
        
        report = {
            'demographic_baselines': self.demographic_baselines,
            'current_disparities': self.current_disparities,
            'fairness_thresholds': self.fairness_thresholds,
            'equity_metrics': self._calculate_equity_metrics(),
            'recommendations': self._generate_fairness_recommendations()
        }
        
        print("✅ Fairness report generated successfully")
        return report
    
    def _calculate_equity_metrics(self) -> Dict[str, float]:
        """Calculate overall equity metrics for the system"""
        metrics = {}
        
        # Calculate demographic parity score (0-1, higher is better)
        if self.current_disparities:
            total_disparity = 0
            disparity_count = 0
            
            for category, disparities in self.current_disparities.items():
                for group, disparity in disparities.items():
                    total_disparity += abs(disparity)
                    disparity_count += 1
            
            if disparity_count > 0:
                avg_disparity = total_disparity / disparity_count
                metrics['demographic_parity_score'] = max(0, 1 - (avg_disparity * 2))  # Scale to 0-1
        
        # Calculate diversity index (Shannon diversity)
        if self.demographic_baselines:
            for category, distribution in self.demographic_baselines.items():
                shannon_diversity = -sum(p * np.log(p) for p in distribution.values() if p > 0)
                metrics[f'{category}_diversity_index'] = shannon_diversity
        
        # Overall fairness score
        if metrics:
            metrics['overall_fairness_score'] = np.mean(list(metrics.values()))
        
        return metrics
    
    def _generate_fairness_recommendations(self) -> List[str]:
        """Generate actionable recommendations for improving fairness"""
        recommendations = []
        
        # Check for significant disparities
        if self.current_disparities:
            for category, disparities in self.current_disparities.items():
                for group, disparity in disparities.items():
                    if disparity < -0.1:  # Significantly underrepresented
                        recommendations.append(
                            f"Increase outreach and opportunities for {group} volunteers in {category} category"
                        )
                    elif disparity > 0.1:  # Significantly overrepresented
                        recommendations.append(
                            f"Ensure balanced representation by expanding opportunities for other groups in {category} category"
                        )
        
        # Branch equity recommendations
        branch_distributions = self._get_branch_distributions()
        for branch, demographics in branch_distributions.items():
            gender_dist = demographics.get('gender', {})
            if len(gender_dist) > 0:
                max_representation = max(gender_dist.values())
                min_representation = min(gender_dist.values())
                if max_representation - min_representation > 0.3:  # 30% difference
                    recommendations.append(
                        f"Improve gender balance at {branch} branch through targeted recruitment"
                    )
        
        # General recommendations
        if not recommendations:
            recommendations.append("Current volunteer distribution shows good demographic balance")
            recommendations.append("Continue monitoring fairness metrics regularly")
        else:
            recommendations.insert(0, "Priority areas for improving fairness and equity:")
        
        return recommendations

# Example usage and testing
if __name__ == "__main__":
    from data_processor import VolunteerDataProcessor
    
    # Load and process data
    processor = VolunteerDataProcessor("Y Volunteer Raw Data - Jan- August 2025.xlsx")
    volunteer_data = processor.get_volunteer_recommendations_data()
    
    # Create fairness engine
    fairness_engine = FairnessConstraintsEngine(volunteer_data)
    
    # Generate fairness report
    report = fairness_engine.generate_fairness_report()
    
    print("\n🎯 FAIRNESS REPORT:")
    print(f"Overall Fairness Score: {report['equity_metrics'].get('overall_fairness_score', 0):.2f}")
    print(f"Demographic Parity Score: {report['equity_metrics'].get('demographic_parity_score', 0):.2f}")
    
    print("\n📋 RECOMMENDATIONS:")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"{i}. {rec}")