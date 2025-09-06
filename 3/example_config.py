#!/usr/bin/env python3
"""
Example configuration for the Data Quality Rules Engine
Shows how to create custom rules and branch-specific overrides
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(__file__))

from data_quality_rules_engine import (
    DataQualityRulesEngine,
    ValidationSeverity,
    RequiredFieldRule,
    FormatRule,
    RangeRule,
    CustomRule,
    ReferenceRule
)


def create_custom_ymca_engine():
    """Create a custom data quality engine for YMCA volunteer data"""
    print("Creating custom YMCA data quality engine...")
    
    engine = DataQualityRulesEngine()
    
    # Core volunteer information rules
    engine.add_global_rule(RequiredFieldRule("first_name", ValidationSeverity.ERROR))
    engine.add_global_rule(RequiredFieldRule("last_name", ValidationSeverity.ERROR))
    engine.add_global_rule(RequiredFieldRule("email", ValidationSeverity.ERROR))
    
    # Format validation rules
    engine.add_global_rule(FormatRule("email", "email", severity=ValidationSeverity.ERROR))
    engine.add_global_rule(FormatRule("phone", "phone", severity=ValidationSeverity.WARNING))
    engine.add_global_rule(FormatRule("zip_code", "zip_code", severity=ValidationSeverity.WARNING))
    
    # Age validation with reasonable ranges
    engine.add_global_rule(RangeRule("age", min_val=13, max_val=100, severity=ValidationSeverity.WARNING))
    
    # Hours validation
    engine.add_global_rule(RangeRule("hours", min_val=0, max_val=50, severity=ValidationSeverity.WARNING))
    engine.add_global_rule(RangeRule("pledged", min_val=0, max_val=100, severity=ValidationSeverity.WARNING))
    
    # YMCA-specific reference data
    ymca_branches = [
        "Blue Ash YMCA",
        "M.E. Lyons YMCA", 
        "Campbell County YMCA",
        "Clippard YMCA",
        "Central YMCA",
        "Northwest YMCA",
        "Butler County YMCA"
    ]
    
    volunteer_types = [
        "Youth Development",
        "Fitness & Wellness", 
        "Special Events",
        "Facility Support",
        "Administrative",
        "Community Outreach",
        "Childcare Support",
        "Senior Programs"
    ]
    
    program_categories = [
        "After School",
        "Summer Camp",
        "Fitness Programs",
        "Special Events",
        "Childcare",
        "Senior Programs", 
        "Community Service",
        "Administrative",
        "Sports & Recreation",
        "Arts & Crafts"
    ]
    
    engine.add_global_rule(ReferenceRule("member_branch", ymca_branches, ValidationSeverity.WARNING))
    engine.add_global_rule(ReferenceRule("volunteer_type", volunteer_types, ValidationSeverity.WARNING))
    engine.add_global_rule(ReferenceRule("project_category", program_categories, ValidationSeverity.WARNING))
    
    # Custom business rules
    engine.add_global_rule(CustomRule(
        "hours_pledged_consistency",
        lambda val, rec: validate_hours_pledge_ratio(rec),
        "Hours worked should not exceed pledged hours by more than 25%",
        severity=ValidationSeverity.WARNING
    ))
    
    engine.add_global_rule(CustomRule(
        "email_domain_check",
        lambda val, rec: validate_email_domain(rec.get("email")),
        "Email should use a common domain",
        severity=ValidationSeverity.INFO
    ))
    
    return engine, ymca_branches, volunteer_types, program_categories


def validate_hours_pledge_ratio(record):
    """Custom validation: hours shouldn't greatly exceed pledged amount"""
    try:
        hours = float(record.get("hours", 0) or 0)
        pledged = float(record.get("pledged", 0) or 0)
        
        if pledged == 0:
            return hours <= 8  # Reasonable default for no pledge
        
        return hours <= pledged * 1.25  # Allow 25% overage
    except (ValueError, TypeError):
        return True


