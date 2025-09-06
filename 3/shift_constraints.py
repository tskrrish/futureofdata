"""
Advanced constraint validation system for shift scheduling
Handles roles, skills, max hours, breaks, and work constraints
"""
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta, time
from models import (
    Employee, Shift, Role, Schedule, WorkConstraint, WorkConstraintType,
    ShiftAssignmentResult, SkillLevel
)


class ConstraintValidator:
    """Validates all scheduling constraints and work rules"""
    
    def __init__(self):
        self.violation_messages = []
        self.warning_messages = []
    
    def validate_shift_assignment(self, schedule: Schedule, employee_id: str, shift_id: str) -> ShiftAssignmentResult:
        """Validate if an employee can be assigned to a shift"""
        self.violation_messages = []
        self.warning_messages = []
        
        employee = schedule.get_employee_by_id(employee_id)
        shift = next((s for s in schedule.shifts if s.id == shift_id), None)
        
        if not employee:
            return ShiftAssignmentResult(
                success=False,
                shift_id=shift_id,
                employee_id=employee_id,
                message="Employee not found",
                violations=["Employee not found in schedule"]
            )
        
        if not shift:
            return ShiftAssignmentResult(
                success=False,
                shift_id=shift_id,
                employee_id=employee_id,
                message="Shift not found",
                violations=["Shift not found in schedule"]
            )
        
        # Run all validation checks
        is_valid = True
        
        # Basic availability and capacity checks
        if not self._validate_shift_capacity(shift):
            is_valid = False
        
        if not self._validate_employee_availability(employee, shift):
            is_valid = False
        
        # Role and skill requirements
        if not self._validate_role_requirements(employee, shift.role):
            is_valid = False
        
        # Work hour constraints
        if not self._validate_work_hours(schedule, employee, shift):
            is_valid = False
        
        # Break requirements
        if not self._validate_break_requirements(schedule, employee, shift):
            is_valid = False
        
        # Schedule conflicts
        if not self._validate_schedule_conflicts(schedule, employee, shift):
            is_valid = False
        
        # Custom constraints
        if not self._validate_custom_constraints(schedule, employee, shift):
            is_valid = False
        
        success_message = "Assignment valid" if is_valid else "Assignment blocked by constraints"
        
        return ShiftAssignmentResult(
            success=is_valid,
            shift_id=shift_id,
            employee_id=employee_id,
            message=success_message,
            violations=self.violation_messages.copy(),
            warnings=self.warning_messages.copy()
        )
    
    def _validate_shift_capacity(self, shift: Shift) -> bool:
        """Check if shift has capacity for more employees"""
        if not shift.has_capacity:
            self.violation_messages.append(f"Shift {shift.id} is at maximum capacity ({shift.max_employees} employees)")
            return False
        return True
    
    def _validate_employee_availability(self, employee: Employee, shift: Shift) -> bool:
        """Check if employee is available for the shift"""
        if not employee.is_active:
            self.violation_messages.append(f"Employee {employee.full_name} is not active")
            return False
        
        # Check if employee is available on this day of week
        shift_day = shift.date.strftime('%A').lower()
        if employee.available_days and shift_day not in [day.lower() for day in employee.available_days]:
            self.violation_messages.append(f"Employee {employee.full_name} is not available on {shift_day.title()}")
            return False
        
        # Check unavailable dates
        if shift.date.date() in [d.date() for d in employee.unavailable_dates]:
            self.violation_messages.append(f"Employee {employee.full_name} is unavailable on {shift.date.date()}")
            return False
        
        # Check preferred shift types
        if employee.preferred_shift_types and shift.shift_type not in employee.preferred_shift_types:
            self.warning_messages.append(f"Shift type {shift.shift_type} is not preferred by {employee.full_name}")
        
        return True
    
    def _validate_role_requirements(self, employee: Employee, role: Role) -> bool:
        """Validate employee meets role requirements"""
        if not role.employee_qualifies(employee):
            missing_skills = []
            missing_certs = []
            
            # Check skills
            for skill, required_level in role.required_skills.items():
                if not employee.has_skill(skill, required_level):
                    if skill in employee.skills:
                        missing_skills.append(f"{skill} (has {employee.skills[skill]}, needs {required_level})")
                    else:
                        missing_skills.append(f"{skill} ({required_level})")
            
            # Check certifications
            for cert in role.required_certifications:
                if cert not in employee.certifications:
                    missing_certs.append(cert)
            
            violation_parts = []
            if missing_skills:
                violation_parts.append(f"Missing skills: {', '.join(missing_skills)}")
            if missing_certs:
                violation_parts.append(f"Missing certifications: {', '.join(missing_certs)}")
            
            self.violation_messages.append(
                f"Employee {employee.full_name} does not meet role requirements: {'; '.join(violation_parts)}"
            )
            return False
        
        return True
    
    def _validate_work_hours(self, schedule: Schedule, employee: Employee, shift: Shift) -> bool:
        """Validate work hour constraints"""
        is_valid = True
        
        # Check daily hour limits
        daily_hours = self._calculate_daily_hours(schedule, employee, shift.date, shift)
        if daily_hours > employee.max_hours_per_day:
            self.violation_messages.append(
                f"Daily hour limit exceeded: {daily_hours:.1f} hours > {employee.max_hours_per_day} hours"
            )
            is_valid = False
        
        # Check weekly hour limits
        weekly_hours = self._calculate_weekly_hours(schedule, employee, shift.date, shift)
        if weekly_hours > employee.max_hours_per_week:
            self.violation_messages.append(
                f"Weekly hour limit exceeded: {weekly_hours:.1f} hours > {employee.max_hours_per_week} hours"
            )
            is_valid = False
        
        return is_valid
    
    def _validate_break_requirements(self, schedule: Schedule, employee: Employee, shift: Shift) -> bool:
        """Validate break requirements between shifts"""
        employee_shifts = schedule.get_shifts_for_employee(employee.id)
        
        for existing_shift in employee_shifts:
            if existing_shift.id == shift.id:
                continue
            
            hours_between = self._calculate_hours_between_shifts(existing_shift, shift)
            
            if hours_between < employee.min_hours_between_shifts:
                self.violation_messages.append(
                    f"Insufficient break between shifts: {hours_between:.1f} hours < {employee.min_hours_between_shifts} hours required"
                )
                return False
        
        # Check if shift duration requires breaks
        if shift.duration_hours > 6 and employee.requires_lunch_break:
            if shift.duration_hours < employee.required_break_duration:
                self.warning_messages.append(
                    f"Long shift ({shift.duration_hours:.1f} hours) may require lunch break"
                )
        
        return True
    
    def _validate_schedule_conflicts(self, schedule: Schedule, employee: Employee, shift: Shift) -> bool:
        """Check for scheduling conflicts with existing assignments"""
        employee_shifts = schedule.get_shifts_for_employee(employee.id)
        
        for existing_shift in employee_shifts:
            if existing_shift.id == shift.id:
                continue
            
            if self._shifts_overlap(existing_shift, shift):
                self.violation_messages.append(
                    f"Schedule conflict with existing shift {existing_shift.id} on {existing_shift.date.date()}"
                )
                return False
        
        return True
    
    def _validate_custom_constraints(self, schedule: Schedule, employee: Employee, shift: Shift) -> bool:
        """Validate custom work constraints"""
        employee_constraints = [c for c in schedule.constraints if c.employee_id == employee.id and c.is_active]
        
        for constraint in employee_constraints:
            # Check if constraint is currently effective
            if constraint.effective_date and shift.date < constraint.effective_date:
                continue
            if constraint.expiry_date and shift.date > constraint.expiry_date:
                continue
            
            if not self._validate_individual_constraint(schedule, employee, shift, constraint):
                return False
        
        return True
    
    def _validate_individual_constraint(self, schedule: Schedule, employee: Employee, 
                                      shift: Shift, constraint: WorkConstraint) -> bool:
        """Validate a specific work constraint"""
        if constraint.constraint_type == WorkConstraintType.MAX_HOURS_PER_DAY:
            daily_hours = self._calculate_daily_hours(schedule, employee, shift.date, shift)
            if daily_hours > constraint.value:
                self.violation_messages.append(
                    f"Custom daily hour constraint: {daily_hours:.1f} > {constraint.value} hours"
                )
                return False
        
        elif constraint.constraint_type == WorkConstraintType.MAX_HOURS_PER_WEEK:
            weekly_hours = self._calculate_weekly_hours(schedule, employee, shift.date, shift)
            if weekly_hours > constraint.value:
                self.violation_messages.append(
                    f"Custom weekly hour constraint: {weekly_hours:.1f} > {constraint.value} hours"
                )
                return False
        
        elif constraint.constraint_type == WorkConstraintType.MIN_HOURS_BETWEEN_SHIFTS:
            employee_shifts = schedule.get_shifts_for_employee(employee.id)
            for existing_shift in employee_shifts:
                if existing_shift.id == shift.id:
                    continue
                hours_between = self._calculate_hours_between_shifts(existing_shift, shift)
                if hours_between < constraint.value:
                    self.violation_messages.append(
                        f"Custom break constraint: {hours_between:.1f} < {constraint.value} hours between shifts"
                    )
                    return False
        
        elif constraint.constraint_type == WorkConstraintType.MAX_CONSECUTIVE_DAYS:
            consecutive_days = self._calculate_consecutive_work_days(schedule, employee, shift.date, shift)
            if consecutive_days > constraint.value:
                self.violation_messages.append(
                    f"Custom consecutive days constraint: {consecutive_days} > {int(constraint.value)} days"
                )
                return False
        
        return True
    
    def _calculate_daily_hours(self, schedule: Schedule, employee: Employee, 
                              date: datetime, new_shift: Shift) -> float:
        """Calculate total hours for employee on a specific date including new shift"""
        daily_shifts = [s for s in schedule.get_shifts_for_employee(employee.id) 
                       if s.date.date() == date.date()]
        
        total_hours = sum(shift.duration_hours for shift in daily_shifts)
        total_hours += new_shift.duration_hours
        
        return total_hours
    
    def _calculate_weekly_hours(self, schedule: Schedule, employee: Employee, 
                               date: datetime, new_shift: Shift) -> float:
        """Calculate total hours for employee in the week containing the given date"""
        # Get start of week (Monday)
        days_since_monday = date.weekday()
        week_start = date - timedelta(days=days_since_monday)
        week_end = week_start + timedelta(days=6)
        
        weekly_shifts = []
        for shift in schedule.get_shifts_for_employee(employee.id):
            if week_start.date() <= shift.date.date() <= week_end.date():
                weekly_shifts.append(shift)
        
        total_hours = sum(shift.duration_hours for shift in weekly_shifts)
        total_hours += new_shift.duration_hours
        
        return total_hours
    
    def _calculate_hours_between_shifts(self, shift1: Shift, shift2: Shift) -> float:
        """Calculate hours between the end of one shift and start of another"""
        shift1_end = datetime.combine(shift1.date, shift1.end_time)
        shift2_start = datetime.combine(shift2.date, shift2.start_time)
        
        # Handle overnight shifts
        if shift1.end_time < shift1.start_time:
            shift1_end += timedelta(days=1)
        if shift2.start_time < shift2.end_time and shift2.date > shift1.date:
            # Normal case, no adjustment needed
            pass
        
        time_diff = abs((shift2_start - shift1_end).total_seconds())
        return time_diff / 3600  # Convert to hours
    
    def _shifts_overlap(self, shift1: Shift, shift2: Shift) -> bool:
        """Check if two shifts overlap in time"""
        if shift1.date.date() != shift2.date.date():
            return False
        
        start1 = datetime.combine(shift1.date, shift1.start_time)
        end1 = datetime.combine(shift1.date, shift1.end_time)
        start2 = datetime.combine(shift2.date, shift2.start_time)
        end2 = datetime.combine(shift2.date, shift2.end_time)
        
        # Handle overnight shifts
        if shift1.end_time < shift1.start_time:
            end1 += timedelta(days=1)
        if shift2.end_time < shift2.start_time:
            end2 += timedelta(days=1)
        
        return not (end1 <= start2 or end2 <= start1)
    
    def _calculate_consecutive_work_days(self, schedule: Schedule, employee: Employee, 
                                       date: datetime, new_shift: Shift) -> int:
        """Calculate consecutive work days including the new shift"""
        employee_shifts = schedule.get_shifts_for_employee(employee.id)
        
        # Get all work dates
        work_dates = set(shift.date.date() for shift in employee_shifts)
        work_dates.add(new_shift.date.date())
        work_dates = sorted(work_dates)
        
        if not work_dates:
            return 1
        
        # Find the consecutive sequence containing the new shift date
        target_date = new_shift.date.date()
        
        # Find consecutive days leading up to and including target date
        consecutive_count = 1
        current_date = target_date
        
        # Count backwards
        while True:
            prev_date = current_date - timedelta(days=1)
            if prev_date in work_dates:
                consecutive_count += 1
                current_date = prev_date
            else:
                break
        
        # Count forwards
        current_date = target_date
        while True:
            next_date = current_date + timedelta(days=1)
            if next_date in work_dates:
                consecutive_count += 1
                current_date = next_date
            else:
                break
        
        return consecutive_count


