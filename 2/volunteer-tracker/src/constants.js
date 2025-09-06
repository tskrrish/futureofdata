// Shared constants for the volunteer tracking frontend
// Mirrors shared_constants.py to eliminate duplication

export const MILESTONES = [
  { threshold: 10, label: "First Impact" },
  { threshold: 25, label: "Service Star" },
  { threshold: 50, label: "Commitment Champion" },
  { threshold: 100, label: "Passion In Action Award" },
  { threshold: 500, label: "Guiding Light Award" },
]

export const MILESTONE_DETAILS = {
  "First Impact": { description: "Your journey begins", reward: "Digital Badge" },
  "Service Star": { description: "Making a difference", reward: "Digital Badge" },
  "Commitment Champion": { description: "Dedicated to service", reward: "Digital Badge" },
  "Passion In Action Award": { description: "100+ hours of impact", reward: "YMCA T-Shirt" },
  "Guiding Light Award": { description: "500+ hours of leadership", reward: "Engraved Glass Star" }
}

export const TIER_CONFIGS = {
  legendary: {
    name: "GUIDING LIGHT",
    minHours: 500,
    rating: 99,
    color: "#FF6B35",
    bgPattern: "icon",
    rarity: "legendary"
  },
  special: {
    name: "PASSION IN ACTION",
    minHours: 100,
    rating: 89,
    color: "#1B1B1B",
    bgPattern: "totw",
    rarity: "special"
  },
  rare: {
    name: "COMMITMENT CHAMPION",
    minHours: 50,
    rating: 84,
    color: "#FFD700",
    bgPattern: "gold",
    rarity: "rare"
  },
  uncommon: {
    name: "SERVICE STAR",
    minHours: 25,
    rating: 74,
    color: "#C0C0C0",
    bgPattern: "silver",
    rarity: "uncommon"
  },
  common: {
    name: "FIRST IMPACT",
    minHours: 10,
    rating: 64,
    color: "#CD7F32",
    bgPattern: "bronze",
    rarity: "common"
  },
  basic: {
    name: "VOLUNTEER",
    minHours: 0,
    rating: 45,
    color: "#8B4513",
    bgPattern: "basic",
    rarity: "basic"
  }
}

// Audio configuration for different tiers
export const AUDIO_CONFIG = {
  fanfare: {
    legendary: [523.25, 659.25, 783.99, 1046.50, 1318.51], // C5, E5, G5, C6, E6
    special: [440, 554.37, 659.25, 880, 1108.73], // A4, C#5, E5, A5, C#6
    rare: [392, 493.88, 587.33, 784], // G4, B4, D5, G5
    uncommon: [349.23, 440, 523.25, 698.46], // F4, A4, C5, F5
    common: [293.66, 369.99, 440, 587.33], // D4, F#4, A4, D5
    basic: [261.63, 329.63, 392, 523.25] // C4, E4, G4, C5
  },
  ambient: {
    legendary: [220, 330, 440, 660], // Rich harmonics
    special: [196, 294, 392], // Purple vibes
    rare: [174.61, 261.63], // Gold warmth
    uncommon: [146.83, 220], // Silver clarity
    common: [130.81, 196], // Bronze earthiness
    basic: [110, 165] // Basic foundation
  }
}

// Storyworld color mappings
export const STORYWORLD_COLORS = {
  "Youth Spark": "sw-yellow",
  "Healthy Together": "sw-red", 
  "Water & Wellness": "sw-blue",
  "Neighbor Power": "sw-green",
  "Sports": "sw-orange"
}

// Utility functions
export function getTierForHours(hours) {
  if (hours >= 500) return 'legendary'
  if (hours >= 100) return 'special'
  if (hours >= 50) return 'rare'
  if (hours >= 25) return 'uncommon'
  if (hours >= 10) return 'common'
  return 'basic'
}

export function getTierData(hours) {
  const tier = getTierForHours(hours)
  return TIER_CONFIGS[tier]
}

export function computeMilestones(totalHours) {
  return MILESTONES
    .filter(m => totalHours >= m.threshold)
    .map(m => m.label)
}

export function getStoryworldChipClass(storyworldName) {
  const name = (storyworldName || '').toLowerCase()
  if (name.includes('youth')) return STORYWORLD_COLORS["Youth Spark"]
  if (name.includes('healthy')) return STORYWORLD_COLORS["Healthy Together"]
  if (name.includes('water')) return STORYWORLD_COLORS["Water & Wellness"]
  if (name.includes('neighbor')) return STORYWORLD_COLORS["Neighbor Power"]
  if (name.includes('sports')) return STORYWORLD_COLORS["Sports"]
  return 'sw-neutral'
}

// Streak configurations  
export const STREAK_TYPES = {
  weekly: {
    name: "Weekly Streak",
    description: "Volunteer at least once per week",
    icon: "🔥",
    color: "#FF6B35"
  },
  monthly: {
    name: "Monthly Streak", 
    description: "Volunteer at least once per month",
    icon: "⭐",
    color: "#FFD700"
  }
}

// Streak milestone rewards
export const STREAK_MILESTONES = [
  { threshold: 2, label: "Streak Starter", description: "Started building consistency" },
  { threshold: 4, label: "Consistent Contributor", description: "One month of consistency" },
  { threshold: 8, label: "Streak Champion", description: "Two months strong" },
  { threshold: 12, label: "Dedicated Streaker", description: "Three months of commitment" },
  { threshold: 24, label: "Streak Master", description: "Six months of unwavering dedication" },
  { threshold: 52, label: "Legendary Streaker", description: "One year of consistent service" }
]

export function getStreakIcon(streakType) {
  return STREAK_TYPES[streakType]?.icon || "🔥"
}

export function getStreakColor(streakType) {
  return STREAK_TYPES[streakType]?.color || "#FF6B35"
}