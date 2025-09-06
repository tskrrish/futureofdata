/**
 * Badge System 2.0: Role-Specific Badges with Rarity Tiers
 * Extends the existing hour-based system with branch/role-specific achievements
 */

// Volunteer roles with progression paths
export const VOLUNTEER_ROLES = {
  GREETER: {
    name: "Greeter",
    level: 1,
    requirements: {
      hours: 10,
      training: ["Safety Training"],
      activities: ["Welcome Desk", "Front Desk", "Hospitality"]
    },
    unlocks: ["LEAD_VOLUNTEER"]
  },
  LEAD_VOLUNTEER: {
    name: "Lead Volunteer",
    level: 2,
    requirements: {
      hours: 25,
      previousRole: "GREETER",
      training: ["Leadership Basics"],
      activities: ["Team Lead", "Volunteer Coordination"]
    },
    unlocks: ["MENTOR", "SPECIALIST"]
  },
  MENTOR: {
    name: "Mentor",
    level: 3,
    requirements: {
      hours: 50,
      previousRole: "LEAD_VOLUNTEER",
      training: ["Mentorship Training"],
      activities: ["Youth Mentoring", "New Volunteer Training"]
    },
    unlocks: ["SENIOR_MENTOR"]
  },
  SPECIALIST: {
    name: "Specialist",
    level: 3,
    requirements: {
      hours: 50,
      previousRole: "LEAD_VOLUNTEER",
      training: ["Specialized Training"],
      specialization: true
    },
    unlocks: ["SENIOR_SPECIALIST"]
  },
  SENIOR_MENTOR: {
    name: "Senior Mentor",
    level: 4,
    requirements: {
      hours: 100,
      previousRole: "MENTOR",
      yearsActive: 2
    },
    unlocks: []
  },
  SENIOR_SPECIALIST: {
    name: "Senior Specialist",
    level: 4,
    requirements: {
      hours: 100,
      previousRole: "SPECIALIST",
      yearsActive: 2
    },
    unlocks: []
  }
};