def validate_email_domain(email):
    """Custom validation: check for common email domains"""
    if not email or "@" not in str(email):
        return True  # Let format rule handle this
    
    common_domains = [
        "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
        "aol.com", "icloud.com", "protonmail.com", "comcast.net"
    ]
    
    domain = str(email).split("@")[-1].lower()
    return domain in common_domains or domain.endswith(".edu") or domain.endswith(".org")


def add_branch_specific_overrides(engine, branches):
    """Add branch-specific rule overrides"""
    print("Adding branch-specific overrides...")
    
    # Blue Ash YMCA: Stricter age requirements for certain programs
    engine.add_branch_override("Blue Ash YMCA", 
        RangeRule("age", min_val=16, max_val=65, severity=ValidationSeverity.ERROR))
    
    # Blue Ash: Higher volunteer hour expectations
    engine.add_branch_override("Blue Ash YMCA",
        RangeRule("pledged", min_val=4, max_val=100, severity=ValidationSeverity.WARNING))
    
    # Campbell County YMCA: Allows longer volunteer sessions
    engine.add_branch_override("Campbell County YMCA",
        RangeRule("hours", min_val=0, max_val=80, severity=ValidationSeverity.WARNING))
    
    # M.E. Lyons YMCA: Has additional specialized programs
    me_lyons_volunteer_types = [
        "Youth Development", "Fitness & Wellness", "Special Events",
        "Facility Support", "Administrative", "Community Outreach",
        "Music Programs", "Art Therapy", "Wellness Coaching"
    ]
    engine.add_branch_override("M.E. Lyons YMCA",
        ReferenceRule("volunteer_type", me_lyons_volunteer_types, ValidationSeverity.WARNING))
    
    # Central YMCA: Urban location with different requirements
    engine.add_branch_override("Central YMCA",
        CustomRule(
            "urban_transportation",
            lambda val, rec: validate_urban_volunteer(rec),
            "Urban volunteers should have reliable transportation",
            severity=ValidationSeverity.INFO
        ))
    
    # Clippard YMCA: Family-focused programs
    clippard_categories = [
        "After School", "Summer Camp", "Family Programs", "Youth Sports",
        "Parent Education", "Community Events", "Childcare"
    ]
    engine.add_branch_override("Clippard YMCA",
        ReferenceRule("project_category", clippard_categories, ValidationSeverity.WARNING))


def validate_urban_volunteer(record):
    """Custom validation for urban location volunteers"""
    # This is a placeholder - in practice, this might check zip code proximity,
    # availability during certain hours, etc.
    age = record.get("age", 0)
    try:
        return int(age) >= 18  # Urban volunteers should be adults
    except (ValueError, TypeError):
        return True


