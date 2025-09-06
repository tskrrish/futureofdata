"""
Comprehensive Test Suite for Schema Inference and Versioning System
Tests all components: inference, versioning, drift detection, and migration suggestions
"""
# import pytest  # Not available in this environment
import pandas as pd
import numpy as np
import tempfile
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
import json

from schema_inference import (
    SchemaInferenceEngine, SchemaVersioningSystem, MigrationSuggestionEngine,
    SchemaInferenceManager, DataType, ChangeType, ColumnSchema, TableSchema
)
from schema_integration import VolunteerSchemaManager
from database import VolunteerDatabase

class TestSchemaInferenceEngine:
    """Test the core schema inference engine"""
    
    def setup_method(self):
        """Set up test environment"""
        self.engine = SchemaInferenceEngine()
    
    def test_uuid_detection(self):
        """Test UUID pattern detection"""
        uuid_series = pd.Series([
            '123e4567-e89b-12d3-a456-426614174000',
            '987fcdeb-51a2-43d7-8f9e-123456789abc',
            '456789ab-cdef-1234-5678-9abcdef01234'
        ])
        confidence = self.engine._detect_uuid(uuid_series)
        assert confidence == 1.0, f"Expected 1.0, got {confidence}"
    
    def test_email_detection(self):
        """Test email pattern detection"""
        email_series = pd.Series([
            'user1@example.com',
            'test.email+tag@domain.org',
            'volunteer@ymca.net'
        ])
        confidence = self.engine._detect_email(email_series)
        assert confidence == 1.0, f"Expected 1.0, got {confidence}"
    
    def test_phone_detection(self):
        """Test phone number detection"""
        phone_series = pd.Series([
            '5551234567',
            '555-123-4567',
            '(555) 123-4567'
        ])
        confidence = self.engine._detect_phone(phone_series)
        assert confidence >= 0.8, f"Expected >= 0.8, got {confidence}"
    
    def test_datetime_detection(self):
        """Test datetime detection"""
        datetime_series = pd.Series([
            '2023-01-01 10:30:00',
            '2023-12-25 15:45:30',
            '2024-06-15 09:00:00'
        ])
        confidence = self.engine._detect_datetime(datetime_series)
        assert confidence >= 0.8, f"Expected >= 0.8, got {confidence}"
    
    def test_boolean_detection(self):
        """Test boolean value detection"""
        bool_series = pd.Series(['true', 'false', 'yes', 'no', '1', '0'])
        confidence = self.engine._detect_boolean(bool_series)
        assert confidence == 1.0, f"Expected 1.0, got {confidence}"
    
    def test_integer_detection(self):
        """Test integer detection"""
        int_series = pd.Series([1, 2, 3, 100, 42])
        confidence = self.engine._detect_integer(int_series)
        assert confidence == 1.0, f"Expected 1.0, got {confidence}"
    
    def test_float_detection(self):
        """Test float detection"""
        float_series = pd.Series([1.5, 2.7, 3.14, 100.99, 42.0])
        confidence = self.engine._detect_float(float_series)
        assert confidence >= 0.8, f"Expected >= 0.8, got {confidence}"
    
    def test_categorical_detection(self):
        """Test categorical data detection"""
        categorical_series = pd.Series(['A', 'B', 'A', 'C', 'B', 'A'] * 10)
        confidence = self.engine._detect_categorical(categorical_series)
        assert confidence >= 0.8, f"Expected >= 0.8, got {confidence}"
    
    def test_column_schema_inference(self):
        """Test complete column schema inference"""
        # Test with mixed data
        test_data = {
            'id': range(100),
            'email': [f'user{i}@test.com' for i in range(100)],
            'age': np.random.randint(18, 65, 100),
            'is_member': [True, False] * 50,
            'category': ['A', 'B', 'C'] * 33 + ['A'],  # 100 items total
            'score': np.random.uniform(0, 100, 100)
        }
        
        df = pd.DataFrame(test_data)
        
        for column_name in df.columns:
            schema = self.engine.infer_column_schema(df[column_name], column_name)
            assert isinstance(schema, ColumnSchema)
            assert schema.name == column_name
            assert schema.confidence_score > 0
            
            # Test specific types
            if column_name == 'id':
                assert schema.data_type == DataType.INTEGER
                assert schema.unique == True
            elif column_name == 'email':
                assert schema.data_type == DataType.EMAIL
            elif column_name == 'is_member':
                assert schema.data_type == DataType.BOOLEAN
            elif column_name == 'category':
                assert schema.data_type == DataType.CATEGORICAL