class BreakEnforcer:
    """Enforces break requirements and policies"""
    
    def __init__(self):
        self.break_policies = {
            "short_break": {"min_shift_hours": 4, "break_duration": 0.25},  # 15 min
            "lunch_break": {"min_shift_hours": 6, "break_duration": 0.5},   # 30 min
            "long_break": {"min_shift_hours": 10, "break_duration": 1.0},   # 1 hour
        }
    
    def calculate_required_breaks(self, shift: Shift) -> Dict[str, float]:
        """Calculate required breaks for a shift based on duration"""
        required_breaks = {}
        
        for break_type, policy in self.break_policies.items():
            if shift.duration_hours >= policy["min_shift_hours"]:
                required_breaks[break_type] = policy["break_duration"]
        
        return required_breaks
    
    def validate_break_compliance(self, schedule: Schedule, employee: Employee) -> List[str]:
        """Validate that all shifts comply with break requirements"""
        violations = []
        employee_shifts = schedule.get_shifts_for_employee(employee.id)
        
        for shift in employee_shifts:
            required_breaks = self.calculate_required_breaks(shift)
            
            if required_breaks and not self._has_sufficient_break_time(shift, required_breaks):
                violations.append(
                    f"Shift {shift.id} on {shift.date.date()} requires breaks: {required_breaks}"
                )
        
        return violations
    
    def _has_sufficient_break_time(self, shift: Shift, required_breaks: Dict[str, float]) -> bool:
        """Check if shift has sufficient time allocated for breaks"""
        # This is a simplified check - in a real implementation,
        # you'd track actual break periods within shifts
        total_break_time = sum(required_breaks.values())
        effective_work_time = shift.duration_hours - total_break_time
        
        # Ensure we have at least the minimum work time after breaks
        return effective_work_time >= 4.0  # At least 4 hours of actual work