def demonstrate_engine_usage():
    """Demonstrate the custom engine with sample data"""
    print("\n=== Demonstrating Custom YMCA Engine ===")
    
    # Create custom engine
    engine, branches, volunteer_types, categories = create_custom_ymca_engine()
    add_branch_specific_overrides(engine, branches)
    
    print(f"Engine configured with {len(engine.global_rules)} global rules")
    print(f"Branch overrides for: {list(engine.branch_overrides.keys())}")
    
    # Sample volunteer data that represents various scenarios
    sample_volunteers = [
        {
            "volunteer_id": "V001",
            "first_name": "Sarah",
            "last_name": "Johnson", 
            "email": "sarah.johnson@gmail.com",
            "phone": "513-555-0123",
            "age": 28,
            "zip_code": "45202",
            "member_branch": "Blue Ash YMCA",
            "volunteer_type": "Youth Development",
            "project_category": "After School",
            "hours": 12,
            "pledged": 15,
            "start_date": "2024-01-15"
        },
        {
            "volunteer_id": "V002", 
            "first_name": "Michael",
            "last_name": "Chen",
            "email": "m.chen@outlook.com",
            "phone": "(513) 555-0456",
            "age": 45,
            "zip_code": "45209",
            "member_branch": "M.E. Lyons YMCA",
            "volunteer_type": "Music Programs",  # Special for M.E. Lyons
            "project_category": "Arts & Crafts",
            "hours": 8,
            "pledged": 10,
            "start_date": "2024-02-01"
        },
        {
            "volunteer_id": "V003",
            "first_name": "Emma",
            "last_name": "Wilson",
            "email": "emma.w@yahoo.com",
            "age": 17,  # Young volunteer 
            "zip_code": "45238",
            "member_branch": "Clippard YMCA",
            "volunteer_type": "Facility Support",
            "project_category": "Family Programs",
            "hours": 6,
            "pledged": 8,
            "start_date": "2024-03-01"
        },
        {
            "volunteer_id": "V004",
            "first_name": "David",
            "last_name": "Brown",
            "email": "david@newcompany.net",  # Non-common domain
            "phone": "513-555-HELP",  # Invalid format
            "age": 15,  # Too young for Blue Ash
            "zip_code": "INVALID",
            "member_branch": "Blue Ash YMCA",
            "volunteer_type": "Unknown Program",  # Invalid
            "project_category": "Invalid Category",
            "hours": 20,  # Way over pledge
            "pledged": 5,
            "start_date": "2024-04-01"
        },
        {
            "volunteer_id": "V005",
            "first_name": "Lisa",
            "last_name": "Garcia",
            "email": "lisa.garcia@uc.edu",  # .edu domain (should pass custom rule)
            "phone": "513.555.0789",
            "age": 22,
            "zip_code": "45221",
            "member_branch": "Central YMCA", 
            "volunteer_type": "Community Outreach",
            "project_category": "Community Service",
            "hours": 25,  # High hours but within pledge ratio
            "pledged": 30,
            "start_date": "2024-05-01"
        }
    ]
    
    # Run validation on the sample data
    print(f"\nValidating {len(sample_volunteers)} volunteer records...")
    report = engine.validate_dataset(sample_volunteers, branch_field="member_branch")
    
    print(f"\n--- Validation Results ---")
    print(f"Total records: {report.total_records}")
    print(f"Passed records: {report.passed_records}")
    print(f"Failed records: {report.failed_records}")
    print(f"Total validations performed: {report.summary['total_validations']}")
    print(f"Errors: {report.summary['errors']}")
    print(f"Warnings: {report.summary['warnings']}")
    print(f"Info messages: {report.summary['info']}")
    
    # Show detailed issues
    if report.summary['errors'] > 0 or report.summary['warnings'] > 0:
        print(f"\n--- Detailed Issues ---")
        
        # Group by volunteer for cleaner output
        issues_by_volunteer = {}
        for result in report.validation_results:
            if not result.passed:
                # Try to identify which volunteer this relates to
                volunteer_key = "Unknown"
                for i, volunteer in enumerate(sample_volunteers):
                    # This is a simplified match - in practice you'd need better record tracking
                    if volunteer.get(result.field) == result.value:
                        volunteer_key = f"V{i+1:03d} ({volunteer['first_name']} {volunteer['last_name']})"
                        break
                
                if volunteer_key not in issues_by_volunteer:
                    issues_by_volunteer[volunteer_key] = []
                
                issues_by_volunteer[volunteer_key].append(result)
        
        for volunteer, issues in issues_by_volunteer.items():
            print(f"\n{volunteer}:")
            for issue in issues:
                severity_icon = "🔴" if issue.severity == ValidationSeverity.ERROR else "🟡" if issue.severity == ValidationSeverity.WARNING else "ℹ️"
                print(f"  {severity_icon} {issue.severity.value.upper()}: {issue.message}")
                if issue.value is not None:
                    print(f"     Value: '{issue.value}'")
    
    # Demonstrate branch-specific differences
    print(f"\n--- Branch-Specific Rule Demonstration ---")
    
    young_volunteer = {
        "first_name": "Teen",
        "last_name": "Volunteer",
        "email": "teen@example.com",
        "age": 15,
        "member_branch": ""  # Will be set per test
    }
    
    branches_to_test = ["Blue Ash YMCA", "M.E. Lyons YMCA", "Clippard YMCA"]
    
    for branch in branches_to_test:
        young_volunteer["member_branch"] = branch
        results = engine.validate_record(young_volunteer, branch)
        
        age_issues = [r for r in results if r.field == "age" and not r.passed]
        if age_issues:
            severity_levels = [r.severity.value for r in age_issues]
            print(f"  {branch}: Age 15 → {len(age_issues)} issues ({', '.join(severity_levels)})")
        else:
            print(f"  {branch}: Age 15 → ✅ Acceptable")
    
    # Show specialized volunteer types
    print(f"\n--- Specialized Volunteer Types ---")
    
    music_volunteer = {
        "first_name": "Music",
        "last_name": "Teacher",
        "email": "music@example.com",
        "age": 30,
        "volunteer_type": "Music Programs",
        "member_branch": ""
    }
    
    for branch in ["M.E. Lyons YMCA", "Blue Ash YMCA"]:
        music_volunteer["member_branch"] = branch
        results = engine.validate_record(music_volunteer, branch)
        
        type_issues = [r for r in results if r.field == "volunteer_type" and not r.passed]
        if type_issues:
            print(f"  {branch}: 'Music Programs' → ❌ Not allowed")
        else:
            print(f"  {branch}: 'Music Programs' → ✅ Allowed")
    
    return engine, report


