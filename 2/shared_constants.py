"""
Shared constants for the volunteer tracking system.
Centralizes milestone definitions, tier configurations, and other constants
to eliminate duplication between frontend and backend.
"""

from typing import Dict, List, Tuple, Any

# Milestone definitions (threshold, label)
MILESTONES: List[Tuple[int, str]] = [
    (10, "First Impact"),
    (25, "Service Star"),
    (50, "Commitment Champion"),
    (100, "Passion In Action Award"),
    (500, "Guiding Light Award"),
]

# Milestone details
MILESTONE_DETAILS: Dict[str, Dict[str, str]] = {
    "First Impact": {"description": "Your journey begins", "reward": "Digital Badge"},
    "Service Star": {"description": "Making a difference", "reward": "Digital Badge"},
    "Commitment Champion": {"description": "Dedicated to service", "reward": "Digital Badge"},
    "Passion In Action Award": {"description": "100+ hours of impact", "reward": "YMCA T-Shirt"},
    "Guiding Light Award": {"description": "500+ hours of leadership", "reward": "Engraved Glass Star"},
}

# Tier configurations for UI display
TIER_CONFIGS: Dict[str, Dict[str, Any]] = {
    "legendary": {
        "name": "GUIDING LIGHT",
        "min_hours": 500,
        "rating": 99,
        "color": "#FF6B35",
        "bg_pattern": "icon",
        "rarity": "legendary"
    },
    "special": {
        "name": "PASSION IN ACTION",
        "min_hours": 100,
        "rating": 89,
        "color": "#1B1B1B",
        "bg_pattern": "totw",
        "rarity": "special"
    },
    "rare": {
        "name": "COMMITMENT CHAMPION",
        "min_hours": 50,
        "rating": 84,
        "color": "#FFD700",
        "bg_pattern": "gold",
        "rarity": "rare"
    },
    "uncommon": {
        "name": "SERVICE STAR",
        "min_hours": 25,
        "rating": 74,
        "color": "#C0C0C0",
        "bg_pattern": "silver",
        "rarity": "uncommon"
    },
    "common": {
        "name": "FIRST IMPACT",
        "min_hours": 10,
        "rating": 64,
        "color": "#CD7F32",
        "bg_pattern": "bronze",
        "rarity": "common"
    },
    "basic": {
        "name": "VOLUNTEER",
        "min_hours": 0,
        "rating": 45,
        "color": "#8B4513",
        "bg_pattern": "basic",
        "rarity": "basic"
    }
}

# CSV column mappings
REQUIRED_CSV_COLUMNS = {
    "Date",
    "First Name",
    "Last Name",
    "Email",
    "Contact ID",
    "Pledged",
    "Fulfilled",
    "Project",
    "Project Tags",
    "Branch",
}

# Storyworld mapping keywords
STORYWORLD_KEYWORDS: Dict[str, List[str]] = {
    "Youth Spark": ["youth", "teen", "after-school", "after school", "camp", "child", "mentor", "education"],
    "Healthy Together": ["healthy", "wellness", "group ex", "fitness", "health"],
    "Water & Wellness": ["aquatics", "swim", "water", "lifeguard", "aerobics"],
    "Neighbor Power": ["community", "garden", "pantry", "outreach", "good neighbor", "bookshelf", "care team", "welcome desk", "branch support"],
    "Sports": ["sports", "basketball", "soccer", "coach", "referee", "flag football", "youth coaching"]
}

def get_tier_for_hours(hours: float) -> str:
    """Get the tier name for a given number of hours."""
    if hours >= 500:
        return "legendary"
    elif hours >= 100:
        return "special"
    elif hours >= 50:
        return "rare"
    elif hours >= 25:
        return "uncommon"
    elif hours >= 10:
        return "common"
    else:
        return "basic"

def compute_milestones(total_hours: float) -> List[str]:
    """Compute unlocked milestones for given hours."""
    unlocked = []
    for threshold, label in MILESTONES:
        if total_hours >= threshold:
            unlocked.append(label)
    return unlocked

# Streak configurations
STREAK_TYPES = {
    "weekly": {
        "name": "Weekly Streak",
        "description": "Volunteer at least once per week",
        "period_days": 7,
        "grace_days": 2,  # Can miss up to 2 days past the week
        "min_hours_per_period": 1.0,
    },
    "monthly": {
        "name": "Monthly Streak", 
        "description": "Volunteer at least once per month",
        "period_days": 30,
        "grace_days": 7,  # Can miss up to 7 days past the month
        "min_hours_per_period": 2.0,
    }
}

# Streak milestone rewards
STREAK_MILESTONES = [
    (2, "Streak Starter", "Started building consistency"),
    (4, "Consistent Contributor", "One month of consistency"),
    (8, "Streak Champion", "Two months strong"),
    (12, "Dedicated Streaker", "Three months of commitment"),
    (24, "Streak Master", "Six months of unwavering dedication"),
    (52, "Legendary Streaker", "One year of consistent service")
]

def compute_streak_milestones(streak_count: int) -> List[str]:
    """Compute unlocked streak milestones for given streak count."""
    unlocked = []
    for threshold, label, _ in STREAK_MILESTONES:
        if streak_count >= threshold:
            unlocked.append(label)
    return unlocked