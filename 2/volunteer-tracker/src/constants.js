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

// Quest System Constants
export const QUEST_TYPES = {
  HOURS_MILESTONE: 'hours_milestone',
  TIME_BOUNDED: 'time_bounded',
  STREAK: 'streak',
  STORYWORLD_FOCUS: 'storyworld_focus',
  COMMUNITY_CHALLENGE: 'community_challenge'
}

export const QUEST_STATUS = {
  ACTIVE: 'active',
  COMPLETED: 'completed',
  EXPIRED: 'expired',
  LOCKED: 'locked'
}

export const QUEST_DIFFICULTY = {
  EASY: 'easy',
  MEDIUM: 'medium',
  HARD: 'hard',
  EPIC: 'epic'
}

export const QUEST_REWARDS = {
  POINTS: 'points',
  BADGE: 'badge',
  TITLE: 'title',
  PHYSICAL: 'physical'
}

// Predefined Quests Configuration
export const QUESTS_CONFIG = [
  {
    id: 'first_steps',
    title: 'First Steps',
    description: 'Complete your first 5 volunteer hours',
    type: QUEST_TYPES.HOURS_MILESTONE,
    difficulty: QUEST_DIFFICULTY.EASY,
    target: 5,
    timeLimit: null,
    rewards: [
      { type: QUEST_REWARDS.POINTS, value: 100 },
      { type: QUEST_REWARDS.BADGE, value: 'First Steps Champion' }
    ],
    icon: '👶',
    unlockCondition: { minHours: 0 }
  },
  {
    id: 'weekend_warrior',
    title: 'Weekend Warrior',
    description: 'Volunteer 10 hours over a weekend (Sat-Sun)',
    type: QUEST_TYPES.TIME_BOUNDED,
    difficulty: QUEST_DIFFICULTY.MEDIUM,
    target: 10,
    timeLimit: 172800000, // 48 hours in ms
    rewards: [
      { type: QUEST_REWARDS.POINTS, value: 300 },
      { type: QUEST_REWARDS.TITLE, value: 'Weekend Warrior' }
    ],
    icon: '⚔️',
    unlockCondition: { minHours: 20 }
  },
  {
    id: 'consistency_king',
    title: 'Consistency King',
    description: 'Volunteer at least 2 hours for 7 consecutive days',
    type: QUEST_TYPES.STREAK,
    difficulty: QUEST_DIFFICULTY.HARD,
    target: 7,
    timeLimit: 604800000, // 7 days in ms
    rewards: [
      { type: QUEST_REWARDS.POINTS, value: 500 },
      { type: QUEST_REWARDS.BADGE, value: 'Consistency Master' },
      { type: QUEST_REWARDS.TITLE, value: 'The Reliable' }
    ],
    icon: '👑',
    unlockCondition: { minHours: 50 }
  },
  {
    id: 'youth_champion',
    title: 'Youth Champion',
    description: 'Complete 25 hours in Youth Spark programs',
    type: QUEST_TYPES.STORYWORLD_FOCUS,
    difficulty: QUEST_DIFFICULTY.MEDIUM,
    target: 25,
    storyworld: 'Youth Spark',
    timeLimit: 2592000000, // 30 days in ms
    rewards: [
      { type: QUEST_REWARDS.POINTS, value: 400 },
      { type: QUEST_REWARDS.BADGE, value: 'Youth Advocate' }
    ],
    icon: '🌟',
    unlockCondition: { minHours: 15 }
  },
  {
    id: 'century_club',
    title: 'Century Club',
    description: 'Reach 100 total volunteer hours',
    type: QUEST_TYPES.HOURS_MILESTONE,
    difficulty: QUEST_DIFFICULTY.EPIC,
    target: 100,
    timeLimit: null,
    rewards: [
      { type: QUEST_REWARDS.POINTS, value: 1000 },
      { type: QUEST_REWARDS.PHYSICAL, value: 'YMCA T-Shirt' },
      { type: QUEST_REWARDS.TITLE, value: 'Century Champion' }
    ],
    icon: '🏆',
    unlockCondition: { minHours: 75 }
  },
  {
    id: 'community_builder',
    title: 'Community Builder',
    description: 'Help recruit 3 new volunteers this month',
    type: QUEST_TYPES.COMMUNITY_CHALLENGE,
    difficulty: QUEST_DIFFICULTY.HARD,
    target: 3,
    timeLimit: 2592000000, // 30 days in ms
    rewards: [
      { type: QUEST_REWARDS.POINTS, value: 750 },
      { type: QUEST_REWARDS.BADGE, value: 'Community Builder' },
      { type: QUEST_REWARDS.TITLE, value: 'The Recruiter' }
    ],
    icon: '🏘️',
    unlockCondition: { minHours: 40 }
  }
]

// Quest utility functions
export function getAvailableQuests(userHours, completedQuestIds = []) {
  return QUESTS_CONFIG.filter(quest => {
    if (completedQuestIds.includes(quest.id)) return false
    return userHours >= quest.unlockCondition.minHours
  })
}

export function calculateQuestProgress(quest, userProgress) {
  const progress = userProgress[quest.type] || 0
  return Math.min(progress, quest.target)
}

export function isQuestExpired(quest, startTime) {
  if (!quest.timeLimit || !startTime) return false
  return Date.now() - startTime > quest.timeLimit
}

export function getQuestStatusColor(status) {
  switch (status) {
    case QUEST_STATUS.ACTIVE: return '#3B82F6'
    case QUEST_STATUS.COMPLETED: return '#10B981'
    case QUEST_STATUS.EXPIRED: return '#EF4444'
    case QUEST_STATUS.LOCKED: return '#6B7280'
    default: return '#6B7280'
  }
}

export function getDifficultyColor(difficulty) {
  switch (difficulty) {
    case QUEST_DIFFICULTY.EASY: return '#10B981'
    case QUEST_DIFFICULTY.MEDIUM: return '#F59E0B'
    case QUEST_DIFFICULTY.HARD: return '#EF4444'
    case QUEST_DIFFICULTY.EPIC: return '#8B5CF6'
    default: return '#6B7280'
  }
}