"""
Streak calculation service for volunteer tracking.
Handles weekly and monthly streak calculations with grace periods.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd

from shared_constants import STREAK_TYPES, compute_streak_milestones


class StreakData:
    """Data class for streak information."""
    def __init__(self, streak_type: str, current_streak: int, longest_streak: int, 
                 is_active: bool, last_activity_date: Optional[str], 
                 grace_period_remaining: int = 0):
        self.streak_type = streak_type
        self.current_streak = current_streak
        self.longest_streak = longest_streak
        self.is_active = is_active
        self.last_activity_date = last_activity_date
        self.grace_period_remaining = grace_period_remaining
        self.milestones = compute_streak_milestones(longest_streak)


def calculate_volunteer_streaks(volunteer_df: pd.DataFrame) -> Dict[str, StreakData]:
    """
    Calculate both weekly and monthly streaks for a volunteer.
    
    Args:
        volunteer_df: DataFrame containing volunteer's activities (filtered to fulfilled only)
        
    Returns:
        Dictionary with 'weekly' and 'monthly' StreakData objects
    """
    streaks = {}
    
    for streak_type, config in STREAK_TYPES.items():
        streak_data = calculate_single_streak(volunteer_df, streak_type, config)
        streaks[streak_type] = streak_data
    
    return streaks


def calculate_single_streak(df: pd.DataFrame, streak_type: str, config: Dict) -> StreakData:
    """
    Calculate streak for a single type (weekly or monthly).
    
    Args:
        df: Volunteer's activity DataFrame
        streak_type: 'weekly' or 'monthly'
        config: Streak configuration from STREAK_TYPES
        
    Returns:
        StreakData object with calculated streak information
    """
    if df.empty:
        return StreakData(streak_type, 0, 0, False, None)
    
    # Convert dates and sort
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date']).sort_values('Date')
    
    # Group by period (week or month)
    period_days = config['period_days']
    min_hours = config['min_hours_per_period']
    grace_days = config['grace_days']
    
    # Create periods from first activity date
    first_date = df['Date'].min()
    last_date = df['Date'].max()
    today = pd.Timestamp.now().normalize()
    
    # Generate all periods from first activity to today
    periods = []
    current_period_start = first_date
    
    while current_period_start <= today:
        period_end = current_period_start + timedelta(days=period_days - 1)
        periods.append((current_period_start, period_end))
        current_period_start = period_end + timedelta(days=1)
    
    # Check which periods have sufficient volunteer hours
    active_periods = []
    
    for period_start, period_end in periods:
        period_data = df[(df['Date'] >= period_start) & (df['Date'] <= period_end)]
        total_hours = period_data['Pledged'].sum() if not period_data.empty else 0
        
        if total_hours >= min_hours:
            active_periods.append((period_start, period_end, total_hours))
    
    if not active_periods:
        return StreakData(streak_type, 0, 0, False, last_date.strftime('%Y-%m-%d'))
    
    # Calculate streaks
    current_streak = 0
    longest_streak = 0
    temp_streak = 0
    
    # Track consecutive periods
    last_active_period_end = None
    
    for i, (period_start, period_end, hours) in enumerate(active_periods):
        if last_active_period_end is None:
            # First active period
            temp_streak = 1
        else:
            # Check if this period is consecutive to the last
            expected_start = last_active_period_end + timedelta(days=1)
            if period_start <= expected_start + timedelta(days=grace_days):
                # Within grace period, continue streak
                temp_streak += 1
            else:
                # Gap too large, reset streak
                longest_streak = max(longest_streak, temp_streak)
                temp_streak = 1
        
        last_active_period_end = period_end
    
    # Final longest streak update
    longest_streak = max(longest_streak, temp_streak)
    
    # Determine current streak status
    if active_periods:
        last_active_start, last_active_end, _ = active_periods[-1]
        days_since_last_period = (today - last_active_end).days
        
        # Check if current period should have activity
        current_period_start = last_active_end + timedelta(days=1)
        current_period_end = current_period_start + timedelta(days=period_days - 1)
        
        if today <= current_period_end + timedelta(days=grace_days):
            # Still within grace period for current streak
            current_streak = temp_streak
            is_active = True
            grace_remaining = max(0, grace_days - (today - current_period_end).days)
        else:
            # Grace period expired, streak is broken
            current_streak = 0
            is_active = False
            grace_remaining = 0
    else:
        current_streak = 0
        is_active = False
        grace_remaining = 0
    
    return StreakData(
        streak_type=streak_type,
        current_streak=current_streak,
        longest_streak=longest_streak,
        is_active=is_active,
        last_activity_date=last_date.strftime('%Y-%m-%d'),
        grace_period_remaining=grace_remaining
    )


def get_streak_summary(volunteer_df: pd.DataFrame) -> Dict:
    """
    Get a summary of streak information for a volunteer.
    
    Args:
        volunteer_df: DataFrame containing volunteer's activities
        
    Returns:
        Dictionary with streak summary information
    """
    streaks = calculate_volunteer_streaks(volunteer_df)
    
    summary = {
        'weekly': {
            'current_streak': streaks['weekly'].current_streak,
            'longest_streak': streaks['weekly'].longest_streak,
            'is_active': streaks['weekly'].is_active,
            'grace_days_remaining': streaks['weekly'].grace_period_remaining,
            'milestones': streaks['weekly'].milestones
        },
        'monthly': {
            'current_streak': streaks['monthly'].current_streak,
            'longest_streak': streaks['monthly'].longest_streak,
            'is_active': streaks['monthly'].is_active,
            'grace_days_remaining': streaks['monthly'].grace_period_remaining,
            'milestones': streaks['monthly'].milestones
        }
    }
    
    return summary