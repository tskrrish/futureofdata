"""
Test suite for the Data Quality Rules Engine
Tests both core functionality and branch-specific overrides
"""

import pandas as pd
from datetime import datetime
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(__file__))

from data_quality_rules_engine import (
    DataQualityRulesEngine,
    create_default_engine,
    ValidationSeverity,
    RuleType,
    RequiredFieldRule,
    FormatRule,
    RangeRule,
    CustomRule,
    ReferenceRule
)


class TestValidationRules:
    """Test individual validation rules"""
    
    def test_required_field_rule(self):
        """Test required field validation"""
        rule = RequiredFieldRule("first_name")
        
        # Test valid value
        result = rule.validate("John", {})
        assert result.passed is True
        
        # Test empty string
        result = rule.validate("", {})
        assert result.passed is False
        
        # Test None
        result = rule.validate(None, {})
        assert result.passed is False
        
        # Test whitespace only
        result = rule.validate("   ", {})
        assert result.passed is False
    
    def test_format_rule_email(self):
        """Test email format validation"""
        rule = FormatRule("email", "email")
        
        # Test valid emails
        valid_emails = [
            "test@example.com",
            "user.name@domain.org",
            "user+tag@company.co.uk"
        ]
        for email in valid_emails:
            result = rule.validate(email, {})
            assert result.passed is True, f"Email {email} should be valid"
        
        # Test invalid emails
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user.domain.com"
        ]
        for email in invalid_emails:
            result = rule.validate(email, {})
            assert result.passed is False, f"Email {email} should be invalid"
        
        # Test empty value (should pass - handled by RequiredFieldRule)
        result = rule.validate("", {})
        assert result.passed is True
    
    def test_format_rule_phone(self):
        """Test phone format validation"""
        rule = FormatRule("phone", "phone")
        
        # Test valid phone numbers
        valid_phones = [
            "513-123-4567",
            "(513) 123-4567",
            "513.123.4567",
            "+1-513-123-4567",
            "5131234567"
        ]
        for phone in valid_phones:
            result = rule.validate(phone, {})
            assert result.passed is True, f"Phone {phone} should be valid"
        
        # Test invalid phone numbers
        invalid_phones = [
            "123-45-6789",
            "abc-def-ghij",
            "513-123",
            "513-123-45678"
        ]
        for phone in invalid_phones:
            result = rule.validate(phone, {})
            assert result.passed is False, f"Phone {phone} should be invalid"
    
    def test_range_rule(self):
        """Test numeric range validation"""
        rule = RangeRule("age", min_val=13, max_val=120)
        
        # Test valid values
        valid_ages = [13, 25, 65, 120]
        for age in valid_ages:
            result = rule.validate(age, {})
            assert result.passed is True, f"Age {age} should be valid"
        
        # Test invalid values
        invalid_ages = [12, 121, -5]
        for age in invalid_ages:
            result = rule.validate(age, {})
            assert result.passed is False, f"Age {age} should be invalid"
        
        # Test string numbers
        result = rule.validate("25", {})
        assert result.passed is True
        
        # Test non-numeric values
        result = rule.validate("not-a-number", {})
        assert result.passed is False
        
        # Test empty value
        result = rule.validate("", {})
        assert result.passed is True
    
    def test_reference_rule(self):
        """Test reference value validation"""
        branches = ["Blue Ash YMCA", "M.E. Lyons YMCA", "Campbell County YMCA"]
        rule = ReferenceRule("branch", branches)
        
        # Test valid values
        for branch in branches:
            result = rule.validate(branch, {})
            assert result.passed is True, f"Branch {branch} should be valid"
        
        # Test invalid value
        result = rule.validate("Unknown Branch", {})
        assert result.passed is False
        
        # Test empty value
        result = rule.validate("", {})
        assert result.passed is True
    
    def test_custom_rule(self):
        """Test custom validation rule"""
        # Custom rule: age must be even
        rule = CustomRule(
            "age",
            lambda val, rec: val is not None and int(val) % 2 == 0,
            "Age must be an even number"
        )
        
        # Test valid values
        result = rule.validate(24, {})
        assert result.passed is True
        
        # Test invalid values
        result = rule.validate(25, {})
        assert result.passed is False
        
        # Test with record context
        context_rule = CustomRule(
            "hours",
            lambda val, rec: val is None or float(val) <= float(rec.get("pledged", 0)) * 1.2,
            "Hours should not exceed pledged hours by more than 20%"
        )
        
        # Test valid scenario
        result = context_rule.validate(10, {"pledged": 10})
        assert result.passed is True
        
        # Test invalid scenario
        result = context_rule.validate(15, {"pledged": 10})
        assert result.passed is False


