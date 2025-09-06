"""
Data Quality Rules Engine
A declarative validation system with branch-specific overrides for volunteer data
"""

import json
import re
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum


class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class RuleType(Enum):
    REQUIRED = "required"
    FORMAT = "format"
    RANGE = "range"
    CUSTOM = "custom"
    REFERENCE = "reference"


@dataclass
class ValidationResult:
    """Result of a single validation rule"""
    field: str
    rule_name: str
    severity: ValidationSeverity
    passed: bool
    message: str
    value: Any = None
    expected: Any = None


@dataclass
class DataQualityReport:
    """Complete validation report for a dataset"""
    total_records: int
    passed_records: int
    failed_records: int
    validation_results: List[ValidationResult]
    summary: Dict[str, int]
    timestamp: datetime
    branch: Optional[str] = None


class ValidationRule:
    """Base class for validation rules"""
    
    def __init__(self, 
                 name: str, 
                 field: str, 
                 rule_type: RuleType, 
                 severity: ValidationSeverity = ValidationSeverity.ERROR,
                 message: str = "",
                 enabled: bool = True):
        self.name = name
        self.field = field
        self.rule_type = rule_type
        self.severity = severity
        self.message = message
        self.enabled = enabled
    
    def validate(self, value: Any, record: Dict[str, Any] = None) -> ValidationResult:
        """Override in subclasses"""
        raise NotImplementedError


class RequiredFieldRule(ValidationRule):
    """Validates that a field is not empty/null"""
    
    def __init__(self, field: str, severity: ValidationSeverity = ValidationSeverity.ERROR):
        super().__init__(
            name=f"{field}_required",
            field=field,
            rule_type=RuleType.REQUIRED,
            severity=severity,
            message=f"Field '{field}' is required"
        )
    
    def validate(self, value: Any, record: Dict[str, Any] = None) -> ValidationResult:
        passed = value is not None and str(value).strip() != ""
        return ValidationResult(
            field=self.field,
            rule_name=self.name,
            severity=self.severity,
            passed=passed,
            message=self.message if not passed else f"Field '{self.field}' is properly filled",
            value=value
        )


class FormatRule(ValidationRule):
    """Validates field format using regex or predefined formats"""
    
    FORMATS = {
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'phone': r'^(\+1-?)?(\([0-9]{3}\)|[0-9]{3})[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$',
        'zip_code': r'^\d{5}(-\d{4})?$',
        'date': r'^\d{4}-\d{2}-\d{2}$',
        'time': r'^\d{2}:\d{2}(:\d{2})?$'
    }
    
    def __init__(self, field: str, format_type: str, pattern: str = None, severity: ValidationSeverity = ValidationSeverity.ERROR):
        self.format_type = format_type
        self.pattern = pattern or self.FORMATS.get(format_type, "")
        
        super().__init__(
            name=f"{field}_{format_type}_format",
            field=field,
            rule_type=RuleType.FORMAT,
            severity=severity,
            message=f"Field '{field}' must match {format_type} format"
        )
    
    def validate(self, value: Any, record: Dict[str, Any] = None) -> ValidationResult:
        if value is None or str(value).strip() == "":
            return ValidationResult(
                field=self.field,
                rule_name=self.name,
                severity=self.severity,
                passed=True,  # Empty values are handled by RequiredFieldRule
                message="Field is empty - skipping format validation",
                value=value
            )
        
        passed = bool(re.match(self.pattern, str(value)))
        return ValidationResult(
            field=self.field,
            rule_name=self.name,
            severity=self.severity,
            passed=passed,
            message=self.message if not passed else f"Field '{self.field}' matches {self.format_type} format",
            value=value,
            expected=self.pattern
        )


