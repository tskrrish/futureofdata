"""
Advanced Data Processor for YMCA Volunteer Data
Cleans, structures, and extracts insights from volunteer Excel data
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import re
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class VolunteerDataProcessor:
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.raw_data = None
        self.processed_data = None
        self.volunteer_profiles = None
        self.project_catalog = None
        self.insights = {}
        
    def load_and_combine_data(self) -> pd.DataFrame:
        """Load all Excel sheets and combine into master dataset"""
        print("🔄 Loading Excel data...")
        
        # Read all sheets
        excel_file = pd.ExcelFile(self.excel_path)
        all_data = []
        
        # Skip problematic sheets and focus on main data sheets
        main_sheets = ['Branch - Hours', 'Branch - Vol', 'Tag - Vol', 'Members', 'YDE - Hours', 'YDE - Vol']
        
        for sheet_name in excel_file.sheet_names:
            if any(main_sheet in sheet_name for main_sheet in main_sheets):
                try:
                    df = pd.read_excel(self.excel_path, sheet_name=sheet_name)
                    if len(df.columns) >= 20 and len(df) > 10:  # Valid data sheet
                        df['source_sheet'] = sheet_name
                        all_data.append(df)
                        print(f"  ✅ Loaded {sheet_name}: {len(df)} records")
                except Exception as e:
                    print(f"  ⚠️  Skipped {sheet_name}: {e}")
        
        # Combine all data
        if all_data:
            self.raw_data = pd.concat(all_data, ignore_index=True)
            print(f"🎉 Combined dataset: {len(self.raw_data)} total records")
            return self.raw_data
        else:
            raise ValueError("No valid data sheets found!")
    
    def clean_data(self) -> pd.DataFrame:
        """Clean and standardize the volunteer data"""
        if self.raw_data is None:
            self.load_and_combine_data()
        
        print("🧹 Cleaning data...")
        df = self.raw_data.copy()
        
        # Standardize column names
        df.columns = [self._clean_column_name(col) for col in df.columns]
        
        # Clean key fields
        df = self._clean_dates(df)
        df = self._clean_demographics(df)
        df = self._clean_projects(df)
        df = self._clean_contacts(df)
        
        # Remove duplicates based on key fields
        df = df.drop_duplicates(subset=['contact_id', 'project_id', 'date'], keep='first')
        
        self.processed_data = df
        print(f"✨ Cleaned data: {len(df)} records")
        return df
    
    def _clean_column_name(self, col: str) -> str:
        """Standardize column names"""
        col = str(col).lower()
        col = re.sub(r'[^\w\s]', '', col)
        col = re.sub(r'\s+', '_', col)
        return col
    
    def _clean_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize date fields"""
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df['year'] = df['date'].dt.year
            df['month'] = df['date'].dt.month
            df['day_of_week'] = df['date'].dt.day_name()
        
        if 'birth_date' in df.columns:
            df['birth_date'] = pd.to_datetime(df['birth_date'], errors='coerce')
            df['calculated_age'] = (datetime.now() - df['birth_date']).dt.days // 365
            df['age'] = df['calculated_age'].fillna(df.get('age', 0))
        
        return df
    
    def _clean_demographics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean demographic fields"""
        # Gender standardization
        if 'gender' in df.columns:
            df['gender'] = df['gender'].str.title().fillna('Unknown')
        
        # Race/ethnicity standardization
        if 'raceethnicity' in df.columns:
            df['raceethnicity'] = df['raceethnicity'].fillna('Not Specified')
        
        # Age groups
        if 'age' in df.columns:
            df['age_group'] = pd.cut(df['age'], bins=[0, 18, 25, 35, 50, 65, 100], 
                                   labels=['Under 18', '18-24', '25-34', '35-49', '50-64', '65+'])
        
        # YMCA membership status
        if 'are_you_a_ymca_member' in df.columns:
            df['is_ymca_member'] = df['are_you_a_ymca_member'].str.lower().str.contains('yes', na=False)
        
        return df
    
    def _clean_projects(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean project-related fields"""
        # Standardize project names
        if 'project' in df.columns:
            df['project_clean'] = df['project'].str.title()
            df['project_category'] = df['project'].apply(self._extract_project_category)
        
        # Clean project tags
        if 'project_tags' in df.columns:
            df['project_tags_clean'] = df['project_tags'].fillna('General')
        
        # Parse branch information
        if 'branch' in df.columns:
            df['branch_clean'] = df['branch'].str.title()
            df['branch_short'] = df['branch'].apply(self._extract_branch_short_name)
        
        return df
    
    def _clean_contacts(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean contact and personal information"""
        # Clean email addresses
        if 'email' in df.columns:
            df['email'] = df['email'].str.lower().str.strip()
            df['has_email'] = df['email'].notna() & (df['email'] != '')
        
        # Clean phone numbers
        if 'mobile' in df.columns:
            df['mobile'] = df['mobile'].astype(str).str.extract(r'(\d{10,})')
            df['has_phone'] = df['mobile'].notna()
        
        # Clean addresses
        if 'home_city' in df.columns:
            df['home_city'] = df['home_city'].str.title()
        
        if 'home_state' in df.columns:
            df['home_state'] = df['home_state'].str.upper()
        
        return df
    
    def _extract_project_category(self, project_name: str) -> str:
        """Extract project category from project name"""
        if pd.isna(project_name):
            return 'General'
        
        project_name = str(project_name).lower()
        
        if 'youth' in project_name or 'child' in project_name:
            return 'Youth Development'
        elif 'fitness' in project_name or 'group ex' in project_name or 'swim' in project_name:
            return 'Fitness & Wellness'
        elif 'special event' in project_name or 'event' in project_name:
            return 'Special Events'
        elif 'facility' in project_name or 'maintenance' in project_name:
            return 'Facility Support'
        elif 'admin' in project_name or 'office' in project_name:
            return 'Administrative'
        else:
            return 'General'
    
    def _extract_branch_short_name(self, branch_name: str) -> str:
        """Extract short branch name"""
        if pd.isna(branch_name):
            return 'Unknown'
        
        branch_name = str(branch_name)
        if 'Blue Ash' in branch_name:
            return 'Blue Ash'
        elif 'M.E. Lyons' in branch_name:
            return 'M.E. Lyons'
        elif 'Campbell' in branch_name:
            return 'Campbell County'
        elif 'Clippard' in branch_name:
            return 'Clippard'
        elif 'Youth Development' in branch_name:
            return 'YDE'
        else:
            return branch_name.split(' ')[0]
    
    def create_volunteer_profiles(self) -> pd.DataFrame:
        """Create individual volunteer profiles with aggregated stats"""
        if self.processed_data is None:
            self.clean_data()
        
        print("👥 Creating volunteer profiles...")
        
        # Group by volunteer (contact_id)
        profiles = self.processed_data.groupby('contact_id').agg({
            'first_name': 'first',
            'last_name': 'first', 
            'email': 'first',
            'age': 'first',
            'gender': 'first',
            'raceethnicity': 'first',
            'home_city': 'first',
            'home_state': 'first',
            'is_ymca_member': 'first',
            'member_branch': 'first',
            'hours': 'sum',
            'project_id': 'nunique',
            'branch_short': lambda x: ', '.join(x.unique()),
            'project_category': lambda x: ', '.join(x.unique()),
            'date': ['min', 'max', 'count']
        }).reset_index()
        
        # Flatten column names
        profiles.columns = ['contact_id', 'first_name', 'last_name', 'email', 'age', 
                           'gender', 'race_ethnicity', 'home_city', 'home_state', 
                           'is_ymca_member', 'member_branch', 'total_hours', 
                           'unique_projects', 'branches_volunteered', 'project_categories',
                           'first_volunteer_date', 'last_volunteer_date', 'volunteer_sessions']
        
        # Calculate volunteer tenure and engagement
        profiles['volunteer_tenure_days'] = (profiles['last_volunteer_date'] - profiles['first_volunteer_date']).dt.days
        profiles['avg_hours_per_session'] = profiles['total_hours'] / profiles['volunteer_sessions']
        profiles['volunteer_frequency'] = profiles['volunteer_sessions'] / (profiles['volunteer_tenure_days'] + 1) * 30  # sessions per month
        
        # Volunteer type classification
        profiles['volunteer_type'] = profiles.apply(self._classify_volunteer_type, axis=1)
        
        self.volunteer_profiles = profiles
        print(f"✨ Created {len(profiles)} volunteer profiles")
        return profiles
    
    def _classify_volunteer_type(self, row) -> str:
        """Classify volunteer based on engagement patterns"""
        hours = row['total_hours']
        sessions = row['volunteer_sessions'] 
        projects = row['unique_projects']
        
        if hours >= 100:
            return 'Champion'
        elif hours >= 50:
            return 'Committed'
        elif sessions >= 10:
            return 'Regular'
        elif projects >= 3:
            return 'Explorer'
        else:
            return 'Newcomer'
    
    def create_project_catalog(self) -> pd.DataFrame:
        """Create project catalog with requirements and statistics"""
        if self.processed_data is None:
            self.clean_data()
        
        print("📋 Creating project catalog...")
        
        # Aggregate project data
        projects = self.processed_data.groupby(['project_id', 'project_clean']).agg({
            'branch_short': 'first',
            'project_category': 'first',
            'project_tags_clean': 'first',
            'type': 'first',
            'need': 'first',
            'hours': ['sum', 'mean', 'count'],
            'contact_id': 'nunique',
            'age': 'mean',
            'gender': lambda x: Counter(x).most_common(1)[0][0] if len(x) > 0 else 'Unknown',
            'active_credentials': 'first',
            'commentsdescription': lambda x: ' | '.join(x.dropna().unique()[:3])
        }).reset_index()
        
        # Flatten columns
        projects.columns = ['project_id', 'project_name', 'branch', 'category', 'tags', 'type', 'need',
                           'total_hours', 'avg_hours_per_session', 'total_sessions', 'unique_volunteers',
                           'avg_volunteer_age', 'common_gender', 'required_credentials', 'sample_activities']
        
        # Calculate project popularity and success metrics
        projects['popularity_score'] = (projects['unique_volunteers'] * 0.4 + 
                                      projects['total_sessions'] * 0.3 + 
                                      projects['total_hours'] * 0.3)
        
        projects['volunteer_retention'] = projects['total_sessions'] / projects['unique_volunteers']
        
        self.project_catalog = projects
        print(f"📊 Created catalog with {len(projects)} projects")
        return projects
    
    def generate_insights(self) -> Dict[str, Any]:
        """Generate key insights from the volunteer data"""
        if self.processed_data is None:
            self.clean_data()
        
        print("🔍 Generating insights...")
        
        insights = {
            'total_volunteers': self.processed_data['contact_id'].nunique(),
            'total_hours': self.processed_data['hours'].sum(),
            'total_projects': self.processed_data['project_id'].nunique(),
            'total_branches': self.processed_data['branch_short'].nunique(),
            'avg_age': self.processed_data['age'].mean(),
            'gender_distribution': self.processed_data['gender'].value_counts().to_dict(),
            'top_project_categories': self.processed_data['project_category'].value_counts().head(5).to_dict(),
            'top_branches': self.processed_data['branch_short'].value_counts().to_dict(),
            'member_vs_nonmember': self.processed_data['is_ymca_member'].value_counts().to_dict(),
            'volunteer_type_distribution': self.volunteer_profiles['volunteer_type'].value_counts().to_dict() if self.volunteer_profiles is not None else {},
            'avg_hours_per_volunteer': self.processed_data['hours'].sum() / self.processed_data['contact_id'].nunique(),
            'peak_volunteer_months': self.processed_data['month'].value_counts().head(3).to_dict()
        }
        
        self.insights = insights
        print("💡 Insights generated successfully!")
        return insights
    
    def get_volunteer_recommendations_data(self) -> Dict[str, Any]:
        """Prepare data for the recommendation engine"""
        if self.processed_data is None:
            self.clean_data()
        
        if self.volunteer_profiles is None:
            self.create_volunteer_profiles()
        
        if self.project_catalog is None:
            self.create_project_catalog()
        
        return {
            'volunteers': self.volunteer_profiles,
            'projects': self.project_catalog,
            'interactions': self.processed_data,
            'insights': self.insights
        }
    
    def export_cleaned_data(self, output_path: str = 'cleaned_volunteer_data.xlsx'):
        """Export cleaned data to Excel file"""
        if self.processed_data is None:
            self.clean_data()
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            self.processed_data.to_excel(writer, sheet_name='All_Data', index=False)
            
            if self.volunteer_profiles is not None:
                self.volunteer_profiles.to_excel(writer, sheet_name='Volunteer_Profiles', index=False)
            
            if self.project_catalog is not None:
                self.project_catalog.to_excel(writer, sheet_name='Project_Catalog', index=False)
        
        print(f"📄 Exported cleaned data to {output_path}")

# Example usage
if __name__ == "__main__":
    processor = VolunteerDataProcessor("Y Volunteer Raw Data - Jan- August 2025.xlsx")
    
    # Process all data
    processor.clean_data()
    processor.create_volunteer_profiles()
    processor.create_project_catalog()
    insights = processor.generate_insights()
    
    # Print insights
    print("\n🎯 KEY INSIGHTS:")
    for key, value in insights.items():
        print(f"{key}: {value}")
    
    # Export cleaned data
    processor.export_cleaned_data()
