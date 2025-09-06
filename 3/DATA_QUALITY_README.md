# YMCA Data Quality Rules Engine

A comprehensive data quality validation system with branch-specific overrides for the YMCA Volunteer PathFinder system.

## Overview

The Data Quality Rules Engine provides declarative validation for volunteer data with the ability to customize rules per branch. It supports multiple validation types, severity levels, and generates detailed reports for data quality monitoring.

## Features

### Core Validation Types
- **Required Fields**: Ensure essential data is present
- **Format Validation**: Email, phone, ZIP code, date/time formats
- **Range Validation**: Numeric constraints (age, hours, etc.)
- **Reference Validation**: Check against allowed values
- **Custom Validation**: Business logic and complex rules

### Branch-Specific Overrides
- Different age requirements per branch
- Branch-specific volunteer types and programs
- Customized hour limits and expectations
- Location-specific business rules

### Validation Severity Levels
- **ERROR**: Critical issues that prevent processing
- **WARNING**: Issues that should be reviewed
- **INFO**: Informational messages for awareness

## Quick Start

### Basic Usage

```python
from data_quality_rules_engine import create_default_engine

# Create engine with default YMCA rules
engine = create_default_engine()

# Sample volunteer data
data = [
    {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@email.com",
        "age": 25,
        "member_branch": "Blue Ash YMCA",
        "volunteer_type": "Youth Development",
        "hours": 5,
        "pledged": 6
    }
]

# Run validation
report = engine.validate_dataset(data, branch_field="member_branch")

print(f"Validation Results:")
print(f"- Total records: {report.total_records}")
print(f"- Passed: {report.passed_records}")
print(f"- Failed: {report.failed_records}")
print(f"- Errors: {report.summary['errors']}")
print(f"- Warnings: {report.summary['warnings']}")
```

### API Endpoints

The engine integrates with FastAPI to provide web-based validation:

```bash
# Health check
GET /api/data-quality/health

# Validate data via JSON
POST /api/data-quality/validate
{
    "data": [{"first_name": "John", ...}],
    "branch_field": "member_branch"
}

# Validate uploaded file
POST /api/data-quality/validate/file
# Upload CSV or Excel file

# Get current rules
GET /api/data-quality/rules?branch=Blue%20Ash%20YMCA

# Add branch override
POST /api/data-quality/rules/branch-override
{
    "branch": "Test Branch",
    "rule": {
        "field": "age",
        "rule_type": "range",
        "min_val": 18,
        "max_val": 65
    }
}

# Web UI for rule management
GET /api/data-quality/ui
```

## Default Rules

### Global Rules (All Branches)
- **Required Fields**: first_name, last_name, email
- **Email Format**: Must be valid email address
- **Phone Format**: US phone number formats (warning)
- **Age Range**: 13-120 years (warning)
- **Hours Range**: 0-80 hours (warning)
- **Pledged Hours**: Must be ≥ 0 (warning)
- **Branch Validation**: Must be valid YMCA branch
- **Volunteer Type**: Must be recognized volunteer type
- **Hours Consistency**: Hours ≤ 120% of pledged (custom rule)

### Branch-Specific Overrides

#### Blue Ash YMCA
- **Age Requirement**: 16-65 years (ERROR)
- **Minimum Pledge**: 4+ hours expected

#### Campbell County YMCA  
- **Extended Hours**: Up to 120 hours allowed

#### M.E. Lyons YMCA
- **Additional Programs**: Music Programs, Art Therapy
- **Specialized Categories**: Arts & wellness focus

#### Central YMCA
- **Urban Requirements**: Age 18+ preferred for urban location

#### Clippard YMCA
- **Family Focus**: Family Programs, Parent Education categories

## Custom Configuration

### Creating Custom Rules

```python
from data_quality_rules_engine import (
    DataQualityRulesEngine,
    RequiredFieldRule,
    FormatRule,
    RangeRule,
    CustomRule,
    ValidationSeverity
)

engine = DataQualityRulesEngine()

# Add custom required field
engine.add_global_rule(RequiredFieldRule("emergency_contact"))

# Add custom format rule
engine.add_global_rule(FormatRule("ssn", "custom", pattern=r'^\d{3}-\d{2}-\d{4}$'))

# Add custom range rule
engine.add_global_rule(RangeRule("experience_years", min_val=0, max_val=50))

# Add custom business rule
engine.add_global_rule(CustomRule(
    "weekend_availability",
    lambda val, rec: check_weekend_availability(rec),
    "Youth programs require weekend availability"
))
```