// Branch/Storyworld specific badge categories
export const BRANCH_BADGE_CATEGORIES = {
  YOUTH_SPARK: {
    name: "Youth Spark Champion",
    storyworld: "Youth Spark",
    activities: ["youth", "teen", "after-school", "camp", "child", "mentor", "education"],
    badges: {
      ROOKIE_MENTOR: {
        name: "Rookie Mentor",
        rarity: "common",
        requirements: { hours: 10, category: "YOUTH_SPARK" },
        icon: "🌟",
        color: "#FFD700"
      },
      YOUTH_ADVOCATE: {
        name: "Youth Advocate",
        rarity: "uncommon",
        requirements: { hours: 25, category: "YOUTH_SPARK" },
        icon: "🎯",
        color: "#FF6B35"
      },
      EDUCATION_HERO: {
        name: "Education Hero",
        rarity: "rare",
        requirements: { hours: 50, category: "YOUTH_SPARK", projects: 5 },
        icon: "📚",
        color: "#9B59B6"
      },
      YOUTH_CHAMPION: {
        name: "Youth Champion",
        rarity: "epic",
        requirements: { hours: 100, category: "YOUTH_SPARK", yearsActive: 2 },
        icon: "🏆",
        color: "#E74C3C"
      },
      LEGENDARY_MENTOR: {
        name: "Legendary Mentor",
        rarity: "legendary",
        requirements: { hours: 250, category: "YOUTH_SPARK", yearsActive: 3, mentees: 10 },
        icon: "👑",
        color: "#F39C12"
      }
    }
  },
  HEALTHY_TOGETHER: {
    name: "Wellness Warrior",
    storyworld: "Healthy Together",
    activities: ["healthy", "wellness", "group ex", "fitness", "health"],
    badges: {
      FITNESS_FRIEND: {
        name: "Fitness Friend",
        rarity: "common",
        requirements: { hours: 10, category: "HEALTHY_TOGETHER" },
        icon: "💪",
        color: "#27AE60"
      },
      WELLNESS_GUIDE: {
        name: "Wellness Guide",
        rarity: "uncommon",
        requirements: { hours: 25, category: "HEALTHY_TOGETHER" },
        icon: "🏃",
        color: "#3498DB"
      },
      HEALTH_CHAMPION: {
        name: "Health Champion",
        rarity: "rare",
        requirements: { hours: 50, category: "HEALTHY_TOGETHER", programs: 3 },
        icon: "🏅",
        color: "#9B59B6"
      },
      FITNESS_MASTER: {
        name: "Fitness Master",
        rarity: "epic",
        requirements: { hours: 100, category: "HEALTHY_TOGETHER", certifications: 1 },
        icon: "🥇",
        color: "#E74C3C"
      },
      WELLNESS_LEGEND: {
        name: "Wellness Legend",
        rarity: "legendary",
        requirements: { hours: 250, category: "HEALTHY_TOGETHER", yearsActive: 3 },
        icon: "⭐",
        color: "#F39C12"
      }
    }
  },
  WATER_WELLNESS: {
    name: "Aquatic Guardian",
    storyworld: "Water & Wellness",
    activities: ["aquatics", "swim", "water", "lifeguard", "aerobics"],
    badges: {
      POOL_HELPER: {
        name: "Pool Helper",
        rarity: "common",
        requirements: { hours: 10, category: "WATER_WELLNESS" },
        icon: "🏊",
        color: "#3498DB"
      },
      SWIM_SUPPORTER: {
        name: "Swim Supporter",
        rarity: "uncommon",
        requirements: { hours: 25, category: "WATER_WELLNESS" },
        icon: "🌊",
        color: "#2ECC71"
      },
      AQUATIC_ACE: {
        name: "Aquatic Ace",
        rarity: "rare",
        requirements: { hours: 50, category: "WATER_WELLNESS", safety: true },
        icon: "🏆",
        color: "#9B59B6"
      },
      LIFEGUARD_LEADER: {
        name: "Lifeguard Leader",
        rarity: "epic",
        requirements: { hours: 100, category: "WATER_WELLNESS", certification: "Lifeguard" },
        icon: "🚨",
        color: "#E74C3C"
      },
      AQUATIC_LEGEND: {
        name: "Aquatic Legend",
        rarity: "legendary",
        requirements: { hours: 250, category: "WATER_WELLNESS", yearsActive: 3, saves: 1 },
        icon: "🌟",
        color: "#F39C12"
      }
    }
  },
  NEIGHBOR_POWER: {
    name: "Community Builder",
    storyworld: "Neighbor Power",
    activities: ["community", "garden", "pantry", "outreach", "good neighbor", "bookshelf", "care team", "welcome desk", "branch support"],
    badges: {
      NEIGHBOR_FRIEND: {
        name: "Neighbor Friend",
        rarity: "common",
        requirements: { hours: 10, category: "NEIGHBOR_POWER" },
        icon: "🤝",
        color: "#27AE60"
      },
      COMMUNITY_HELPER: {
        name: "Community Helper",
        rarity: "uncommon",
        requirements: { hours: 25, category: "NEIGHBOR_POWER" },
        icon: "🏘️",
        color: "#3498DB"
      },
      OUTREACH_CHAMPION: {
        name: "Outreach Champion",
        rarity: "rare",
        requirements: { hours: 50, category: "NEIGHBOR_POWER", events: 5 },
        icon: "🌍",
        color: "#9B59B6"
      },
      COMMUNITY_LEADER: {
        name: "Community Leader",
        rarity: "epic",
        requirements: { hours: 100, category: "NEIGHBOR_POWER", initiatives: 2 },
        icon: "👨‍👩‍👧‍👦",
        color: "#E74C3C"
      },
      NEIGHBORHOOD_LEGEND: {
        name: "Neighborhood Legend",
        rarity: "legendary",
        requirements: { hours: 250, category: "NEIGHBOR_POWER", yearsActive: 3, impact: "high" },
        icon: "🏛️",
        color: "#F39C12"
      }
    }
  },
  SPORTS: {
    name: "Athletic Ambassador",
    storyworld: "Sports",
    activities: ["sports", "basketball", "soccer", "coach", "referee", "flag football", "youth coaching"],
    badges: {
      SPORTS_STARTER: {
        name: "Sports Starter",
        rarity: "common",
        requirements: { hours: 10, category: "SPORTS" },
        icon: "⚽",
        color: "#E67E22"
      },
      TEAM_PLAYER: {
        name: "Team Player",
        rarity: "uncommon",
        requirements: { hours: 25, category: "SPORTS" },
        icon: "🏀",
        color: "#3498DB"
      },
      COACHING_ACE: {
        name: "Coaching Ace",
        rarity: "rare",
        requirements: { hours: 50, category: "SPORTS", teams: 2 },
        icon: "🏅",
        color: "#9B59B6"
      },
      SPORTS_LEADER: {
        name: "Sports Leader",
        rarity: "epic",
        requirements: { hours: 100, category: "SPORTS", coaching_cert: true },
        icon: "🥇",
        color: "#E74C3C"
      },
      ATHLETIC_LEGEND: {
        name: "Athletic Legend",
        rarity: "legendary",
        requirements: { hours: 250, category: "SPORTS", yearsActive: 3, championships: 1 },
        icon: "👑",
        color: "#F39C12"
      }
    }
  }
};

