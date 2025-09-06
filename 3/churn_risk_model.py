"""
Volunteer Churn Risk Model with Scoring and Intervention Insights

This module provides:
1. Individual volunteer churn risk scores (0-100)
2. Top reasons for churn risk
3. Personalized intervention recommendations
4. Risk trend analysis
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class VolunteerChurnRiskModel:
    def __init__(self, volunteer_data: Dict[str, Any]):
        self.volunteer_data = volunteer_data
        self.volunteers_df = volunteer_data.get('volunteers')
        self.interactions_df = volunteer_data.get('interactions')
        self.projects_df = volunteer_data.get('projects')
        
        # ML Models
        self.churn_predictor = GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        self.feature_scaler = StandardScaler()
        
        # Feature importance storage
        self.feature_names = []
        self.feature_importance = {}
        
        # Risk categories
        self.risk_categories = {
            'low': (0, 30),
            'medium': (30, 70), 
            'high': (70, 100)
        }
        
        # Intervention templates
        self.interventions = {
            'low_engagement': [
                "Schedule a check-in call to understand their experience",
                "Offer additional training or mentorship opportunities",
                "Connect them with a volunteer buddy or mentor"
            ],
            'scheduling_issues': [
                "Offer more flexible scheduling options",
                "Provide advance notice of schedule changes",
                "Match with projects that have consistent timing"
            ],
            'role_mismatch': [
                "Reassess their interests and skills through a survey",
                "Offer to try different volunteer roles",
                "Provide role shadowing opportunities"
            ],
            'lack_recognition': [
                "Acknowledge their contributions publicly", 
                "Send personalized thank you notes",
                "Invite them to recognition events"
            ],
            'burnout_risk': [
                "Reduce volunteer workload temporarily",
                "Offer longer breaks between assignments",
                "Provide stress management resources"
            ],
            'social_isolation': [
                "Introduce them to other volunteers",
                "Invite to social events and gatherings",
                "Pair with a volunteer partner"
            ]
        }
        
        self.model_trained = False
        self._prepare_churn_data()
    
    def _prepare_churn_data(self):
        """Prepare data for churn prediction modeling"""
        if self.volunteers_df is None or self.interactions_df is None:
            print("⚠️  Warning: Missing volunteer or interaction data for churn model")
            return
        
        print("🔧 Preparing churn prediction data...")
        
        # Create volunteer features with engagement metrics
        self.volunteer_features = self._extract_churn_features()
        
        # Define churn labels (volunteers who haven't been active recently)
        self.churn_labels = self._define_churn_labels()
        
        print(f"✅ Churn data prepared: {len(self.volunteer_features)} volunteers")
    
    def _extract_churn_features(self) -> pd.DataFrame:
        """Extract features that predict volunteer churn"""
        features = self.volunteers_df.copy()
        
        # Basic demographics
        le_gender = LabelEncoder()
        features['gender_encoded'] = le_gender.fit_transform(features['gender'].fillna('Unknown'))
        
        le_race = LabelEncoder()
        features['race_encoded'] = le_race.fit_transform(features['race_ethnicity'].fillna('Unknown'))
        
        # Age groups
        features['age_group'] = pd.cut(features['age'], bins=[0, 25, 35, 50, 65, 100], 
                                     labels=[1, 2, 3, 4, 5]).fillna(3).astype(float)
        
        # Engagement metrics
        features['total_hours'] = features['total_hours'].fillna(0)
        features['volunteer_sessions'] = features['volunteer_sessions'].fillna(0)
        features['unique_projects'] = features['unique_projects'].fillna(0)
        features['volunteer_tenure_days'] = features['volunteer_tenure_days'].fillna(0)
        features['avg_hours_per_session'] = features['avg_hours_per_session'].fillna(0)
        
        # Calculate risk indicators
        features['hours_per_day_ratio'] = np.where(
            features['volunteer_tenure_days'] > 0,
            features['total_hours'] / features['volunteer_tenure_days'],
            0
        )
        
        features['session_frequency'] = np.where(
            features['volunteer_tenure_days'] > 0,
            features['volunteer_sessions'] / (features['volunteer_tenure_days'] / 30),  # sessions per month
            0
        )
        
        features['project_diversity_ratio'] = np.where(
            features['volunteer_sessions'] > 0,
            features['unique_projects'] / features['volunteer_sessions'],
            0
        )
        
        # Recent activity indicators
        if self.interactions_df is not None:
            recent_activity = self._calculate_recent_activity()
            features = features.merge(recent_activity, on='contact_id', how='left')
        
        # Fill missing values
        numeric_columns = features.select_dtypes(include=[np.number]).columns
        features[numeric_columns] = features[numeric_columns].fillna(0)
        
        return features
    
    def _calculate_recent_activity(self) -> pd.DataFrame:
        """Calculate recent activity metrics for each volunteer"""
        interactions = self.interactions_df.copy()
        
        # Convert date to datetime if it's not already
        if 'date' in interactions.columns:
            interactions['date'] = pd.to_datetime(interactions['date'])
            
            # Calculate days since last activity
            max_date = interactions['date'].max()
            last_activity = interactions.groupby('contact_id')['date'].max().reset_index()
            last_activity['days_since_last_activity'] = (max_date - last_activity['date']).dt.days
            
            # Recent activity trends (last 30, 60, 90 days)
            for days in [30, 60, 90]:
                cutoff_date = max_date - timedelta(days=days)
                recent_interactions = interactions[interactions['date'] >= cutoff_date]
                
                activity_stats = recent_interactions.groupby('contact_id').agg({
                    'hours': 'sum',
                    'date': 'count'
                }).reset_index()
                activity_stats.columns = ['contact_id', f'hours_last_{days}d', f'sessions_last_{days}d']
                
                last_activity = last_activity.merge(activity_stats, on='contact_id', how='left')
            
            # Fill missing values with 0 (no recent activity)
            activity_columns = [col for col in last_activity.columns if col not in ['contact_id', 'date']]
            last_activity[activity_columns] = last_activity[activity_columns].fillna(0)
            
            return last_activity[['contact_id', 'days_since_last_activity', 
                                'hours_last_30d', 'sessions_last_30d',
                                'hours_last_60d', 'sessions_last_60d', 
                                'hours_last_90d', 'sessions_last_90d']]
        
        # Return empty DataFrame with required columns if no date data
        return pd.DataFrame(columns=['contact_id', 'days_since_last_activity', 
                                   'hours_last_30d', 'sessions_last_30d',
                                   'hours_last_60d', 'sessions_last_60d',
                                   'hours_last_90d', 'sessions_last_90d'])
    
    def _define_churn_labels(self) -> pd.Series:
        """Define churn labels based on recent activity"""
        if 'days_since_last_activity' not in self.volunteer_features.columns:
            # Fallback: use low session count as churn indicator
            return (self.volunteer_features['volunteer_sessions'] <= 1).astype(int)
        
        # Consider volunteers churned if they haven't been active in 90+ days
        # and had at least some prior activity
        churned = (
            (self.volunteer_features['days_since_last_activity'] >= 90) & 
            (self.volunteer_features['volunteer_sessions'] >= 1)
        ).astype(int)
        
        return churned
    
    def train_model(self):
        """Train the churn prediction model"""
        if len(self.volunteer_features) < 50:
            print("⚠️  Insufficient data to train churn model (need at least 50 volunteers)")
            return
        
        print("🤖 Training churn prediction model...")
        
        # Select features for training
        feature_columns = [
            'age', 'gender_encoded', 'race_encoded', 'age_group',
            'total_hours', 'volunteer_sessions', 'unique_projects', 
            'volunteer_tenure_days', 'avg_hours_per_session',
            'hours_per_day_ratio', 'session_frequency', 'project_diversity_ratio',
            'days_since_last_activity', 'hours_last_30d', 'sessions_last_30d',
            'hours_last_60d', 'sessions_last_60d', 'hours_last_90d', 'sessions_last_90d'
        ]
        
        # Filter to available columns
        available_features = [col for col in feature_columns if col in self.volunteer_features.columns]
        
        X = self.volunteer_features[available_features].fillna(0)
        y = self.churn_labels
        
        self.feature_names = available_features
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        X_train_scaled = self.feature_scaler.fit_transform(X_train)
        X_test_scaled = self.feature_scaler.transform(X_test)
        
        # Train model
        self.churn_predictor.fit(X_train_scaled, y_train)
        
        # Evaluate model
        y_pred = self.churn_predictor.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Store feature importance
        self.feature_importance = dict(zip(self.feature_names, self.churn_predictor.feature_importances_))
        
        self.model_trained = True
        print(f"✅ Churn model trained successfully! Accuracy: {accuracy:.2f}")
    
    def predict_churn_risk(self, contact_id: int) -> Dict[str, Any]:
        """Predict churn risk for a specific volunteer"""
        if not self.model_trained:
            self.train_model()
        
        if not self.model_trained:
            return self._get_default_risk_assessment(contact_id)
        
        # Find volunteer in dataset
        volunteer = self.volunteer_features[self.volunteer_features['contact_id'] == contact_id]
        
        if volunteer.empty:
            return {'error': f'Volunteer with contact_id {contact_id} not found'}
        
        volunteer = volunteer.iloc[0]
        
        # Prepare features
        feature_vector = volunteer[self.feature_names].fillna(0).values.reshape(1, -1)
        feature_vector_scaled = self.feature_scaler.transform(feature_vector)
        
        # Get predictions
        churn_probability = self.churn_predictor.predict_proba(feature_vector_scaled)[0][1]
        risk_score = int(churn_probability * 100)  # Convert to 0-100 scale
        
        # Determine risk category
        risk_category = self._get_risk_category(risk_score)
        
        # Identify top risk factors
        top_risk_factors = self._identify_risk_factors(volunteer)
        
        # Generate intervention recommendations
        interventions = self._generate_interventions(top_risk_factors, volunteer)
        
        return {
            'contact_id': contact_id,
            'risk_score': risk_score,
            'risk_category': risk_category,
            'churn_probability': churn_probability,
            'top_risk_factors': top_risk_factors,
            'intervention_recommendations': interventions,
            'volunteer_summary': self._get_volunteer_summary(volunteer),
            'generated_at': datetime.now().isoformat()
        }
    
    def batch_predict_churn_risk(self, contact_ids: List[int] = None) -> List[Dict[str, Any]]:
        """Predict churn risk for multiple volunteers"""
        if contact_ids is None:
            # Predict for all volunteers
            contact_ids = self.volunteer_features['contact_id'].tolist()
        
        results = []
        for contact_id in contact_ids:
            risk_assessment = self.predict_churn_risk(contact_id)
            results.append(risk_assessment)
        
        return results
    
    def get_high_risk_volunteers(self, threshold: int = 70, limit: int = 20) -> List[Dict[str, Any]]:
        """Get list of volunteers with high churn risk"""
        if not self.model_trained:
            self.train_model()
        
        if not self.model_trained:
            return []
        
        # Predict for all volunteers
        all_predictions = self.batch_predict_churn_risk()
        
        # Filter high-risk volunteers
        high_risk = [pred for pred in all_predictions if 
                    pred.get('risk_score', 0) >= threshold and 
                    'error' not in pred]
        
        # Sort by risk score (descending)
        high_risk.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return high_risk[:limit]
    
    def _get_risk_category(self, risk_score: int) -> str:
        """Determine risk category from score"""
        for category, (min_score, max_score) in self.risk_categories.items():
            if min_score <= risk_score < max_score:
                return category
        return 'high'  # Default for scores >= 70
    
    def _identify_risk_factors(self, volunteer: pd.Series) -> List[Dict[str, Any]]:
        """Identify the top risk factors for a volunteer"""
        risk_factors = []
        
        # Check various risk indicators
        if volunteer.get('days_since_last_activity', 0) > 60:
            risk_factors.append({
                'factor': 'Recent Inactivity',
                'description': f"No activity in {volunteer.get('days_since_last_activity', 0)} days",
                'severity': 'high' if volunteer.get('days_since_last_activity', 0) > 90 else 'medium',
                'impact_score': 0.8
            })
        
        if volunteer.get('session_frequency', 0) < 0.5:  # Less than 0.5 sessions per month
            risk_factors.append({
                'factor': 'Low Engagement Frequency',
                'description': 'Infrequent volunteer participation',
                'severity': 'medium',
                'impact_score': 0.6
            })
        
        if volunteer.get('avg_hours_per_session', 0) < 1:
            risk_factors.append({
                'factor': 'Low Time Investment',
                'description': 'Spending very little time per volunteer session',
                'severity': 'medium',
                'impact_score': 0.5
            })
        
        if volunteer.get('unique_projects', 0) <= 1 and volunteer.get('volunteer_sessions', 0) > 3:
            risk_factors.append({
                'factor': 'Limited Project Diversity',
                'description': 'Stuck in same volunteer role without variety',
                'severity': 'low',
                'impact_score': 0.4
            })
        
        if volunteer.get('volunteer_tenure_days', 0) < 30:
            risk_factors.append({
                'factor': 'New Volunteer',
                'description': 'Recently started volunteering, high early-stage churn risk',
                'severity': 'medium',
                'impact_score': 0.7
            })
        
        # Age-related risk factors
        age = volunteer.get('age', 0)
        if age < 25:
            risk_factors.append({
                'factor': 'Young Volunteer',
                'description': 'Younger volunteers often have changing life circumstances',
                'severity': 'low',
                'impact_score': 0.3
            })
        elif age > 65:
            risk_factors.append({
                'factor': 'Senior Volunteer',
                'description': 'May face health or mobility challenges affecting participation',
                'severity': 'low',
                'impact_score': 0.3
            })
        
        # Sort by impact score (descending) and return top 5
        risk_factors.sort(key=lambda x: x['impact_score'], reverse=True)
        return risk_factors[:5]
    
    def _generate_interventions(self, risk_factors: List[Dict[str, Any]], volunteer: pd.Series) -> List[Dict[str, Any]]:
        """Generate personalized intervention recommendations"""
        interventions = []
        
        # Map risk factors to intervention categories
        factor_mapping = {
            'Recent Inactivity': 'low_engagement',
            'Low Engagement Frequency': 'scheduling_issues',
            'Low Time Investment': 'role_mismatch',
            'Limited Project Diversity': 'role_mismatch',
            'New Volunteer': 'social_isolation',
            'Young Volunteer': 'scheduling_issues',
            'Senior Volunteer': 'scheduling_issues'
        }
        
        # Generate interventions based on top risk factors
        for risk_factor in risk_factors[:3]:  # Top 3 risk factors
            factor_name = risk_factor['factor']
            intervention_category = factor_mapping.get(factor_name, 'low_engagement')
            
            intervention_options = self.interventions[intervention_category]
            
            # Select best intervention based on volunteer profile
            selected_intervention = self._select_best_intervention(
                intervention_options, volunteer, risk_factor
            )
            
            interventions.append({
                'risk_factor': factor_name,
                'intervention': selected_intervention,
                'category': intervention_category,
                'priority': risk_factor['severity'],
                'expected_impact': risk_factor['impact_score']
            })
        
        # Add general interventions if not many specific ones
        if len(interventions) < 2:
            interventions.append({
                'risk_factor': 'General Engagement',
                'intervention': 'Send personalized check-in message about volunteer experience',
                'category': 'low_engagement',
                'priority': 'low',
                'expected_impact': 0.4
            })
        
        return interventions
    
    def _select_best_intervention(self, intervention_options: List[str], 
                                volunteer: pd.Series, risk_factor: Dict[str, Any]) -> str:
        """Select the most appropriate intervention for a volunteer"""
        # Simple selection logic - can be enhanced with more sophisticated matching
        
        # For new volunteers, prioritize mentorship
        if volunteer.get('volunteer_tenure_days', 0) < 60:
            mentorship_options = [opt for opt in intervention_options if 'mentor' in opt.lower()]
            if mentorship_options:
                return mentorship_options[0]
        
        # For inactive volunteers, prioritize direct outreach
        if 'inactivity' in risk_factor['factor'].lower():
            outreach_options = [opt for opt in intervention_options if 'call' in opt.lower() or 'contact' in opt.lower()]
            if outreach_options:
                return outreach_options[0]
        
        # Default to first option
        return intervention_options[0] if intervention_options else "Schedule follow-up conversation"
    
    def _get_volunteer_summary(self, volunteer: pd.Series) -> Dict[str, Any]:
        """Generate a summary of volunteer's profile"""
        return {
            'name': f"Volunteer {volunteer.get('contact_id', 'Unknown')}",
            'total_hours': volunteer.get('total_hours', 0),
            'volunteer_sessions': volunteer.get('volunteer_sessions', 0),
            'unique_projects': volunteer.get('unique_projects', 0),
            'tenure_days': volunteer.get('volunteer_tenure_days', 0),
            'last_activity_days_ago': volunteer.get('days_since_last_activity', 0),
            'age': volunteer.get('age', None),
            'is_ymca_member': volunteer.get('is_ymca_member', False)
        }
    
    def _get_default_risk_assessment(self, contact_id: int) -> Dict[str, Any]:
        """Provide default risk assessment when model can't be trained"""
        volunteer = self.volunteer_features[self.volunteer_features['contact_id'] == contact_id]
        
        if volunteer.empty:
            return {'error': f'Volunteer with contact_id {contact_id} not found'}
        
        volunteer = volunteer.iloc[0]
        
        # Simple rule-based risk assessment
        risk_score = 50  # Default medium risk
        
        # Adjust based on available indicators
        if volunteer.get('days_since_last_activity', 0) > 90:
            risk_score += 30
        elif volunteer.get('days_since_last_activity', 0) > 60:
            risk_score += 20
        
        if volunteer.get('volunteer_sessions', 0) <= 1:
            risk_score += 15
        
        if volunteer.get('volunteer_tenure_days', 0) < 30:
            risk_score += 10
        
        risk_score = min(risk_score, 100)  # Cap at 100
        risk_category = self._get_risk_category(risk_score)
        
        return {
            'contact_id': contact_id,
            'risk_score': risk_score,
            'risk_category': risk_category,
            'churn_probability': risk_score / 100,
            'top_risk_factors': [{'factor': 'Assessment based on simple rules', 'description': 'Model training data insufficient'}],
            'intervention_recommendations': [{'intervention': 'Schedule personal check-in call', 'priority': 'medium'}],
            'volunteer_summary': self._get_volunteer_summary(volunteer),
            'generated_at': datetime.now().isoformat(),
            'note': 'Risk assessment based on simple rules due to insufficient training data'
        }
    
    def get_model_insights(self) -> Dict[str, Any]:
        """Get insights about the churn model performance and feature importance"""
        if not self.model_trained:
            return {'error': 'Model not trained yet'}
        
        # Sort features by importance
        sorted_features = sorted(self.feature_importance.items(), 
                               key=lambda x: x[1], reverse=True)
        
        return {
            'model_trained': self.model_trained,
            'total_volunteers': len(self.volunteer_features),
            'churned_volunteers': self.churn_labels.sum(),
            'churn_rate': self.churn_labels.mean(),
            'top_predictive_features': sorted_features[:10],
            'feature_importance': self.feature_importance,
            'risk_categories': self.risk_categories,
            'available_interventions': list(self.interventions.keys())
        }

# Example usage
if __name__ == "__main__":
    # This would be used with real volunteer data
    sample_data = {
        'volunteers': pd.DataFrame(),
        'interactions': pd.DataFrame(), 
        'projects': pd.DataFrame()
    }
    
    churn_model = VolunteerChurnRiskModel(sample_data)
    print("Churn risk model initialized")