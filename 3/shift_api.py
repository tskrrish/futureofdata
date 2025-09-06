"""
API endpoints for advanced shift scheduling system
Provides RESTful interface for managing schedules, employees, shifts, and constraints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime, date, time

from models import (
    Employee, Shift, Role, Schedule, WorkConstraint, WorkConstraintType,
    ShiftAssignmentResult, ScheduleOptimizationResult, ShiftRequest, 
    ShiftSwapRequest, SkillLevel, ShiftType
)
from shift_scheduler import ShiftScheduler
from shift_constraints import ConstraintValidator, BreakEnforcer


# Initialize router
router = APIRouter(prefix="/api/shifts", tags=["shift-scheduling"])

# Initialize components
scheduler = ShiftScheduler()
validator = ConstraintValidator()
break_enforcer = BreakEnforcer()

# In-memory storage (in production, use a proper database)
schedules_db: Dict[str, Schedule] = {}


# Request/Response models
class CreateEmployeeRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    skills: Dict[str, SkillLevel] = Field(default_factory=dict)
    certifications: List[str] = Field(default_factory=list)
    max_hours_per_day: float = 8.0
    max_hours_per_week: float = 40.0
    available_days: List[str] = Field(default_factory=list)
    preferred_shift_types: List[ShiftType] = Field(default_factory=list)


class CreateRoleRequest(BaseModel):
    name: str
    description: Optional[str] = None
    required_skills: Dict[str, SkillLevel] = Field(default_factory=dict)
    required_certifications: List[str] = Field(default_factory=list)
    preferred_skills: Dict[str, SkillLevel] = Field(default_factory=dict)


class CreateShiftRequest(BaseModel):
    date: datetime
    start_time: time
    end_time: time
    role_id: str
    location: str
    department: str
    shift_type: ShiftType
    required_employees: int = 1
    max_employees: int = 1
    priority: int = 1
    description: Optional[str] = None


class CreateScheduleRequest(BaseModel):
    name: str
    start_date: datetime
    end_date: datetime


class AssignShiftRequest(BaseModel):
    employee_id: str
    shift_id: str


class OptimizeScheduleRequest(BaseModel):
    max_iterations: int = 1000


class AddConstraintRequest(BaseModel):
    employee_id: str
    constraint_type: WorkConstraintType
    value: float
    description: Optional[str] = None
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None


# Employee Management Endpoints
@router.post("/employees", response_model=Employee)
async def create_employee(request: CreateEmployeeRequest):
    """Create a new employee"""
    employee = Employee(
        id=f"emp_{len(schedules_db) + 1}_{int(datetime.now().timestamp())}",
        **request.dict()
    )
    
    return employee


@router.get("/employees/{employee_id}", response_model=Employee)
async def get_employee(employee_id: str):
    """Get employee by ID"""
    for schedule in schedules_db.values():
        employee = schedule.get_employee_by_id(employee_id)
        if employee:
            return employee
    
    raise HTTPException(status_code=404, detail="Employee not found")


@router.put("/employees/{employee_id}", response_model=Employee)
async def update_employee(employee_id: str, request: CreateEmployeeRequest):
    """Update employee information"""
    for schedule in schedules_db.values():
        employee = schedule.get_employee_by_id(employee_id)
        if employee:
            # Update employee fields
            for field, value in request.dict(exclude_unset=True).items():
                setattr(employee, field, value)
            return employee
    
    raise HTTPException(status_code=404, detail="Employee not found")


# Role Management Endpoints
@router.post("/roles", response_model=Role)
async def create_role(request: CreateRoleRequest):
    """Create a new role"""
    role = Role(
        id=f"role_{int(datetime.now().timestamp())}",
        **request.dict()
    )
    
    return role


# Schedule Management Endpoints
@router.post("/schedules", response_model=Schedule)
async def create_schedule(request: CreateScheduleRequest):
    """Create a new schedule"""
    schedule_id = f"schedule_{int(datetime.now().timestamp())}"
    schedule = Schedule(
        id=schedule_id,
        **request.dict()
    )
    
    schedules_db[schedule_id] = schedule
    return schedule


@router.get("/schedules/{schedule_id}", response_model=Schedule)
async def get_schedule(schedule_id: str):
    """Get schedule by ID"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    return schedules_db[schedule_id]


