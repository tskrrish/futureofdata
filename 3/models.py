"""
Data models for advanced shift scheduling with constraints
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Set
from datetime import datetime, time, timedelta
from enum import Enum


class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ShiftType(str, Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"
    OVERNIGHT = "overnight"


class WorkConstraintType(str, Enum):
    MAX_HOURS_PER_DAY = "max_hours_per_day"
    MAX_HOURS_PER_WEEK = "max_hours_per_week"
    REQUIRED_BREAK_BETWEEN_SHIFTS = "required_break_between_shifts"
    MAX_CONSECUTIVE_DAYS = "max_consecutive_days"
    MIN_HOURS_BETWEEN_SHIFTS = "min_hours_between_shifts"


class Employee(BaseModel):
    """Employee/Worker model with skills and constraints"""
    id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    
    # Skills and capabilities
    skills: Dict[str, SkillLevel] = Field(default_factory=dict)
    certifications: List[str] = Field(default_factory=list)
    
    # Work preferences and constraints
    max_hours_per_day: float = 8.0
    max_hours_per_week: float = 40.0
    min_hours_between_shifts: float = 8.0
    max_consecutive_days: int = 5
    
    # Availability
    available_days: List[str] = Field(default_factory=list)  # ["monday", "tuesday", etc.]
    preferred_shift_types: List[ShiftType] = Field(default_factory=list)
    unavailable_dates: List[datetime] = Field(default_factory=list)
    
    # Break requirements
    required_break_duration: float = 0.5  # hours
    requires_lunch_break: bool = True
    
    # Current status
    is_active: bool = True
    hire_date: Optional[datetime] = None
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    def has_skill(self, skill: str, min_level: SkillLevel = SkillLevel.BEGINNER) -> bool:
        """Check if employee has required skill at minimum level"""
        if skill not in self.skills:
            return False
        
        skill_levels = [SkillLevel.BEGINNER, SkillLevel.INTERMEDIATE, SkillLevel.ADVANCED, SkillLevel.EXPERT]
        current_level_idx = skill_levels.index(self.skills[skill])
        required_level_idx = skill_levels.index(min_level)
        
        return current_level_idx >= required_level_idx


class Role(BaseModel):
    """Role/Position requirements for shifts"""
    id: str
    name: str
    description: Optional[str] = None
    
    # Required skills and certifications
    required_skills: Dict[str, SkillLevel] = Field(default_factory=dict)
    required_certifications: List[str] = Field(default_factory=list)
    preferred_skills: Dict[str, SkillLevel] = Field(default_factory=dict)
    
    # Role constraints
    min_experience_days: int = 0
    requires_supervision: bool = False
    can_supervise: bool = False
    
    # Physical requirements
    physical_demands: List[str] = Field(default_factory=list)
    
    def employee_qualifies(self, employee: Employee) -> bool:
        """Check if employee meets role requirements"""
        # Check required skills
        for skill, level in self.required_skills.items():
            if not employee.has_skill(skill, level):
                return False
        
        # Check required certifications
        for cert in self.required_certifications:
            if cert not in employee.certifications:
                return False
        
        return True


class Shift(BaseModel):
    """Shift with role requirements and constraints"""
    id: str
    date: datetime
    start_time: time
    end_time: time
    
    # Role requirements
    role: Role
    required_employees: int = 1
    max_employees: int = 1
    
    # Shift details
    location: str
    department: str
    shift_type: ShiftType
    description: Optional[str] = None
    
    # Priority and scheduling
    priority: int = 1  # 1=low, 5=high
    is_mandatory: bool = False
    
    # Current assignments
    assigned_employees: List[str] = Field(default_factory=list)  # Employee IDs
    
    # Status
    is_published: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    
    @property
    def duration_hours(self) -> float:
        """Calculate shift duration in hours"""
        start_dt = datetime.combine(self.date, self.start_time)
        end_dt = datetime.combine(self.date, self.end_time)
        
        # Handle overnight shifts
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
        
        return (end_dt - start_dt).total_seconds() / 3600
    
    @property
    def is_fully_staffed(self) -> bool:
        """Check if shift has minimum required staff"""
        return len(self.assigned_employees) >= self.required_employees
    
    @property
    def has_capacity(self) -> bool:
        """Check if shift can accept more employees"""
        return len(self.assigned_employees) < self.max_employees


class WorkConstraint(BaseModel):
    """Individual work constraint"""
    employee_id: str
    constraint_type: WorkConstraintType
    value: float
    description: Optional[str] = None
    is_active: bool = True
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None


class Schedule(BaseModel):
    """Complete schedule for a time period"""
    id: str
    name: str
    start_date: datetime
    end_date: datetime
    
    shifts: List[Shift] = Field(default_factory=list)
    employees: List[Employee] = Field(default_factory=list)
    constraints: List[WorkConstraint] = Field(default_factory=list)
    
    # Metadata
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    last_modified: datetime = Field(default_factory=datetime.now)
    
    # Status
    is_published: bool = False
    is_locked: bool = False
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Employee]:
        """Get employee by ID"""
        for employee in self.employees:
            if employee.id == employee_id:
                return employee
        return None
    
    def get_shifts_for_employee(self, employee_id: str) -> List[Shift]:
        """Get all shifts assigned to an employee"""
        return [shift for shift in self.shifts if employee_id in shift.assigned_employees]
    
    def get_shifts_for_date(self, date: datetime) -> List[Shift]:
        """Get all shifts for a specific date"""
        return [shift for shift in self.shifts if shift.date.date() == date.date()]


class ShiftAssignmentResult(BaseModel):
    """Result of shift assignment attempt"""
    success: bool
    shift_id: str
    employee_id: str
    message: str
    violations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ScheduleOptimizationResult(BaseModel):
    """Result of schedule optimization"""
    success: bool
    schedule: Optional[Schedule] = None
    unassigned_shifts: List[str] = Field(default_factory=list)
    constraint_violations: List[str] = Field(default_factory=list)
    optimization_score: float = 0.0
    execution_time: float = 0.0
    message: str = ""


class ShiftRequest(BaseModel):
    """Request for shift scheduling"""
    employee_id: str
    shift_id: str
    priority: int = 1
    reason: Optional[str] = None
    requested_at: datetime = Field(default_factory=datetime.now)


class ShiftSwapRequest(BaseModel):
    """Request to swap shifts between employees"""
    requesting_employee_id: str
    target_employee_id: str
    requesting_shift_id: str
    target_shift_id: str
    reason: Optional[str] = None
    status: str = "pending"  # pending, approved, rejected
    requested_at: datetime = Field(default_factory=datetime.now)