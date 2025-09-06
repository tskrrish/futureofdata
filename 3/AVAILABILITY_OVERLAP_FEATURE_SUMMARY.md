# Availability Overlap Scoring Feature

## Overview
This feature implements fine-grained window matching for volunteer shifts using sophisticated availability overlap scoring algorithms. It provides precise time-based matching between volunteer availability windows and shift requirements.

## Key Components

### 1. Core Classes (`availability_overlap_scorer.py`)

#### `TimeWindow`
- Represents specific time periods with start/end times and day of week
- Calculates duration and overlap with other windows
- Handles edge cases like overnight shifts

#### `VolunteerAvailability` 
- Contains volunteer's complete availability schedule
- Includes preferences, skills, and constraints
- Supports multiple time windows per volunteer

#### `ShiftRequirement`
- Defines shift needs with time windows and requirements  
- Includes preferred skills, priority levels, and minimum overlap requirements
- Flexible priority system (high/normal/low)

#### `AvailabilityOverlapScorer`
- Main scoring engine with multi-dimensional algorithm
- Weighted scoring across 5 components:
  - **Overlap Duration (40%)** - Total hours of overlap
  - **Coverage Percentage (25%)** - How much of shift is covered
  - **Volunteer Utilization (15%)** - Efficient use of volunteer time
  - **Preference Match (10%)** - Skills and preference alignment
  - **Shift Priority (10%)** - Priority boost for high-priority shifts

### 2. Enhanced Matching Engine Integration (`matching_engine.py`)

#### New Methods Added:
- `find_shift_matches_with_availability()` - Core shift matching with overlap scoring
- `create_enhanced_matches()` - Combines traditional ML matching with availability scoring
- `_create_volunteer_availability_from_preferences()` - Converts user preferences to availability objects
- `_create_shift_requirement_from_dict()` - Converts shift data to requirement objects

#### Backward Compatibility:
- Graceful fallback when ML libraries not available
- Maintains existing API while adding new functionality
- Supports both basic and detailed availability formats

### 3. Utility Functions

#### Time Window Creation:
```python
create_time_window_from_string("monday", "09:00-17:00")
```

#### Availability from Dictionary:
```python
create_availability_from_dict(volunteer_id, {
    'windows': [
        {'day': 'monday', 'start': '09:00', 'end': '17:00'},
        {'day': 'tuesday', 'start': '18:00', 'end': '21:00'}
    ],
    'preferences': {'skills': ['mentoring'], 'prefers_evening': True}
})
```

## Scoring Algorithm Details

### Multi-Dimensional Scoring:
1. **Overlap Duration Score**: Normalized by typical shift length (1-8 hours)
2. **Coverage Percentage**: Percentage of shift duration covered by volunteer availability
3. **Utilization Score**: How efficiently volunteer's time window is used
4. **Preference Match**: Time-of-day preferences, skill matching, day preferences
5. **Priority Bonus**: Multiplier based on shift priority level

### Score Interpretation:
- **0.8-1.0**: Excellent match - Highly recommended
- **0.6-0.8**: Good match - Suitable for scheduling  
- **0.4-0.6**: Partial match - May work with flexibility
- **0.2-0.4**: Limited match - Consider alternatives
- **0.0-0.2**: Poor match - Not recommended

## Usage Examples

### Basic Usage:
```python
from availability_overlap_scorer import AvailabilityOverlapScorer, TimeWindow, VolunteerAvailability, ShiftRequirement, DayOfWeek
from datetime import time

# Create scorer
scorer = AvailabilityOverlapScorer()

# Create volunteer availability
volunteer = VolunteerAvailability(
    volunteer_id="volunteer_001",
    time_windows=[
        TimeWindow(time(9, 0), time(17, 0), DayOfWeek.MONDAY)
    ],
    preferences={'skills': ['mentoring']}
)

# Create shift requirement  
shift = ShiftRequirement(
    shift_id="shift_001",
    project_id="project_001", 
    time_window=TimeWindow(time(10, 0), time(14, 0), DayOfWeek.MONDAY),
    required_volunteers=1,
    preferred_skills=['mentoring']
)

# Calculate overlap score
result = scorer.calculate_overlap_score(volunteer, shift)
print(f"Score: {result['total_score']}")
print(f"Overlap: {result['overlap_duration']} hours")
```

