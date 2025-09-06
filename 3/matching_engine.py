"""
ML-Powered Volunteer Matching Engine with Proximity-Based Matching
Uses scikit-learn models with existing volunteer data patterns
Enhanced with travel time and public transit aware scoring
"""
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from typing import Dict, List, Tuple, Any, Optional
import re
from collections import Counter
from proximity_matcher import ProximityMatcher

class VolunteerMatchingEngine:
    def __init__(self, volunteer_data: Dict[str, Any]):
        self.volunteer_data = volunteer_data
        self.volunteers_df = volunteer_data.get('volunteers')
        self.projects_df = volunteer_data.get('projects') 
        self.interactions_df = volunteer_data.get('interactions')
        self.insights = volunteer_data.get('insights', {})
        
        # ML Models
        self.tfidf_vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        self.scaler = StandardScaler()
        self.volunteer_clusterer = KMeans(n_clusters=5, random_state=42)
        self.success_predictor = RandomForestClassifier(n_estimators=100, random_state=42)
        
        # Fitted models flags
        self.models_trained = False
        
        # Initialize proximity matcher for travel time and transit scoring
        self.proximity_matcher = ProximityMatcher()
        
        # Volunteer types and characteristics
        self.volunteer_personas = {
            'Champion': {'hours_min': 100, 'description': 'Highly committed, long-term volunteers'},
            'Committed': {'hours_min': 50, 'description': 'Regular volunteers with strong engagement'},
            'Regular': {'hours_min': 20, 'description': 'Consistent volunteers with moderate engagement'},
            'Explorer': {'hours_min': 5, 'description': 'Volunteers who try multiple projects'},
            'Newcomer': {'hours_min': 0, 'description': 'New or occasional volunteers'}
        }
        
        self._prepare_data()
    
    def _prepare_data(self):
        """Prepare data for machine learning models"""
        if self.volunteers_df is None or self.projects_df is None:
            print("⚠️  Warning: Missing volunteer or project data")
            return
        
        print("🔧 Preparing data for ML models...")
        
        # Prepare volunteer features
        self.volunteer_features = self._extract_volunteer_features()
        
        # Prepare project features  
        self.project_features = self._extract_project_features()
        
        # Create interaction matrix
        self.interaction_matrix = self._create_interaction_matrix()
        
        print("✅ Data preparation complete!")
    
    def _extract_volunteer_features(self) -> pd.DataFrame:
        """Extract numerical features from volunteer profiles"""
        if self.volunteers_df is None:
            return pd.DataFrame()
        
        features = self.volunteers_df.copy()
        
        # Encode categorical variables
        le_gender = LabelEncoder()
        features['gender_encoded'] = le_gender.fit_transform(features['gender'].fillna('Unknown'))
        
        le_race = LabelEncoder()
        features['race_encoded'] = le_race.fit_transform(features['race_ethnicity'].fillna('Unknown'))
        
        # Age groups
        features['age_group'] = pd.cut(features['age'], bins=[0, 25, 35, 50, 65, 100], 
                                     labels=[1, 2, 3, 4, 5]).fillna(3)
        
        # Engagement metrics
        features['engagement_score'] = (
            features['total_hours'] * 0.4 + 
            features['volunteer_sessions'] * 0.3 + 
            features['unique_projects'] * 0.3
        )
        
        features['loyalty_score'] = features['volunteer_tenure_days'] / (features['volunteer_sessions'] + 1)
        features['intensity_score'] = features['avg_hours_per_session']
        
        # Project diversity
        features['project_diversity'] = features['project_categories'].str.count(',') + 1
        
        # Extract location features
        features['is_cincinnati'] = features['home_city'].str.contains('Cincinnati', na=False).astype(int)
        features['is_ohio'] = features['home_state'].str.contains('OH|Ohio', na=False).astype(int)
        
        return features
    
    def _extract_project_features(self) -> pd.DataFrame:
        """Extract numerical features from project catalog"""
        if self.projects_df is None:
            return pd.DataFrame()
        
        features = self.projects_df.copy()
        
        # Encode project categories
        le_category = LabelEncoder()
        features['category_encoded'] = le_category.fit_transform(features['category'].fillna('General'))
        
        le_branch = LabelEncoder()
        features['branch_encoded'] = le_branch.fit_transform(features['branch'].fillna('Unknown'))
        
        # Project characteristics
        features['time_commitment'] = pd.cut(features['avg_hours_per_session'], 
                                           bins=[0, 1, 3, 6, 24], 
                                           labels=[1, 2, 3, 4]).fillna(2)
        
        features['popularity'] = pd.qcut(features['unique_volunteers'], q=5, labels=[1, 2, 3, 4, 5]).fillna(3)
        
        # Extract keywords from project descriptions
        project_keywords = self._extract_project_keywords(features)
        features = features.join(project_keywords)
        
        return features
    
    def _extract_project_keywords(self, projects_df: pd.DataFrame) -> pd.DataFrame:
        """Extract important keywords from project descriptions"""
        # Combine relevant text fields
        text_fields = ['project_name', 'need', 'sample_activities']
        combined_text = []
        
        for _, row in projects_df.iterrows():
            text_parts = []
            for field in text_fields:
                if field in row and pd.notna(row[field]):
                    text_parts.append(str(row[field]))
            combined_text.append(' '.join(text_parts))
        
        # Create TF-IDF features
        if combined_text:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(combined_text)
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            # Convert to DataFrame
            tfidf_df = pd.DataFrame(tfidf_matrix.toarray(), columns=feature_names, index=projects_df.index)
            return tfidf_df
        
        return pd.DataFrame()
    
    def _create_interaction_matrix(self) -> pd.DataFrame:
        """Create volunteer-project interaction matrix"""
        if self.interactions_df is None:
            return pd.DataFrame()
        
        # Create pivot table of volunteer-project interactions
        interaction_matrix = self.interactions_df.pivot_table(
            index='contact_id',
            columns='project_id',
            values='hours',
            aggfunc='sum',
            fill_value=0
        )
        
        return interaction_matrix
    
    def train_models(self):
        """Train all ML models"""
        if self.volunteer_features.empty or self.project_features.empty:
            print("⚠️  Cannot train models: insufficient data")
            return
        
        print("🤖 Training ML models...")
        
        # Train volunteer clustering model
        volunteer_features_numeric = self.volunteer_features[[
            'age', 'total_hours', 'volunteer_sessions', 'unique_projects',
            'engagement_score', 'loyalty_score', 'intensity_score'
        ]].fillna(0)
        
        scaled_features = self.scaler.fit_transform(volunteer_features_numeric)
        self.volunteer_clusterer.fit(scaled_features)
        
        # Add cluster labels to volunteer features
        self.volunteer_features['cluster'] = self.volunteer_clusterer.labels_
        
        # Train success prediction model (predict if volunteer will return)
        if len(self.volunteer_features) > 50:  # Need minimum data for training
            X = scaled_features
            y = (self.volunteer_features['volunteer_sessions'] > 1).astype(int)  # Multi-session volunteers
            self.success_predictor.fit(X, y)
        
        self.models_trained = True
        print("✅ ML models trained successfully!")
    
    def find_matches(self, user_preferences: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        """Find best volunteer matches for user preferences"""
        if not self.models_trained:
            self.train_models()
        
        print(f"🎯 Finding top {top_k} matches for user preferences...")
        
        # Create user profile vector
        user_vector = self._create_user_vector(user_preferences)
        
        # Calculate similarity scores
        match_scores = []
        
        for _, project in self.project_features.iterrows():
            # Calculate match score
            score = self._calculate_match_score(user_vector, project, user_preferences)
            
            match_scores.append({
                'project_id': project['project_id'],
                'project_name': project['project_name'],
                'branch': project['branch'],
                'category': project['category'],
                'score': score,
                'reasons': self._explain_match(user_preferences, project),
                'requirements': project.get('required_credentials', 'Basic volunteer requirements'),
                'time_commitment': self._describe_time_commitment(project),
                'volunteer_count': project.get('unique_volunteers', 0),
                'avg_hours': project.get('avg_hours_per_session', 0)
            })
        
        # Sort by score and return top matches
        match_scores.sort(key=lambda x: x['score'], reverse=True)
        
        return match_scores[:top_k]
    
    def find_proximity_matches(self, user_preferences: Dict[str, Any], 
                             user_location: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find volunteer matches enhanced with proximity, travel time, and transit scoring
        
        Args:
            user_preferences: User preferences and interests
            user_location: User's location (address, city, or landmark)
            top_k: Number of top matches to return
            
        Returns:
            List of enhanced matches with proximity information
        """
        # Get base matches using traditional algorithm
        base_matches = self.find_matches(user_preferences, top_k * 2)  # Get more for reranking
        
        if not user_location:
            # If no location provided, return original matches
            print("ℹ️ No user location provided, returning traditional matches")
            return base_matches[:top_k]
        
        print(f"🌍 Enhancing matches with proximity and transit scoring for location: {user_location}")
        
        # Enhance matches with proximity information
        enhanced_matches = self.proximity_matcher.enhance_project_matches(
            base_matches, user_location, user_preferences
        )
        
        return enhanced_matches[:top_k]
    
    def get_location_analysis(self, user_location: str, 
                            user_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze location accessibility and travel options to all YMCA branches
        
        Args:
            user_location: User's location
            user_preferences: User preferences for transportation
            
        Returns:
            Comprehensive location analysis with travel information
        """
        if not user_preferences:
            user_preferences = {}
        
        print(f"🗺️ Analyzing location accessibility for: {user_location}")
        
        branch_analysis = {}
        
        for branch_name in self.proximity_matcher.branch_locations.keys():
            proximity_info = self.proximity_matcher.calculate_proximity_score(
                user_location, branch_name, user_preferences
            )
            branch_analysis[branch_name] = proximity_info
        
        # Sort branches by proximity score
        sorted_branches = sorted(
            branch_analysis.items(), 
            key=lambda x: x[1]['score'], 
            reverse=True
        )
        
        # Get branch accessibility report
        accessibility_report = self.proximity_matcher.get_branch_accessibility_report()
        
        return {
            "user_location": user_location,
            "branch_analysis": dict(sorted_branches),
            "accessibility_report": accessibility_report,
            "recommendations": self._generate_location_recommendations(sorted_branches, user_preferences)
        }
    
    def _create_user_vector(self, preferences: Dict[str, Any]) -> Dict[str, float]:
        """Create numerical vector from user preferences"""
        vector = {
            'age': preferences.get('age', 35),
            'interests_youth': 1 if 'youth' in str(preferences.get('interests', '')).lower() else 0,
            'interests_fitness': 1 if 'fitness' in str(preferences.get('interests', '')).lower() else 0,
            'interests_events': 1 if 'event' in str(preferences.get('interests', '')).lower() else 0,
            'interests_admin': 1 if 'admin' in str(preferences.get('interests', '')).lower() else 0,
            'availability_weekday': 1 if preferences.get('availability', {}).get('weekday', False) else 0,
            'availability_weekend': 1 if preferences.get('availability', {}).get('weekend', False) else 0,
            'availability_evening': 1 if preferences.get('availability', {}).get('evening', False) else 0,
            'time_commitment': preferences.get('time_commitment', 2),  # 1=low, 2=medium, 3=high
            'location_preference': preferences.get('location', 'any'),
            'experience_level': preferences.get('experience_level', 1),  # 1=beginner, 2=some, 3=experienced
            'is_ymca_member': 1 if preferences.get('is_ymca_member', False) else 0
        }
        
        return vector
    
    def _calculate_match_score(self, user_vector: Dict[str, float], project: pd.Series, preferences: Dict[str, Any]) -> float:
        """Calculate match score between user and project"""
        score = 0.0
        
        # Interest matching (40% weight)
        interest_score = 0
        if user_vector['interests_youth'] and 'youth' in project['category'].lower():
            interest_score += 1
        if user_vector['interests_fitness'] and 'fitness' in project['category'].lower():
            interest_score += 1
        if user_vector['interests_events'] and 'event' in project['category'].lower():
            interest_score += 1
        if user_vector['interests_admin'] and 'admin' in project['category'].lower():
            interest_score += 1
        
        score += interest_score * 0.4
        
        # Time commitment matching (20% weight)
        project_time_commitment = project.get('avg_hours_per_session', 2)
        user_time_commitment = user_vector['time_commitment']
        time_diff = abs(project_time_commitment - user_time_commitment)
        time_score = max(0, 1 - (time_diff / 3))  # Normalize difference
        score += time_score * 0.2
        
        # Location preference (15% weight)
        location_score = 1  # Default to full score
        if preferences.get('location') and preferences['location'] != 'any':
            preferred_location = preferences['location'].lower()
            if preferred_location in project['branch'].lower():
                location_score = 1
            else:
                location_score = 0.5  # Partial score for different location
        
        score += location_score * 0.15
        
        # Project popularity/success (10% weight)
        popularity_score = min(1, project.get('unique_volunteers', 0) / 20)  # Normalize to 0-1
        score += popularity_score * 0.1
        
        # Experience level matching (10% weight)
        # Assume beginners match better with high-support projects
        experience_score = 0.8  # Default good match
        if user_vector['experience_level'] == 1:  # Beginner
            if project.get('unique_volunteers', 0) > 10:  # Well-established program
                experience_score = 1.0
        
        score += experience_score * 0.1
        
        # Age appropriateness (5% weight)
        age_score = 1  # Default appropriate for all ages
        if 'youth' in project['category'].lower() and user_vector['age'] < 25:
            age_score = 1.2  # Bonus for young people in youth programs
        
        score += min(age_score, 1) * 0.05
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _explain_match(self, preferences: Dict[str, Any], project: pd.Series) -> List[str]:
        """Generate explanations for why this is a good match"""
        reasons = []
        
        # Interest alignment
        interests = str(preferences.get('interests', '')).lower()
        category = project['category'].lower()
        
        if 'youth' in interests and 'youth' in category:
            reasons.append("Matches your interest in working with young people")
        if 'fitness' in interests and 'fitness' in category:
            reasons.append("Aligns with your fitness and wellness interests")
        if 'event' in interests and 'event' in category:
            reasons.append("Perfect for your interest in special events")
        
        # Experience level
        volunteer_count = project.get('unique_volunteers', 0)
        if volunteer_count > 15:
            reasons.append("Well-established program with strong volunteer support")
        elif volunteer_count > 5:
            reasons.append("Growing program where you can make a real impact")
        
        # Time commitment
        avg_hours = project.get('avg_hours_per_session', 0)
        if avg_hours <= 2:
            reasons.append("Flexible time commitment that fits busy schedules")
        elif avg_hours <= 4:
            reasons.append("Moderate time commitment with meaningful impact")
        
        # Location convenience
        if preferences.get('location'):
            reasons.append(f"Conveniently located at {project['branch']}")
        
        # Default reasons if no specific matches
        if not reasons:
            reasons.append("Great opportunity to get started with volunteering")
            reasons.append("Supportive environment for new volunteers")
        
        return reasons[:3]  # Return top 3 reasons
    
    def _describe_time_commitment(self, project: pd.Series) -> str:
        """Describe the time commitment for a project"""
        avg_hours = project.get('avg_hours_per_session', 0)
        
        if avg_hours <= 1:
            return "Light commitment (1 hour or less per session)"
        elif avg_hours <= 3:
            return f"Moderate commitment (~{avg_hours:.1f} hours per session)"
        elif avg_hours <= 6:
            return f"Regular commitment (~{avg_hours:.1f} hours per session)"
        else:
            return f"High commitment ({avg_hours:.1f}+ hours per session)"
    
    def predict_volunteer_success(self, user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Predict likelihood of volunteer success and engagement"""
        if not self.models_trained:
            self.train_models()
        
        # Create user feature vector
        user_features = [
            user_preferences.get('age', 35),
            0,  # total_hours (new volunteer)
            0,  # volunteer_sessions (new volunteer) 
            0,  # unique_projects (new volunteer)
            0,  # engagement_score (new volunteer)
            0,  # loyalty_score (new volunteer)
            user_preferences.get('time_commitment', 2)  # intensity_score estimate
        ]
        
        # Scale features
        user_features_scaled = self.scaler.transform([user_features])
        
        # Predict cluster
        cluster = self.volunteer_clusterer.predict(user_features_scaled)[0]
        
        # Predict success probability
        success_prob = 0.7  # Default probability
        if hasattr(self.success_predictor, 'predict_proba'):
            try:
                success_prob = self.success_predictor.predict_proba(user_features_scaled)[0][1]
            except:
                pass
        
        # Generate insights
        cluster_insights = self._get_cluster_insights(cluster)
        
        return {
            'volunteer_cluster': cluster,
            'success_probability': success_prob,
            'predicted_persona': self._map_cluster_to_persona(cluster),
            'insights': cluster_insights,
            'recommendations': self._get_success_recommendations(cluster, success_prob)
        }
    
    def _get_cluster_insights(self, cluster: int) -> Dict[str, Any]:
        """Get insights about a volunteer cluster"""
        if cluster in self.volunteer_features['cluster'].values:
            cluster_data = self.volunteer_features[self.volunteer_features['cluster'] == cluster]
            
            return {
                'avg_hours': cluster_data['total_hours'].mean(),
                'avg_sessions': cluster_data['volunteer_sessions'].mean(),
                'common_age_range': f"{cluster_data['age'].quantile(0.25):.0f}-{cluster_data['age'].quantile(0.75):.0f}",
                'retention_rate': (cluster_data['volunteer_sessions'] > 1).mean(),
                'popular_categories': cluster_data['project_categories'].str.split(',').explode().value_counts().head(3).to_dict()
            }
        
        return {'message': 'Insufficient data for cluster insights'}
    
    def _map_cluster_to_persona(self, cluster: int) -> str:
        """Map cluster number to volunteer persona"""
        persona_mapping = {
            0: 'Explorer',
            1: 'Newcomer', 
            2: 'Regular',
            3: 'Committed',
            4: 'Champion'
        }
        
        return persona_mapping.get(cluster, 'Explorer')
    
    def _get_success_recommendations(self, cluster: int, success_prob: float) -> List[str]:
        """Get personalized recommendations for volunteer success"""
        recommendations = []
        
        if success_prob > 0.8:
            recommendations.append("You show strong potential for long-term volunteering engagement!")
            recommendations.append("Consider exploring leadership or mentoring opportunities")
        elif success_prob > 0.6:
            recommendations.append("You're likely to enjoy regular volunteering")
            recommendations.append("Start with 1-2 projects to build your experience")
        else:
            recommendations.append("Try starting with shorter-term or event-based opportunities")
            recommendations.append("Focus on projects that align closely with your interests")
        
        # Cluster-specific recommendations
        persona = self._map_cluster_to_persona(cluster)
        if persona == 'Explorer':
            recommendations.append("Perfect for trying different types of volunteer work")
        elif persona == 'Newcomer':
            recommendations.append("Look for opportunities with strong volunteer support and training")
        
        return recommendations[:3]
    
    def _generate_location_recommendations(self, sorted_branches: List[Tuple], 
                                         user_preferences: Dict[str, Any]) -> List[str]:
        """Generate personalized location and transportation recommendations"""
        recommendations = []
        
        if not sorted_branches:
            return ["Consider exploring different YMCA branches for volunteering opportunities"]
        
        # Best branch recommendation
        best_branch, best_info = sorted_branches[0]
        recommendations.append(f"Based on your location, {best_branch} offers the best combination of accessibility and programs")
        
        # Travel mode recommendations
        best_travel = best_info.get('best_option', {})
        travel_mode = best_travel.get('mode', 'driving')
        travel_time = best_travel.get('duration_minutes', 0)
        
        if travel_time < 15:
            recommendations.append("Very convenient location with short travel time")
        elif travel_time < 30:
            recommendations.append(f"Reasonable {travel_time} minute {travel_mode.replace('_', ' ')} commute")
        else:
            recommendations.append(f"Consider the {travel_time} minute travel time when scheduling volunteer activities")
        
        # Transit-specific recommendations
        transport_prefs = user_preferences.get('transportation', {})
        has_car = transport_prefs.get('has_car', True)
        
        if not has_car:
            # Find best transit-accessible branches
            transit_branches = [
                (name, info) for name, info in sorted_branches[:3]
                if any(opt.get('mode') == 'transit' and opt.get('transit_score', 0) > 0.5 
                      for opt in info.get('travel_options', []))
            ]
            
            if transit_branches:
                transit_branch = transit_branches[0][0]
                recommendations.append(f"For public transit users, {transit_branch} has the best accessibility")
            else:
                recommendations.append("Consider carpooling or rideshare options for better access to volunteer opportunities")
        
        # Multiple good options
        if len([b for b in sorted_branches[:3] if b[1]['score'] > 0.7]) > 1:
            recommendations.append("You have multiple convenient YMCA locations to choose from")
        
        return recommendations[:3]
    
    def get_branch_recommendations(self, user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend YMCA branches based on user location and preferences"""
        branches = {
            'Blue Ash YMCA': {
                'location': 'Blue Ash, OH',
                'specialties': ['Fitness', 'Youth Programs', 'Competitive Swimming'],
                'volunteer_count': self.insights.get('top_branches', {}).get('Blue Ash', 0),
                'description': 'Full-service branch with diverse programs'
            },
            'M.E. Lyons YMCA': {
                'location': 'Oakley, OH', 
                'specialties': ['Group Exercise', 'Community Events', 'Senior Programs'],
                'volunteer_count': self.insights.get('top_branches', {}).get('M.E. Lyons', 0),
                'description': 'Community-focused branch with strong volunteer culture'
            },
            'Campbell County YMCA': {
                'location': 'Newport, KY',
                'specialties': ['Youth Development', 'Childcare', 'Family Programs'],
                'volunteer_count': self.insights.get('top_branches', {}).get('Campbell County', 0),
                'description': 'Family-oriented branch serving Northern Kentucky'
            },
            'Clippard YMCA': {
                'location': 'Cincinnati, OH',
                'specialties': ['Youth Sports', 'Leadership Development', 'Community Outreach'],
                'volunteer_count': self.insights.get('top_branches', {}).get('Clippard', 0),
                'description': 'Youth-focused branch with strong community ties'
            }
        }
        
        # Score branches based on user preferences
        scored_branches = []
        for branch_name, branch_info in branches.items():
            score = self._score_branch_match(user_preferences, branch_info)
            scored_branches.append({
                'name': branch_name,
                'score': score,
                'info': branch_info
            })
        
        # Sort by score
        scored_branches.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'recommended_branches': scored_branches,
            'total_branches': len(branches)
        }
    
    def _score_branch_match(self, preferences: Dict[str, Any], branch_info: Dict[str, Any]) -> float:
        """Score how well a branch matches user preferences"""
        score = 0.5  # Base score
        
        # Interest matching
        interests = str(preferences.get('interests', '')).lower()
        specialties = [s.lower() for s in branch_info['specialties']]
        
        for specialty in specialties:
            if any(interest in specialty for interest in interests.split()):
                score += 0.2
        
        # Location preference (if specified)
        if preferences.get('location'):
            if preferences['location'].lower() in branch_info['location'].lower():
                score += 0.3
        
        # Volunteer activity level (more active branches might be better for engagement)
        volunteer_count = branch_info.get('volunteer_count', 0)
        if volunteer_count > 50:
            score += 0.1
        
        return min(score, 1.0)

# Example usage
if __name__ == "__main__":
    from data_processor import VolunteerDataProcessor
    
    # Load and process data
    processor = VolunteerDataProcessor("Y Volunteer Raw Data - Jan- August 2025.xlsx")
    volunteer_data = processor.get_volunteer_recommendations_data()
    
    # Create matching engine
    matching_engine = VolunteerMatchingEngine(volunteer_data)
    matching_engine.train_models()
    
    # Test matching
    test_preferences = {
        'age': 28,
        'interests': 'youth development mentoring',
        'availability': {'weekday': True, 'evening': True},
        'time_commitment': 2,
        'location': 'Blue Ash',
        'experience_level': 1
    }
    
    matches = matching_engine.find_matches(test_preferences)
    print("Top Matches:")
    for i, match in enumerate(matches, 1):
        print(f"{i}. {match['project_name']} (Score: {match['score']:.2f})")
        print(f"   Branch: {match['branch']}")
        print(f"   Reasons: {', '.join(match['reasons'])}")
        print()