class RangeRule(ValidationRule):
    """Validates numeric ranges"""
    
    def __init__(self, field: str, min_val: Union[int, float] = None, max_val: Union[int, float] = None, 
                 severity: ValidationSeverity = ValidationSeverity.ERROR):
        self.min_val = min_val
        self.max_val = max_val
        
        range_desc = []
        if min_val is not None:
            range_desc.append(f"minimum {min_val}")
        if max_val is not None:
            range_desc.append(f"maximum {max_val}")
        
        super().__init__(
            name=f"{field}_range",
            field=field,
            rule_type=RuleType.RANGE,
            severity=severity,
            message=f"Field '{field}' must be within range: {', '.join(range_desc)}"
        )
    
    def validate(self, value: Any, record: Dict[str, Any] = None) -> ValidationResult:
        if value is None or str(value).strip() == "":
            return ValidationResult(
                field=self.field,
                rule_name=self.name,
                severity=self.severity,
                passed=True,  # Empty values are handled by RequiredFieldRule
                message="Field is empty - skipping range validation",
                value=value
            )
        
        try:
            num_val = float(value)
            passed = True
            
            if self.min_val is not None and num_val < self.min_val:
                passed = False
            if self.max_val is not None and num_val > self.max_val:
                passed = False
                
            return ValidationResult(
                field=self.field,
                rule_name=self.name,
                severity=self.severity,
                passed=passed,
                message=self.message if not passed else f"Field '{self.field}' is within valid range",
                value=value,
                expected=f"min: {self.min_val}, max: {self.max_val}"
            )
        except (ValueError, TypeError):
            return ValidationResult(
                field=self.field,
                rule_name=self.name,
                severity=self.severity,
                passed=False,
                message=f"Field '{self.field}' is not numeric",
                value=value
            )


class CustomRule(ValidationRule):
    """Custom validation using a lambda function"""
    
    def __init__(self, field: str, validator: Callable[[Any, Dict[str, Any]], bool], 
                 message: str, severity: ValidationSeverity = ValidationSeverity.ERROR):
        self.validator = validator
        
        super().__init__(
            name=f"{field}_custom",
            field=field,
            rule_type=RuleType.CUSTOM,
            severity=severity,
            message=message
        )
    
    def validate(self, value: Any, record: Dict[str, Any] = None) -> ValidationResult:
        try:
            passed = self.validator(value, record or {})
            return ValidationResult(
                field=self.field,
                rule_name=self.name,
                severity=self.severity,
                passed=passed,
                message=self.message if not passed else f"Field '{self.field}' passes custom validation",
                value=value
            )
        except Exception as e:
            return ValidationResult(
                field=self.field,
                rule_name=self.name,
                severity=self.severity,
                passed=False,
                message=f"Custom validation error: {str(e)}",
                value=value
            )


class ReferenceRule(ValidationRule):
    """Validates that a value exists in a reference list/set"""
    
    def __init__(self, field: str, reference_values: List[Any], 
                 severity: ValidationSeverity = ValidationSeverity.ERROR):
        self.reference_values = set(reference_values)
        
        super().__init__(
            name=f"{field}_reference",
            field=field,
            rule_type=RuleType.REFERENCE,
            severity=severity,
            message=f"Field '{field}' must be one of the allowed values"
        )
    
    def validate(self, value: Any, record: Dict[str, Any] = None) -> ValidationResult:
        if value is None or str(value).strip() == "":
            return ValidationResult(
                field=self.field,
                rule_name=self.name,
                severity=self.severity,
                passed=True,  # Empty values are handled by RequiredFieldRule
                message="Field is empty - skipping reference validation",
                value=value
            )
        
        passed = value in self.reference_values
        return ValidationResult(
            field=self.field,
            rule_name=self.name,
            severity=self.severity,
            passed=passed,
            message=self.message if not passed else f"Field '{self.field}' matches reference value",
            value=value,
            expected=list(self.reference_values)
        )


