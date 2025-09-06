"""
Schema Inference Integration Module
Integrates schema inference with existing volunteer data processing pipeline
"""
import pandas as pd
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from data_processor import VolunteerDataProcessor
from schema_inference import SchemaInferenceManager, SchemaChange, ChangeType
from database import VolunteerDatabase

logger = logging.getLogger(__name__)

class VolunteerSchemaManager:
    """
    Enhanced volunteer data processor with integrated schema inference and versioning
    """
    
    def __init__(self, excel_path: str, database: VolunteerDatabase = None):
        self.excel_path = excel_path
        self.database = database or VolunteerDatabase()
        
        # Initialize components
        self.data_processor = VolunteerDataProcessor(excel_path)
        self.schema_manager = SchemaInferenceManager(self.database)
        
        # Track schema versions for different data views
        self.schema_versions = {
            'raw_data': None,
            'processed_data': None,
            'volunteer_profiles': None,
            'project_catalog': None
        }
        
        self.processing_history = []
    
    async def initialize(self):
        """Initialize the integrated system"""
        print("🚀 Initializing Schema-Aware Volunteer Data System...")
        
        # Initialize schema tracking
        await self.schema_manager.initialize()
        
        print("✅ System initialized successfully!")
        return True
    
    async def process_with_schema_tracking(self, track_drift: bool = True) -> Dict[str, Any]:
        """
        Process volunteer data with full schema inference and drift tracking
        """
        print("📊 Starting comprehensive data processing with schema tracking...")
        
        processing_session = {
            'start_time': datetime.now(),
            'version': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'changes_detected': [],
            'recommendations': []
        }
        
        # Step 1: Load and analyze raw data
        print("\n🔍 Step 1: Loading and analyzing raw data...")
        raw_data = self.data_processor.load_and_combine_data()
        
        raw_analysis = await self.schema_manager.analyze_data_source(
            raw_data, 
            "volunteer_raw_data", 
            f"raw_{processing_session['version']}"
        )
        
        self.schema_versions['raw_data'] = raw_analysis
        processing_session['changes_detected'].extend(
            raw_analysis['drift_analysis'].get('changes', [])
        )
        
        # Step 2: Clean data and track schema evolution
        print("\n🧹 Step 2: Cleaning data with schema evolution tracking...")
        cleaned_data = self.data_processor.clean_data()
        
        cleaned_analysis = await self.schema_manager.analyze_data_source(
            cleaned_data,
            "volunteer_processed_data",
            f"processed_{processing_session['version']}"
        )
        
        self.schema_versions['processed_data'] = cleaned_analysis
        processing_session['changes_detected'].extend(
            cleaned_analysis['drift_analysis'].get('changes', [])
        )
        
        # Step 3: Generate volunteer profiles with schema tracking
        print("\n👥 Step 3: Creating volunteer profiles...")
        volunteer_profiles = self.data_processor.create_volunteer_profiles()
        
        profiles_analysis = await self.schema_manager.analyze_data_source(
            volunteer_profiles,
            "volunteer_profiles",
            f"profiles_{processing_session['version']}"
        )
        
        self.schema_versions['volunteer_profiles'] = profiles_analysis
        
        # Step 4: Create project catalog
        print("\n📋 Step 4: Building project catalog...")
        project_catalog = self.data_processor.create_project_catalog()
        
        catalog_analysis = await self.schema_manager.analyze_data_source(
            project_catalog,
            "project_catalog", 
            f"catalog_{processing_session['version']}"
        )
        
        self.schema_versions['project_catalog'] = catalog_analysis
        
        # Step 5: Generate comprehensive insights
        print("\n💡 Step 5: Generating insights...")
        data_insights = self.data_processor.generate_insights()
        schema_insights = self.analyze_schema_evolution()
        
        # Step 6: Generate recommendations
        processing_session['recommendations'] = self.generate_processing_recommendations()
        
        # Finalize processing session
        processing_session['end_time'] = datetime.now()
        processing_session['duration'] = (
            processing_session['end_time'] - processing_session['start_time']
        ).total_seconds()
        
        self.processing_history.append(processing_session)
        
        # Create comprehensive report
        report = self.create_comprehensive_report(
            data_insights, schema_insights, processing_session
        )
        
        print(f"\n🎉 Processing complete! Duration: {processing_session['duration']:.1f}s")
        return report
    
    def analyze_schema_evolution(self) -> Dict[str, Any]:
        """Analyze how schemas have evolved across different data views"""
        evolution_analysis = {
            'data_transformation_impact': {},
            'type_stability': {},
            'column_lifecycle': {},
            'quality_improvements': {}
        }
        
        # Compare raw vs processed data schemas
        if (self.schema_versions['raw_data'] and 
            self.schema_versions['processed_data']):
            
            raw_schema = self.schema_versions['raw_data']['schema']
            processed_schema = self.schema_versions['processed_data']['schema']
            
            evolution_analysis['data_transformation_impact'] = self._compare_schemas(
                raw_schema, processed_schema, 'Raw → Processed'
            )
        
        # Analyze derived data quality
        for view_name, analysis in self.schema_versions.items():
            if analysis and analysis.get('data_quality'):
                quality = analysis['data_quality']
                evolution_analysis['quality_improvements'][view_name] = {
                    'completeness': quality.get('completeness', 0),
                    'consistency': quality.get('consistency', {}),
                    'row_count': quality.get('row_count', 0)
                }
        
        return evolution_analysis
    
    def _compare_schemas(self, schema1: Dict, schema2: Dict, comparison_name: str) -> Dict[str, Any]:
        """Compare two schemas and analyze differences"""
        cols1 = {col['name']: col for col in schema1.get('columns', [])}
        cols2 = {col['name']: col for col in schema2.get('columns', [])}
        
        comparison = {
            'name': comparison_name,
            'columns_added': list(set(cols2.keys()) - set(cols1.keys())),
            'columns_removed': list(set(cols1.keys()) - set(cols2.keys())),
            'type_changes': [],
            'quality_changes': {}
        }
        
        # Analyze common columns
        common_columns = set(cols1.keys()) & set(cols2.keys())
        for col_name in common_columns:
            col1, col2 = cols1[col_name], cols2[col_name]
            
            # Type changes
            if col1.get('data_type') != col2.get('data_type'):
                comparison['type_changes'].append({
                    'column': col_name,
                    'from': col1.get('data_type'),
                    'to': col2.get('data_type')
                })
            
            # Quality changes
            conf1 = col1.get('confidence_score', 0)
            conf2 = col2.get('confidence_score', 0)
            if abs(conf1 - conf2) > 0.1:
                comparison['quality_changes'][col_name] = {
                    'confidence_change': conf2 - conf1
                }
        
        return comparison
    
    def generate_processing_recommendations(self) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on schema analysis"""
        recommendations = []
        
        # Analyze all schema versions for issues
        for view_name, analysis in self.schema_versions.items():
            if not analysis:
                continue
            
            schema = analysis.get('schema', {})
            data_quality = analysis.get('data_quality', {})
            drift_analysis = analysis.get('drift_analysis', {})
            
            # Data quality recommendations
            if data_quality.get('completeness', 100) < 95:
                recommendations.append({
                    'type': 'data_quality',
                    'priority': 'high',
                    'view': view_name,
                    'issue': 'low_completeness',
                    'description': f"Data completeness is {data_quality['completeness']:.1f}% in {view_name}",
                    'action': 'Review data collection process and add validation rules'
                })
            
            # Schema drift recommendations
            if drift_analysis.get('has_drift'):
                high_impact_changes = [
                    c for c in drift_analysis.get('changes', [])
                    if c.get('impact_score', 0) > 0.6
                ]
                
                if high_impact_changes:
                    recommendations.append({
                        'type': 'schema_drift',
                        'priority': 'high',
                        'view': view_name,
                        'issue': 'high_impact_changes',
                        'description': f"{len(high_impact_changes)} high-impact schema changes detected",
                        'action': 'Review migration suggestions and plan data pipeline updates'
                    })
            
            # Type confidence recommendations
            low_confidence_columns = [
                col for col in schema.get('columns', [])
                if col.get('confidence_score', 1) < 0.7
            ]
            
            if low_confidence_columns:
                recommendations.append({
                    'type': 'type_inference',
                    'priority': 'medium',
                    'view': view_name,
                    'issue': 'low_confidence_types',
                    'description': f"{len(low_confidence_columns)} columns have uncertain data types",
                    'action': 'Review and validate data types for these columns',
                    'columns': [col['name'] for col in low_confidence_columns]
                })
        
        return recommendations
    
    def create_comprehensive_report(self, 
                                   data_insights: Dict[str, Any],
                                   schema_insights: Dict[str, Any],
                                   processing_session: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive report combining data and schema insights"""
        
        report = {
            'report_generated_at': datetime.now().isoformat(),
            'processing_session': processing_session,
            
            # Data insights
            'data_summary': {
                'total_volunteers': data_insights.get('total_volunteers', 0),
                'total_hours': data_insights.get('total_hours', 0),
                'total_projects': data_insights.get('total_projects', 0),
                'total_branches': data_insights.get('total_branches', 0)
            },
            
            # Schema insights
            'schema_summary': {
                'tables_analyzed': len([v for v in self.schema_versions.values() if v]),
                'total_columns': sum([
                    len(v['schema'].get('columns', []))
                    for v in self.schema_versions.values() if v
                ]),
                'schema_changes_detected': len(processing_session.get('changes_detected', [])),
                'data_quality_score': self._calculate_overall_quality_score()
            },
            
            # Detailed analysis
            'schema_versions': self.schema_versions,
            'schema_evolution': schema_insights,
            'recommendations': processing_session.get('recommendations', []),
            'migration_suggestions': self._aggregate_migration_suggestions(),
            
            # Processing metadata
            'processing_metadata': {
                'version': processing_session['version'],
                'duration_seconds': processing_session.get('duration', 0),
                'data_source': self.excel_path
            }
        }
        
        return report
    
    def _calculate_overall_quality_score(self) -> float:
        """Calculate an overall data quality score"""
        quality_scores = []
        
        for analysis in self.schema_versions.values():
            if analysis and analysis.get('data_quality'):
                completeness = analysis['data_quality'].get('completeness', 0)
                
                # Average confidence score
                consistency_scores = list(analysis['data_quality'].get('consistency', {}).values())
                avg_consistency = sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0
                
                quality_score = (completeness + avg_consistency * 100) / 2
                quality_scores.append(quality_score)
        
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0
    
    def _aggregate_migration_suggestions(self) -> Dict[str, List[str]]:
        """Aggregate migration suggestions from all schema analyses"""
        all_suggestions = {}
        
        for view_name, analysis in self.schema_versions.items():
            if analysis and analysis.get('drift_analysis', {}).get('migration_suggestions'):
                suggestions = analysis['drift_analysis']['migration_suggestions']
                for table_name, table_suggestions in suggestions.items():
                    key = f"{view_name}_{table_name}"
                    all_suggestions[key] = table_suggestions
        
        return all_suggestions
    
    async def export_schema_report(self, output_path: str = None) -> str:
        """Export a comprehensive schema analysis report"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"volunteer_schema_report_{timestamp}.json"
        
        # Process data if not already done
        if not any(self.schema_versions.values()):
            await self.process_with_schema_tracking()
        
        # Create report
        report = self.create_comprehensive_report(
            self.data_processor.insights if hasattr(self.data_processor, 'insights') else {},
            self.analyze_schema_evolution(),
            self.processing_history[-1] if self.processing_history else {}
        )
        
        # Export report
        import json
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📄 Schema report exported to: {output_path}")
        return output_path
    
    def get_current_schemas(self) -> Dict[str, Any]:
        """Get current schema versions for all data views"""
        return {
            view: analysis['schema'] if analysis else None
            for view, analysis in self.schema_versions.items()
        }
    
    def get_schema_changes_summary(self) -> Dict[str, Any]:
        """Get a summary of all detected schema changes"""
        all_changes = []
        
        for analysis in self.schema_versions.values():
            if analysis and analysis.get('drift_analysis', {}).get('changes'):
                all_changes.extend(analysis['drift_analysis']['changes'])
        
        if not all_changes:
            return {'total_changes': 0, 'summary': 'No schema changes detected'}
        
        # Summarize by change type
        from collections import Counter
        change_types = Counter([c.get('change_type', 'unknown') for c in all_changes])
        high_impact = [c for c in all_changes if c.get('impact_score', 0) > 0.6]
        
        return {
            'total_changes': len(all_changes),
            'change_types': dict(change_types),
            'high_impact_changes': len(high_impact),
            'requires_attention': len(high_impact) > 0,
            'summary': f"Detected {len(all_changes)} changes across all data views"
        }

# Enhanced main function for testing
async def main():
    """Test the integrated schema inference system"""
    print("🧪 Testing Integrated Schema Inference System")
    print("=" * 50)
    
    # Initialize the system
    db = VolunteerDatabase()
    
    try:
        # Test with actual data file if available
        excel_path = "Y Volunteer Raw Data - Jan- August 2025.xlsx"
        manager = VolunteerSchemaManager(excel_path, db)
        
        await manager.initialize()
        
        print("\n📊 Processing volunteer data with schema tracking...")
        report = await manager.process_with_schema_tracking()
        
        # Display results
        print("\n" + "=" * 50)
        print("📋 PROCESSING RESULTS")
        print("=" * 50)
        
        print(f"🔢 Data Summary:")
        data_summary = report.get('data_summary', {})
        for key, value in data_summary.items():
            print(f"   {key}: {value}")
        
        print(f"\n🗄️  Schema Summary:")
        schema_summary = report.get('schema_summary', {})
        for key, value in schema_summary.items():
            print(f"   {key}: {value}")
        
        print(f"\n⚠️  Recommendations ({len(report.get('recommendations', []))}):")
        for i, rec in enumerate(report.get('recommendations', [])[:5], 1):
            print(f"   {i}. [{rec.get('priority', 'medium').upper()}] {rec.get('description', '')}")
        
        # Export detailed report
        report_path = await manager.export_schema_report()
        print(f"\n📄 Detailed report exported to: {report_path}")
        
    except FileNotFoundError:
        print("📝 Test data file not found - creating demonstration with sample data...")
        
        # Create sample data for demonstration
        import numpy as np
        sample_data = pd.DataFrame({
            'volunteer_id': range(1, 101),
            'email': [f'volunteer{i}@example.com' for i in range(1, 101)],
            'first_name': [f'Volunteer{i}' for i in range(1, 101)],
            'age': np.random.randint(18, 65, 100),
            'is_ymca_member': np.random.choice([True, False], 100),
            'member_since': pd.date_range('2020-01-01', periods=100, freq='D'),
            'total_hours': np.random.uniform(5, 100, 100),
            'branch': np.random.choice(['Blue Ash', 'M.E. Lyons', 'Campbell County'], 100),
            'project_category': np.random.choice(['Youth Development', 'Fitness', 'Events'], 100)
        })
        
        # Save sample data
        sample_path = 'sample_volunteer_data.xlsx'
        sample_data.to_excel(sample_path, index=False)
        
        # Test with sample data
        manager = VolunteerSchemaManager(sample_path, db)
        await manager.initialize()
        
        # Directly analyze the sample dataframe
        analysis = await manager.schema_manager.analyze_data_source(
            sample_data, "sample_volunteers", "v1.0"
        )
        
        print("\n📊 Sample Data Analysis:")
        print(f"   Columns analyzed: {len(analysis['schema']['columns'])}")
        print(f"   Data quality score: {analysis['data_quality']['completeness']:.1f}%")
        print(f"   Schema drift: {'Yes' if analysis['drift_analysis']['has_drift'] else 'No'}")
        
        print("\n✅ Schema inference system is working correctly!")

if __name__ == "__main__":
    asyncio.run(main())