// Special achievement badges (cross-category)
export const SPECIAL_BADGES = {
  MULTI_TALENT: {
    name: "Multi-Talent Master",
    rarity: "epic",
    requirements: { categories: 3, hours: 75 },
    icon: "🌈",
    color: "#8E44AD",
    description: "Active in 3+ different storyworlds"
  },
  CONSISTENCY_CHAMPION: {
    name: "Consistency Champion",
    rarity: "rare",
    requirements: { consecutiveMonths: 6 },
    icon: "📅",
    color: "#16A085",
    description: "Volunteered consistently for 6+ months"
  },
  EARLY_BIRD: {
    name: "Early Bird",
    rarity: "uncommon",
    requirements: { earlyShifts: 10 },
    icon: "🌅",
    color: "#F39C12",
    description: "Completed 10+ early morning shifts"
  },
  NIGHT_OWL: {
    name: "Night Owl",
    rarity: "uncommon",
    requirements: { lateShifts: 10 },
    icon: "🦉",
    color: "#8E44AD",
    description: "Completed 10+ evening shifts"
  },
  WEEKEND_WARRIOR: {
    name: "Weekend Warrior",
    rarity: "uncommon",
    requirements: { weekendHours: 25 },
    icon: "🏋️",
    color: "#E67E22",
    description: "25+ hours on weekends"
  },
  HOLIDAY_HERO: {
    name: "Holiday Hero",
    rarity: "rare",
    requirements: { holidayShifts: 5 },
    icon: "🎄",
    color: "#C0392B",
    description: "Volunteered during 5+ holidays"
  },
  MILESTONE_MASTER: {
    name: "Milestone Master",
    rarity: "legendary",
    requirements: { allMilestones: true },
    icon: "💎",
    color: "#2C3E50",
    description: "Achieved all major milestones"
  }
};

// Rarity system with enhanced properties
export const RARITY_TIERS = {
  common: {
    name: "Common",
    color: "#95A5A6",
    glow: false,
    animation: "none",
    probability: 0.4,
    points: 1
  },
  uncommon: {
    name: "Uncommon",
    color: "#27AE60",
    glow: true,
    animation: "subtle",
    probability: 0.3,
    points: 2
  },
  rare: {
    name: "Rare",
    color: "#3498DB",
    glow: true,
    animation: "moderate",
    probability: 0.2,
    points: 5
  },
  epic: {
    name: "Epic",
    color: "#9B59B6",
    glow: true,
    animation: "strong",
    probability: 0.08,
    points: 10
  },
  legendary: {
    name: "Legendary",
    color: "#F39C12",
    glow: true,
    animation: "intense",
    probability: 0.02,
    points: 25
  }
};

// Badge calculation utilities
export function calculateVolunteerBadges(volunteerData) {
  const badges = [];
  const { hours_total, storyworlds = [], projects = [], yearsActive, assignments_count } = volunteerData;
  
  // Check role-based progression
  const currentRole = determineVolunteerRole(volunteerData);
  if (currentRole) {
    badges.push({
      type: 'role',
      badge: currentRole,
      earnedAt: new Date()
    });
  }
  
  // Check storyworld-specific badges
  storyworlds.forEach(storyworld => {
    const category = getStoryworldCategory(storyworld);
    if (category) {
      const storyworldBadges = checkStoryworldBadges(volunteerData, category);
      badges.push(...storyworldBadges);
    }
  });
  
  // Check special achievement badges
  const specialBadges = checkSpecialBadges(volunteerData);
  badges.push(...specialBadges);
  
  return badges;
}