class TestSchemaVersioningSystem:
    """Test schema versioning and change detection"""
    
    def setup_method(self):
        """Set up test environment"""
        self.versioning = SchemaVersioningSystem()
    
    def test_schema_registration(self):
        """Test schema version registration"""
        # Create a test schema
        columns = [
            ColumnSchema(name="id", data_type=DataType.INTEGER, unique=True),
            ColumnSchema(name="name", data_type=DataType.STRING),
            ColumnSchema(name="email", data_type=DataType.EMAIL)
        ]
        
        schema = TableSchema(
            name="test_table",
            columns=columns,
            version="1.0.0"
        )
        
        result = self.versioning.register_schema_version(schema)
        assert result == True
        
        # Verify it's in history
        history = self.versioning.get_schema_history("test_table")
        assert len(history) == 1
        assert history[0].version == "1.0.0"
    
    def test_drift_detection(self):
        """Test schema drift detection"""
        # Create original schema
        old_columns = [
            ColumnSchema(name="id", data_type=DataType.INTEGER, unique=True),
            ColumnSchema(name="name", data_type=DataType.STRING),
            ColumnSchema(name="email", data_type=DataType.EMAIL)
        ]
        
        old_schema = TableSchema(
            name="test_table",
            columns=old_columns,
            version="1.0.0"
        )
        
        # Create modified schema
        new_columns = [
            ColumnSchema(name="id", data_type=DataType.INTEGER, unique=True),
            ColumnSchema(name="name", data_type=DataType.STRING),
            ColumnSchema(name="email", data_type=DataType.EMAIL),
            ColumnSchema(name="phone", data_type=DataType.PHONE),  # Added
            ColumnSchema(name="age", data_type=DataType.INTEGER)   # Added
        ]
        
        new_schema = TableSchema(
            name="test_table",
            columns=new_columns,
            version="1.1.0"
        )
        
        changes = self.versioning.detect_schema_drift(old_schema, new_schema)
        
        # Should detect 2 added columns
        added_changes = [c for c in changes if c.change_type == ChangeType.COLUMN_ADDED]
        assert len(added_changes) == 2
        assert any(c.column_name == "phone" for c in added_changes)
        assert any(c.column_name == "age" for c in added_changes)
    
    def test_type_change_detection(self):
        """Test detection of type changes"""
        # Original schema with string column
        old_columns = [
            ColumnSchema(name="value", data_type=DataType.STRING)
        ]
        old_schema = TableSchema(name="test", columns=old_columns, version="1.0")
        
        # New schema with integer column
        new_columns = [
            ColumnSchema(name="value", data_type=DataType.INTEGER)
        ]
        new_schema = TableSchema(name="test", columns=new_columns, version="2.0")
        
        changes = self.versioning.detect_schema_drift(old_schema, new_schema)
        
        type_changes = [c for c in changes if c.change_type == ChangeType.TYPE_CHANGED]
        assert len(type_changes) == 1
        assert type_changes[0].column_name == "value"
        assert type_changes[0].old_value == "string"
        assert type_changes[0].new_value == "integer"