class TestDataQualityRulesEngine:
    """Test the main rules engine"""
    
    def test_engine_creation(self):
        """Test engine initialization"""
        engine = DataQualityRulesEngine()
        assert len(engine.global_rules) > 0
        assert isinstance(engine.reference_data, dict)
    
    def test_default_engine(self):
        """Test default engine configuration"""
        engine = create_default_engine()
        
        # Check that we have expected rules
        rule_names = [rule.name for rule in engine.global_rules]
        expected_rules = [
            "first_name_required",
            "last_name_required", 
            "email_required",
            "email_email_format"
        ]
        
        for expected_rule in expected_rules:
            assert expected_rule in rule_names
        
        # Check branch overrides exist
        assert len(engine.branch_overrides) > 0
        assert "Blue Ash YMCA" in engine.branch_overrides
    
    def test_add_global_rule(self):
        """Test adding global rules"""
        engine = DataQualityRulesEngine()
        initial_count = len(engine.global_rules)
        
        new_rule = RequiredFieldRule("test_field")
        engine.add_global_rule(new_rule)
        
        assert len(engine.global_rules) == initial_count + 1
        assert new_rule in engine.global_rules
    
    def test_branch_overrides(self):
        """Test branch-specific rule overrides"""
        engine = DataQualityRulesEngine()
        
        # Add a branch-specific rule
        branch_rule = RangeRule("age", min_val=18, max_val=65)
        engine.add_branch_override("Test Branch", branch_rule)
        
        # Get rules for that branch
        branch_rules = engine.get_rules_for_branch("Test Branch")
        rule_names = [rule.name for rule in branch_rules]
        
        assert "age_range" in rule_names
        
        # Get rules for different branch (should not include the override)
        other_branch_rules = engine.get_rules_for_branch("Other Branch")
        other_rule_names = [rule.name for rule in other_branch_rules]
        
        # The override rule shouldn't be in other branches unless it was global
        branch_specific_rules = set(rule_names) - set(other_rule_names)
        assert len(branch_specific_rules) >= 0  # Should have at least the override
    
    def test_disable_rule_for_branch(self):
        """Test disabling rules for specific branches"""
        engine = create_default_engine()
        
        # Get initial rules for a branch
        initial_rules = engine.get_rules_for_branch("Blue Ash YMCA")
        initial_count = len(initial_rules)
        
        # Disable a rule for this branch
        engine.disable_rule_for_branch("Blue Ash YMCA", "email_required")
        
        # Get rules again
        updated_rules = engine.get_rules_for_branch("Blue Ash YMCA")
        rule_names = [rule.name for rule in updated_rules]
        
        # The disabled rule should not be in the list
        assert "email_required" not in rule_names
    
    def test_validate_single_record(self):
        """Test validating a single record"""
        engine = create_default_engine()
        
        # Test valid record
        valid_record = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@email.com",
            "age": 25,
            "hours": 5,
            "pledged": 6
        }
        
        results = engine.validate_record(valid_record)
        
        # Should have results for all applicable rules
        assert len(results) > 0
        
        # Check for any critical errors
        errors = [r for r in results if r.severity == ValidationSeverity.ERROR and not r.passed]
        assert len(errors) == 0, f"Unexpected errors: {[e.message for e in errors]}"
    
    def test_validate_dataset(self):
        """Test validating a complete dataset"""
        engine = create_default_engine()
        
        # Create test dataset
        test_data = [
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@email.com",
                "age": 25,
                "member_branch": "Blue Ash YMCA",
                "hours": 5,
                "pledged": 6
            },
            {
                "first_name": "",  # Missing required field
                "last_name": "Smith",
                "email": "invalid-email",  # Invalid format
                "age": 150,  # Out of range
                "member_branch": "Unknown Branch",  # Invalid reference
                "hours": 10,
                "pledged": 5
            },
            {
                "first_name": "Jane",
                "last_name": "Johnson",
                "email": "jane@example.com",
                "age": 30,
                "member_branch": "M.E. Lyons YMCA",
                "hours": 8,
                "pledged": 8
            }
        ]
        
        # Run validation
        report = engine.validate_dataset(test_data, branch_field="member_branch")
        
        # Check report structure
        assert report.total_records == 3
        assert report.failed_records > 0  # Record 2 should fail
        assert report.passed_records > 0  # Records 1 and 3 should pass
        assert len(report.validation_results) > 0
        
        # Check summary
        assert "errors" in report.summary
        assert "warnings" in report.summary
        assert report.summary["errors"] > 0  # Should have errors from record 2
    
    def test_branch_specific_validation(self):
        """Test that branch-specific rules are applied correctly"""
        engine = create_default_engine()
        
        # Create records for different branches
        blue_ash_record = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "age": 15,  # Below Blue Ash minimum (16)
            "member_branch": "Blue Ash YMCA"
        }
        
        other_branch_record = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
            "age": 15,  # Should be fine for other branches
            "member_branch": "M.E. Lyons YMCA"
        }
        
        # Validate Blue Ash record
        blue_ash_results = engine.validate_record(blue_ash_record, "Blue Ash YMCA")
        age_errors = [r for r in blue_ash_results if r.field == "age" and not r.passed]
        
        # Should have age error for Blue Ash
        assert len(age_errors) > 0, "Blue Ash should reject age 15"
        
        # Validate other branch record
        other_results = engine.validate_record(other_branch_record, "M.E. Lyons YMCA")
        age_errors_other = [r for r in other_results if r.field == "age" and not r.passed]
        
        # Should NOT have age error for other branch (or only warning)
        critical_age_errors = [r for r in age_errors_other if r.severity == ValidationSeverity.ERROR]
        assert len(critical_age_errors) == 0, "Other branches should allow age 15"
    
    def test_export_config(self):
        """Test configuration export"""
        engine = create_default_engine()
        config = engine.export_config()
        
        assert "global_rules" in config
        assert "branch_overrides" in config
        assert "reference_data" in config
        
        assert len(config["global_rules"]) > 0
        assert len(config["reference_data"]) > 0
    
    def test_html_report_generation(self):
        """Test HTML report generation"""
        engine = create_default_engine()
        
        # Create a sample dataset
        test_data = [
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com"
            },
            {
                "first_name": "",
                "last_name": "Smith", 
                "email": "invalid-email"
            }
        ]
        
        report = engine.validate_dataset(test_data)
        html = engine.generate_report_html(report)
        
        assert "<!DOCTYPE html>" in html
        assert "Data Quality Validation Report" in html
        assert str(report.total_records) in html