### Integration with Matching Engine:
```python
from matching_engine import VolunteerMatchingEngine

# Enhanced matching with availability overlap
enhanced_results = matching_engine.create_enhanced_matches(
    user_preferences={
        'volunteer_id': 'user_001',
        'availability': {'weekday': True, 'evening': True},
        'shifts': [shift_data, ...]
    },
    include_shifts=True
)

# Access different match types
traditional_matches = enhanced_results['traditional_matches']
shift_matches = enhanced_results['shift_matches'] 
combined_matches = enhanced_results['combined_score_matches']
availability_report = enhanced_results['availability_report']
```

## Real-World Scenarios Supported

### 1. Working Parents
- Limited evening/weekend availability
- Childcare constraints
- Preference-based matching

### 2. College Students  
- Class schedule gaps
- Afternoon/evening preference
- Skill-based tutoring matches

### 3. Retirees
- Full weekday flexibility
- Experience-based matching
- High-commitment opportunities

### 4. Professionals
- Lunch break volunteering
- Before/after work hours
- Weekend intensive programs

## Testing & Validation

### Test Coverage:
- **Unit Tests**: 12 comprehensive test cases covering all core functionality
- **Integration Tests**: Real-world scenario validation
- **Edge Cases**: Overnight shifts, zero duration, boundary conditions
- **Performance Tests**: Multi-shift scoring efficiency

### Test Files:
- `test_availability_overlap.py` - Complete unit test suite
- `test_integration_simple.py` - Integration testing without dependencies  
- `demo_availability_overlap.py` - Comprehensive feature demonstration

## Performance Characteristics

### Scoring Efficiency:
- O(n*m) complexity for n volunteers and m shifts
- Optimized for typical volunteer program scales (100s of volunteers, 10s of shifts)
- Memory efficient with minimal object overhead

### Scalability:
- Batch scoring for multiple volunteers/shifts
- Configurable scoring weights for different use cases
- Caching potential for repeated calculations

## Configuration Options

### Scoring Weights (Customizable):
```python
scorer.scoring_weights = {
    'overlap_duration': 0.4,      # Adjust importance of overlap hours
    'coverage_percentage': 0.25,   # Adjust importance of shift coverage
    'volunteer_utilization': 0.15, # Adjust importance of time efficiency
    'preference_match': 0.1,       # Adjust importance of preferences
    'shift_priority': 0.1          # Adjust importance of shift priority
}
```

### Volunteer Constraints:
- `max_hours_per_week`: Total weekly hour limit
- `min_shift_duration`: Minimum acceptable shift length
- `max_shift_duration`: Maximum acceptable shift length

## Future Enhancement Opportunities

### 1. Advanced Features:
- Multi-day shift scheduling
- Recurring shift pattern matching
- Travel time considerations
- Team scheduling optimization

### 2. Machine Learning Integration:
- Historical success prediction
- Dynamic weight optimization
- Volunteer retention modeling
- Seasonal pattern recognition

### 3. User Experience:
- Visual availability calendar
- Interactive scheduling interface
- Mobile-friendly time selection
- Automated scheduling suggestions

## Production Deployment

### Requirements:
- Python 3.7+
- No external dependencies for core functionality
- Optional: pandas/scikit-learn for advanced ML features

### Integration Points:
- Existing volunteer management systems
- Calendar applications (Google Calendar, Outlook)
- Mobile applications
- Web-based scheduling interfaces

### Monitoring & Analytics:
- Match success rates
- Volunteer satisfaction scores
- Scheduling efficiency metrics
- Usage pattern analysis

## Conclusion

The Availability Overlap Scoring Feature provides a robust, scalable solution for fine-grained volunteer shift matching. It combines sophisticated algorithms with practical usability, supporting diverse volunteer scenarios while maintaining high performance and reliability.

The feature is production-ready and can be easily integrated into existing volunteer management systems to significantly improve scheduling efficiency and volunteer satisfaction.