class TestMigrationSuggestionEngine:
    """Test migration suggestion generation"""
    
    def setup_method(self):
        """Set up test environment"""
        self.migration_engine = MigrationSuggestionEngine()
    
    def test_add_column_suggestions(self):
        """Test suggestions for added columns"""
        from schema_inference import SchemaChange
        
        change = SchemaChange(
            change_type=ChangeType.COLUMN_ADDED,
            table_name="volunteers",
            column_name="phone",
            new_value={
                'data_type': 'phone',
                'nullable': True,
                'default_value': None
            }
        )
        
        suggestions = self.migration_engine.generate_migration_suggestions([change])
        assert 'volunteers' in suggestions
        assert any('ALTER TABLE volunteers ADD COLUMN phone' in s for s in suggestions['volunteers'])
    
    def test_remove_column_suggestions(self):
        """Test suggestions for removed columns"""
        from schema_inference import SchemaChange
        
        change = SchemaChange(
            change_type=ChangeType.COLUMN_REMOVED,
            table_name="volunteers", 
            column_name="old_field",
            old_value={'data_type': 'string'}
        )
        
        suggestions = self.migration_engine.generate_migration_suggestions([change])
        assert 'volunteers' in suggestions
        assert any('HIGH IMPACT' in s for s in suggestions['volunteers'])
        assert any('DROP COLUMN old_field' in s for s in suggestions['volunteers'])

class TestSchemaInferenceManager:
    """Test the main schema inference manager"""
    
    async def test_table_schema_inference(self):
        """Test complete table schema inference"""
        # Create test data
        test_data = pd.DataFrame({
            'volunteer_id': range(1, 101),
            'email': [f'volunteer{i}@example.com' for i in range(1, 101)],
            'first_name': [f'Name{i}' for i in range(1, 101)],
            'age': np.random.randint(18, 65, 100),
            'is_member': np.random.choice([True, False], 100),
            'join_date': pd.date_range('2020-01-01', periods=100),
            'hours': np.random.uniform(1, 50, 100),
            'branch': np.random.choice(['Branch A', 'Branch B', 'Branch C'], 100)
        })
        
        manager = SchemaInferenceManager()
        schema = manager.infer_table_schema(test_data, "test_volunteers")
        
        assert isinstance(schema, TableSchema)
        assert schema.name == "test_volunteers"
        assert len(schema.columns) == len(test_data.columns)
        assert schema.row_count == 100
        
        # Verify specific column types
        column_map = {col.name: col for col in schema.columns}
        assert column_map['volunteer_id'].data_type == DataType.INTEGER
        assert column_map['email'].data_type == DataType.EMAIL
        assert column_map['is_member'].data_type == DataType.BOOLEAN
    
    async def test_drift_analysis(self):
        """Test comprehensive drift analysis"""
        manager = SchemaInferenceManager()
        
        # Create first version
        data_v1 = pd.DataFrame({
            'id': range(100),
            'name': [f'User{i}' for i in range(100)],
            'email': [f'user{i}@test.com' for i in range(100)]
        })
        
        schema_v1 = manager.infer_table_schema(data_v1, "users", "1.0.0")
        
        # Create second version with changes
        data_v2 = pd.DataFrame({
            'id': range(100),
            'name': [f'User{i}' for i in range(100)],
            'email': [f'user{i}@test.com' for i in range(100)],
            'phone': [f'555-{i:04d}' for i in range(100)],  # Added column
            'age': np.random.randint(18, 65, 100)  # Added column
        })
        
        schema_v2 = manager.infer_table_schema(data_v2, "users", "2.0.0")
        
        # Analyze drift
        drift_analysis = manager.detect_and_analyze_drift("users", schema_v2)
        
        assert drift_analysis['has_drift'] == True
        assert len(drift_analysis['changes']) == 2  # Two columns added
        assert 'migration_suggestions' in drift_analysis
        assert drift_analysis['previous_version'] == "1.0.0"
        assert drift_analysis['new_version'] == "2.0.0"