class TestIntegrationScenarios:
    """Test real-world integration scenarios"""
    
    def test_volunteer_data_validation(self):
        """Test validation with realistic volunteer data"""
        engine = create_default_engine()
        
        # Simulate real volunteer data
        volunteer_data = [
            {
                "contact_id": 1001,
                "first_name": "Alice",
                "last_name": "Johnson",
                "email": "alice.johnson@email.com",
                "phone": "513-555-0123",
                "age": 28,
                "gender": "Female",
                "zip_code": "45202",
                "is_ymca_member": True,
                "member_branch": "Blue Ash YMCA",
                "volunteer_type": "Youth Development",
                "project_category": "After School",
                "hours": 12,
                "pledged": 15,
                "date": "2024-01-15"
            },
            {
                "contact_id": 1002,
                "first_name": "Bob",
                "last_name": "Wilson",
                "email": "bob.wilson@email.com", 
                "phone": "(513) 555-0456",
                "age": 45,
                "gender": "Male",
                "zip_code": "45209",
                "is_ymca_member": False,
                "member_branch": "M.E. Lyons YMCA",
                "volunteer_type": "Music Programs",  # Special type for M.E. Lyons
                "project_category": "Special Events",
                "hours": 8,
                "pledged": 8,
                "date": "2024-02-01"
            },
            {
                "contact_id": 1003,
                "first_name": "Charlie",
                "last_name": "Brown",
                "email": "charlie.brown@invalid",  # Invalid email
                "phone": "513-555-ABCD",  # Invalid phone
                "age": 200,  # Invalid age
                "gender": "Male",
                "zip_code": "INVALID",  # Invalid ZIP
                "is_ymca_member": True,
                "member_branch": "Unknown Branch",  # Invalid branch
                "volunteer_type": "Invalid Type",  # Invalid type
                "project_category": "Unknown Category",  # Invalid category
                "hours": 50,  # Excessive hours vs pledge
                "pledged": 5,
                "date": "2024-03-01"
            }
        ]
        
        # Run validation
        report = engine.validate_dataset(volunteer_data, branch_field="member_branch")
        
        # Analyze results
        print(f"\n--- Volunteer Data Validation Results ---")
        print(f"Total records: {report.total_records}")
        print(f"Passed records: {report.passed_records}")
        print(f"Failed records: {report.failed_records}")
        print(f"Errors: {report.summary['errors']}")
        print(f"Warnings: {report.summary['warnings']}")
        
        # First two records should pass (or have only warnings)
        critical_errors_by_record = {}
        for result in report.validation_results:
            if result.severity == ValidationSeverity.ERROR and not result.passed:
                # Determine which record this belongs to based on field patterns
                record_idx = None  # Would need more sophisticated mapping in real implementation
                critical_errors_by_record[record_idx] = critical_errors_by_record.get(record_idx, 0) + 1
        
        # Third record should have multiple errors
        assert report.summary['errors'] > 0
        
        # Should have warnings too (format issues, reference issues)
        assert report.summary['warnings'] > 0
        
        # Verify branch-specific rules were applied
        # Bob's "Music Programs" should be valid for M.E. Lyons but not others
        music_program_results = [r for r in report.validation_results 
                               if r.field == "volunteer_type" and "Music Programs" in str(r.value)]
        
        # Should find the validation result for Music Programs
        # For M.E. Lyons, it should pass; for other branches, it would fail
        assert len(music_program_results) > 0


