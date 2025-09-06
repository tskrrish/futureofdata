"""
Advanced shift assignment algorithm with constraint optimization
Implements intelligent scheduling with skill matching, hour limits, and break enforcement
"""
from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime, timedelta
import random
from dataclasses import dataclass
import heapq
from models import (
    Employee, Shift, Role, Schedule, WorkConstraint, 
    ShiftAssignmentResult, ScheduleOptimizationResult, SkillLevel
)
from shift_constraints import ConstraintValidator, BreakEnforcer


@dataclass
class AssignmentScore:
    """Score for a potential shift assignment"""
    employee_id: str
    shift_id: str
    total_score: float
    skill_match_score: float
    preference_score: float
    workload_score: float
    constraint_penalty: float


class ShiftScheduler:
    """Advanced shift scheduling algorithm with constraint optimization"""
    
    def __init__(self):
        self.constraint_validator = ConstraintValidator()
        self.break_enforcer = BreakEnforcer()
        
        # Scoring weights
        self.weights = {
            'skill_match': 0.4,
            'employee_preference': 0.25,
            'workload_balance': 0.2,
            'schedule_continuity': 0.15
        }
    
    def optimize_schedule(self, schedule: Schedule, max_iterations: int = 1000) -> ScheduleOptimizationResult:
        """Optimize complete schedule using constraint satisfaction and local search"""
        start_time = datetime.now()
        
        try:
            # Clear existing assignments
            for shift in schedule.shifts:
                shift.assigned_employees = []
            
            # Phase 1: Greedy initial assignment
            initial_result = self._greedy_assignment(schedule)
            
            if not initial_result.success:
                return ScheduleOptimizationResult(
                    success=False,
                    message="Failed to create initial assignment",
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
            
            # Phase 2: Local search optimization
            optimized_schedule = self._local_search_optimization(schedule, max_iterations)
            
            # Calculate final metrics
            unassigned_shifts = [s.id for s in optimized_schedule.shifts if not s.is_fully_staffed]
            violations = self._get_all_constraint_violations(optimized_schedule)
            optimization_score = self._calculate_schedule_score(optimized_schedule)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ScheduleOptimizationResult(
                success=len(violations) == 0,
                schedule=optimized_schedule,
                unassigned_shifts=unassigned_shifts,
                constraint_violations=violations,
                optimization_score=optimization_score,
                execution_time=execution_time,
                message=f"Optimization completed. {len(unassigned_shifts)} unassigned shifts, {len(violations)} violations"
            )
        
        except Exception as e:
            return ScheduleOptimizationResult(
                success=False,
                message=f"Optimization failed: {str(e)}",
                execution_time=(datetime.now() - start_time).total_seconds()
            )
    
    def assign_shift(self, schedule: Schedule, employee_id: str, shift_id: str) -> ShiftAssignmentResult:
        """Assign a specific employee to a specific shift"""
        result = self.constraint_validator.validate_shift_assignment(schedule, employee_id, shift_id)
        
        if result.success:
            shift = next(s for s in schedule.shifts if s.id == shift_id)
            if employee_id not in shift.assigned_employees:
                shift.assigned_employees.append(employee_id)
                result.message = f"Successfully assigned employee {employee_id} to shift {shift_id}"
        
        return result
    
    def find_best_employees_for_shift(self, schedule: Schedule, shift_id: str, limit: int = 5) -> List[AssignmentScore]:
        """Find the best employees for a specific shift"""
        shift = next((s for s in schedule.shifts if s.id == shift_id), None)
        if not shift:
            return []
        
        scores = []
        
        for employee in schedule.employees:
            if employee.id in shift.assigned_employees:
                continue  # Skip already assigned employees
            
            # Validate assignment
            validation = self.constraint_validator.validate_shift_assignment(schedule, employee.id, shift_id)
            if not validation.success:
                continue  # Skip invalid assignments
            
            # Calculate assignment score
            score = self._calculate_assignment_score(schedule, employee, shift)
            scores.append(score)
        
        # Sort by total score (descending)
        scores.sort(key=lambda x: x.total_score, reverse=True)
        return scores[:limit]
    
    def _greedy_assignment(self, schedule: Schedule) -> ScheduleOptimizationResult:
        """Greedy initial assignment prioritizing high-priority shifts"""
        # Sort shifts by priority and difficulty
        sorted_shifts = sorted(
            schedule.shifts,
            key=lambda s: (s.priority, -len(s.role.required_skills), s.date),
            reverse=True
        )
        
        assigned_count = 0
        violations = []
        
        for shift in sorted_shifts:
            if shift.is_fully_staffed:
                continue
            
            # Find best available employees
            candidates = self.find_best_employees_for_shift(schedule, shift.id)
            
            employees_needed = shift.required_employees - len(shift.assigned_employees)
            assignments_made = 0
            
            for candidate in candidates[:employees_needed]:
                assignment_result = self.assign_shift(schedule, candidate.employee_id, shift.id)
                if assignment_result.success:
                    assignments_made += 1
                    assigned_count += 1
                else:
                    violations.extend(assignment_result.violations)
                
                if assignments_made >= employees_needed:
                    break
        
        return ScheduleOptimizationResult(
            success=len(violations) == 0,
            schedule=schedule,
            message=f"Greedy assignment completed. {assigned_count} assignments made."
        )
    
    def _local_search_optimization(self, schedule: Schedule, max_iterations: int) -> Schedule:
        """Local search optimization using swap and reassignment operations"""
        current_score = self._calculate_schedule_score(schedule)
        iterations_without_improvement = 0
        
        for iteration in range(max_iterations):
            # Try different improvement operations
            improved = False
            
            # Operation 1: Try reassigning unassigned shifts
            if self._try_reassign_unassigned_shifts(schedule):
                new_score = self._calculate_schedule_score(schedule)
                if new_score > current_score:
                    current_score = new_score
                    improved = True
            
            # Operation 2: Try swapping assignments for better optimization
            if self._try_swap_assignments(schedule):
                new_score = self._calculate_schedule_score(schedule)
                if new_score > current_score:
                    current_score = new_score
                    improved = True
            
            # Operation 3: Try load balancing
            if self._try_load_balancing(schedule):
                new_score = self._calculate_schedule_score(schedule)
                if new_score > current_score:
                    current_score = new_score
                    improved = True
            
            if improved:
                iterations_without_improvement = 0
            else:
                iterations_without_improvement += 1
            
            # Early termination if no improvement for a while
            if iterations_without_improvement > 100:
                break
        
        return schedule
    
    def _try_reassign_unassigned_shifts(self, schedule: Schedule) -> bool:
        """Try to assign unassigned shifts"""
        improved = False
        unassigned_shifts = [s for s in schedule.shifts if not s.is_fully_staffed]
        
        for shift in unassigned_shifts:
            candidates = self.find_best_employees_for_shift(schedule, shift.id, limit=3)
            
            for candidate in candidates:
                result = self.assign_shift(schedule, candidate.employee_id, shift.id)
                if result.success:
                    improved = True
                    break
        
        return improved
    
    def _try_swap_assignments(self, schedule: Schedule) -> bool:
        """Try swapping assignments between employees for better scores"""
        improved = False
        
        # Find potential swaps
        for shift1 in schedule.shifts:
            if not shift1.assigned_employees:
                continue
                
            for shift2 in schedule.shifts:
                if shift1.id == shift2.id or not shift2.assigned_employees:
                    continue
                
                # Try swapping first employee from each shift
                emp1_id = shift1.assigned_employees[0]
                emp2_id = shift2.assigned_employees[0]
                
                if self._would_swap_improve_score(schedule, emp1_id, emp2_id, shift1, shift2):
                    # Perform the swap
                    shift1.assigned_employees[0] = emp2_id
                    shift2.assigned_employees[0] = emp1_id
                    
                    # Validate the swap
                    val1 = self.constraint_validator.validate_shift_assignment(schedule, emp2_id, shift1.id)
                    val2 = self.constraint_validator.validate_shift_assignment(schedule, emp1_id, shift2.id)
                    
                    if val1.success and val2.success:
                        improved = True
                    else:
                        # Revert the swap
                        shift1.assigned_employees[0] = emp1_id
                        shift2.assigned_employees[0] = emp2_id
        
        return improved
    
    def _try_load_balancing(self, schedule: Schedule) -> bool:
        """Try to balance workload among employees"""
        improved = False
        
        # Calculate workload for each employee
        employee_workloads = {}
        for employee in schedule.employees:
            shifts = schedule.get_shifts_for_employee(employee.id)
            workload = sum(shift.duration_hours for shift in shifts)
            employee_workloads[employee.id] = workload
        
        # Find overloaded and underloaded employees
        avg_workload = sum(employee_workloads.values()) / len(employee_workloads) if employee_workloads else 0
        
        overloaded = [(emp_id, load) for emp_id, load in employee_workloads.items() if load > avg_workload * 1.2]
        underloaded = [(emp_id, load) for emp_id, load in employee_workloads.items() if load < avg_workload * 0.8]
        
        # Try to move shifts from overloaded to underloaded employees
        for overloaded_emp, _ in overloaded:
            overloaded_shifts = schedule.get_shifts_for_employee(overloaded_emp)
            
            for shift in overloaded_shifts:
                for underloaded_emp, _ in underloaded:
                    # Check if underloaded employee can take this shift
                    validation = self.constraint_validator.validate_shift_assignment(schedule, underloaded_emp, shift.id)
                    
                    if validation.success:
                        # Move the shift
                        shift.assigned_employees = [emp_id if emp_id != overloaded_emp else underloaded_emp 
                                                  for emp_id in shift.assigned_employees]
                        improved = True
                        break
                
                if improved:
                    break
        
        return improved
    
    def _calculate_assignment_score(self, schedule: Schedule, employee: Employee, shift: Shift) -> AssignmentScore:
        """Calculate a comprehensive score for assigning an employee to a shift"""
        # Skill match score
        skill_score = self._calculate_skill_match_score(employee, shift.role)
        
        # Employee preference score
        preference_score = self._calculate_preference_score(employee, shift)
        
        # Workload balance score
        workload_score = self._calculate_workload_score(schedule, employee, shift)
        
        # Constraint penalty (lower is better)
        constraint_penalty = self._calculate_constraint_penalty(schedule, employee, shift)
        
        # Calculate weighted total score
        total_score = (
            self.weights['skill_match'] * skill_score +
            self.weights['employee_preference'] * preference_score +
            self.weights['workload_balance'] * workload_score -
            constraint_penalty  # Penalty reduces total score
        )
        
        return AssignmentScore(
            employee_id=employee.id,
            shift_id=shift.id,
            total_score=total_score,
            skill_match_score=skill_score,
            preference_score=preference_score,
            workload_score=workload_score,
            constraint_penalty=constraint_penalty
        )
    
    def _calculate_skill_match_score(self, employee: Employee, role: Role) -> float:
        """Calculate how well employee skills match role requirements"""
        if not role.required_skills:
            return 1.0
        
        skill_scores = []
        skill_levels = [SkillLevel.BEGINNER, SkillLevel.INTERMEDIATE, SkillLevel.ADVANCED, SkillLevel.EXPERT]
        
        for skill, required_level in role.required_skills.items():
            if skill in employee.skills:
                emp_level_idx = skill_levels.index(employee.skills[skill])
                req_level_idx = skill_levels.index(required_level)
                
                # Score based on how much the employee exceeds requirements
                skill_score = min(1.0, (emp_level_idx + 1) / (req_level_idx + 1))
                skill_scores.append(skill_score)
            else:
                skill_scores.append(0.0)  # Missing skill
        
        # Bonus for preferred skills
        for skill, preferred_level in role.preferred_skills.items():
            if skill in employee.skills:
                emp_level_idx = skill_levels.index(employee.skills[skill])
                pref_level_idx = skill_levels.index(preferred_level)
                
                if emp_level_idx >= pref_level_idx:
                    skill_scores.append(0.5)  # Bonus for preferred skills
        
        return sum(skill_scores) / len(skill_scores) if skill_scores else 0.0
    
    def _calculate_preference_score(self, employee: Employee, shift: Shift) -> float:
        """Calculate score based on employee preferences"""
        score = 0.5  # Base score
        
        # Preferred shift types
        if employee.preferred_shift_types:
            if shift.shift_type in employee.preferred_shift_types:
                score += 0.3
            else:
                score -= 0.2
        
        # Day availability
        shift_day = shift.date.strftime('%A').lower()
        if employee.available_days:
            if shift_day in [day.lower() for day in employee.available_days]:
                score += 0.2
            else:
                score -= 0.3
        
        return max(0.0, min(1.0, score))
    
    def _calculate_workload_score(self, schedule: Schedule, employee: Employee, shift: Shift) -> float:
        """Calculate workload balance score (higher is better for balanced workload)"""
        current_shifts = schedule.get_shifts_for_employee(employee.id)
        current_hours = sum(s.duration_hours for s in current_shifts)
        
        # Calculate workload after adding this shift
        new_total_hours = current_hours + shift.duration_hours
        
        # Ideal workload (can be configured)
        ideal_weekly_hours = employee.max_hours_per_week * 0.8  # 80% of maximum
        
        # Score based on how close to ideal workload
        workload_ratio = new_total_hours / ideal_weekly_hours
        
        if workload_ratio <= 1.0:
            return 1.0 - abs(workload_ratio - 0.8)  # Prefer 80% utilization
        else:
            return max(0.0, 1.0 - (workload_ratio - 1.0))  # Penalty for overload
    
    def _calculate_constraint_penalty(self, schedule: Schedule, employee: Employee, shift: Shift) -> float:
        """Calculate penalty for constraint violations and warnings"""
        validation = self.constraint_validator.validate_shift_assignment(schedule, employee.id, shift.id)
        
        penalty = 0.0
        
        # Heavy penalty for violations
        penalty += len(validation.violations) * 0.5
        
        # Light penalty for warnings
        penalty += len(validation.warnings) * 0.1
        
        return penalty
    
    def _calculate_schedule_score(self, schedule: Schedule) -> float:
        """Calculate overall schedule quality score"""
        total_score = 0.0
        total_assignments = 0
        
        for shift in schedule.shifts:
            for emp_id in shift.assigned_employees:
                employee = schedule.get_employee_by_id(emp_id)
                if employee:
                    assignment_score = self._calculate_assignment_score(schedule, employee, shift)
                    total_score += assignment_score.total_score
                    total_assignments += 1
        
        # Penalty for unassigned shifts
        unassigned_count = sum(1 for shift in schedule.shifts if not shift.is_fully_staffed)
        unassigned_penalty = unassigned_count * 0.5
        
        base_score = total_score / max(total_assignments, 1)
        return max(0.0, base_score - unassigned_penalty)
    
    def _would_swap_improve_score(self, schedule: Schedule, emp1_id: str, emp2_id: str, 
                                shift1: Shift, shift2: Shift) -> bool:
        """Check if swapping two employees would improve the overall score"""
        # Calculate current scores
        emp1 = schedule.get_employee_by_id(emp1_id)
        emp2 = schedule.get_employee_by_id(emp2_id)
        
        if not emp1 or not emp2:
            return False
        
        current_score1 = self._calculate_assignment_score(schedule, emp1, shift1).total_score
        current_score2 = self._calculate_assignment_score(schedule, emp2, shift2).total_score
        current_total = current_score1 + current_score2
        
        # Calculate scores after swap
        new_score1 = self._calculate_assignment_score(schedule, emp2, shift1).total_score
        new_score2 = self._calculate_assignment_score(schedule, emp1, shift2).total_score
        new_total = new_score1 + new_score2
        
        return new_total > current_total
    
    def _get_all_constraint_violations(self, schedule: Schedule) -> List[str]:
        """Get all constraint violations in the current schedule"""
        violations = []
        
        for shift in schedule.shifts:
            for emp_id in shift.assigned_employees:
                validation = self.constraint_validator.validate_shift_assignment(schedule, emp_id, shift.id)
                violations.extend(validation.violations)
        
        # Check break compliance
        for employee in schedule.employees:
            break_violations = self.break_enforcer.validate_break_compliance(schedule, employee)
            violations.extend(break_violations)
        
        return violations