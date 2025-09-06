#!/usr/bin/env python3
"""
Simple test for the Data Quality Rules Engine
Tests core functionality without external dependencies
"""

import sys
import os
from datetime import datetime

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


def test_required_field_rule():
    """Test required field validation"""
    print("Testing RequiredFieldRule...")
    
    rule = RequiredFieldRule("first_name")
    
    # Test valid value
    result = rule.validate("John", {})
    assert result.passed is True, "Valid name should pass"
    
    # Test empty string
    result = rule.validate("", {})
    assert result.passed is False, "Empty string should fail"
    
    # Test None
    result = rule.validate(None, {})
    assert result.passed is False, "None should fail"
    
    print("✓ RequiredFieldRule tests passed")


def test_format_rule_email():
    """Test email format validation"""
    print("Testing FormatRule for email...")
    
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
    
    print("✓ FormatRule email tests passed")


def test_range_rule():
    """Test numeric range validation"""
    print("Testing RangeRule...")
    
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
    assert result.passed is True, "String number should be valid"
    
    # Test non-numeric values
    result = rule.validate("not-a-number", {})
    assert result.passed is False, "Non-numeric should be invalid"
    
    print("✓ RangeRule tests passed")


def test_reference_rule():
    """Test reference value validation"""
    print("Testing ReferenceRule...")
    
    branches = ["Blue Ash YMCA", "M.E. Lyons YMCA", "Campbell County YMCA"]
    rule = ReferenceRule("branch", branches)
    
    # Test valid values
    for branch in branches:
        result = rule.validate(branch, {})
        assert result.passed is True, f"Branch {branch} should be valid"
    
    # Test invalid value
    result = rule.validate("Unknown Branch", {})
    assert result.passed is False, "Unknown branch should be invalid"
    
    print("✓ ReferenceRule tests passed")


def test_custom_rule():
    """Test custom validation rule"""
    print("Testing CustomRule...")
    
    # Custom rule: value must be even
    rule = CustomRule(
        "age",
        lambda val, rec: val is not None and int(val) % 2 == 0,
        "Age must be an even number"
    )
    
    # Test valid values
    result = rule.validate(24, {})
    assert result.passed is True, "Even number should pass"
    
    # Test invalid values
    result = rule.validate(25, {})
    assert result.passed is False, "Odd number should fail"
    
    print("✓ CustomRule tests passed")


def test_engine_creation():
    """Test engine initialization"""
    print("Testing DataQualityRulesEngine creation...")
    
    engine = DataQualityRulesEngine()
    assert len(engine.global_rules) > 0, "Should have global rules"
    assert isinstance(engine.reference_data, dict), "Should have reference data"
    
    print("✓ Engine creation tests passed")


def test_default_engine():
    """Test default engine configuration"""
    print("Testing default engine configuration...")
    
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
        assert expected_rule in rule_names, f"Should have {expected_rule} rule"
    
    # Check branch overrides exist
    assert len(engine.branch_overrides) > 0, "Should have branch overrides"
    assert "Blue Ash YMCA" in engine.branch_overrides, "Should have Blue Ash overrides"
    
    print("✓ Default engine tests passed")


def test_validate_single_record():
    """Test validating a single record"""
    print("Testing single record validation...")
    
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
    assert len(results) > 0, "Should have validation results"
    
    # Check for any critical errors
    errors = [r for r in results if r.severity == ValidationSeverity.ERROR and not r.passed]
    assert len(errors) == 0, f"Unexpected errors: {[e.message for e in errors]}"
    
    print("✓ Single record validation tests passed")


def test_validate_dataset():
    """Test validating a complete dataset"""
    print("Testing dataset validation...")
    
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
    assert report.total_records == 3, f"Should have 3 records, got {report.total_records}"
    assert report.failed_records > 0, "Record 2 should fail"
    assert report.passed_records > 0, "Records 1 and 3 should pass"
    assert len(report.validation_results) > 0, "Should have validation results"
    
    # Check summary
    assert "errors" in report.summary, "Should have errors in summary"
    assert "warnings" in report.summary, "Should have warnings in summary"
    assert report.summary["errors"] > 0, "Should have errors from record 2"
    
    print(f"   Dataset validation completed:")
    print(f"   - Total records: {report.total_records}")
    print(f"   - Passed: {report.passed_records}")
    print(f"   - Failed: {report.failed_records}")
    print(f"   - Errors: {report.summary['errors']}")
    print(f"   - Warnings: {report.summary['warnings']}")
    
    print("✓ Dataset validation tests passed")


