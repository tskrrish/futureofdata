"""
Recurring Role Matching Engine with Conflict Resolution
Handles automatic assignment of recurring volunteer shifts with conflict detection
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class ConflictType(Enum):
    TIME_OVERLAP = "time_overlap"
    VOLUNTEER_UNAVAILABLE = "volunteer_unavailable" 
    CAPACITY_EXCEEDED = "capacity_exceeded"
    SKILL_MISMATCH = "skill_mismatch"
    LOCATION_CONFLICT = "location_conflict"

class ShiftStatus(Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    CONFLICT = "conflict"
    FILLED = "filled"

@dataclass
class RecurringShift:
    id: str
    name: str
    description: str
    branch: str
    category: str
    day_of_week: int  # 0=Monday, 6=Sunday
    start_time: str   # "09:00"
    end_time: str     # "12:00"
    required_volunteers: int
    required_skills: List[str] = field(default_factory=list)
    recurrence_pattern: str = "weekly"  # weekly, biweekly, monthly
    start_date: date = None
    end_date: Optional[date] = None
    active: bool = True
    
@dataclass
class VolunteerAvailability:
    volunteer_id: str
    day_of_week: int
    start_time: str
    end_time: str
    preferred: bool = False
    
@dataclass
class ShiftAssignment:
    id: str
    shift_id: str
    volunteer_id: str
    assignment_date: date
    status: ShiftStatus = ShiftStatus.ASSIGNED
    confidence_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Conflict:
    type: ConflictType
    description: str
    shift_id: str
    volunteer_id: Optional[str] = None
    severity: str = "medium"  # low, medium, high
    resolution_suggestions: List[str] = field(default_factory=list)

class RecurringRoleManager:
    def __init__(self, volunteer_data: Dict[str, Any], database=None):
        self.volunteer_data = volunteer_data
        self.database = database
        
        # Core data structures
        self.recurring_shifts: Dict[str, RecurringShift] = {}
        self.volunteer_availability: Dict[str, List[VolunteerAvailability]] = {}
        self.assignments: Dict[str, ShiftAssignment] = {}
        self.conflicts: Dict[str, List[Conflict]] = {}
        
        # Matching parameters
        self.match_weights = {
            'availability': 0.3,
            'skill_match': 0.25,
            'location_preference': 0.2,
            'volunteer_history': 0.15,
            'reliability_score': 0.1
        }
        
        logger.info("RecurringRoleManager initialized")

    def create_recurring_shift(self, shift_data: Dict[str, Any]) -> str:
        """Create a new recurring shift"""
        shift_id = str(uuid.uuid4())
        
        shift = RecurringShift(
            id=shift_id,
            name=shift_data['name'],
            description=shift_data.get('description', ''),
            branch=shift_data['branch'],
            category=shift_data['category'],
            day_of_week=shift_data['day_of_week'],
            start_time=shift_data['start_time'],
            end_time=shift_data['end_time'],
            required_volunteers=shift_data.get('required_volunteers', 1),
            required_skills=shift_data.get('required_skills', []),
            recurrence_pattern=shift_data.get('recurrence_pattern', 'weekly'),
            start_date=shift_data.get('start_date', date.today()),
            end_date=shift_data.get('end_date')
        )
        
        self.recurring_shifts[shift_id] = shift
        logger.info(f"Created recurring shift: {shift.name}")
        return shift_id

    def add_volunteer_availability(self, volunteer_id: str, availability: List[Dict[str, Any]]) -> bool:
        """Add volunteer availability preferences"""
        volunteer_availability = []
        
        for avail in availability:
            availability_obj = VolunteerAvailability(
                volunteer_id=volunteer_id,
                day_of_week=avail['day_of_week'],
                start_time=avail['start_time'],
                end_time=avail['end_time'],
                preferred=avail.get('preferred', False)
            )
            volunteer_availability.append(availability_obj)
        
        self.volunteer_availability[volunteer_id] = volunteer_availability
        logger.info(f"Added availability for volunteer {volunteer_id}")
        return True

    def generate_shift_assignments(self, weeks_ahead: int = 4) -> Dict[str, List[ShiftAssignment]]:
        """Generate shift assignments for the next N weeks"""
        logger.info(f"Generating assignments for next {weeks_ahead} weeks")
        
        assignments = {}
        current_date = date.today()
        
        for shift_id, shift in self.recurring_shifts.items():
            if not shift.active:
                continue
                
            shift_assignments = []
            
            # Generate dates for this shift based on recurrence pattern
            shift_dates = self._generate_shift_dates(shift, current_date, weeks_ahead)
            
            for shift_date in shift_dates:
                # Find potential volunteers for this shift
                candidates = self._find_shift_candidates(shift, shift_date)
                
                # Detect conflicts before assignment
                conflict_free_candidates = self._filter_conflict_candidates(candidates, shift, shift_date)
                
                # Select best volunteers based on matching algorithm
                selected_volunteers = self._select_volunteers(
                    conflict_free_candidates, 
                    shift, 
                    shift_date
                )
                
                # Create assignments
                for volunteer_id, confidence in selected_volunteers:
                    assignment = ShiftAssignment(
                        id=str(uuid.uuid4()),
                        shift_id=shift_id,
                        volunteer_id=volunteer_id,
                        assignment_date=shift_date,
                        confidence_score=confidence
                    )
                    
                    shift_assignments.append(assignment)
                    self.assignments[assignment.id] = assignment
            
            assignments[shift_id] = shift_assignments
        
        logger.info(f"Generated {sum(len(assigns) for assigns in assignments.values())} total assignments")
        return assignments

    def _generate_shift_dates(self, shift: RecurringShift, start_date: date, weeks_ahead: int) -> List[date]:
        """Generate list of dates when this shift occurs"""
        dates = []
        current_date = start_date
        end_date = start_date + timedelta(weeks=weeks_ahead)
        
        # Find the first occurrence of the shift day
        days_ahead = shift.day_of_week - current_date.weekday()
        if days_ahead < 0:
            days_ahead += 7
        
        first_occurrence = current_date + timedelta(days=days_ahead)
        
        # Generate recurring dates
        occurrence_date = first_occurrence
        while occurrence_date <= end_date:
            if shift.start_date <= occurrence_date:
                if shift.end_date is None or occurrence_date <= shift.end_date:
                    dates.append(occurrence_date)
            
            # Calculate next occurrence based on pattern
            if shift.recurrence_pattern == 'weekly':
                occurrence_date += timedelta(weeks=1)
            elif shift.recurrence_pattern == 'biweekly':
                occurrence_date += timedelta(weeks=2)
            elif shift.recurrence_pattern == 'monthly':
                occurrence_date += timedelta(weeks=4)
            else:
                break
        
        return dates

    def _find_shift_candidates(self, shift: RecurringShift, shift_date: date) -> List[Tuple[str, float]]:
        """Find volunteers who could potentially fill this shift"""
        candidates = []
        
        volunteers_df = self.volunteer_data.get('volunteers')
        if volunteers_df is None:
            return candidates
        
        for _, volunteer in volunteers_df.iterrows():
            volunteer_id = str(volunteer['contact_id'])
            
            # Check basic availability
            if self._is_volunteer_available(volunteer_id, shift, shift_date):
                # Calculate initial match score
                match_score = self._calculate_base_match_score(volunteer, shift)
                candidates.append((volunteer_id, match_score))
        
        # Sort by match score
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates

    def _is_volunteer_available(self, volunteer_id: str, shift: RecurringShift, shift_date: date) -> bool:
        """Check if volunteer is available for this shift"""
        # Check if volunteer has declared availability for this day/time
        volunteer_avail = self.volunteer_availability.get(volunteer_id, [])
        
        day_of_week = shift_date.weekday()
        
        for avail in volunteer_avail:
            if avail.day_of_week == day_of_week:
                # Check time overlap
                if self._times_overlap(
                    avail.start_time, avail.end_time,
                    shift.start_time, shift.end_time
                ):
                    return True
        
        # If no explicit availability, assume available (can be overridden)
        return len(volunteer_avail) == 0

    def _times_overlap(self, start1: str, end1: str, start2: str, end2: str) -> bool:
        """Check if two time ranges overlap"""
        start1_min = self._time_to_minutes(start1)
        end1_min = self._time_to_minutes(end1)
        start2_min = self._time_to_minutes(start2)
        end2_min = self._time_to_minutes(end2)
        
        return not (end1_min <= start2_min or end2_min <= start1_min)

    def _time_to_minutes(self, time_str: str) -> int:
        """Convert time string to minutes since midnight"""
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes

    def _calculate_base_match_score(self, volunteer: pd.Series, shift: RecurringShift) -> float:
        """Calculate base match score for volunteer-shift pair"""
        score = 0.0
        
        # Location preference
        volunteer_branch = volunteer.get('member_branch', '')
        if volunteer_branch == shift.branch:
            score += self.match_weights['location_preference']
        elif volunteer_branch:  # Different branch but has preference
            score += self.match_weights['location_preference'] * 0.5
        else:  # No preference
            score += self.match_weights['location_preference'] * 0.7
        
        # Category alignment
        volunteer_categories = str(volunteer.get('project_categories', '')).lower()
        if shift.category.lower() in volunteer_categories:
            score += self.match_weights['skill_match']
        elif any(cat in volunteer_categories for cat in ['general', 'all']):
            score += self.match_weights['skill_match'] * 0.6
        
        # Volunteer history and reliability
        total_hours = volunteer.get('total_hours', 0)
        volunteer_sessions = volunteer.get('volunteer_sessions', 0)
        
        if volunteer_sessions > 0:
            reliability = min(1.0, total_hours / volunteer_sessions / 3)  # Normalize by expected hours
            score += self.match_weights['reliability_score'] * reliability
        
        # Experience level
        if total_hours > 50:
            score += self.match_weights['volunteer_history']
        elif total_hours > 20:
            score += self.match_weights['volunteer_history'] * 0.7
        elif total_hours > 0:
            score += self.match_weights['volunteer_history'] * 0.5
        
        # Availability bonus (if explicitly available)
        volunteer_id = str(volunteer['contact_id'])
        if volunteer_id in self.volunteer_availability:
            # Check if this matches preferred times
            for avail in self.volunteer_availability[volunteer_id]:
                if avail.preferred and avail.day_of_week == shift.day_of_week:
                    score += self.match_weights['availability']
                    break
            else:
                score += self.match_weights['availability'] * 0.7
        else:
            score += self.match_weights['availability'] * 0.5
        
        return min(score, 1.0)

    def _filter_conflict_candidates(self, candidates: List[Tuple[str, float]], 
                                  shift: RecurringShift, shift_date: date) -> List[Tuple[str, float]]:
        """Filter out candidates who have conflicts"""
        filtered_candidates = []
        
        for volunteer_id, score in candidates:
            conflicts = self._detect_volunteer_conflicts(volunteer_id, shift, shift_date)
            
            if not conflicts:
                filtered_candidates.append((volunteer_id, score))
            else:
                # Store conflicts for later resolution
                shift_key = f"{shift.id}_{shift_date.isoformat()}"
                if shift_key not in self.conflicts:
                    self.conflicts[shift_key] = []
                self.conflicts[shift_key].extend(conflicts)
        
        return filtered_candidates

    def _detect_volunteer_conflicts(self, volunteer_id: str, shift: RecurringShift, 
                                  shift_date: date) -> List[Conflict]:
        """Detect conflicts for a volunteer on a specific shift"""
        conflicts = []
        
        # Check for time conflicts with other assignments
        existing_assignments = self._get_volunteer_assignments(volunteer_id, shift_date)
        
        for assignment in existing_assignments:
            other_shift = self.recurring_shifts.get(assignment.shift_id)
            if other_shift and self._times_overlap(
                shift.start_time, shift.end_time,
                other_shift.start_time, other_shift.end_time
            ):
                conflicts.append(Conflict(
                    type=ConflictType.TIME_OVERLAP,
                    description=f"Volunteer {volunteer_id} has overlapping shift: {other_shift.name}",
                    shift_id=shift.id,
                    volunteer_id=volunteer_id,
                    severity="high",
                    resolution_suggestions=[
                        "Adjust shift times to avoid overlap",
                        "Find alternative volunteer",
                        "Split shift into smaller segments"
                    ]
                ))
        
        # Check availability conflicts
        if not self._is_volunteer_available(volunteer_id, shift, shift_date):
            conflicts.append(Conflict(
                type=ConflictType.VOLUNTEER_UNAVAILABLE,
                description=f"Volunteer {volunteer_id} not available during shift time",
                shift_id=shift.id,
                volunteer_id=volunteer_id,
                severity="medium",
                resolution_suggestions=[
                    "Contact volunteer to confirm availability",
                    "Adjust shift timing",
                    "Find alternative volunteer"
                ]
            ))
        
        # Check skill requirements
        volunteer_data = self._get_volunteer_data(volunteer_id)
        if volunteer_data is not None and shift.required_skills:
            volunteer_skills = str(volunteer_data.get('skills', '')).lower()
            missing_skills = [skill for skill in shift.required_skills 
                            if skill.lower() not in volunteer_skills]
            
            if missing_skills:
                conflicts.append(Conflict(
                    type=ConflictType.SKILL_MISMATCH,
                    description=f"Volunteer {volunteer_id} missing skills: {missing_skills}",
                    shift_id=shift.id,
                    volunteer_id=volunteer_id,
                    severity="low",
                    resolution_suggestions=[
                        "Provide training before shift",
                        "Pair with experienced volunteer",
                        "Find volunteer with required skills"
                    ]
                ))
        
        return conflicts

    def _get_volunteer_assignments(self, volunteer_id: str, assignment_date: date) -> List[ShiftAssignment]:
        """Get all assignments for a volunteer on a specific date"""
        return [assignment for assignment in self.assignments.values()
                if assignment.volunteer_id == volunteer_id 
                and assignment.assignment_date == assignment_date]

    def _get_volunteer_data(self, volunteer_id: str) -> Optional[pd.Series]:
        """Get volunteer data from the dataset"""
        volunteers_df = self.volunteer_data.get('volunteers')
        if volunteers_df is None:
            return None
        
        volunteer_matches = volunteers_df[volunteers_df['contact_id'] == int(volunteer_id)]
        return volunteer_matches.iloc[0] if len(volunteer_matches) > 0 else None

    def _select_volunteers(self, candidates: List[Tuple[str, float]], 
                          shift: RecurringShift, shift_date: date) -> List[Tuple[str, float]]:
        """Select the best volunteers for this shift"""
        if not candidates:
            return []
        
        # Sort by score and select top candidates
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Select required number of volunteers
        selected = candidates[:shift.required_volunteers]
        
        return selected

    def resolve_conflicts(self, shift_id: str, conflict_resolution_strategy: str = "auto") -> Dict[str, Any]:
        """Resolve conflicts for a specific shift"""
        shift_conflicts = []
        
        # Find all conflicts related to this shift
        for key, conflicts in self.conflicts.items():
            if shift_id in key:
                shift_conflicts.extend(conflicts)
        
        if not shift_conflicts:
            return {"status": "no_conflicts", "conflicts_resolved": 0}
        
        resolved_conflicts = 0
        
        for conflict in shift_conflicts:
            if conflict_resolution_strategy == "auto":
                if self._auto_resolve_conflict(conflict):
                    resolved_conflicts += 1
        
        return {
            "status": "conflicts_resolved",
            "total_conflicts": len(shift_conflicts),
            "conflicts_resolved": resolved_conflicts,
            "remaining_conflicts": len(shift_conflicts) - resolved_conflicts
        }

    def _auto_resolve_conflict(self, conflict: Conflict) -> bool:
        """Attempt to automatically resolve a conflict"""
        if conflict.type == ConflictType.TIME_OVERLAP:
            # Try to find alternative volunteers
            return self._reassign_conflicted_volunteer(conflict)
        elif conflict.type == ConflictType.VOLUNTEER_UNAVAILABLE:
            # Remove assignment and find replacement
            return self._find_replacement_volunteer(conflict)
        elif conflict.type == ConflictType.SKILL_MISMATCH:
            # Lower priority - can be handled with training
            return True
        
        return False

    def _reassign_conflicted_volunteer(self, conflict: Conflict) -> bool:
        """Reassign a volunteer with time conflicts"""
        # This is a simplified implementation
        # In reality, this would involve complex rescheduling
        logger.info(f"Attempting to resolve time conflict for volunteer {conflict.volunteer_id}")
        return False  # Placeholder

    def _find_replacement_volunteer(self, conflict: Conflict) -> bool:
        """Find a replacement volunteer"""
        logger.info(f"Looking for replacement for volunteer {conflict.volunteer_id}")
        return False  # Placeholder

    def get_assignment_summary(self, weeks_ahead: int = 4) -> Dict[str, Any]:
        """Get summary of current assignments"""
        assignments = self.generate_shift_assignments(weeks_ahead)
        
        total_assignments = sum(len(shift_assigns) for shift_assigns in assignments.values())
        total_shifts = len(self.recurring_shifts)
        
        # Calculate fill rate
        expected_assignments = total_shifts * weeks_ahead * sum(
            shift.required_volunteers for shift in self.recurring_shifts.values()
        )
        fill_rate = total_assignments / expected_assignments if expected_assignments > 0 else 0
        
        # Conflict summary
        total_conflicts = sum(len(conflicts) for conflicts in self.conflicts.values())
        
        return {
            "total_shifts": total_shifts,
            "total_assignments": total_assignments,
            "expected_assignments": expected_assignments,
            "fill_rate": fill_rate,
            "total_conflicts": total_conflicts,
            "weeks_ahead": weeks_ahead,
            "assignments_by_shift": {
                shift_id: len(assigns) for shift_id, assigns in assignments.items()
            }
        }

    def export_assignments_to_dict(self) -> Dict[str, Any]:
        """Export assignments to dictionary format"""
        return {
            "shifts": {
                shift_id: {
                    "name": shift.name,
                    "description": shift.description,
                    "branch": shift.branch,
                    "category": shift.category,
                    "day_of_week": shift.day_of_week,
                    "start_time": shift.start_time,
                    "end_time": shift.end_time,
                    "required_volunteers": shift.required_volunteers,
                    "required_skills": shift.required_skills,
                    "active": shift.active
                }
                for shift_id, shift in self.recurring_shifts.items()
            },
            "assignments": {
                assign_id: {
                    "shift_id": assign.shift_id,
                    "volunteer_id": assign.volunteer_id,
                    "assignment_date": assign.assignment_date.isoformat(),
                    "status": assign.status.value,
                    "confidence_score": assign.confidence_score
                }
                for assign_id, assign in self.assignments.items()
            },
            "conflicts": {
                key: [
                    {
                        "type": conflict.type.value,
                        "description": conflict.description,
                        "shift_id": conflict.shift_id,
                        "volunteer_id": conflict.volunteer_id,
                        "severity": conflict.severity,
                        "resolution_suggestions": conflict.resolution_suggestions
                    }
                    for conflict in conflicts
                ]
                for key, conflicts in self.conflicts.items()
            }
        }