export function determineVolunteerRole(volunteerData) {
  const { hours_total, training = [], yearsActive } = volunteerData;
  
  if (hours_total >= 100 && yearsActive >= 2) {
    return VOLUNTEER_ROLES.SENIOR_MENTOR;
  } else if (hours_total >= 50) {
    return VOLUNTEER_ROLES.MENTOR;
  } else if (hours_total >= 25) {
    return VOLUNTEER_ROLES.LEAD_VOLUNTEER;
  } else if (hours_total >= 10) {
    return VOLUNTEER_ROLES.GREETER;
  }
  
  return null;
}

export function getStoryworldCategory(storyworld) {
  const name = storyworld.toLowerCase();
  
  if (name.includes('youth')) return 'YOUTH_SPARK';
  if (name.includes('healthy') || name.includes('fitness')) return 'HEALTHY_TOGETHER';
  if (name.includes('water') || name.includes('aquatic')) return 'WATER_WELLNESS';
  if (name.includes('neighbor') || name.includes('community')) return 'NEIGHBOR_POWER';
  if (name.includes('sports')) return 'SPORTS';
  
  return null;
}

export function checkStoryworldBadges(volunteerData, category) {
  const badges = [];
  const categoryData = BRANCH_BADGE_CATEGORIES[category];
  
  if (!categoryData) return badges;
  
  const categoryHours = getCategoryHours(volunteerData, category);
  
  Object.entries(categoryData.badges).forEach(([key, badgeData]) => {
    if (meetsRequirements(volunteerData, badgeData.requirements, categoryHours)) {
      badges.push({
        type: 'storyworld',
        badge: badgeData,
        category,
        earnedAt: new Date()
      });
    }
  });
  
  return badges;
}

export function checkSpecialBadges(volunteerData) {
  const badges = [];
  
  Object.entries(SPECIAL_BADGES).forEach(([key, badgeData]) => {
    if (meetsSpecialRequirements(volunteerData, badgeData.requirements)) {
      badges.push({
        type: 'special',
        badge: badgeData,
        earnedAt: new Date()
      });
    }
  });
  
  return badges;
}

function getCategoryHours(volunteerData, category) {
  // This would need to be implemented based on actual data structure
  // For now, return approximate based on storyworld involvement
  const categoryKeywords = BRANCH_BADGE_CATEGORIES[category].activities;
  const { projects = [], storyworlds = [], hours_total } = volunteerData;
  
  let relevantProjects = 0;
  projects.forEach(project => {
    const projectLower = project.toLowerCase();
    if (categoryKeywords.some(keyword => projectLower.includes(keyword))) {
      relevantProjects++;
    }
  });
  
  // Estimate category hours based on involvement
  return relevantProjects > 0 ? Math.min(hours_total, hours_total * (relevantProjects / projects.length)) : 0;
}

function meetsRequirements(volunteerData, requirements, categoryHours = 0) {
  const { hours_total, yearsActive = 1 } = volunteerData;
  
  if (requirements.hours && categoryHours < requirements.hours) return false;
  if (requirements.yearsActive && yearsActive < requirements.yearsActive) return false;
  if (requirements.projects && (volunteerData.projects || []).length < requirements.projects) return false;
  
  return true;
}

function meetsSpecialRequirements(volunteerData, requirements) {
  const { storyworlds = [], hours_total } = volunteerData;
  
  if (requirements.categories && storyworlds.length < requirements.categories) return false;
  if (requirements.hours && hours_total < requirements.hours) return false;
  if (requirements.consecutiveMonths) {
    // This would need actual date analysis - simplified for demo
    return volunteerData.yearsActive >= 1;
  }
  
  return true;
}

// Badge display utilities
export function getBadgeDisplayData(badge) {
  const rarity = RARITY_TIERS[badge.rarity] || RARITY_TIERS.common;
  
  return {
    ...badge,
    rarityData: rarity,
    displayColor: badge.color || rarity.color,
    shouldGlow: rarity.glow,
    animation: rarity.animation,
    points: rarity.points
  };
}

export function calculateBadgeScore(badges) {
  return badges.reduce((total, badge) => {
    const rarity = RARITY_TIERS[badge.rarity] || RARITY_TIERS.common;
    return total + rarity.points;
  }, 0);
}