def test_branch_specific_validation():
    """Test that branch-specific rules are applied correctly"""
    print("Testing branch-specific validation...")
    
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
    
    print("✓ Branch-specific validation tests passed")


def test_html_report_generation():
    """Test HTML report generation"""
    print("Testing HTML report generation...")
    
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
    
    assert "<!DOCTYPE html>" in html, "Should generate valid HTML"
    assert "Data Quality Validation Report" in html, "Should have report title"
    assert str(report.total_records) in html, "Should include record count"
    
    print("✓ HTML report generation tests passed")


def demo_data_quality_engine():
    """Demonstrate the data quality engine with sample data"""
    print("\n=== Demo: Data Quality Engine ===")
    
    engine = create_default_engine()
    
    # Show current configuration
    print(f"Engine loaded with {len(engine.global_rules)} global rules")
    print(f"Branch overrides configured for: {list(engine.branch_overrides.keys())}")
    
    # Test with sample volunteer data
    sample_data = [
        {
            "first_name": "Alice",
            "last_name": "Johnson",
            "email": "alice.johnson@email.com",
            "phone": "513-555-0123",
            "age": 28,
            "member_branch": "Blue Ash YMCA",
            "volunteer_type": "Youth Development",
            "hours": 12,
            "pledged": 15
        },
        {
            "first_name": "Bob",
            "last_name": "Wilson",
            "email": "bob.wilson@email.com", 
            "age": 45,
            "member_branch": "M.E. Lyons YMCA",
            "volunteer_type": "Music Programs",  # Special type for M.E. Lyons
            "hours": 8,
            "pledged": 8
        },
        {
            "first_name": "",  # Missing name
            "last_name": "Brown",
            "email": "invalid-email-format",  # Bad email
            "age": 200,  # Invalid age
            "member_branch": "Unknown Branch",  # Invalid branch
            "volunteer_type": "Invalid Type",
            "hours": 50,  # Way more than pledged
            "pledged": 5
        }
    ]
    
    print(f"\nValidating {len(sample_data)} volunteer records...")
    report = engine.validate_dataset(sample_data, branch_field="member_branch")
    
    print(f"Results:")
    print(f"  - Total records: {report.total_records}")
    print(f"  - Passed: {report.passed_records}")
    print(f"  - Failed: {report.failed_records}")
    print(f"  - Total validations: {report.summary['total_validations']}")
    print(f"  - Errors: {report.summary['errors']}")
    print(f"  - Warnings: {report.summary['warnings']}")
    
    if report.summary['errors'] > 0 or report.summary['warnings'] > 0:
        print(f"\nDetailed issues:")
        for result in report.validation_results:
            if not result.passed:
                print(f"  {result.severity.value.upper()}: {result.field} - {result.message}")
                if result.value is not None:
                    print(f"    Value: {result.value}")
    
    print("\n=== Branch-Specific Rules Demo ===")
    
    # Show difference between branches for age validation
    young_volunteer = {
        "first_name": "Teenager",
        "last_name": "Smith",
        "email": "teen@example.com",
        "age": 15,
        "member_branch": ""  # Will be set dynamically
    }
    
    branches_to_test = ["Blue Ash YMCA", "M.E. Lyons YMCA", "Campbell County YMCA"]
    
    for branch in branches_to_test:
        young_volunteer["member_branch"] = branch
        results = engine.validate_record(young_volunteer, branch)
        
        age_issues = [r for r in results if r.field == "age" and not r.passed]
        if age_issues:
            issue_types = [r.severity.value for r in age_issues]
            print(f"  {branch}: Age 15 has {len(age_issues)} issues: {issue_types}")
        else:
            print(f"  {branch}: Age 15 is acceptable")
    
    print("\nDemo completed!")


def run_all_tests():
    """Run all tests"""
    print("=== Running Data Quality Rules Engine Tests ===\n")
    
    tests = [
        test_required_field_rule,
        test_format_rule_email,
        test_range_rule,
        test_reference_rule,
        test_custom_rule,
        test_engine_creation,
        test_default_engine,
        test_validate_single_record,
        test_validate_dataset,
        test_branch_specific_validation,
        test_html_report_generation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} FAILED: {str(e)}")
            failed += 1
    
    print(f"\n=== Test Summary ===")
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(passed/len(tests))*100:.1f}%")
    
    if failed == 0:
        print("🎉 All tests passed!")
    
    return failed == 0


if __name__ == "__main__":
    # Run all tests
    success = run_all_tests()
    
    # Run demo
    demo_data_quality_engine()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)