class DataQualityRulesEngine:
    """Main rules engine with branch-specific override capability"""
    
    def __init__(self):
        self.global_rules: List[ValidationRule] = []
        self.branch_overrides: Dict[str, List[ValidationRule]] = {}
        self.reference_data: Dict[str, List[Any]] = {}
        
        # Load default volunteer data validation rules
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default validation rules for volunteer data"""
        
        # Core volunteer profile rules
        self.add_global_rule(RequiredFieldRule("first_name"))
        self.add_global_rule(RequiredFieldRule("last_name"))
        self.add_global_rule(RequiredFieldRule("email"))
        self.add_global_rule(FormatRule("email", "email"))
        
        # Optional but validated when present
        self.add_global_rule(FormatRule("phone", "phone", severity=ValidationSeverity.WARNING))
        self.add_global_rule(FormatRule("zip_code", "zip_code", severity=ValidationSeverity.WARNING))
        self.add_global_rule(RangeRule("age", min_val=13, max_val=120, severity=ValidationSeverity.WARNING))
        
        # Project/volunteer interaction rules
        self.add_global_rule(RangeRule("hours", min_val=0, max_val=80, severity=ValidationSeverity.WARNING))
        self.add_global_rule(RangeRule("pledged", min_val=0, severity=ValidationSeverity.WARNING))
        
        # Reference data validation
        self.reference_data["branches"] = [
            "Blue Ash YMCA", "M.E. Lyons YMCA", "Campbell County YMCA", 
            "Clippard YMCA", "Central YMCA", "Northwest YMCA"
        ]
        
        self.reference_data["volunteer_types"] = [
            "Youth Development", "Fitness & Wellness", "Special Events", 
            "Facility Support", "Administrative", "Community Outreach"
        ]
        
        self.reference_data["project_categories"] = [
            "After School", "Summer Camp", "Fitness Programs", "Special Events",
            "Childcare", "Senior Programs", "Community Service", "Administrative"
        ]
        
        # Add reference rules
        self.add_global_rule(ReferenceRule("member_branch", self.reference_data["branches"], 
                                         severity=ValidationSeverity.WARNING))
        self.add_global_rule(ReferenceRule("volunteer_type", self.reference_data["volunteer_types"],
                                         severity=ValidationSeverity.WARNING))
        self.add_global_rule(ReferenceRule("project_category", self.reference_data["project_categories"],
                                         severity=ValidationSeverity.WARNING))
        
        # Custom business rules
        self.add_global_rule(CustomRule(
            "hours_vs_pledged",
            lambda val, rec: self._validate_hours_consistency(rec),
            "Hours worked should not exceed pledged hours by more than 20%",
            severity=ValidationSeverity.WARNING
        ))
    
    def _validate_hours_consistency(self, record: Dict[str, Any]) -> bool:
        """Custom validation for hours vs pledged consistency"""
        try:
            hours = float(record.get("hours", 0) or 0)
            pledged = float(record.get("pledged", 0) or 0)
            
            if pledged == 0:
                return True  # Can't validate if no pledge
            
            # Allow up to 20% overage
            return hours <= pledged * 1.2
        except (ValueError, TypeError):
            return True  # Skip validation if values aren't numeric
    
    def add_global_rule(self, rule: ValidationRule):
        """Add a rule that applies to all data"""
        self.global_rules.append(rule)
    
    def add_branch_override(self, branch: str, rule: ValidationRule):
        """Add a branch-specific rule override"""
        if branch not in self.branch_overrides:
            self.branch_overrides[branch] = []
        self.branch_overrides[branch].append(rule)
    
    def remove_global_rule(self, rule_name: str):
        """Remove a global rule by name"""
        self.global_rules = [rule for rule in self.global_rules if rule.name != rule_name]
    
    def disable_rule_for_branch(self, branch: str, rule_name: str):
        """Disable a specific rule for a branch"""
        disabled_rule = CustomRule(
            field="__disabled__",
            validator=lambda v, r: True,
            message=f"Rule {rule_name} disabled for {branch}"
        )
        disabled_rule.name = f"disable_{rule_name}"
        disabled_rule.enabled = False
        
        self.add_branch_override(branch, disabled_rule)
    
    def get_rules_for_branch(self, branch: str = None) -> List[ValidationRule]:
        """Get all applicable rules for a specific branch"""
        rules = []
        
        # Start with global rules
        for rule in self.global_rules:
            if rule.enabled:
                rules.append(rule)
        
        # Apply branch-specific overrides
        if branch and branch in self.branch_overrides:
            # Remove any globally disabled rules for this branch
            disabled_rules = {rule.name.replace("disable_", "") 
                            for rule in self.branch_overrides[branch] 
                            if not rule.enabled}
            
            rules = [rule for rule in rules if rule.name not in disabled_rules]
            
            # Add branch-specific rules
            branch_rules = [rule for rule in self.branch_overrides[branch] if rule.enabled]
            rules.extend(branch_rules)
        
        return rules
    
    def validate_record(self, record: Dict[str, Any], branch: str = None) -> List[ValidationResult]:
        """Validate a single record"""
        results = []
        rules = self.get_rules_for_branch(branch)
        
        for rule in rules:
            if rule.field == "__disabled__":
                continue
                
            value = record.get(rule.field)
            result = rule.validate(value, record)
            results.append(result)
        
        return results
    
    def validate_dataset(self, data: List[Dict[str, Any]], 
                        branch_field: str = None) -> DataQualityReport:
        """Validate an entire dataset"""
        
        # Data should be a list of dictionaries
        records = data
        
        all_results = []
        passed_count = 0
        failed_count = 0
        
        for record in records:
            # Determine branch for this record
            record_branch = record.get(branch_field) if branch_field else None
            
            # Validate the record
            record_results = self.validate_record(record, record_branch)
            all_results.extend(record_results)
            
            # Check if record passes all ERROR-level validations
            has_errors = any(result.severity == ValidationSeverity.ERROR and not result.passed 
                           for result in record_results)
            
            if has_errors:
                failed_count += 1
            else:
                passed_count += 1
        
        # Generate summary
        summary = {
            "total_validations": len(all_results),
            "passed_validations": sum(1 for r in all_results if r.passed),
            "failed_validations": sum(1 for r in all_results if not r.passed),
            "errors": sum(1 for r in all_results if r.severity == ValidationSeverity.ERROR and not r.passed),
            "warnings": sum(1 for r in all_results if r.severity == ValidationSeverity.WARNING and not r.passed),
            "info": sum(1 for r in all_results if r.severity == ValidationSeverity.INFO and not r.passed)
        }
        
        return DataQualityReport(
            total_records=len(records),
            passed_records=passed_count,
            failed_records=failed_count,
            validation_results=all_results,
            summary=summary,
            timestamp=datetime.now(),
            branch=branch_field
        )
    
    def export_config(self) -> Dict[str, Any]:
        """Export current rule configuration to JSON-serializable format"""
        config = {
            "global_rules": [],
            "branch_overrides": {},
            "reference_data": self.reference_data
        }
        
        # Note: This is a simplified export - full rule serialization would need more work
        for rule in self.global_rules:
            rule_config = {
                "name": rule.name,
                "field": rule.field,
                "type": rule.rule_type.value,
                "severity": rule.severity.value,
                "enabled": rule.enabled,
                "message": rule.message
            }
            config["global_rules"].append(rule_config)
        
        return config
    
    def generate_report_html(self, report: DataQualityReport) -> str:
        """Generate an HTML report of validation results"""
        
        errors = [r for r in report.validation_results if r.severity == ValidationSeverity.ERROR and not r.passed]
        warnings = [r for r in report.validation_results if r.severity == ValidationSeverity.WARNING and not r.passed]
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Data Quality Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 15px; border-radius: 5px; }}
                .summary {{ margin: 20px 0; }}
                .error {{ color: #d32f2f; }}
                .warning {{ color: #f57c00; }}
                .success {{ color: #388e3c; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Data Quality Validation Report</h1>
                <p>Generated: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                {f'<p>Branch: {report.branch}</p>' if report.branch else ''}
            </div>
            
            <div class="summary">
                <h2>Summary</h2>
                <p><span class="success">Passed Records: {report.passed_records}/{report.total_records}</span></p>
                <p><span class="error">Failed Records: {report.failed_records}/{report.total_records}</span></p>
                <p>Total Validations: {report.summary['total_validations']}</p>
                <p><span class="error">Errors: {report.summary['errors']}</span></p>
                <p><span class="warning">Warnings: {report.summary['warnings']}</span></p>
            </div>
        """
        
        if errors:
            html += """
            <div>
                <h2>Errors</h2>
                <table>
                    <tr><th>Field</th><th>Rule</th><th>Message</th><th>Value</th></tr>
            """
            for error in errors[:50]:  # Limit to first 50 errors
                html += f"""
                    <tr class="error">
                        <td>{error.field}</td>
                        <td>{error.rule_name}</td>
                        <td>{error.message}</td>
                        <td>{str(error.value)[:100]}</td>
                    </tr>
                """
            html += "</table></div>"
        
        if warnings:
            html += """
            <div>
                <h2>Warnings</h2>
                <table>
                    <tr><th>Field</th><th>Rule</th><th>Message</th><th>Value</th></tr>
            """
            for warning in warnings[:50]:  # Limit to first 50 warnings
                html += f"""
                    <tr class="warning">
                        <td>{warning.field}</td>
                        <td>{warning.rule_name}</td>
                        <td>{warning.message}</td>
                        <td>{str(warning.value)[:100]}</td>
                    </tr>
                """
            html += "</table></div>"
        
        html += "</body></html>"
        return html


