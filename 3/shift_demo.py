"""
Demonstration script for the advanced shift scheduling system
Shows how to use the scheduling features with sample data
"""
from datetime import datetime, time, timedelta
from models import (
    Employee, Shift, Role, Schedule, WorkConstraint, WorkConstraintType,
    SkillLevel, ShiftType
)
from shift_scheduler import ShiftScheduler
from shift_constraints import ConstraintValidator, BreakEnforcer


def create_sample_data():
    """Create sample employees, roles, and shifts for demonstration"""
    
    # Create sample employees with different skills
    employees = [
        Employee(
            id="emp_001",
            first_name="Alice",
            last_name="Johnson",
            email="alice.johnson@ymca.org",
            skills={
                "customer_service": SkillLevel.EXPERT,
                "swimming_instruction": SkillLevel.ADVANCED,
                "first_aid": SkillLevel.INTERMEDIATE
            },
            certifications=["CPR", "First Aid", "Lifeguard"],
            max_hours_per_day=8.0,
            max_hours_per_week=40.0,
            available_days=["monday", "tuesday", "wednesday", "thursday", "friday"],
            preferred_shift_types=[ShiftType.MORNING, ShiftType.AFTERNOON]
        ),
        Employee(
            id="emp_002",
            first_name="Bob",
            last_name="Smith",
            email="bob.smith@ymca.org",
            skills={
                "customer_service": SkillLevel.INTERMEDIATE,
                "fitness_training": SkillLevel.EXPERT,
                "equipment_maintenance": SkillLevel.ADVANCED
            },
            certifications=["Personal Trainer", "CPR"],
            max_hours_per_day=6.0,
            max_hours_per_week=30.0,
            available_days=["monday", "wednesday", "friday", "saturday", "sunday"],
            preferred_shift_types=[ShiftType.MORNING, ShiftType.EVENING]
        ),
        Employee(
            id="emp_003",
            first_name="Carol",
            last_name="Davis",
            email="carol.davis@ymca.org",
            skills={
                "customer_service": SkillLevel.ADVANCED,
                "child_care": SkillLevel.EXPERT,
                "program_coordination": SkillLevel.ADVANCED
            },
            certifications=["Child Development Associate", "CPR", "First Aid"],
            max_hours_per_day=8.0,
            max_hours_per_week=32.0,
            available_days=["tuesday", "wednesday", "thursday", "friday", "saturday"],
            preferred_shift_types=[ShiftType.AFTERNOON, ShiftType.EVENING]
        ),
        Employee(
            id="emp_004",
            first_name="David",
            last_name="Wilson",
            email="david.wilson@ymca.org",
            skills={
                "customer_service": SkillLevel.BEGINNER,
                "cleaning": SkillLevel.INTERMEDIATE,
                "equipment_maintenance": SkillLevel.BEGINNER
            },
            certifications=[],
            max_hours_per_day=4.0,
            max_hours_per_week=20.0,
            available_days=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
            preferred_shift_types=[ShiftType.EVENING, ShiftType.NIGHT]
        )
    ]
    
    # Create sample roles
    roles = [
        Role(
            id="role_lifeguard",
            name="Lifeguard",
            description="Pool supervision and water safety",
            required_skills={
                "swimming_instruction": SkillLevel.INTERMEDIATE,
                "first_aid": SkillLevel.INTERMEDIATE
            },
            required_certifications=["Lifeguard", "CPR"]
        ),
        Role(
            id="role_fitness_instructor",
            name="Fitness Instructor", 
            description="Lead fitness classes and assist members",
            required_skills={
                "fitness_training": SkillLevel.ADVANCED,
                "customer_service": SkillLevel.INTERMEDIATE
            },
            required_certifications=["Personal Trainer"]
        ),
        Role(
            id="role_front_desk",
            name="Front Desk Associate",
            description="Member services and facility operations",
            required_skills={
                "customer_service": SkillLevel.INTERMEDIATE
            },
            required_certifications=[]
        ),
        Role(
            id="role_child_care",
            name="Child Care Worker",
            description="Supervise children in child care programs",
            required_skills={
                "child_care": SkillLevel.ADVANCED,
                "customer_service": SkillLevel.INTERMEDIATE
            },
            required_certifications=["Child Development Associate", "CPR"]
        ),
        Role(
            id="role_maintenance",
            name="Facility Maintenance",
            description="Cleaning and basic maintenance tasks",
            required_skills={
                "cleaning": SkillLevel.INTERMEDIATE
            },
            required_certifications=[]
        )
    ]
    
    # Create sample shifts for a week
    base_date = datetime(2024, 3, 18)  # Monday
    shifts = []
    
    for day_offset in range(7):  # One week
        current_date = base_date + timedelta(days=day_offset)
        day_name = current_date.strftime('%A')
        
        # Morning shifts
        if day_offset < 5:  # Weekdays only
            shifts.extend([
                Shift(
                    id=f"shift_lifeguard_morning_{day_offset}",
                    date=current_date,
                    start_time=time(6, 0),
                    end_time=time(14, 0),
                    role=roles[0],  # Lifeguard
                    location="Pool Area",
                    department="Aquatics",
                    shift_type=ShiftType.MORNING,
                    required_employees=2,
                    max_employees=2,
                    priority=5
                ),
                Shift(
                    id=f"shift_front_desk_morning_{day_offset}",
                    date=current_date,
                    start_time=time(5, 30),
                    end_time=time(13, 30),
                    role=roles[2],  # Front Desk
                    location="Main Lobby",
                    department="Member Services",
                    shift_type=ShiftType.MORNING,
                    required_employees=1,
                    max_employees=2,
                    priority=4
                )
            ])
        
        # Afternoon shifts
        shifts.extend([
            Shift(
                id=f"shift_fitness_afternoon_{day_offset}",
                date=current_date,
                start_time=time(14, 0),
                end_time=time(22, 0),
                role=roles[1],  # Fitness Instructor
                location="Fitness Center",
                department="Wellness",
                shift_type=ShiftType.AFTERNOON,
                required_employees=1,
                max_employees=1,
                priority=3
            ),
            Shift(
                id=f"shift_childcare_afternoon_{day_offset}",
                date=current_date,
                start_time=time(15, 0),
                end_time=time(19, 0),
                role=roles[3],  # Child Care
                location="Child Care Room",
                department="Youth Programs",
                shift_type=ShiftType.AFTERNOON,
                required_employees=1,
                max_employees=2,
                priority=5
            )
        ])
        
        # Evening maintenance
        if day_offset in [0, 2, 4]:  # Monday, Wednesday, Friday
            shifts.append(
                Shift(
                    id=f"shift_maintenance_evening_{day_offset}",
                    date=current_date,
                    start_time=time(22, 0),
                    end_time=time(2, 0),  # Next day 2 AM
                    role=roles[4],  # Maintenance
                    location="Entire Facility",
                    department="Operations",
                    shift_type=ShiftType.NIGHT,
                    required_employees=1,
                    max_employees=1,
                    priority=2
                )
            )
    
    return employees, roles, shifts


