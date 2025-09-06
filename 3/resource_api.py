"""
FastAPI routes for Resource/Equipment Assignment Management
Provides REST API endpoints for managing shifts, resources, and assignments
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
import logging
from resource_management import ResourceManagement

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class ShiftCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    branch: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = None
    start_time: datetime
    end_time: datetime
    max_volunteers: int = Field(default=1, ge=1)

class ShiftUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(scheduled|active|completed|cancelled)$")
    max_volunteers: Optional[int] = Field(None, ge=1)

class ResourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    resource_type: str = Field(..., min_length=1, max_length=50)
    branch: str = Field(..., min_length=1, max_length=100)
    serial_number: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    purchase_date: Optional[str] = None
    condition: str = Field(default="good", pattern="^(excellent|good|fair|poor|maintenance)$")
    max_concurrent_assignments: int = Field(default=1, ge=1)
    requires_training: bool = Field(default=False)
    maintenance_schedule_days: int = Field(default=30, ge=1)

class ResourceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    condition: Optional[str] = Field(None, pattern="^(excellent|good|fair|poor|maintenance)$")
    status: Optional[str] = Field(None, pattern="^(available|assigned|maintenance|retired)$")
    max_concurrent_assignments: Optional[int] = Field(None, ge=1)
    requires_training: Optional[bool] = None
    last_maintenance_date: Optional[str] = None

class ResourceAssignmentCreate(BaseModel):
    shift_id: str
    resource_id: str
    assigned_to_user_id: Optional[str] = None
    assigned_by_user_id: Optional[str] = None
    quantity_assigned: int = Field(default=1, ge=1)
    assignment_notes: Optional[str] = None

class ResourceAssignmentStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(assigned|checked_out|in_use|returned|damaged|lost)$")
    condition_at_checkout: Optional[str] = Field(None, pattern="^(excellent|good|fair|poor)$")
    condition_at_return: Optional[str] = Field(None, pattern="^(excellent|good|fair|poor)$")
    return_notes: Optional[str] = None

class MaintenanceSchedule(BaseModel):
    resource_id: str
    maintenance_type: str = Field(..., min_length=1, max_length=50)
    scheduled_date: str
    description: Optional[str] = None
    performed_by_user_id: Optional[str] = None

# Initialize FastAPI app
app = FastAPI(
    title="Resource Assignment Management API",
    description="API for managing resource/equipment assignments to volunteer shifts",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database instance
async def get_resource_manager():
    return ResourceManagement()

# Shifts endpoints
@app.post("/api/shifts", response_model=dict)
async def create_shift(
    shift_data: ShiftCreate,
    rm: ResourceManagement = Depends(get_resource_manager)
):
    """Create a new shift"""
    try:
        shift = await rm.create_shift(shift_data.dict())
        if shift:
            return {"success": True, "data": shift}
        else:
            raise HTTPException(status_code=400, detail="Failed to create shift")
    except Exception as e:
        logger.error(f"Error creating shift: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/shifts", response_model=dict)
async def get_shifts(
    branch: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    rm: ResourceManagement = Depends(get_resource_manager)
):
    """Get shifts with optional filtering"""
    try:
        date_range = None
        if start_date and end_date:
            date_range = (start_date, end_date)
        
        shifts = await rm.get_shifts(branch=branch, date_range=date_range, status=status)
        return {"success": True, "data": shifts, "count": len(shifts)}
    except Exception as e:
        logger.error(f"Error getting shifts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/shifts/{shift_id}", response_model=dict)
async def get_shift(
    shift_id: str,
    rm: ResourceManagement = Depends(get_resource_manager)
):
    """Get a specific shift by ID"""
    try:
        shifts = await rm.get_shifts()
        shift = next((s for s in shifts if s['id'] == shift_id), None)
        if not shift:
            raise HTTPException(status_code=404, detail="Shift not found")
        return {"success": True, "data": shift}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting shift: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/shifts/{shift_id}", response_model=dict)
async def update_shift(
    shift_id: str,
    updates: ShiftUpdate,
    rm: ResourceManagement = Depends(get_resource_manager)
):
    """Update a shift"""
    try:
        # Filter out None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        success = await rm.update_shift(shift_id, update_data)
        if success:
            return {"success": True, "message": "Shift updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update shift")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating shift: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/shifts/{shift_id}/summary", response_model=dict)
async def get_shift_resource_summary(
    shift_id: str,
    rm: ResourceManagement = Depends(get_resource_manager)
):
    """Get a summary of all resources assigned to a shift"""
    try:
        summary = await rm.get_shift_resource_summary(shift_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Shift not found")
        return {"success": True, "data": summary}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting shift summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Resources endpoints
@app.post("/api/resources", response_model=dict)
async def create_resource(
    resource_data: ResourceCreate,
    rm: ResourceManagement = Depends(get_resource_manager)
):
    """Create a new resource"""
    try:
        resource = await rm.create_resource(resource_data.dict())
        if resource:
            return {"success": True, "data": resource}
        else:
            raise HTTPException(status_code=400, detail="Failed to create resource")
    except Exception as e:
        logger.error(f"Error creating resource: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/resources", response_model=dict)
async def get_resources(
    branch: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    rm: ResourceManagement = Depends(get_resource_manager)
):
    """Get resources with optional filtering"""
    try:
        resources = await rm.get_resources(branch=branch, resource_type=resource_type, status=status)
        return {"success": True, "data": resources, "count": len(resources)}
    except Exception as e:
        logger.error(f"Error getting resources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/resources/{resource_id}", response_model=dict)
async def get_resource(
    resource_id: str,
    rm: ResourceManagement = Depends(get_resource_manager)
):
    """Get a specific resource by ID"""
    try:
        resources = await rm.get_resources()
        resource = next((r for r in resources if r['id'] == resource_id), None)
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        return {"success": True, "data": resource}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting resource: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/resources/{resource_id}", response_model=dict)
async def update_resource(
    resource_id: str,
    updates: ResourceUpdate,
    rm: ResourceManagement = Depends(get_resource_manager)
):
    """Update a resource"""
    try:
        # Filter out None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        success = await rm.update_resource(resource_id, update_data)
        if success:
            return {"success": True, "message": "Resource updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update resource")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating resource: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Resource Assignments endpoints
@app.post("/api/assignments", response_model=dict)
async def create_resource_assignment(
    assignment_data: ResourceAssignmentCreate,
    rm: ResourceManagement = Depends(get_resource_manager)
):
    """Create a new resource assignment"""
    try:
        # Get shift details to add timing info for availability check
        shifts = await rm.get_shifts()
        shift = next((s for s in shifts if s['id'] == assignment_data.shift_id), None)
        if not shift:
            raise HTTPException(status_code=404, detail="Shift not found")
        
        assignment_dict = assignment_data.dict()
        assignment_dict['shift_start_time'] = shift['start_time']
        assignment_dict['shift_end_time'] = shift['end_time']
        
        assignment = await rm.create_resource_assignment(assignment_dict)
        if assignment:
            return {"success": True, "data": assignment}
        else:
            raise HTTPException(status_code=400, detail="Failed to create assignment - resource may not be available")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating assignment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assignments", response_model=dict)
async def get_resource_assignments(
    shift_id: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    rm: ResourceManagement = Depends(get_resource_manager)
):
    """Get resource assignments with optional filtering"""
    try:
        assignments = await rm.get_resource_assignments(
            shift_id=shift_id, resource_id=resource_id, user_id=user_id, status=status
        )
        return {"success": True, "data": assignments, "count": len(assignments)}
    except Exception as e:
        logger.error(f"Error getting assignments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/assignments/{assignment_id}/status", response_model=dict)
async def update_assignment_status(
    assignment_id: str,
    status_update: ResourceAssignmentStatusUpdate,
    rm: ResourceManagement = Depends(get_resource_manager)
):
    """Update the status of a resource assignment"""
    try:
        additional_data = {k: v for k, v in status_update.dict().items() if v is not None and k != 'status'}
        success = await rm.update_assignment_status(assignment_id, status_update.status, additional_data)
        if success:
            return {"success": True, "message": "Assignment status updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update assignment status")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating assignment status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Usage tracking endpoints
@app.get("/api/usage-logs", response_model=dict)
async def get_usage_logs(
    resource_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    shift_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    rm: ResourceManagement = Depends(get_resource_manager)
):
    """Get resource usage logs"""
    try:
        date_range = None
        if start_date and end_date:
            date_range = (start_date, end_date)
        
        logs = await rm.get_usage_logs(
            resource_id=resource_id, user_id=user_id, shift_id=shift_id, date_range=date_range
        )
        return {"success": True, "data": logs, "count": len(logs)}
    except Exception as e:
        logger.error(f"Error getting usage logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/utilization", response_model=dict)
async def get_resource_utilization_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    rm: ResourceManagement = Depends(get_resource_manager)
):
    """Get resource utilization statistics"""
    try:
        date_range = None
        if start_date and end_date:
            date_range = (start_date, end_date)
        
        stats = await rm.get_resource_utilization_stats(date_range=date_range)
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"Error getting utilization stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Maintenance endpoints
@app.post("/api/maintenance", response_model=dict)
async def schedule_maintenance(
    maintenance_data: MaintenanceSchedule,
    rm: ResourceManagement = Depends(get_resource_manager)
):
    """Schedule maintenance for a resource"""
    try:
        maintenance = await rm.schedule_maintenance(maintenance_data.dict())
        if maintenance:
            return {"success": True, "data": maintenance}
        else:
            raise HTTPException(status_code=400, detail="Failed to schedule maintenance")
    except Exception as e:
        logger.error(f"Error scheduling maintenance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/maintenance", response_model=dict)
async def get_maintenance_schedule(
    resource_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    rm: ResourceManagement = Depends(get_resource_manager)
):
    """Get maintenance schedules"""
    try:
        date_range = None
        if start_date and end_date:
            date_range = (start_date, end_date)
        
        schedules = await rm.get_maintenance_schedule(
            resource_id=resource_id, status=status, date_range=date_range
        )
        return {"success": True, "data": schedules, "count": len(schedules)}
    except Exception as e:
        logger.error(f"Error getting maintenance schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Root endpoint with API information
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Resource Assignment Management API",
        "version": "1.0.0",
        "endpoints": {
            "shifts": "/api/shifts",
            "resources": "/api/resources", 
            "assignments": "/api/assignments",
            "usage_logs": "/api/usage-logs",
            "analytics": "/api/analytics/utilization",
            "maintenance": "/api/maintenance",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)