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