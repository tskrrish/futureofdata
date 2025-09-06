"""
Availability Overlap Scoring System for Volunteer Shift Matching
Provides fine-grained window matching for shifts with time-based scoring
"""

from datetime import datetime, time, timedelta
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum

class DayOfWeek(Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

@dataclass
class TimeWindow:
    """Represents a time window with start and end times"""
    start_time: time
    end_time: time
    day_of_week: DayOfWeek
    
    def duration_hours(self) -> float:
        """Calculate duration in hours"""
        start_datetime = datetime.combine(datetime.today(), self.start_time)
        end_datetime = datetime.combine(datetime.today(), self.end_time)
        
        # Handle overnight shifts
        if self.end_time < self.start_time:
            end_datetime += timedelta(days=1)
            
        return (end_datetime - start_datetime).total_seconds() / 3600
    
    def overlaps_with(self, other: 'TimeWindow') -> bool:
        """Check if this window overlaps with another"""
        if self.day_of_week != other.day_of_week:
            return False
            
        # Convert times to minutes for easier comparison
        self_start = self.start_time.hour * 60 + self.start_time.minute
        self_end = self.end_time.hour * 60 + self.end_time.minute
        other_start = other.start_time.hour * 60 + other.start_time.minute
        other_end = other.end_time.hour * 60 + other.end_time.minute
        
        # Handle overnight windows
        if self_end < self_start:
            self_end += 24 * 60
        if other_end < other_start:
            other_end += 24 * 60
            
        return not (self_end <= other_start or other_end <= self_start)
    
    def overlap_duration(self, other: 'TimeWindow') -> float:
        """Calculate overlap duration in hours"""
        if not self.overlaps_with(other):
            return 0.0
            
        # Convert to minutes
        self_start = self.start_time.hour * 60 + self.start_time.minute
        self_end = self.end_time.hour * 60 + self.end_time.minute
        other_start = other.start_time.hour * 60 + other.start_time.minute
        other_end = other.end_time.hour * 60 + other.end_time.minute
        
        # Handle overnight windows
        if self_end < self_start:
            self_end += 24 * 60
        if other_end < other_start:
            other_end += 24 * 60
            
        overlap_start = max(self_start, other_start)
        overlap_end = min(self_end, other_end)
        
        return max(0, overlap_end - overlap_start) / 60.0

@dataclass
class VolunteerAvailability:
    """Represents a volunteer's availability windows"""
    volunteer_id: str
    time_windows: List[TimeWindow]
    preferences: Dict[str, Any]
    max_hours_per_week: Optional[float] = None
    min_shift_duration: Optional[float] = None
    max_shift_duration: Optional[float] = None
    
    def get_total_available_hours(self) -> float:
        """Calculate total available hours per week"""
        return sum(window.duration_hours() for window in self.time_windows)
    
    def is_available_during(self, shift_window: TimeWindow) -> bool:
        """Check if volunteer is available during a shift window"""
        return any(window.overlaps_with(shift_window) for window in self.time_windows)

@dataclass
class ShiftRequirement:
    """Represents a shift that needs volunteers"""
    shift_id: str
    project_id: str
    time_window: TimeWindow
    required_volunteers: int
    preferred_skills: List[str]
    minimum_duration_overlap: float = 1.0  # Minimum overlap in hours
    priority: str = "normal"  # high, normal, low
    
class AvailabilityOverlapScorer:
    """Main class for calculating availability overlap scores"""
    
    def __init__(self):
        self.scoring_weights = {
            'overlap_duration': 0.4,      # How much time overlaps
            'coverage_percentage': 0.25,   # Percentage of shift covered
            'volunteer_utilization': 0.15, # How well it uses volunteer's time
            'preference_match': 0.1,       # Matches volunteer preferences
            'shift_priority': 0.1          # Priority of the shift
        }
    
    def calculate_overlap_score(self, 
                              volunteer_availability: VolunteerAvailability,
                              shift_requirement: ShiftRequirement) -> Dict[str, Any]:
        """
        Calculate comprehensive overlap score between volunteer availability and shift requirement
        
        Returns:
            Dict containing detailed scoring breakdown
        """
        shift_window = shift_requirement.time_window
        
        # Find best matching availability window
        best_window = None
        max_overlap = 0
        
        for window in volunteer_availability.time_windows:
            overlap_duration = window.overlap_duration(shift_window)
            if overlap_duration > max_overlap:
                max_overlap = overlap_duration
                best_window = window
        
        if best_window is None or max_overlap < shift_requirement.minimum_duration_overlap:
            return {
                'total_score': 0.0,
                'overlap_duration': 0.0,
                'coverage_percentage': 0.0,
                'volunteer_utilization': 0.0,
                'preference_match': 0.0,
                'shift_priority_bonus': 0.0,
                'detailed_breakdown': {},
                'recommendation': 'No suitable overlap found'
            }
        
        # Calculate individual scoring components
        overlap_score = self._calculate_overlap_duration_score(max_overlap, shift_window.duration_hours())
        coverage_score = self._calculate_coverage_percentage_score(max_overlap, shift_window.duration_hours())
        utilization_score = self._calculate_volunteer_utilization_score(max_overlap, best_window.duration_hours())
        preference_score = self._calculate_preference_match_score(volunteer_availability, shift_requirement)
        priority_bonus = self._calculate_shift_priority_bonus(shift_requirement.priority)
        
        # Calculate weighted total score
        total_score = (
            overlap_score * self.scoring_weights['overlap_duration'] +
            coverage_score * self.scoring_weights['coverage_percentage'] +
            utilization_score * self.scoring_weights['volunteer_utilization'] +
            preference_score * self.scoring_weights['preference_match'] +
            priority_bonus * self.scoring_weights['shift_priority']
        )
        
        return {
            'total_score': round(total_score, 3),
            'overlap_duration': max_overlap,
            'coverage_percentage': round(coverage_score * 100, 1),
            'volunteer_utilization': round(utilization_score * 100, 1),
            'preference_match': round(preference_score * 100, 1),
            'shift_priority_bonus': round(priority_bonus * 100, 1),
            'detailed_breakdown': {
                'overlap_duration_score': overlap_score,
                'coverage_percentage_score': coverage_score,
                'volunteer_utilization_score': utilization_score,
                'preference_match_score': preference_score,
                'shift_priority_bonus': priority_bonus,
                'weights_used': self.scoring_weights
            },
            'recommendation': self._generate_recommendation(total_score, max_overlap, shift_window.duration_hours())
        }
    
    def _calculate_overlap_duration_score(self, overlap_hours: float, shift_hours: float) -> float:
        """Score based on absolute overlap duration"""
        # Normalize based on typical shift lengths (1-8 hours)
        normalized_overlap = min(overlap_hours / 8.0, 1.0)
        return normalized_overlap
    
    def _calculate_coverage_percentage_score(self, overlap_hours: float, shift_hours: float) -> float:
        """Score based on what percentage of the shift is covered"""
        if shift_hours == 0:
            return 0.0
        coverage_ratio = min(overlap_hours / shift_hours, 1.0)
        return coverage_ratio
    
    def _calculate_volunteer_utilization_score(self, overlap_hours: float, volunteer_window_hours: float) -> float:
        """Score based on how efficiently volunteer's available time is used"""
        if volunteer_window_hours == 0:
            return 0.0
        utilization_ratio = overlap_hours / volunteer_window_hours
        # Optimal utilization is around 70-90%
        if utilization_ratio > 0.9:
            return 1.0
        elif utilization_ratio > 0.7:
            return 0.9
        elif utilization_ratio > 0.5:
            return 0.7
        else:
            return utilization_ratio * 1.4  # Scale up smaller utilizations
    
    def _calculate_preference_match_score(self, volunteer_availability: VolunteerAvailability, 
                                        shift_requirement: ShiftRequirement) -> float:
        """Score based on volunteer preferences matching shift characteristics"""
        score = 0.5  # Base score
        
        preferences = volunteer_availability.preferences
        
        # Time of day preferences
        shift_start_hour = shift_requirement.time_window.start_time.hour
        if preferences.get('prefers_morning', False) and 6 <= shift_start_hour < 12:
            score += 0.2
        if preferences.get('prefers_afternoon', False) and 12 <= shift_start_hour < 18:
            score += 0.2
        if preferences.get('prefers_evening', False) and 18 <= shift_start_hour < 22:
            score += 0.2
        
        # Day of week preferences
        day_preferences = preferences.get('preferred_days', [])
        if day_preferences and shift_requirement.time_window.day_of_week.name.lower() in [d.lower() for d in day_preferences]:
            score += 0.15
        
        # Skill matching
        volunteer_skills = preferences.get('skills', [])
        required_skills = shift_requirement.preferred_skills
        if volunteer_skills and required_skills:
            skill_matches = len(set(volunteer_skills) & set(required_skills))
            if skill_matches > 0:
                score += 0.15 * min(skill_matches / len(required_skills), 1.0)
        
        return min(score, 1.0)
    
    def _calculate_shift_priority_bonus(self, priority: str) -> float:
        """Calculate bonus score based on shift priority"""
        priority_multipliers = {
            'high': 1.0,
            'normal': 0.7,
            'low': 0.4
        }
        return priority_multipliers.get(priority.lower(), 0.7)
    
    def _generate_recommendation(self, total_score: float, overlap_hours: float, shift_hours: float) -> str:
        """Generate human-readable recommendation"""
        if total_score >= 0.8:
            return f"Excellent match - {overlap_hours:.1f}h overlap covers {(overlap_hours/shift_hours)*100:.1f}% of shift"
        elif total_score >= 0.6:
            return f"Good match - {overlap_hours:.1f}h overlap, consider for scheduling"
        elif total_score >= 0.4:
            return f"Partial match - {overlap_hours:.1f}h overlap, may work with flexibility"
        elif total_score >= 0.2:
            return f"Limited match - only {overlap_hours:.1f}h overlap available"
        else:
            return "Poor match - insufficient overlap for effective scheduling"
    
    def score_multiple_shifts(self, volunteer_availability: VolunteerAvailability,
                            shift_requirements: List[ShiftRequirement]) -> List[Dict[str, Any]]:
        """Score a volunteer against multiple shifts and return ranked results"""
        scored_shifts = []
        
        for shift in shift_requirements:
            score_result = self.calculate_overlap_score(volunteer_availability, shift)
            score_result['shift_id'] = shift.shift_id
            score_result['project_id'] = shift.project_id
            scored_shifts.append(score_result)
        
        # Sort by total score descending
        scored_shifts.sort(key=lambda x: x['total_score'], reverse=True)
        return scored_shifts
    
    def find_optimal_matches(self, volunteers: List[VolunteerAvailability],
                           shifts: List[ShiftRequirement],
                           max_matches_per_shift: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """Find optimal volunteer-shift matches across all volunteers and shifts"""
        shift_matches = {}
        
        for shift in shifts:
            volunteer_scores = []
            
            for volunteer in volunteers:
                score_result = self.calculate_overlap_score(volunteer, shift)
                if score_result['total_score'] > 0:
                    score_result['volunteer_id'] = volunteer.volunteer_id
                    volunteer_scores.append(score_result)
            
            # Sort and take top matches
            volunteer_scores.sort(key=lambda x: x['total_score'], reverse=True)
            shift_matches[shift.shift_id] = volunteer_scores[:max_matches_per_shift]
        
        return shift_matches
    
    def generate_availability_report(self, volunteer_availability: VolunteerAvailability) -> Dict[str, Any]:
        """Generate detailed availability report for a volunteer"""
        windows_by_day = {}
        total_hours = 0
        
        for window in volunteer_availability.time_windows:
            day_name = window.day_of_week.name
            if day_name not in windows_by_day:
                windows_by_day[day_name] = []
            
            windows_by_day[day_name].append({
                'start_time': window.start_time.strftime('%H:%M'),
                'end_time': window.end_time.strftime('%H:%M'),
                'duration_hours': round(window.duration_hours(), 2)
            })
            total_hours += window.duration_hours()
        
        return {
            'volunteer_id': volunteer_availability.volunteer_id,
            'total_available_hours_per_week': round(total_hours, 2),
            'availability_by_day': windows_by_day,
            'preferences': volunteer_availability.preferences,
            'constraints': {
                'max_hours_per_week': volunteer_availability.max_hours_per_week,
                'min_shift_duration': volunteer_availability.min_shift_duration,
                'max_shift_duration': volunteer_availability.max_shift_duration
            }
        }

# Utility functions for creating time windows from common formats
def create_time_window_from_string(day_str: str, time_range_str: str) -> TimeWindow:
    """
    Create TimeWindow from string format
    Example: create_time_window_from_string("monday", "09:00-17:00")
    """
    day_map = {
        'monday': DayOfWeek.MONDAY,
        'tuesday': DayOfWeek.TUESDAY,
        'wednesday': DayOfWeek.WEDNESDAY,
        'thursday': DayOfWeek.THURSDAY,
        'friday': DayOfWeek.FRIDAY,
        'saturday': DayOfWeek.SATURDAY,
        'sunday': DayOfWeek.SUNDAY
    }
    
    start_str, end_str = time_range_str.split('-')
    start_time = datetime.strptime(start_str.strip(), '%H:%M').time()
    end_time = datetime.strptime(end_str.strip(), '%H:%M').time()
    
    return TimeWindow(
        start_time=start_time,
        end_time=end_time,
        day_of_week=day_map[day_str.lower()]
    )

def create_availability_from_dict(volunteer_id: str, availability_dict: Dict[str, Any]) -> VolunteerAvailability:
    """
    Create VolunteerAvailability from dictionary format
    Example format:
    {
        'windows': [
            {'day': 'monday', 'start': '09:00', 'end': '17:00'},
            {'day': 'tuesday', 'start': '10:00', 'end': '16:00'}
        ],
        'preferences': {
            'prefers_morning': True,
            'skills': ['customer_service', 'admin']
        }
    }
    """
    time_windows = []
    
    for window_dict in availability_dict.get('windows', []):
        window = create_time_window_from_string(
            window_dict['day'], 
            f"{window_dict['start']}-{window_dict['end']}"
        )
        time_windows.append(window)
    
    return VolunteerAvailability(
        volunteer_id=volunteer_id,
        time_windows=time_windows,
        preferences=availability_dict.get('preferences', {}),
        max_hours_per_week=availability_dict.get('max_hours_per_week'),
        min_shift_duration=availability_dict.get('min_shift_duration'),
        max_shift_duration=availability_dict.get('max_shift_duration')
    )