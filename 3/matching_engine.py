"""
ML-Powered Volunteer Matching Engine
Uses scikit-learn models with existing volunteer data patterns
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
            
            # Get comprehensive match explanation
            match_explanation = self._explain_match(user_preferences, project)
            
            match_scores.append({
                'project_id': project['project_id'],
                'project_name': project['project_name'],
                'branch': project['branch'],
                'category': project['category'],
                'score': score,
                'match_explanation': match_explanation,
                'reasons': match_explanation['primary_reasons'][:3],  # Keep backward compatibility
                'match_factors': match_explanation['match_factors'],
                'compatibility_score': match_explanation['compatibility_score'],
                'detailed_breakdown': match_explanation['detailed_breakdown'],
                'requirements': project.get('required_credentials', 'Basic volunteer requirements'),
                'time_commitment': self._describe_time_commitment(project),
                'volunteer_count': project.get('unique_volunteers', 0),
                'avg_hours': project.get('avg_hours_per_session', 0)
            })
        
        # Sort by score and return top matches
        match_scores.sort(key=lambda x: x['score'], reverse=True)
        
        return match_scores[:top_k]
    
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
    
    def _explain_match(self, preferences: Dict[str, Any], project: pd.Series) -> Dict[str, Any]:
        """Generate comprehensive explanations for why this is a good match"""
        explanation = {
            'primary_reasons': [],
            'match_factors': {},
            'compatibility_score': 0.0,
            'detailed_breakdown': {}
        }
        
        # Calculate individual factor scores and explanations
        skills_match = self._analyze_skills_match(preferences, project)
        proximity_match = self._analyze_proximity_match(preferences, project)
        history_match = self._analyze_history_match(preferences, project)
        schedule_match = self._analyze_schedule_match(preferences, project)
        experience_match = self._analyze_experience_match(preferences, project)
        
        # Store detailed breakdown
        explanation['detailed_breakdown'] = {
            'skills': skills_match,
            'proximity': proximity_match,
            'history': history_match,
            'schedule': schedule_match,
            'experience': experience_match
        }
        
        # Calculate overall compatibility score
        explanation['compatibility_score'] = (
            skills_match['score'] * 0.35 +
            proximity_match['score'] * 0.20 +
            history_match['score'] * 0.20 +
            schedule_match['score'] * 0.15 +
            experience_match['score'] * 0.10
        )
        
        # Generate primary reasons based on strongest matches
        factors = [
            (skills_match, 'Skills'),
            (proximity_match, 'Location'),
            (history_match, 'Experience'),
            (schedule_match, 'Schedule'),
            (experience_match, 'Level')
        ]
        
        # Sort by score and take top reasons
        factors.sort(key=lambda x: x[0]['score'], reverse=True)
        
        for factor, category in factors[:3]:
            if factor['score'] > 0.6:  # Only include strong matches
                explanation['primary_reasons'].extend(factor['reasons'])
        
        # Generate match factor summary
        explanation['match_factors'] = {
            'skills_alignment': min(100, int(skills_match['score'] * 100)),
            'location_convenience': min(100, int(proximity_match['score'] * 100)),
            'experience_relevance': min(100, int(history_match['score'] * 100)),
            'schedule_compatibility': min(100, int(schedule_match['score'] * 100)),
            'level_appropriateness': min(100, int(experience_match['score'] * 100))
        }
        
        # Ensure we always have at least some reasons
        if not explanation['primary_reasons']:
            explanation['primary_reasons'] = [
                "New volunteer opportunity with good learning potential",
                "Supportive environment for getting started"
            ]
        
        return explanation
    
    def _analyze_skills_match(self, preferences: Dict[str, Any], project: pd.Series) -> Dict[str, Any]:
        """Analyze how well user skills and interests match the project"""
        match_info = {'score': 0.0, 'reasons': [], 'details': {}}
        
        # Extract user interests and skills
        interests = str(preferences.get('interests', '')).lower()
        skills = str(preferences.get('skills', '')).lower()
        combined_skills = f"{interests} {skills}".strip()
        
        # Project information
        category = project['category'].lower()
        project_name = str(project['project_name']).lower()
        sample_activities = str(project.get('sample_activities', '')).lower()
        project_text = f"{category} {project_name} {sample_activities}"
        
        # Skills matching keywords
        skill_keywords = {
            'youth_development': ['youth', 'child', 'teen', 'mentoring', 'tutoring', 'coaching', 'leadership'],
            'fitness_wellness': ['fitness', 'exercise', 'wellness', 'health', 'sport', 'swim', 'gym'],
            'events_admin': ['event', 'planning', 'coordination', 'administrative', 'office', 'organize'],
            'community_service': ['community', 'outreach', 'volunteer', 'service', 'help', 'support'],
            'creative_arts': ['art', 'creative', 'music', 'theater', 'craft', 'design'],
            'technical_skills': ['computer', 'technology', 'data', 'digital', 'tech', 'website']
        }
        
        matched_skills = []
        total_matches = 0
        
        for skill_category, keywords in skill_keywords.items():
            user_has_skill = any(keyword in combined_skills for keyword in keywords)
            project_needs_skill = any(keyword in project_text for keyword in keywords)
            
            if user_has_skill and project_needs_skill:
                matched_skills.append(skill_category)
                total_matches += 1
                
                # Generate specific reasons
                if 'youth' in skill_category and user_has_skill:
                    match_info['reasons'].append("Your youth development interests perfectly align with this project")
                elif 'fitness' in skill_category and user_has_skill:
                    match_info['reasons'].append("Your fitness and wellness background is highly valuable here")
                elif 'event' in skill_category and user_has_skill:
                    match_info['reasons'].append("Your event planning skills are exactly what this project needs")
                elif 'community' in skill_category and user_has_skill:
                    match_info['reasons'].append("Your community service passion matches this opportunity")
        
        # Calculate score based on matches
        if total_matches >= 2:
            match_info['score'] = 0.9
        elif total_matches == 1:
            match_info['score'] = 0.7
        elif interests and any(word in project_text for word in interests.split()):
            match_info['score'] = 0.5
            match_info['reasons'].append("Good potential for skill development in this area")
        else:
            match_info['score'] = 0.3
        
        match_info['details'] = {
            'matched_skill_categories': matched_skills,
            'total_skill_matches': total_matches,
            'user_interests': interests,
            'project_category': category
        }
        
        return match_info
    
    def _analyze_proximity_match(self, preferences: Dict[str, Any], project: pd.Series) -> Dict[str, Any]:
        """Analyze location convenience and proximity factors"""
        match_info = {'score': 0.0, 'reasons': [], 'details': {}}
        
        project_branch = project['branch']
        user_location = preferences.get('location_preference', '').lower()
        
        # Branch proximity mapping (simplified - in real system could use actual distances)
        branch_proximity = {
            'blue ash': ['blue ash', 'mason', 'sharonville', 'montgomery'],
            'm.e. lyons': ['oakley', 'hyde park', 'madeira', 'mariemont'],
            'campbell county': ['newport', 'bellevue', 'dayton', 'fort thomas'],
            'clippard': ['western hills', 'price hill', 'cheviot', 'delhi']
        }
        
        # Direct branch match
        if user_location and user_location in project_branch.lower():
            match_info['score'] = 1.0
            match_info['reasons'].append(f"Located at your preferred {project_branch} branch")
        
        # Proximity match
        elif user_location:
            for branch, nearby_areas in branch_proximity.items():
                if branch in project_branch.lower() and any(area in user_location for area in nearby_areas):
                    match_info['score'] = 0.8
                    match_info['reasons'].append(f"Conveniently located near your area at {project_branch}")
                    break
            else:
                match_info['score'] = 0.4
                match_info['reasons'].append(f"Accessible location at {project_branch}")
        
        # No location preference specified
        else:
            match_info['score'] = 0.6  # Neutral score
        
        # Consider branch popularity/accessibility
        volunteer_count = project.get('unique_volunteers', 0)
        if volunteer_count > 20:
            match_info['reasons'].append("Popular branch with excellent facilities and parking")
        
        match_info['details'] = {
            'project_branch': project_branch,
            'user_location_preference': user_location,
            'distance_category': 'exact' if match_info['score'] >= 1.0 else 'nearby' if match_info['score'] >= 0.7 else 'accessible'
        }
        
        return match_info
    
    def _analyze_history_match(self, preferences: Dict[str, Any], project: pd.Series) -> Dict[str, Any]:
        """Analyze how project aligns with user's volunteer history and patterns"""
        match_info = {'score': 0.0, 'reasons': [], 'details': {}}
        
        # Extract historical preferences from affinity data
        branch_affinity = preferences.get('affinity', {}).get('branches', {})
        category_affinity = preferences.get('affinity', {}).get('categories', {})
        volunteer_type = preferences.get('volunteer_type', '')
        
        project_branch = project['branch']
        project_category = project['category']
        
        # Branch history match
        branch_score = 0
        if branch_affinity:
            if project_branch in branch_affinity:
                branch_score = min(1.0, branch_affinity[project_branch] / 5)  # Normalize
                match_info['reasons'].append(f"You've successfully volunteered at {project_branch} before")
        
        # Category history match
        category_score = 0
        if category_affinity:
            if project_category in category_affinity:
                category_score = min(1.0, category_affinity[project_category] / 3)  # Normalize
                match_info['reasons'].append(f"Great fit based on your {project_category} volunteer history")
        
        # Volunteer type alignment
        type_score = 0
        if volunteer_type:
            project_hours = project.get('avg_hours_per_session', 0)
            project_volunteers = project.get('unique_volunteers', 0)
            
            if volunteer_type == 'Champion' and project_hours > 3:
                type_score = 0.9
                match_info['reasons'].append("Perfect for experienced volunteers like yourself")
            elif volunteer_type == 'Regular' and 1 <= project_hours <= 4:
                type_score = 0.8
                match_info['reasons'].append("Ideal time commitment for regular volunteers")
            elif volunteer_type == 'Explorer' and project_volunteers > 10:
                type_score = 0.7
                match_info['reasons'].append("Well-established program great for exploring new opportunities")
            elif volunteer_type == 'Newcomer' and project_volunteers > 5:
                type_score = 0.6
                match_info['reasons'].append("Supportive environment perfect for new volunteers")
        
        # Calculate overall history score
        match_info['score'] = (branch_score * 0.4 + category_score * 0.4 + type_score * 0.2)
        
        # If no history, provide encouragement
        if match_info['score'] < 0.3 and not branch_affinity and not category_affinity:
            match_info['score'] = 0.5
            match_info['reasons'].append("Great opportunity to start building your volunteer experience")
        
        match_info['details'] = {
            'branch_history_score': branch_score,
            'category_history_score': category_score,
            'volunteer_type_match_score': type_score,
            'has_volunteer_history': bool(branch_affinity or category_affinity)
        }
        
        return match_info
    
    def _analyze_schedule_match(self, preferences: Dict[str, Any], project: pd.Series) -> Dict[str, Any]:
        """Analyze schedule and time commitment compatibility"""
        match_info = {'score': 0.0, 'reasons': [], 'details': {}}
        
        # User availability preferences
        availability = preferences.get('availability', {})
        user_time_commitment = preferences.get('time_commitment', 2)  # 1=low, 2=medium, 3=high
        
        # Project time characteristics
        project_hours = project.get('avg_hours_per_session', 2)
        project_sessions = project.get('total_sessions', 0)
        
        # Time commitment matching
        time_score = 0
        if user_time_commitment == 1:  # Low commitment preference
            if project_hours <= 2:
                time_score = 0.9
                match_info['reasons'].append("Perfect for your flexible schedule with short time commitments")
            elif project_hours <= 4:
                time_score = 0.6
                match_info['reasons'].append("Manageable time commitment that fits most schedules")
        elif user_time_commitment == 2:  # Medium commitment
            if 1 <= project_hours <= 4:
                time_score = 0.8
                match_info['reasons'].append("Ideal time commitment for regular volunteer involvement")
        elif user_time_commitment == 3:  # High commitment
            if project_hours >= 3:
                time_score = 0.9
                match_info['reasons'].append("Great opportunity for deeper volunteer engagement")
        
        # Schedule flexibility based on availability
        schedule_score = 0
        if availability:
            if availability.get('weekday', False) and availability.get('weekend', False):
                schedule_score = 0.9
                match_info['reasons'].append("Your flexible availability fits perfectly with volunteer opportunities")
            elif availability.get('weekday', False) or availability.get('weekend', False):
                schedule_score = 0.7
                match_info['reasons'].append("Good scheduling options available for this opportunity")
            elif availability.get('evening', False):
                schedule_score = 0.6
                match_info['reasons'].append("Evening volunteer options may be available")
        else:
            schedule_score = 0.5  # Neutral if no availability specified
        
        # Project frequency consideration
        frequency_score = 0
        if project_sessions > 20:
            frequency_score = 0.8
            match_info['reasons'].append("Flexible scheduling with multiple session options")
        elif project_sessions > 5:
            frequency_score = 0.6
        else:
            frequency_score = 0.4
        
        match_info['score'] = (time_score * 0.5 + schedule_score * 0.3 + frequency_score * 0.2)
        
        match_info['details'] = {
            'user_time_commitment_level': user_time_commitment,
            'project_hours_per_session': project_hours,
            'time_compatibility_score': time_score,
            'schedule_flexibility_score': schedule_score,
            'user_availability': availability
        }
        
        return match_info
    
    def _analyze_experience_match(self, preferences: Dict[str, Any], project: pd.Series) -> Dict[str, Any]:
        """Analyze experience level and project difficulty alignment"""
        match_info = {'score': 0.0, 'reasons': [], 'details': {}}
        
        user_experience = preferences.get('experience_level', 1)  # 1=beginner, 2=some, 3=experienced
        project_volunteers = project.get('unique_volunteers', 0)
        project_hours = project.get('avg_hours_per_session', 0)
        credentials_required = str(project.get('required_credentials', '')).lower()
        
        # Experience level matching
        if user_experience == 1:  # Beginner
            if project_volunteers > 15:  # Well-established program
                match_info['score'] = 0.9
                match_info['reasons'].append("Excellent support system for new volunteers")
            elif project_volunteers > 5:
                match_info['score'] = 0.7
                match_info['reasons'].append("Good beginner-friendly environment with volunteer support")
            elif 'basic' in credentials_required or 'none' in credentials_required:
                match_info['score'] = 0.8
                match_info['reasons'].append("No special credentials required - perfect for getting started")
            else:
                match_info['score'] = 0.5
                match_info['reasons'].append("Opportunity to develop new volunteer skills")
        
        elif user_experience == 2:  # Some experience
            if project_hours <= 4:
                match_info['score'] = 0.8
                match_info['reasons'].append("Perfect match for your volunteer experience level")
            elif project_volunteers > 10:
                match_info['score'] = 0.7
                match_info['reasons'].append("Great way to expand your volunteer experience")
        
        elif user_experience == 3:  # Experienced
            if project_hours > 3 or 'leadership' in credentials_required:
                match_info['score'] = 0.9
                match_info['reasons'].append("Excellent opportunity to utilize your volunteer expertise")
            elif project_volunteers < 10:
                match_info['score'] = 0.8
                match_info['reasons'].append("Your experience could make a significant impact here")
            else:
                match_info['score'] = 0.7
        
        # Credential requirements consideration
        if 'background check' in credentials_required:
            match_info['details']['requires_background_check'] = True
            if user_experience >= 2:
                match_info['reasons'].append("Your experience makes credential requirements manageable")
        
        # Age appropriateness
        user_age = preferences.get('age', 35)
        if 'youth' in project['category'].lower():
            if 18 <= user_age <= 65:
                match_info['score'] = min(match_info['score'] + 0.1, 1.0)
                match_info['reasons'].append("Great age match for youth development programs")
        
        match_info['details'] = {
            'user_experience_level': user_experience,
            'project_complexity_indicators': {
                'volunteer_count': project_volunteers,
                'hours_per_session': project_hours,
                'credentials_required': credentials_required
            },
            'experience_match_category': 'perfect' if match_info['score'] >= 0.8 else 'good' if match_info['score'] >= 0.6 else 'developing'
        }
        
        return match_info
    
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