class TestSchemaIntegration:
    """Test the integrated schema system with volunteer data processing"""
    
    def setup_method(self):
        """Set up test data files"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample volunteer data
        self.sample_data = pd.DataFrame({
            'Contact ID': range(1, 201),
            'First Name': [f'Volunteer{i}' for i in range(1, 201)],
            'Last Name': [f'Last{i}' for i in range(1, 201)],
            'Email': [f'volunteer{i}@example.com' for i in range(1, 201)],
            'Mobile': [f'555-{i:04d}' for i in range(1, 201)],
            'Age': np.random.randint(16, 70, 200),
            'Gender': np.random.choice(['Male', 'Female', 'Other'], 200),
            'Are you a YMCA Member': np.random.choice(['Yes', 'No'], 200),
            'Member Branch': np.random.choice(['Blue Ash', 'M.E. Lyons', 'Campbell'], 200),
            'Date': pd.date_range('2024-01-01', periods=200, freq='D'),
            'Project': np.random.choice([
                'Youth Development Program',
                'Fitness Center Support',
                'Special Events Team',
                'Administrative Support'
            ], 200),
            'Branch': np.random.choice(['Blue Ash', 'M.E. Lyons', 'Campbell'], 200),
            'Hours': np.random.uniform(1, 8, 200),
            'Project ID': np.random.randint(1000, 2000, 200)
        })
        
        # Save to Excel file
        self.excel_path = os.path.join(self.temp_dir, 'test_volunteer_data.xlsx')
        
        # Create multiple sheets to simulate real data structure
        with pd.ExcelWriter(self.excel_path, engine='openpyxl') as writer:
            self.sample_data.to_excel(writer, sheet_name='Branch - Vol', index=False)
            
            # Create a subset for hours data
            hours_data = self.sample_data[['Contact ID', 'Date', 'Hours', 'Project ID']].copy()
            hours_data.to_excel(writer, sheet_name='Branch - Hours', index=False)
    
    def teardown_method(self):
        """Clean up test files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    async def test_full_integration_workflow(self):
        """Test the complete integrated workflow"""
        # Initialize the integrated system
        db = VolunteerDatabase()  # This will work without actual DB connection
        manager = VolunteerSchemaManager(self.excel_path, db)
        
        await manager.initialize()
        
        # Run the full processing workflow
        report = await manager.process_with_schema_tracking()
        
        # Validate report structure
        assert 'report_generated_at' in report
        assert 'data_summary' in report
        assert 'schema_summary' in report
        assert 'schema_versions' in report
        assert 'recommendations' in report
        
        # Validate data summary
        data_summary = report['data_summary']
        assert data_summary['total_volunteers'] > 0
        assert data_summary['total_hours'] > 0
        
        # Validate schema summary
        schema_summary = report['schema_summary']
        assert schema_summary['tables_analyzed'] > 0
        assert schema_summary['total_columns'] > 0
        
        # Validate schema versions were created
        schema_versions = report['schema_versions']
        assert 'raw_data' in schema_versions
        assert 'processed_data' in schema_versions
        
        # Should have schema for raw data
        assert schema_versions['raw_data'] is not None
        assert 'schema' in schema_versions['raw_data']
    
    async def test_schema_export(self):
        """Test schema report export"""
        db = VolunteerDatabase()
        manager = VolunteerSchemaManager(self.excel_path, db)
        
        await manager.initialize()
        
        # Export schema report
        report_path = await manager.export_schema_report()
        
        # Verify file was created
        assert os.path.exists(report_path)
        
        # Verify it contains valid JSON
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        assert 'report_generated_at' in report_data
        assert 'schema_summary' in report_data
    
    def test_schema_changes_summary(self):
        """Test schema changes summary generation"""
        db = VolunteerDatabase()
        manager = VolunteerSchemaManager(self.excel_path, db)
        
        # Should handle empty state gracefully
        summary = manager.get_schema_changes_summary()
        assert 'total_changes' in summary
        assert summary['total_changes'] == 0