@router.get("/schedules", response_model=List[Schedule])
async def list_schedules():
    """List all schedules"""
    return list(schedules_db.values())


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str):
    """Delete a schedule"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    del schedules_db[schedule_id]
    return {"message": "Schedule deleted successfully"}


# Shift Management Endpoints
@router.post("/schedules/{schedule_id}/shifts", response_model=Shift)
async def create_shift(schedule_id: str, request: CreateShiftRequest):
    """Create a new shift in a schedule"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule = schedules_db[schedule_id]
    
    # Find role (in a real implementation, you'd have a roles database)
    role = Role(
        id=request.role_id,
        name=f"Role_{request.role_id}",
        required_skills={},
        required_certifications=[]
    )
    
    shift = Shift(
        id=f"shift_{len(schedule.shifts) + 1}_{int(datetime.now().timestamp())}",
        role=role,
        **{k: v for k, v in request.dict().items() if k != 'role_id'}
    )
    
    schedule.shifts.append(shift)
    schedule.last_modified = datetime.now()
    
    return shift


@router.get("/schedules/{schedule_id}/shifts", response_model=List[Shift])
async def list_shifts(schedule_id: str, date_filter: Optional[date] = Query(None)):
    """List shifts in a schedule, optionally filtered by date"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule = schedules_db[schedule_id]
    shifts = schedule.shifts
    
    if date_filter:
        shifts = schedule.get_shifts_for_date(datetime.combine(date_filter, time.min))
    
    return shifts


@router.get("/schedules/{schedule_id}/shifts/{shift_id}", response_model=Shift)
async def get_shift(schedule_id: str, shift_id: str):
    """Get a specific shift"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule = schedules_db[schedule_id]
    shift = next((s for s in schedule.shifts if s.id == shift_id), None)
    
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    
    return shift


@router.delete("/schedules/{schedule_id}/shifts/{shift_id}")
async def delete_shift(schedule_id: str, shift_id: str):
    """Delete a shift"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule = schedules_db[schedule_id]
    schedule.shifts = [s for s in schedule.shifts if s.id != shift_id]
    schedule.last_modified = datetime.now()
    
    return {"message": "Shift deleted successfully"}


# Employee Assignment Endpoints
@router.post("/schedules/{schedule_id}/employees")
async def add_employee_to_schedule(schedule_id: str, employee: Employee):
    """Add an employee to a schedule"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule = schedules_db[schedule_id]
    
    # Check if employee already exists
    if any(e.id == employee.id for e in schedule.employees):
        raise HTTPException(status_code=409, detail="Employee already exists in schedule")
    
    schedule.employees.append(employee)
    schedule.last_modified = datetime.now()
    
    return {"message": "Employee added to schedule successfully"}


@router.get("/schedules/{schedule_id}/employees", response_model=List[Employee])
async def list_employees_in_schedule(schedule_id: str):
    """List all employees in a schedule"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    return schedules_db[schedule_id].employees


# Shift Assignment Endpoints
@router.post("/schedules/{schedule_id}/assign", response_model=ShiftAssignmentResult)
async def assign_employee_to_shift(schedule_id: str, request: AssignShiftRequest):
    """Assign an employee to a specific shift"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule = schedules_db[schedule_id]
    result = scheduler.assign_shift(schedule, request.employee_id, request.shift_id)
    
    if result.success:
        schedule.last_modified = datetime.now()
    
    return result