def export_configuration_example(engine):
    """Show how to export and work with engine configuration"""
    print(f"\n--- Configuration Export Example ---")
    
    config = engine.export_config()
    
    print(f"Exported configuration contains:")
    print(f"  - Global rules: {len(config['global_rules'])}")
    print(f"  - Reference data categories: {len(config['reference_data'])}")
    print(f"  - Branch overrides: {len(engine.branch_overrides)} branches")
    
    # Show sample of the configuration
    print(f"\nSample global rules:")
    for rule in config['global_rules'][:5]:
        print(f"  - {rule['name']} ({rule['field']}) - {rule['severity']}")
    
    print(f"\nReference data categories:")
    for category, values in config['reference_data'].items():
        print(f"  - {category}: {len(values)} values")
        if len(values) <= 5:
            print(f"    {', '.join(map(str, values))}")
        else:
            print(f"    {', '.join(map(str, values[:3]))}, ... (+{len(values)-3} more)")


def main():
    """Main demonstration function"""
    print("YMCA Data Quality Rules Engine - Custom Configuration Example")
    print("=" * 65)
    
    # Create and demonstrate the engine
    engine, report = demonstrate_engine_usage()
    
    # Show configuration export
    export_configuration_example(engine)
    
    # Generate HTML report example
    print(f"\n--- HTML Report Generation ---")
    html_report = engine.generate_report_html(report)
    
    # Save the report to a file
    report_filename = "data_quality_report.html"
    with open(report_filename, "w") as f:
        f.write(html_report)
    
    print(f"✅ HTML report generated: {report_filename}")
    print(f"   Report contains {len(html_report)} characters")
    
    print(f"\n--- Summary ---")
    print(f"✅ Custom YMCA data quality engine configured successfully")
    print(f"✅ {len(engine.global_rules)} global rules defined")
    print(f"✅ {len(engine.branch_overrides)} branches with specific overrides")
    print(f"✅ Validation system ready for production use")
    
    print(f"\nTo integrate this engine:")
    print(f"1. Import: from data_quality_rules_engine import create_default_engine")
    print(f"2. Create: engine = create_default_engine()")
    print(f"3. Validate: report = engine.validate_dataset(your_data)")
    print(f"4. Use the FastAPI endpoints for web-based validation")


if __name__ == "__main__":
    main()