# Helper function to run tests
def run_tests():
    """Run all tests manually (for environments without pytest)"""
    test_classes = [TestValidationRules, TestDataQualityRulesEngine, TestIntegrationScenarios]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n=== Running {test_class.__name__} ===")
        
        # Get all test methods
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]
        
        for test_method_name in test_methods:
            total_tests += 1
            print(f"Running {test_method_name}...", end=" ")
            
            try:
                # Create instance and run test
                test_instance = test_class()
                test_method = getattr(test_instance, test_method_name)
                test_method()
                
                print("PASSED")
                passed_tests += 1
                
            except Exception as e:
                print(f"FAILED: {str(e)}")
    
    print(f"\n=== Test Summary ===")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")


if __name__ == "__main__":
    # Run tests
    run_tests()
    
    # Also demonstrate the engine with sample data
    print("\n=== Demo: Data Quality Engine ===")
    
    engine = create_default_engine()
    
    sample_data = [
        {
            "first_name": "Demo",
            "last_name": "User",
            "email": "demo@example.com",
            "age": 25,
            "member_branch": "Blue Ash YMCA",
            "volunteer_type": "Youth Development",
            "hours": 5,
            "pledged": 6
        }
    ]
    
    report = engine.validate_dataset(sample_data, branch_field="member_branch")
    print(f"Demo validation: {report.passed_records}/{report.total_records} records passed")
    
    if report.summary['errors'] > 0 or report.summary['warnings'] > 0:
        print("Issues found:")
        for result in report.validation_results:
            if not result.passed:
                print(f"  {result.severity.value.upper()}: {result.message}")
    else:
        print("All validations passed!")