@router.delete("/schedules/{schedule_id}/shifts/{shift_id}/employees/{employee_id}")
async def unassign_employee_from_shift(schedule_id: str, shift_id: str, employee_id: str):
    """Remove an employee from a shift"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule = schedules_db[schedule_id]
    shift = next((s for s in schedule.shifts if s.id == shift_id), None)
    
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    
    if employee_id in shift.assigned_employees:
        shift.assigned_employees.remove(employee_id)
        schedule.last_modified = datetime.now()
        return {"message": "Employee unassigned successfully"}
    
    raise HTTPException(status_code=404, detail="Employee not assigned to this shift")


@router.get("/schedules/{schedule_id}/shifts/{shift_id}/candidates")
async def get_shift_candidates(schedule_id: str, shift_id: str, limit: int = Query(5, ge=1, le=20)):
    """Get best employee candidates for a shift"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule = schedules_db[schedule_id]
    candidates = scheduler.find_best_employees_for_shift(schedule, shift_id, limit)
    
    return [
        {
            "employee_id": c.employee_id,
            "employee_name": schedule.get_employee_by_id(c.employee_id).full_name if schedule.get_employee_by_id(c.employee_id) else "Unknown",
            "total_score": c.total_score,
            "skill_match_score": c.skill_match_score,
            "preference_score": c.preference_score,
            "workload_score": c.workload_score,
            "constraint_penalty": c.constraint_penalty
        }
        for c in candidates
    ]


# Schedule Optimization Endpoints
@router.post("/schedules/{schedule_id}/optimize", response_model=ScheduleOptimizationResult)
async def optimize_schedule(schedule_id: str, request: OptimizeScheduleRequest, background_tasks: BackgroundTasks):
    """Optimize shift assignments in a schedule"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule = schedules_db[schedule_id]
    
    # Run optimization in background for long-running operations
    if request.max_iterations > 100:
        background_tasks.add_task(
            _background_optimization,
            schedule_id,
            request.max_iterations
        )
        return ScheduleOptimizationResult(
            success=True,
            message="Optimization started in background. Check status later.",
            execution_time=0.0
        )
    
    result = scheduler.optimize_schedule(schedule, request.max_iterations)
    
    if result.success:
        schedules_db[schedule_id] = result.schedule
        schedule.last_modified = datetime.now()
    
    return result


async def _background_optimization(schedule_id: str, max_iterations: int):
    """Background task for long-running optimizations"""
    if schedule_id in schedules_db:
        schedule = schedules_db[schedule_id]
        result = scheduler.optimize_schedule(schedule, max_iterations)
        
        if result.success and result.schedule:
            schedules_db[schedule_id] = result.schedule
            schedule.last_modified = datetime.now()


# Constraint Management Endpoints
@router.post("/schedules/{schedule_id}/constraints")
async def add_constraint(schedule_id: str, request: AddConstraintRequest):
    """Add a work constraint to a schedule"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule = schedules_db[schedule_id]
    
    constraint = WorkConstraint(
        employee_id=request.employee_id,
        constraint_type=request.constraint_type,
        value=request.value,
        description=request.description,
        effective_date=request.effective_date,
        expiry_date=request.expiry_date
    )
    
    schedule.constraints.append(constraint)
    schedule.last_modified = datetime.now()
    
    return {"message": "Constraint added successfully", "constraint": constraint}


@router.get("/schedules/{schedule_id}/constraints")
async def list_constraints(schedule_id: str, employee_id: Optional[str] = Query(None)):
    """List constraints in a schedule, optionally filtered by employee"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule = schedules_db[schedule_id]
    constraints = schedule.constraints
    
    if employee_id:
        constraints = [c for c in constraints if c.employee_id == employee_id]
    
    return constraints


# Validation Endpoints
@router.post("/schedules/{schedule_id}/validate")
async def validate_schedule(schedule_id: str):
    """Validate all constraints in a schedule"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule = schedules_db[schedule_id]
    violations = []
    warnings = []
    
    # Validate all current assignments
    for shift in schedule.shifts:
        for emp_id in shift.assigned_employees:
            result = validator.validate_shift_assignment(schedule, emp_id, shift.id)
            violations.extend(result.violations)
            warnings.extend(result.warnings)
    
    # Validate break compliance
    for employee in schedule.employees:
        break_violations = break_enforcer.validate_break_compliance(schedule, employee)
        violations.extend(break_violations)
    
    return {
        "is_valid": len(violations) == 0,
        "violations": violations,
        "warnings": warnings,
        "validation_timestamp": datetime.now().isoformat()
    }