def create_sample_constraints(employees):
    """Create sample work constraints"""
    return [
        WorkConstraint(
            employee_id="emp_002",  # Bob - part-time worker
            constraint_type=WorkConstraintType.MAX_HOURS_PER_WEEK,
            value=25.0,
            description="Part-time employee - maximum 25 hours per week"
        ),
        WorkConstraint(
            employee_id="emp_003",  # Carol - needs longer breaks
            constraint_type=WorkConstraintType.MIN_HOURS_BETWEEN_SHIFTS,
            value=12.0,
            description="Requires 12 hours between shifts for childcare responsibilities"
        ),
        WorkConstraint(
            employee_id="emp_004",  # David - limited consecutive days
            constraint_type=WorkConstraintType.MAX_CONSECUTIVE_DAYS,
            value=3.0,
            description="Student worker - maximum 3 consecutive work days"
        )
    ]


def demonstrate_shift_scheduling():
    """Main demonstration function"""
    print("🏃‍♂️ YMCA Advanced Shift Scheduling System Demo")
    print("=" * 60)
    
    # Create sample data
    employees, roles, shifts = create_sample_data()
    constraints = create_sample_constraints(employees)
    
    # Create schedule
    schedule = Schedule(
        id="demo_schedule_001",
        name="YMCA March 2024 Weekly Schedule",
        start_date=datetime(2024, 3, 18),
        end_date=datetime(2024, 3, 24),
        employees=employees,
        shifts=shifts,
        constraints=constraints
    )
    
    print(f"📋 Created schedule: {schedule.name}")
    print(f"👥 Employees: {len(employees)}")
    print(f"📊 Shifts: {len(shifts)}")
    print(f"⚖️  Constraints: {len(constraints)}")
    print()
    
    # Initialize scheduler and validator
    scheduler = ShiftScheduler()
    validator = ConstraintValidator()
    break_enforcer = BreakEnforcer()
    
    # Demonstrate individual assignment validation
    print("🔍 Testing Individual Assignment Validation")
    print("-" * 40)
    
    test_assignments = [
        ("emp_001", "shift_lifeguard_morning_0"),  # Alice -> Lifeguard (should work)
        ("emp_002", "shift_fitness_afternoon_1"),   # Bob -> Fitness (should work)
        ("emp_003", "shift_childcare_afternoon_2"), # Carol -> Child Care (should work)
        ("emp_004", "shift_lifeguard_morning_0"),   # David -> Lifeguard (should fail - no qualifications)
    ]
    
    for emp_id, shift_id in test_assignments:
        employee = schedule.get_employee_by_id(emp_id)
        shift = next(s for s in shifts if s.id == shift_id)
        
        result = validator.validate_shift_assignment(schedule, emp_id, shift_id)
        
        status = "✅ VALID" if result.success else "❌ BLOCKED"
        print(f"{status}: {employee.full_name} -> {shift.role.name}")
        
        if result.violations:
            for violation in result.violations:
                print(f"   🚫 {violation}")
        
        if result.warnings:
            for warning in result.warnings:
                print(f"   ⚠️  {warning}")
        
        print()
    
    # Demonstrate schedule optimization
    print("🎯 Running Schedule Optimization")
    print("-" * 40)
    
    optimization_result = scheduler.optimize_schedule(schedule, max_iterations=500)
    
    print(f"Optimization Status: {'✅ SUCCESS' if optimization_result.success else '❌ FAILED'}")
    print(f"Execution Time: {optimization_result.execution_time:.2f} seconds")
    print(f"Optimization Score: {optimization_result.optimization_score:.3f}")
    print(f"Unassigned Shifts: {len(optimization_result.unassigned_shifts)}")
    print(f"Constraint Violations: {len(optimization_result.constraint_violations)}")
    print()
    
    if optimization_result.constraint_violations:
        print("⚠️  Constraint Violations:")
        for violation in optimization_result.constraint_violations[:5]:  # Show first 5
            print(f"   • {violation}")
        print()
    
    # Show assignment results
    print("📈 Final Schedule Assignments")
    print("-" * 40)
    
    for day_offset in range(7):
        date = schedule.start_date + timedelta(days=day_offset)
        day_shifts = schedule.get_shifts_for_date(date)
        
        print(f"📅 {date.strftime('%A, %B %d, %Y')}")
        
        for shift in sorted(day_shifts, key=lambda s: s.start_time):
            assignment_status = f"{len(shift.assigned_employees)}/{shift.required_employees}"
            status_icon = "✅" if shift.is_fully_staffed else "⚠️"
            
            print(f"   {status_icon} {shift.start_time.strftime('%H:%M')}-{shift.end_time.strftime('%H:%M')} "
                  f"{shift.role.name} ({assignment_status})")
            
            for emp_id in shift.assigned_employees:
                employee = schedule.get_employee_by_id(emp_id)
                print(f"      👤 {employee.full_name}")
        
        print()
    
    # Show employee workload summary
    print("👥 Employee Workload Summary")
    print("-" * 40)
    
    for employee in employees:
        employee_shifts = schedule.get_shifts_for_employee(employee.id)
        total_hours = sum(shift.duration_hours for shift in employee_shifts)
        utilization = (total_hours / employee.max_hours_per_week) * 100
        
        print(f"👤 {employee.full_name}:")
        print(f"   📊 {len(employee_shifts)} shifts, {total_hours:.1f} hours ({utilization:.1f}% utilization)")
        print(f"   🎯 Skills: {', '.join(employee.skills.keys())}")
        
        # Check for constraint violations
        violations = []
        for shift in employee_shifts:
            result = validator.validate_shift_assignment(schedule, employee.id, shift.id)
            violations.extend(result.violations)
        
        if violations:
            print(f"   ⚠️  Issues: {violations[0]}")  # Show first issue
        
        print()
    
    # Demonstrate break enforcement
    print("⏰ Break Compliance Check")
    print("-" * 40)
    
    for employee in employees:
        break_violations = break_enforcer.validate_break_compliance(schedule, employee)
        
        if break_violations:
            print(f"⚠️  {employee.full_name}:")
            for violation in break_violations:
                print(f"   • {violation}")
        else:
            print(f"✅ {employee.full_name}: Break compliance OK")
    
    print()
    
    # Demonstrate finding candidates for a shift
    print("🎯 Finding Best Candidates for Specific Shift")
    print("-" * 40)
    
    test_shift = shifts[0]  # First shift
    candidates = scheduler.find_best_employees_for_shift(schedule, test_shift.id, limit=3)
    
    print(f"Shift: {test_shift.role.name} on {test_shift.date.strftime('%A')} "
          f"{test_shift.start_time.strftime('%H:%M')}-{test_shift.end_time.strftime('%H:%M')}")
    print("Best Candidates:")
    
    for i, candidate in enumerate(candidates, 1):
        employee = schedule.get_employee_by_id(candidate.employee_id)
        print(f"   {i}. {employee.full_name} (Score: {candidate.total_score:.3f})")
        print(f"      Skill Match: {candidate.skill_match_score:.3f}, "
              f"Preference: {candidate.preference_score:.3f}, "
              f"Workload: {candidate.workload_score:.3f}")
    
    print()
    print("✨ Demo completed successfully!")


if __name__ == "__main__":
    demonstrate_shift_scheduling()