### Adding Branch Overrides

```python
# Stricter age requirement for specific branch
engine.add_branch_override("Downtown YMCA", 
    RangeRule("age", min_val=21, max_val=60, severity=ValidationSeverity.ERROR))

# Branch-specific volunteer types
downtown_types = ["Urban Outreach", "Adult Education", "Job Training"]
engine.add_branch_override("Downtown YMCA",
    ReferenceRule("volunteer_type", downtown_types))

# Disable global rule for specific branch
engine.disable_rule_for_branch("Rural YMCA", "phone_phone_format")
```

## File Structure

```
data_quality_rules_engine.py  # Core engine implementation
data_quality_api.py          # FastAPI integration
simple_test.py               # Test suite
example_config.py           # Configuration examples
DATA_QUALITY_README.md      # This documentation
```

## API Reference

### DataQualityRulesEngine Class

#### Methods
- `validate_record(record, branch=None)` - Validate single record
- `validate_dataset(data, branch_field=None)` - Validate dataset
- `add_global_rule(rule)` - Add rule for all branches
- `add_branch_override(branch, rule)` - Add branch-specific rule
- `disable_rule_for_branch(branch, rule_name)` - Disable rule for branch
- `get_rules_for_branch(branch)` - Get applicable rules
- `generate_report_html(report)` - Generate HTML report
- `export_config()` - Export configuration

### ValidationResult Class

```python
@dataclass
class ValidationResult:
    field: str              # Field that was validated
    rule_name: str         # Name of the rule
    severity: ValidationSeverity  # ERROR, WARNING, or INFO
    passed: bool           # Whether validation passed
    message: str           # Human-readable message
    value: Any            # Actual value (optional)
    expected: Any         # Expected value (optional)
```

### DataQualityReport Class

```python
@dataclass  
class DataQualityReport:
    total_records: int                    # Total records processed
    passed_records: int                   # Records with no ERROR-level failures
    failed_records: int                   # Records with ERROR-level failures
    validation_results: List[ValidationResult]  # All validation results
    summary: Dict[str, int]              # Summary statistics
    timestamp: datetime                   # When report was generated
    branch: Optional[str]                # Branch context (if any)
```

## Testing

Run the test suite:

```bash
# Core functionality tests
python simple_test.py

# Configuration examples and demos
python example_config.py
```

## Integration with Main Application

The data quality engine is integrated into the main YMCA Volunteer PathFinder application:

```python
# In main.py
from data_quality_api import add_data_quality_routes

# Add routes to main app
app = add_data_quality_routes(app)
```

This provides web endpoints for:
- Data validation via API
- File upload validation  
- Rule management UI
- HTML report generation

## Production Considerations

### Performance
- Rules are evaluated in memory for fast validation
- Consider caching reference data for large datasets
- Batch validation recommended for large files

### Security
- Input validation on all API endpoints
- File upload size limits
- Sanitize user-provided validation patterns

### Monitoring
- Track validation failure rates by branch
- Monitor rule performance and accuracy
- Set up alerts for data quality degradation

### Maintenance
- Regular review of branch-specific overrides
- Update reference data as YMCA branches change
- Archive old validation reports

## Troubleshooting

### Common Issues

**"No module named 'pandas'"**
- The engine works without pandas for basic validation
- Pandas is only required for file upload endpoints
- Install pandas: `pip install pandas`

**"Rule not applying to branch"**
- Check branch name spelling (case-sensitive)
- Verify branch exists in reference data
- Use `get_rules_for_branch()` to debug

**"Custom rule always fails"**
- Check lambda function syntax
- Ensure function handles None/empty values
- Test custom validation logic separately

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run validation with debug info
report = engine.validate_dataset(data)
for result in report.validation_results:
    if not result.passed:
        print(f"FAILED: {result.field} - {result.message}")
```

## Contributing

To extend the data quality engine:

1. Add new rule types by inheriting from `ValidationRule`
2. Update reference data in `_load_default_rules()`
3. Add branch-specific logic in `create_default_engine()`
4. Include tests in `simple_test.py`
5. Update this documentation

## License

Part of the YMCA Volunteer PathFinder system. See main project license.