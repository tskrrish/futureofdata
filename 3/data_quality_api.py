"""
Data Quality API endpoints for the volunteer management system
Integrates the rules engine with FastAPI for web-based data validation
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional, Union
# import pandas as pd  # Optional dependency - will be imported when needed
import json
import io
from datetime import datetime

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

# Create router for data quality endpoints
data_quality_router = APIRouter(prefix="/api/data-quality", tags=["data-quality"])

# Global engine instance (would be managed better in production)
dq_engine = create_default_engine()


# Pydantic models for API
class ValidationRequest(BaseModel):
    data: List[Dict[str, Any]]
    branch: Optional[str] = None
    branch_field: Optional[str] = None


class RuleDefinition(BaseModel):
    name: str
    field: str
    rule_type: str
    severity: str = "error"
    message: str = ""
    enabled: bool = True
    # Rule-specific parameters
    min_val: Optional[Union[int, float]] = None
    max_val: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    format_type: Optional[str] = None
    reference_values: Optional[List[Any]] = None
    custom_validator: Optional[str] = None  # For custom rules (would need careful handling)


class BranchOverrideRequest(BaseModel):
    branch: str
    rule: RuleDefinition


@data_quality_router.get("/health")
async def data_quality_health():
    """Health check for data quality service"""
    return {
        "status": "healthy",
        "engine_loaded": dq_engine is not None,
        "global_rules_count": len(dq_engine.global_rules),
        "branch_overrides_count": len(dq_engine.branch_overrides),
        "timestamp": datetime.now().isoformat()
    }


@data_quality_router.post("/validate")
async def validate_data(request: ValidationRequest) -> JSONResponse:
    """Validate data against quality rules"""
    try:
        # Run validation
        report = dq_engine.validate_dataset(
            data=request.data,
            branch_field=request.branch_field
        )
        
        # Convert report to JSON-serializable format
        results_data = []
        for result in report.validation_results:
            results_data.append({
                "field": result.field,
                "rule_name": result.rule_name,
                "severity": result.severity.value,
                "passed": result.passed,
                "message": result.message,
                "value": str(result.value) if result.value is not None else None,
                "expected": str(result.expected) if result.expected is not None else None
            })
        
        response_data = {
            "total_records": report.total_records,
            "passed_records": report.passed_records,
            "failed_records": report.failed_records,
            "summary": report.summary,
            "validation_results": results_data,
            "timestamp": report.timestamp.isoformat(),
            "branch": report.branch
        }
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@data_quality_router.post("/validate/file")
async def validate_file(
    file: UploadFile = File(...),
    branch: Optional[str] = Form(None),
    branch_field: Optional[str] = Form(None)
):
    """Validate data from uploaded CSV/Excel file"""
    try:
        # Read file content
        content = await file.read()
        
        # Parse based on file type
        try:
            if file.filename.endswith('.csv'):
                import pandas as pd
                df = pd.read_csv(io.StringIO(content.decode('utf-8')))
                data = df.to_dict('records')
            elif file.filename.endswith(('.xlsx', '.xls')):
                import pandas as pd
                df = pd.read_excel(io.BytesIO(content))
                data = df.to_dict('records')
            else:
                raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV or Excel files.")
        except ImportError:
            raise HTTPException(status_code=500, detail="Pandas not available for file parsing. Please validate data via JSON API.")
        
        # Run validation
        report = dq_engine.validate_dataset(data, branch_field=branch_field)
        
        # Convert report to JSON-serializable format
        results_data = []
        for result in report.validation_results:
            results_data.append({
                "field": result.field,
                "rule_name": result.rule_name,
                "severity": result.severity.value,
                "passed": result.passed,
                "message": result.message,
                "value": str(result.value) if result.value is not None else None,
                "expected": str(result.expected) if result.expected is not None else None
            })
        
        response_data = {
            "filename": file.filename,
            "total_records": report.total_records,
            "passed_records": report.passed_records,
            "failed_records": report.failed_records,
            "summary": report.summary,
            "validation_results": results_data,
            "timestamp": report.timestamp.isoformat(),
            "branch": branch
        }
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File validation failed: {str(e)}")


@data_quality_router.get("/report/html")
async def generate_html_report(
    records_passed: int = 0,
    records_failed: int = 0,
    errors: int = 0,
    warnings: int = 0
) -> HTMLResponse:
    """Generate HTML report for validation results"""
    try:
        # This is a simplified version - in practice you'd store and retrieve actual report data
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Data Quality Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
                .metric {{ padding: 15px; border-radius: 5px; text-align: center; min-width: 120px; }}
                .success {{ background: #e8f5e8; color: #2e7d32; }}
                .error {{ background: #ffebee; color: #c62828; }}
                .warning {{ background: #fff3e0; color: #ef6c00; }}
                .info {{ background: #e3f2fd; color: #1565c0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>YMCA Volunteer Data Quality Report</h1>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="summary">
                <div class="metric success">
                    <h3>{records_passed}</h3>
                    <p>Records Passed</p>
                </div>
                <div class="metric error">
                    <h3>{records_failed}</h3>
                    <p>Records Failed</p>
                </div>
                <div class="metric error">
                    <h3>{errors}</h3>
                    <p>Errors</p>
                </div>
                <div class="metric warning">
                    <h3>{warnings}</h3>
                    <p>Warnings</p>
                </div>
            </div>
            
            <div>
                <h2>Data Quality Standards</h2>
                <ul>
                    <li><strong>Required Fields:</strong> first_name, last_name, email</li>
                    <li><strong>Format Validation:</strong> Email addresses, phone numbers, ZIP codes</li>
                    <li><strong>Range Validation:</strong> Age (13-120), Hours (0-80), Pledged hours (≥0)</li>
                    <li><strong>Reference Validation:</strong> Branch names, volunteer types, project categories</li>
                    <li><strong>Business Rules:</strong> Hours vs pledged consistency checks</li>
                </ul>
            </div>
            
            <div>
                <h2>Branch-Specific Overrides</h2>
                <ul>
                    <li><strong>Blue Ash YMCA:</strong> Stricter age requirements (16-65)</li>
                    <li><strong>Campbell County YMCA:</strong> Extended hour limits (0-120)</li>
                    <li><strong>M.E. Lyons YMCA:</strong> Additional volunteer types (Music Programs, Art Therapy)</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@data_quality_router.get("/rules")
async def get_rules(branch: Optional[str] = None) -> JSONResponse:
    """Get all validation rules, optionally filtered by branch"""
    try:
        rules = dq_engine.get_rules_for_branch(branch)
        
        rules_data = []
        for rule in rules:
            rule_data = {
                "name": rule.name,
                "field": rule.field,
                "rule_type": rule.rule_type.value,
                "severity": rule.severity.value,
                "message": rule.message,
                "enabled": rule.enabled
            }
            
            # Add rule-specific parameters
            if hasattr(rule, 'min_val'):
                rule_data["min_val"] = rule.min_val
            if hasattr(rule, 'max_val'):
                rule_data["max_val"] = rule.max_val
            if hasattr(rule, 'pattern'):
                rule_data["pattern"] = rule.pattern
            if hasattr(rule, 'format_type'):
                rule_data["format_type"] = rule.format_type
            if hasattr(rule, 'reference_values'):
                rule_data["reference_values"] = list(rule.reference_values)
                
            rules_data.append(rule_data)
        
        return JSONResponse(content={
            "branch": branch,
            "rules_count": len(rules_data),
            "rules": rules_data
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get rules: {str(e)}")


@data_quality_router.post("/rules/branch-override")
async def add_branch_override(request: BranchOverrideRequest) -> JSONResponse:
    """Add a branch-specific rule override"""
    try:
        rule_def = request.rule
        
        # Create the appropriate rule type
        if rule_def.rule_type == "required":
            rule = RequiredFieldRule(
                field=rule_def.field,
                severity=ValidationSeverity(rule_def.severity)
            )
        elif rule_def.rule_type == "format":
            rule = FormatRule(
                field=rule_def.field,
                format_type=rule_def.format_type or "custom",
                pattern=rule_def.pattern,
                severity=ValidationSeverity(rule_def.severity)
            )
        elif rule_def.rule_type == "range":
            rule = RangeRule(
                field=rule_def.field,
                min_val=rule_def.min_val,
                max_val=rule_def.max_val,
                severity=ValidationSeverity(rule_def.severity)
            )
        elif rule_def.rule_type == "reference":
            rule = ReferenceRule(
                field=rule_def.field,
                reference_values=rule_def.reference_values or [],
                severity=ValidationSeverity(rule_def.severity)
            )
        else:
            raise ValueError(f"Unsupported rule type: {rule_def.rule_type}")
        
        # Override the name if provided
        if rule_def.name:
            rule.name = rule_def.name
        
        # Override the message if provided
        if rule_def.message:
            rule.message = rule_def.message
            
        rule.enabled = rule_def.enabled
        
        # Add the override
        dq_engine.add_branch_override(request.branch, rule)
        
        return JSONResponse(content={
            "success": True,
            "message": f"Added rule override for branch '{request.branch}'",
            "rule_name": rule.name
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add branch override: {str(e)}")


@data_quality_router.delete("/rules/global/{rule_name}")
async def remove_global_rule(rule_name: str) -> JSONResponse:
    """Remove a global rule"""
    try:
        dq_engine.remove_global_rule(rule_name)
        
        return JSONResponse(content={
            "success": True,
            "message": f"Removed global rule '{rule_name}'"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove rule: {str(e)}")


@data_quality_router.post("/rules/disable-for-branch")
async def disable_rule_for_branch(branch: str = Form(...), rule_name: str = Form(...)) -> JSONResponse:
    """Disable a specific rule for a branch"""
    try:
        dq_engine.disable_rule_for_branch(branch, rule_name)
        
        return JSONResponse(content={
            "success": True,
            "message": f"Disabled rule '{rule_name}' for branch '{branch}'"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disable rule: {str(e)}")


@data_quality_router.get("/reference-data")
async def get_reference_data() -> JSONResponse:
    """Get all reference data for validation"""
    try:
        return JSONResponse(content=dq_engine.reference_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get reference data: {str(e)}")


@data_quality_router.put("/reference-data/{category}")
async def update_reference_data(category: str, values: List[Any]) -> JSONResponse:
    """Update reference data for a category"""
    try:
        dq_engine.reference_data[category] = values
        
        return JSONResponse(content={
            "success": True,
            "message": f"Updated reference data for category '{category}'",
            "values": values
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update reference data: {str(e)}")


@data_quality_router.get("/config/export")
async def export_config() -> JSONResponse:
    """Export current engine configuration"""
    try:
        config = dq_engine.export_config()
        return JSONResponse(content=config)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export config: {str(e)}")


# UI endpoints for data quality management
@data_quality_router.get("/ui", response_class=HTMLResponse)
async def data_quality_ui():
    """Data quality management UI"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Data Quality Rules Management</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
            .section { margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
            .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; border-radius: 5px; }
            .upload-area:hover { background: #fafafa; }
            input[type="file"] { margin: 10px 0; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .form-group { margin: 15px 0; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, select { width: 100%; max-width: 300px; padding: 8px; border: 1px solid #ccc; border-radius: 3px; }
            .results { margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>YMCA Data Quality Rules Management</h1>
            
            <div class="section">
                <h2>Upload Data for Validation</h2>
                <div class="upload-area">
                    <p>Drop CSV or Excel files here, or click to select</p>
                    <input type="file" id="dataFile" accept=".csv,.xlsx,.xls">
                    <div class="form-group">
                        <label>Branch (optional):</label>
                        <select id="branch">
                            <option value="">All branches</option>
                            <option value="Blue Ash YMCA">Blue Ash YMCA</option>
                            <option value="M.E. Lyons YMCA">M.E. Lyons YMCA</option>
                            <option value="Campbell County YMCA">Campbell County YMCA</option>
                            <option value="Clippard YMCA">Clippard YMCA</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Branch Field Name (optional):</label>
                        <input type="text" id="branchField" placeholder="e.g., member_branch">
                    </div>
                    <button onclick="validateFile()">Validate Data</button>
                </div>
                <div id="validationResults" class="results" style="display:none;"></div>
            </div>
            
            <div class="section">
                <h2>Current Validation Rules</h2>
                <button onclick="loadRules()">Load Rules</button>
                <div id="rulesDisplay" class="results" style="display:none;"></div>
            </div>
            
            <div class="section">
                <h2>Add Branch Override</h2>
                <form id="branchOverrideForm">
                    <div class="form-group">
                        <label>Branch:</label>
                        <select id="overrideBranch" required>
                            <option value="">Select branch</option>
                            <option value="Blue Ash YMCA">Blue Ash YMCA</option>
                            <option value="M.E. Lyons YMCA">M.E. Lyons YMCA</option>
                            <option value="Campbell County YMCA">Campbell County YMCA</option>
                            <option value="Clippard YMCA">Clippard YMCA</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Field:</label>
                        <input type="text" id="overrideField" required>
                    </div>
                    <div class="form-group">
                        <label>Rule Type:</label>
                        <select id="overrideRuleType" required>
                            <option value="required">Required</option>
                            <option value="format">Format</option>
                            <option value="range">Range</option>
                            <option value="reference">Reference</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Severity:</label>
                        <select id="overrideSeverity">
                            <option value="error">Error</option>
                            <option value="warning">Warning</option>
                            <option value="info">Info</option>
                        </select>
                    </div>
                    <button type="submit">Add Override</button>
                </form>
                <div id="overrideResults" class="results" style="display:none;"></div>
            </div>
        </div>
        
        <script>
            async function validateFile() {
                const fileInput = document.getElementById('dataFile');
                const branchSelect = document.getElementById('branch');
                const branchField = document.getElementById('branchField');
                const resultsDiv = document.getElementById('validationResults');
                
                if (!fileInput.files[0]) {
                    alert('Please select a file');
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                if (branchSelect.value) formData.append('branch', branchSelect.value);
                if (branchField.value) formData.append('branch_field', branchField.value);
                
                try {
                    const response = await fetch('/api/data-quality/validate/file', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    resultsDiv.innerHTML = `
                        <h3>Validation Results for ${data.filename}</h3>
                        <p><strong>Records:</strong> ${data.passed_records}/${data.total_records} passed</p>
                        <p><strong>Errors:</strong> ${data.summary.errors}</p>
                        <p><strong>Warnings:</strong> ${data.summary.warnings}</p>
                        <p><strong>Generated:</strong> ${data.timestamp}</p>
                        <a href="/api/data-quality/report/html?records_passed=${data.passed_records}&records_failed=${data.failed_records}&errors=${data.summary.errors}&warnings=${data.summary.warnings}" target="_blank">
                            <button>View Detailed Report</button>
                        </a>
                    `;
                    resultsDiv.style.display = 'block';
                } catch (error) {
                    resultsDiv.innerHTML = `<p style="color:red;">Error: ${error.message}</p>`;
                    resultsDiv.style.display = 'block';
                }
            }
            
            async function loadRules() {
                const resultsDiv = document.getElementById('rulesDisplay');
                
                try {
                    const response = await fetch('/api/data-quality/rules');
                    const data = await response.json();
                    
                    let rulesHtml = `<h3>${data.rules_count} Active Rules</h3><ul>`;
                    data.rules.forEach(rule => {
                        rulesHtml += `<li><strong>${rule.name}</strong> (${rule.field}) - ${rule.severity} - ${rule.message}</li>`;
                    });
                    rulesHtml += '</ul>';
                    
                    resultsDiv.innerHTML = rulesHtml;
                    resultsDiv.style.display = 'block';
                } catch (error) {
                    resultsDiv.innerHTML = `<p style="color:red;">Error: ${error.message}</p>`;
                    resultsDiv.style.display = 'block';
                }
            }
            
            document.getElementById('branchOverrideForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const branch = document.getElementById('overrideBranch').value;
                const field = document.getElementById('overrideField').value;
                const ruleType = document.getElementById('overrideRuleType').value;
                const severity = document.getElementById('overrideSeverity').value;
                
                const overrideData = {
                    branch: branch,
                    rule: {
                        name: `${field}_${ruleType}_override`,
                        field: field,
                        rule_type: ruleType,
                        severity: severity,
                        message: `Branch override for ${field}`,
                        enabled: true
                    }
                };
                
                try {
                    const response = await fetch('/api/data-quality/rules/branch-override', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(overrideData)
                    });
                    
                    const data = await response.json();
                    const resultsDiv = document.getElementById('overrideResults');
                    
                    resultsDiv.innerHTML = `<p style="color:green;">${data.message}</p>`;
                    resultsDiv.style.display = 'block';
                    
                    // Reset form
                    document.getElementById('branchOverrideForm').reset();
                } catch (error) {
                    const resultsDiv = document.getElementById('overrideResults');
                    resultsDiv.innerHTML = `<p style="color:red;">Error: ${error.message}</p>`;
                    resultsDiv.style.display = 'block';
                }
            });
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


# Function to integrate with main app
def add_data_quality_routes(main_app):
    """Add data quality routes to the main FastAPI app"""
    main_app.include_router(data_quality_router)
    return main_app