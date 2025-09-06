"""
Skill Gap Analysis and Training Recommendation System
Analyzes volunteer skill gaps and recommends targeted training to improve matches
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from collections import defaultdict, Counter
import re
from dataclasses import dataclass


@dataclass
class SkillGap:
    """Represents a skill gap with its details"""
    skill_name: str
    gap_score: float
    importance: float
    projects_requiring: List[str]
    current_proficiency: float
    target_proficiency: float
    category: str


@dataclass
class TrainingRecommendation:
    """Represents a training recommendation"""
    training_name: str
    skill_targets: List[str]
    priority: str
    duration_hours: int
    format: str  # online, in-person, hybrid
    cost: Optional[float]
    provider: str
    description: str
    prerequisites: List[str]
    outcomes: List[str]


class SkillGapAnalyzer:
    def __init__(self, volunteer_data: Dict[str, Any]):
        self.volunteer_data = volunteer_data
        self.volunteers_df = volunteer_data.get('volunteers')
        self.projects_df = volunteer_data.get('projects')
        self.interactions_df = volunteer_data.get('interactions')
        self.insights = volunteer_data.get('insights', {})
        
        # Skill taxonomy
        self.skill_taxonomy = {
            'Youth Development': {
                'core_skills': ['mentoring', 'child_development', 'behavior_management', 'communication'],
                'advanced_skills': ['program_planning', 'crisis_intervention', 'educational_support', 'leadership_development']
            },
            'Fitness & Wellness': {
                'core_skills': ['exercise_knowledge', 'safety_protocols', 'equipment_operation', 'basic_first_aid'],
                'advanced_skills': ['group_fitness_instruction', 'personal_training', 'nutrition_counseling', 'adaptive_exercise']
            },
            'Special Events': {
                'core_skills': ['event_coordination', 'customer_service', 'time_management', 'teamwork'],
                'advanced_skills': ['project_management', 'vendor_coordination', 'marketing', 'fundraising']
            },
            'Administrative': {
                'core_skills': ['data_entry', 'phone_etiquette', 'basic_computer_skills', 'organization'],
                'advanced_skills': ['database_management', 'report_generation', 'process_improvement', 'training_delivery']
            },
            'Facility Support': {
                'core_skills': ['maintenance_basics', 'safety_awareness', 'tool_usage', 'cleaning_protocols'],
                'advanced_skills': ['equipment_repair', 'facility_management', 'inventory_control', 'emergency_procedures']
            }
        }
        
        # Training catalog
        self.training_catalog = {
            'Youth Development Fundamentals': {
                'skills': ['mentoring', 'child_development', 'communication'],
                'duration': 8,
                'format': 'hybrid',
                'cost': 0,
                'provider': 'YMCA Training Center',
                'description': 'Essential skills for working with children and teens',
                'prerequisites': ['background_check'],
                'outcomes': ['Understand child development stages', 'Apply effective mentoring techniques', 'Communicate appropriately with youth']
            },
            'Group Fitness Leadership': {
                'skills': ['group_fitness_instruction', 'exercise_knowledge', 'safety_protocols'],
                'duration': 16,
                'format': 'in-person',
                'cost': 200,
                'provider': 'ACSM Certified Provider',
                'description': 'Comprehensive group fitness instructor certification',
                'prerequisites': ['basic_first_aid', 'cpr_certification'],
                'outcomes': ['Lead safe and effective group fitness classes', 'Modify exercises for different fitness levels', 'Handle fitness emergencies']
            },
            'Event Management Excellence': {
                'skills': ['project_management', 'event_coordination', 'vendor_coordination'],
                'duration': 12,
                'format': 'online',
                'cost': 150,
                'provider': 'Event Planning Institute',
                'description': 'Professional event planning and execution skills',
                'prerequisites': ['customer_service'],
                'outcomes': ['Plan and execute successful events', 'Manage event budgets and timelines', 'Coordinate with multiple stakeholders']
            },
            'Digital Literacy for Nonprofits': {
                'skills': ['database_management', 'basic_computer_skills', 'report_generation'],
                'duration': 6,
                'format': 'online',
                'cost': 0,
                'provider': 'TechSoup',
                'description': 'Essential digital skills for nonprofit operations',
                'prerequisites': [],
                'outcomes': ['Navigate database systems effectively', 'Generate basic reports', 'Use common software tools']
            },
            'Crisis Intervention and De-escalation': {
                'skills': ['crisis_intervention', 'behavior_management', 'communication'],
                'duration': 8,
                'format': 'in-person',
                'cost': 100,
                'provider': 'Crisis Prevention Institute',
                'description': 'Professional crisis intervention techniques',
                'prerequisites': ['youth_development_fundamentals'],
                'outcomes': ['Recognize crisis situations', 'Apply de-escalation techniques', 'Ensure safety for all participants']
            },
            'Facility Safety and Maintenance': {
                'skills': ['maintenance_basics', 'safety_awareness', 'emergency_procedures'],
                'duration': 4,
                'format': 'in-person',
                'cost': 0,
                'provider': 'YMCA Facilities Team',
                'description': 'Basic facility safety and maintenance protocols',
                'prerequisites': [],
                'outcomes': ['Identify safety hazards', 'Perform basic maintenance tasks', 'Respond to facility emergencies']
            }
        }
        
        self.tfidf_vectorizer = TfidfVectorizer(max_features=50, stop_words='english')
        self.scaler = StandardScaler()
        
    def analyze_volunteer_skills(self, contact_id: str) -> Dict[str, Any]:
        """Analyze skills of a specific volunteer"""
        if self.volunteers_df is None:
            return {'error': 'No volunteer data available'}
        
        volunteer = self.volunteers_df[self.volunteers_df['contact_id'] == contact_id]
        if volunteer.empty:
            return {'error': 'Volunteer not found'}
        
        volunteer_row = volunteer.iloc[0]
        
        # Extract current skills from volunteer history
        volunteer_interactions = self.interactions_df[self.interactions_df['contact_id'] == contact_id]
        current_skills = self._extract_skills_from_experience(volunteer_interactions)
        
        # Determine skill proficiency levels
        skill_proficiencies = self._calculate_skill_proficiency(volunteer_row, volunteer_interactions, current_skills)
        
        return {
            'contact_id': contact_id,
            'name': f"{volunteer_row.get('first_name', '')} {volunteer_row.get('last_name', '')}",
            'volunteer_type': volunteer_row.get('volunteer_type', 'Newcomer'),
            'current_skills': current_skills,
            'skill_proficiencies': skill_proficiencies,
            'primary_categories': volunteer_row.get('project_categories', '').split(', ')
        }
    
    def identify_skill_gaps(self, contact_id: str, target_projects: Optional[List[str]] = None) -> List[SkillGap]:
        """Identify skill gaps for improved volunteer matching"""
        volunteer_skills = self.analyze_volunteer_skills(contact_id)
        if 'error' in volunteer_skills:
            return []
        
        # Determine target opportunities
        if target_projects is None:
            target_projects = self._suggest_target_projects(volunteer_skills)
        
        # Analyze required skills for target projects
        required_skills = self._get_required_skills_for_projects(target_projects)
        
        # Compare current vs required skills
        skill_gaps = []
        current_proficiencies = volunteer_skills['skill_proficiencies']
        
        for project_category, skills in required_skills.items():
            for skill, required_level in skills.items():
                current_level = current_proficiencies.get(skill, 0.0)
                
                if current_level < required_level:
                    gap_score = required_level - current_level
                    importance = self._calculate_skill_importance(skill, project_category)
                    
                    projects_requiring = [
                        project for project in target_projects 
                        if self._project_requires_skill(project, skill)
                    ]
                    
                    skill_gap = SkillGap(
                        skill_name=skill,
                        gap_score=gap_score,
                        importance=importance,
                        projects_requiring=projects_requiring,
                        current_proficiency=current_level,
                        target_proficiency=required_level,
                        category=project_category
                    )
                    skill_gaps.append(skill_gap)
        
        # Sort by priority (gap_score * importance)
        skill_gaps.sort(key=lambda x: x.gap_score * x.importance, reverse=True)
        
        return skill_gaps
    
    def recommend_training(self, skill_gaps: List[SkillGap], volunteer_preferences: Dict[str, Any] = None) -> List[TrainingRecommendation]:
        """Recommend training programs to address skill gaps"""
        if not skill_gaps:
            return []
        
        recommendations = []
        covered_skills = set()
        
        # Group skills by category for efficient training selection
        skills_by_category = defaultdict(list)
        for gap in skill_gaps:
            if gap.skill_name not in covered_skills:
                skills_by_category[gap.category].append(gap)
        
        # Find optimal training combinations
        for category, gaps in skills_by_category.items():
            category_recommendations = self._find_optimal_training_for_category(gaps, volunteer_preferences)
            recommendations.extend(category_recommendations)
            
            for rec in category_recommendations:
                covered_skills.update(rec.skill_targets)
        
        # Add foundational training if needed
        foundational_recs = self._add_foundational_training(skill_gaps, covered_skills, volunteer_preferences)
        recommendations.extend(foundational_recs)
        
        # Sort by priority and return
        recommendations.sort(key=lambda x: self._calculate_training_priority_score(x, skill_gaps), reverse=True)
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def generate_training_plan(self, contact_id: str, target_projects: Optional[List[str]] = None, volunteer_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a comprehensive training plan for a volunteer"""
        # Analyze current skills and gaps
        skill_gaps = self.identify_skill_gaps(contact_id, target_projects)
        
        if not skill_gaps:
            return {
                'contact_id': contact_id,
                'message': 'No significant skill gaps identified',
                'current_match_quality': 'Excellent',
                'recommendations': []
            }
        
        # Get training recommendations
        training_recommendations = self.recommend_training(skill_gaps, volunteer_preferences)
        
        # Create implementation timeline
        timeline = self._create_training_timeline(training_recommendations)
        
        # Calculate impact metrics
        impact_metrics = self._calculate_training_impact(skill_gaps, training_recommendations)
        
        # Generate actionable plan
        return {
            'contact_id': contact_id,
            'skill_gaps_identified': len(skill_gaps),
            'priority_gaps': [gap.skill_name for gap in skill_gaps[:3]],
            'training_recommendations': [
                {
                    'name': rec.training_name,
                    'priority': rec.priority,
                    'duration': rec.duration_hours,
                    'format': rec.format,
                    'cost': rec.cost,
                    'skills_addressed': rec.skill_targets,
                    'description': rec.description,
                    'prerequisites': rec.prerequisites,
                    'expected_outcomes': rec.outcomes
                }
                for rec in training_recommendations
            ],
            'implementation_timeline': timeline,
            'impact_metrics': impact_metrics,
            'next_steps': self._generate_next_steps(training_recommendations)
        }
    
    def _extract_skills_from_experience(self, interactions_df: pd.DataFrame) -> Dict[str, float]:
        """Extract skills from volunteer experience data"""
        skills = defaultdict(float)
        
        if interactions_df.empty:
            return skills
        
        # Extract skills from project categories and descriptions
        for _, interaction in interactions_df.iterrows():
            project_category = interaction.get('project_category', '')
            hours = interaction.get('hours', 0)
            
            # Map project categories to skills
            category_skills = self.skill_taxonomy.get(project_category, {})
            
            # Add core skills based on participation
            for skill in category_skills.get('core_skills', []):
                skills[skill] += hours * 0.1
            
            # Add advanced skills if significant experience
            if hours > 10:
                for skill in category_skills.get('advanced_skills', []):
                    skills[skill] += hours * 0.05
        
        # Normalize skill scores
        max_score = max(skills.values()) if skills else 1
        normalized_skills = {skill: min(score/max_score, 1.0) for skill, score in skills.items()}
        
        return normalized_skills
    
    def _calculate_skill_proficiency(self, volunteer_row: pd.Series, interactions_df: pd.DataFrame, current_skills: Dict[str, float]) -> Dict[str, float]:
        """Calculate skill proficiency levels"""
        proficiencies = current_skills.copy()
        
        # Factor in volunteer experience and type
        volunteer_type = volunteer_row.get('volunteer_type', 'Newcomer')
        total_hours = volunteer_row.get('total_hours', 0)
        experience_multiplier = {
            'Champion': 1.3,
            'Committed': 1.2,
            'Regular': 1.1,
            'Explorer': 1.0,
            'Newcomer': 0.8
        }.get(volunteer_type, 1.0)
        
        # Adjust proficiencies based on experience
        for skill in proficiencies:
            base_proficiency = proficiencies[skill]
            experience_boost = min(total_hours / 100, 0.3)  # Up to 30% boost
            proficiencies[skill] = min(base_proficiency * experience_multiplier + experience_boost, 1.0)
        
        return proficiencies
    
    def _suggest_target_projects(self, volunteer_skills: Dict[str, Any]) -> List[str]:
        """Suggest target projects based on volunteer profile"""
        if self.projects_df is None:
            return []
        
        primary_categories = volunteer_skills.get('primary_categories', [])
        volunteer_type = volunteer_skills.get('volunteer_type', 'Newcomer')
        
        # Find projects in primary categories or related areas
        target_projects = []
        
        for _, project in self.projects_df.iterrows():
            project_category = project.get('category', '')
            
            # Include current categories and growth opportunities
            if (project_category in primary_categories or 
                self._is_growth_opportunity(project_category, volunteer_type)):
                target_projects.append(project.get('project_name', ''))
        
        return target_projects[:10]  # Limit to top 10 targets
    
    def _get_required_skills_for_projects(self, project_names: List[str]) -> Dict[str, Dict[str, float]]:
        """Determine required skills and proficiency levels for projects"""
        required_skills = defaultdict(lambda: defaultdict(float))
        
        for project_name in project_names:
            project_info = self._get_project_info(project_name)
            if not project_info:
                continue
            
            category = project_info.get('category', 'General')
            complexity = self._assess_project_complexity(project_info)
            
            # Add skills based on project category and complexity
            category_skills = self.skill_taxonomy.get(category, {})
            
            # Core skills (required at proficiency level based on complexity)
            for skill in category_skills.get('core_skills', []):
                required_skills[category][skill] = max(required_skills[category][skill], 0.3 + complexity * 0.4)
            
            # Advanced skills (required for complex projects)
            if complexity > 0.5:
                for skill in category_skills.get('advanced_skills', []):
                    required_skills[category][skill] = max(required_skills[category][skill], complexity * 0.6)
        
        return dict(required_skills)
    
    def _calculate_skill_importance(self, skill: str, category: str) -> float:
        """Calculate the importance of a skill within a category"""
        category_skills = self.skill_taxonomy.get(category, {})
        
        if skill in category_skills.get('core_skills', []):
            return 1.0  # Core skills are most important
        elif skill in category_skills.get('advanced_skills', []):
            return 0.7  # Advanced skills are moderately important
        else:
            return 0.4  # Other skills are less critical
    
    def _project_requires_skill(self, project_name: str, skill: str) -> bool:
        """Check if a project requires a specific skill"""
        project_info = self._get_project_info(project_name)
        if not project_info:
            return False
        
        category = project_info.get('category', '')
        category_skills = self.skill_taxonomy.get(category, {})
        
        return skill in (category_skills.get('core_skills', []) + category_skills.get('advanced_skills', []))
    
    def _find_optimal_training_for_category(self, gaps: List[SkillGap], preferences: Dict[str, Any] = None) -> List[TrainingRecommendation]:
        """Find optimal training programs for a category's skill gaps"""
        recommendations = []
        gap_skills = [gap.skill_name for gap in gaps]
        
        # Find training programs that cover multiple gaps
        for training_name, training_info in self.training_catalog.items():
            covered_skills = [skill for skill in training_info['skills'] if skill in gap_skills]
            
            if covered_skills:
                priority = self._determine_training_priority(gaps, covered_skills, preferences)
                
                recommendation = TrainingRecommendation(
                    training_name=training_name,
                    skill_targets=covered_skills,
                    priority=priority,
                    duration_hours=training_info['duration'],
                    format=training_info['format'],
                    cost=training_info['cost'],
                    provider=training_info['provider'],
                    description=training_info['description'],
                    prerequisites=training_info['prerequisites'],
                    outcomes=training_info['outcomes']
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    def _add_foundational_training(self, skill_gaps: List[SkillGap], covered_skills: set, preferences: Dict[str, Any] = None) -> List[TrainingRecommendation]:
        """Add foundational training recommendations"""
        foundational_recs = []
        
        # Check if foundational skills are needed
        foundational_skills = ['communication', 'customer_service', 'basic_computer_skills', 'safety_awareness']
        needed_foundational = [
            gap for gap in skill_gaps 
            if gap.skill_name in foundational_skills and gap.skill_name not in covered_skills
        ]
        
        if needed_foundational:
            # Add digital literacy if computer skills needed
            if any(gap.skill_name == 'basic_computer_skills' for gap in needed_foundational):
                digital_literacy = self.training_catalog.get('Digital Literacy for Nonprofits')
                if digital_literacy:
                    recommendation = TrainingRecommendation(
                        training_name='Digital Literacy for Nonprofits',
                        skill_targets=['basic_computer_skills', 'database_management'],
                        priority='High',
                        duration_hours=digital_literacy['duration'],
                        format=digital_literacy['format'],
                        cost=digital_literacy['cost'],
                        provider=digital_literacy['provider'],
                        description=digital_literacy['description'],
                        prerequisites=digital_literacy['prerequisites'],
                        outcomes=digital_literacy['outcomes']
                    )
                    foundational_recs.append(recommendation)
        
        return foundational_recs
    
    def _calculate_training_priority_score(self, recommendation: TrainingRecommendation, skill_gaps: List[SkillGap]) -> float:
        """Calculate priority score for training recommendation"""
        score = 0.0
        
        # Score based on skill gaps addressed
        for skill in recommendation.skill_targets:
            matching_gaps = [gap for gap in skill_gaps if gap.skill_name == skill]
            for gap in matching_gaps:
                score += gap.gap_score * gap.importance
        
        # Bonus for comprehensive training (covers multiple skills)
        if len(recommendation.skill_targets) > 2:
            score *= 1.2
        
        # Penalty for high cost
        if recommendation.cost and recommendation.cost > 100:
            score *= 0.9
        
        return score
    
    def _create_training_timeline(self, recommendations: List[TrainingRecommendation]) -> Dict[str, List[str]]:
        """Create implementation timeline for training recommendations"""
        timeline = {
            'immediate': [],  # 0-4 weeks
            'short_term': [],  # 1-3 months
            'medium_term': []  # 3-6 months
        }
        
        for rec in recommendations:
            if rec.priority == 'High' or rec.duration_hours <= 8:
                timeline['immediate'].append(rec.training_name)
            elif rec.priority == 'Medium' or rec.duration_hours <= 16:
                timeline['short_term'].append(rec.training_name)
            else:
                timeline['medium_term'].append(rec.training_name)
        
        return timeline
    
    def _calculate_training_impact(self, skill_gaps: List[SkillGap], recommendations: List[TrainingRecommendation]) -> Dict[str, Any]:
        """Calculate expected impact of training recommendations"""
        total_gaps = len(skill_gaps)
        addressed_skills = set()
        
        for rec in recommendations:
            addressed_skills.update(rec.skill_targets)
        
        addressed_gaps = len([gap for gap in skill_gaps if gap.skill_name in addressed_skills])
        
        return {
            'total_skill_gaps': total_gaps,
            'gaps_addressed': addressed_gaps,
            'improvement_percentage': (addressed_gaps / total_gaps * 100) if total_gaps > 0 else 0,
            'estimated_match_improvement': min(addressed_gaps * 15, 75),  # Up to 75% improvement
            'total_training_hours': sum(rec.duration_hours for rec in recommendations),
            'total_cost': sum(rec.cost or 0 for rec in recommendations)
        }
    
    def _generate_next_steps(self, recommendations: List[TrainingRecommendation]) -> List[str]:
        """Generate actionable next steps"""
        if not recommendations:
            return ['Continue gaining experience in current volunteer roles']
        
        next_steps = []
        high_priority = [rec for rec in recommendations if rec.priority == 'High']
        
        if high_priority:
            next_steps.append(f"1. Enroll in '{high_priority[0].training_name}' within the next 2 weeks")
        
        # Add prerequisite steps
        all_prerequisites = set()
        for rec in recommendations:
            all_prerequisites.update(rec.prerequisites)
        
        if all_prerequisites:
            next_steps.append(f"2. Complete prerequisites: {', '.join(all_prerequisites)}")
        
        # Add general guidance
        next_steps.extend([
            "3. Discuss training plans with your volunteer coordinator",
            "4. Track your skill development progress",
            "5. Apply new skills in upcoming volunteer opportunities"
        ])
        
        return next_steps[:5]
    
    def _get_project_info(self, project_name: str) -> Dict[str, Any]:
        """Get project information by name"""
        if self.projects_df is None:
            return {}
        
        project_match = self.projects_df[self.projects_df['project_name'] == project_name]
        if project_match.empty:
            return {}
        
        return project_match.iloc[0].to_dict()
    
    def _assess_project_complexity(self, project_info: Dict[str, Any]) -> float:
        """Assess project complexity (0-1 scale)"""
        complexity = 0.3  # Base complexity
        
        # Factor in volunteer requirements
        if project_info.get('unique_volunteers', 0) > 20:
            complexity += 0.2  # Popular projects tend to be more structured
        
        # Factor in time commitment
        avg_hours = project_info.get('avg_hours_per_session', 0)
        if avg_hours > 4:
            complexity += 0.2
        
        # Factor in credentials required
        credentials = str(project_info.get('required_credentials', ''))
        if 'background' in credentials.lower() or 'certification' in credentials.lower():
            complexity += 0.3
        
        return min(complexity, 1.0)
    
    def _is_growth_opportunity(self, category: str, volunteer_type: str) -> bool:
        """Determine if a category represents a growth opportunity"""
        growth_map = {
            'Newcomer': ['Facility Support', 'Administrative'],
            'Explorer': ['Special Events', 'Fitness & Wellness'],
            'Regular': ['Youth Development', 'Special Events'],
            'Committed': ['Youth Development', 'Administrative'],
            'Champion': ['Administrative', 'Special Events']  # Leadership opportunities
        }
        
        return category in growth_map.get(volunteer_type, [])
    
    def _determine_training_priority(self, gaps: List[SkillGap], covered_skills: List[str], preferences: Dict[str, Any] = None) -> str:
        """Determine training priority level"""
        # Calculate average importance of covered skills
        avg_importance = np.mean([
            gap.importance for gap in gaps if gap.skill_name in covered_skills
        ])
        
        # Calculate average gap score
        avg_gap = np.mean([
            gap.gap_score for gap in gaps if gap.skill_name in covered_skills
        ])
        
        # Combine metrics for priority
        priority_score = avg_importance * avg_gap
        
        if priority_score >= 0.7:
            return 'High'
        elif priority_score >= 0.4:
            return 'Medium'
        else:
            return 'Low'


# Example usage
if __name__ == "__main__":
    from data_processor import VolunteerDataProcessor
    
    # Load data
    processor = VolunteerDataProcessor("Y Volunteer Raw Data - Jan- August 2025.xlsx")
    volunteer_data = processor.get_volunteer_recommendations_data()
    
    # Create skill gap analyzer
    analyzer = SkillGapAnalyzer(volunteer_data)
    
    # Test with sample volunteer
    if not volunteer_data['volunteers'].empty:
        contact_id = volunteer_data['volunteers']['contact_id'].iloc[0]
        
        # Generate training plan
        training_plan = analyzer.generate_training_plan(contact_id)
        
        print("🎯 SKILL GAP TRAINING PLAN")
        print(f"Contact ID: {training_plan['contact_id']}")
        print(f"Skill gaps identified: {training_plan['skill_gaps_identified']}")
        print(f"Priority gaps: {', '.join(training_plan['priority_gaps'])}")
        print("\n📚 RECOMMENDED TRAINING:")
        
        for i, rec in enumerate(training_plan['training_recommendations'], 1):
            print(f"{i}. {rec['name']} ({rec['priority']} priority)")
            print(f"   Duration: {rec['duration']} hours | Format: {rec['format']}")
            print(f"   Skills: {', '.join(rec['skills_addressed'])}")
            print()