@router.get("/schedules/{schedule_id}/employees/{employee_id}/workload")
async def get_employee_workload(schedule_id: str, employee_id: str):
    """Get detailed workload information for an employee"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule = schedules_db[schedule_id]
    employee = schedule.get_employee_by_id(employee_id)
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    employee_shifts = schedule.get_shifts_for_employee(employee_id)
    
    # Calculate workload metrics
    total_hours = sum(shift.duration_hours for shift in employee_shifts)
    total_shifts = len(employee_shifts)
    
    # Group by week
    weekly_breakdown = {}
    for shift in employee_shifts:
        week_start = shift.date - timedelta(days=shift.date.weekday())
        week_key = week_start.strftime("%Y-W%U")
        
        if week_key not in weekly_breakdown:
            weekly_breakdown[week_key] = {"shifts": 0, "hours": 0.0}
        
        weekly_breakdown[week_key]["shifts"] += 1
        weekly_breakdown[week_key]["hours"] += shift.duration_hours
    
    return {
        "employee_id": employee_id,
        "employee_name": employee.full_name,
        "total_hours": total_hours,
        "total_shifts": total_shifts,
        "average_shift_duration": total_hours / max(total_shifts, 1),
        "max_hours_per_week": employee.max_hours_per_week,
        "max_hours_per_day": employee.max_hours_per_day,
        "weekly_breakdown": weekly_breakdown,
        "utilization_percentage": (total_hours / (employee.max_hours_per_week * len(weekly_breakdown))) * 100 if weekly_breakdown else 0
    }


# Reports and Analytics Endpoints
@router.get("/schedules/{schedule_id}/analytics")
async def get_schedule_analytics(schedule_id: str):
    """Get comprehensive analytics for a schedule"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule = schedules_db[schedule_id]
    
    # Calculate metrics
    total_shifts = len(schedule.shifts)
    assigned_shifts = sum(1 for shift in schedule.shifts if shift.assigned_employees)
    fully_staffed_shifts = sum(1 for shift in schedule.shifts if shift.is_fully_staffed)
    
    # Employee utilization
    employee_stats = []
    for employee in schedule.employees:
        shifts = schedule.get_shifts_for_employee(employee.id)
        hours = sum(shift.duration_hours for shift in shifts)
        utilization = (hours / employee.max_hours_per_week) * 100 if employee.max_hours_per_week > 0 else 0
        
        employee_stats.append({
            "employee_id": employee.id,
            "employee_name": employee.full_name,
            "assigned_shifts": len(shifts),
            "total_hours": hours,
            "utilization_percentage": utilization
        })
    
    # Constraint violations
    violations = []
    for shift in schedule.shifts:
        for emp_id in shift.assigned_employees:
            result = validator.validate_shift_assignment(schedule, emp_id, shift.id)
            violations.extend(result.violations)
    
    return {
        "schedule_id": schedule_id,
        "schedule_name": schedule.name,
        "period": {
            "start_date": schedule.start_date.date(),
            "end_date": schedule.end_date.date()
        },
        "shift_statistics": {
            "total_shifts": total_shifts,
            "assigned_shifts": assigned_shifts,
            "fully_staffed_shifts": fully_staffed_shifts,
            "assignment_rate": (assigned_shifts / max(total_shifts, 1)) * 100,
            "staffing_rate": (fully_staffed_shifts / max(total_shifts, 1)) * 100
        },
        "employee_statistics": {
            "total_employees": len(schedule.employees),
            "average_utilization": sum(emp["utilization_percentage"] for emp in employee_stats) / max(len(employee_stats), 1),
            "employees": employee_stats
        },
        "constraint_compliance": {
            "total_violations": len(violations),
            "is_compliant": len(violations) == 0,
            "violations": violations[:10]  # Show first 10 violations
        },
        "generated_at": datetime.now().isoformat()
    }