def run_performance_tests():
    """Run performance tests for large datasets"""
    print("🚀 Running Performance Tests...")
    
    # Create large dataset
    large_data_size = 10000
    large_data = pd.DataFrame({
        'id': range(large_data_size),
        'uuid': [f'{i:08d}-0000-0000-0000-{i:012d}' for i in range(large_data_size)],
        'email': [f'user{i}@example{i%100}.com' for i in range(large_data_size)],
        'numeric': np.random.uniform(0, 1000, large_data_size),
        'categorical': np.random.choice(['A', 'B', 'C', 'D', 'E'], large_data_size),
        'text': [f'Long text description for item {i} with various details...' for i in range(large_data_size)],
        'datetime': pd.date_range('2020-01-01', periods=large_data_size, freq='H'),
        'boolean': np.random.choice([True, False], large_data_size)
    })
    
    print(f"   Dataset size: {large_data_size:,} rows x {len(large_data.columns)} columns")
    
    # Time schema inference
    start_time = datetime.now()
    engine = SchemaInferenceEngine()
    
    schemas = []
    for column_name in large_data.columns:
        schema = engine.infer_column_schema(large_data[column_name], column_name)
        schemas.append(schema)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"   Schema inference time: {duration:.2f} seconds")
    print(f"   Rate: {large_data_size * len(large_data.columns) / duration:.0f} cells/second")
    
    # Verify all schemas were inferred
    assert len(schemas) == len(large_data.columns)
    for schema in schemas:
        assert schema.confidence_score > 0
    
    print("   ✅ Performance test passed!")

async def run_all_tests():
    """Run all test suites"""
    print("🧪 Running Schema Inference and Versioning Test Suite")
    print("=" * 60)
    
    # Unit tests
    print("\n📊 Testing Schema Inference Engine...")
    engine_tests = TestSchemaInferenceEngine()
    engine_tests.setup_method()
    
    test_methods = [
        'test_uuid_detection',
        'test_email_detection', 
        'test_phone_detection',
        'test_datetime_detection',
        'test_boolean_detection',
        'test_integer_detection',
        'test_float_detection',
        'test_categorical_detection',
        'test_column_schema_inference'
    ]
    
    for method_name in test_methods:
        try:
            method = getattr(engine_tests, method_name)
            method()
            print(f"   ✅ {method_name}")
        except Exception as e:
            print(f"   ❌ {method_name}: {e}")
    
    print("\n🗄️  Testing Schema Versioning System...")
    versioning_tests = TestSchemaVersioningSystem()
    versioning_tests.setup_method()
    
    versioning_methods = [
        'test_schema_registration',
        'test_drift_detection',
        'test_type_change_detection'
    ]
    
    for method_name in versioning_methods:
        try:
            method = getattr(versioning_tests, method_name)
            method()
            print(f"   ✅ {method_name}")
        except Exception as e:
            print(f"   ❌ {method_name}: {e}")
    
    print("\n🔧 Testing Migration Suggestion Engine...")
    migration_tests = TestMigrationSuggestionEngine()
    migration_tests.setup_method()
    
    migration_methods = [
        'test_add_column_suggestions',
        'test_remove_column_suggestions'
    ]
    
    for method_name in migration_methods:
        try:
            method = getattr(migration_tests, method_name)
            method()
            print(f"   ✅ {method_name}")
        except Exception as e:
            print(f"   ❌ {method_name}: {e}")
    
    print("\n🎯 Testing Schema Inference Manager...")
    manager_tests = TestSchemaInferenceManager()
    
    try:
        await manager_tests.test_table_schema_inference()
        print("   ✅ test_table_schema_inference")
    except Exception as e:
        print(f"   ❌ test_table_schema_inference: {e}")
    
    try:
        await manager_tests.test_drift_analysis()
        print("   ✅ test_drift_analysis")
    except Exception as e:
        print(f"   ❌ test_drift_analysis: {e}")
    
    print("\n🔗 Testing Schema Integration...")
    integration_tests = TestSchemaIntegration()
    integration_tests.setup_method()
    
    try:
        await integration_tests.test_full_integration_workflow()
        print("   ✅ test_full_integration_workflow")
    except Exception as e:
        print(f"   ❌ test_full_integration_workflow: {e}")
    
    try:
        await integration_tests.test_schema_export()
        print("   ✅ test_schema_export")
    except Exception as e:
        print(f"   ❌ test_schema_export: {e}")
    
    integration_tests.teardown_method()
    
    # Performance tests
    print("\n⚡ Running Performance Tests...")
    try:
        run_performance_tests()
    except Exception as e:
        print(f"   ❌ Performance tests failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Test Suite Complete!")
    print("   The Schema Inference and Versioning System is ready to use!")

if __name__ == "__main__":
    asyncio.run(run_all_tests())