def create_default_engine() -> DataQualityRulesEngine:
    """Factory function to create a pre-configured rules engine"""
    engine = DataQualityRulesEngine()
    
    # Add some branch-specific overrides as examples
    
    # Blue Ash YMCA has stricter age requirements for certain programs
    engine.add_branch_override("Blue Ash YMCA", 
        RangeRule("age", min_val=16, max_val=65, severity=ValidationSeverity.ERROR))
    
    # Campbell County YMCA allows longer volunteer sessions
    engine.add_branch_override("Campbell County YMCA",
        RangeRule("hours", min_val=0, max_val=120, severity=ValidationSeverity.WARNING))
    
    # M.E. Lyons YMCA has additional volunteer types
    expanded_types = engine.reference_data["volunteer_types"] + ["Music Programs", "Art Therapy"]
    engine.add_branch_override("M.E. Lyons YMCA",
        ReferenceRule("volunteer_type", expanded_types, severity=ValidationSeverity.WARNING))
    
    return engine


# Example usage
if __name__ == "__main__":
    # Create engine
    engine = create_default_engine()
    
    # Sample data
    sample_data = [
        {
            "first_name": "John",
            "last_name": "Doe", 
            "email": "john.doe@email.com",
            "age": 25,
            "member_branch": "Blue Ash YMCA",
            "volunteer_type": "Youth Development",
            "hours": 5,
            "pledged": 4
        },
        {
            "first_name": "",  # Missing required field
            "last_name": "Smith",
            "email": "invalid-email",  # Invalid format
            "age": 150,  # Out of range
            "member_branch": "Unknown Branch",  # Invalid reference
            "hours": 10,
            "pledged": 5
        }
    ]
    
    # Run validation
    report = engine.validate_dataset(sample_data, branch_field="member_branch")
    
    print(f"Validation complete: {report.passed_records}/{report.total_records} records passed")
    print(f"Errors: {report.summary['errors']}, Warnings: {report.summary['warnings']}")
    
    # Print detailed results
    for result in report.validation_results:
        if not result.passed:
            print(f"{result.severity.value.upper()}: {result.message}")