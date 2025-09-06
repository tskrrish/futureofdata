export const SKILLS_CATEGORIES = {
  YOUTH_DEVELOPMENT: "Youth Development",
  COMMUNITY_SERVICES: "Community Services", 
  HEALTH_WELLNESS: "Health & Wellness",
  AQUATICS: "Aquatics",
  SENIOR_SERVICES: "Senior Services",
  ARTS_MUSIC: "Arts & Music",
  LEADERSHIP: "Leadership",
  TECHNOLOGY: "Technology"
};

export const SKILLS_DATA = [
  // Youth Development Skills
  { id: "child-safety", name: "Child Safety & Protection", category: SKILLS_CATEGORIES.YOUTH_DEVELOPMENT, level: "essential" },
  { id: "youth-mentoring", name: "Youth Mentoring", category: SKILLS_CATEGORIES.YOUTH_DEVELOPMENT, level: "intermediate" },
  { id: "sports-coaching", name: "Sports Coaching", category: SKILLS_CATEGORIES.YOUTH_DEVELOPMENT, level: "intermediate" },
  { id: "behavior-management", name: "Behavior Management", category: SKILLS_CATEGORIES.YOUTH_DEVELOPMENT, level: "intermediate" },
  { id: "early-learning", name: "Early Learning Principles", category: SKILLS_CATEGORIES.YOUTH_DEVELOPMENT, level: "advanced" },
  
  // Community Services Skills
  { id: "food-service", name: "Food Service & Safety", category: SKILLS_CATEGORIES.COMMUNITY_SERVICES, level: "essential" },
  { id: "event-coordination", name: "Event Coordination", category: SKILLS_CATEGORIES.COMMUNITY_SERVICES, level: "intermediate" },
  { id: "volunteer-coordination", name: "Volunteer Coordination", category: SKILLS_CATEGORIES.COMMUNITY_SERVICES, level: "advanced" },
  { id: "fundraising", name: "Fundraising & Development", category: SKILLS_CATEGORIES.COMMUNITY_SERVICES, level: "advanced" },
  
  // Health & Wellness Skills
  { id: "cpr-first-aid", name: "CPR & First Aid", category: SKILLS_CATEGORIES.HEALTH_WELLNESS, level: "essential" },
  { id: "fitness-instruction", name: "Fitness Instruction", category: SKILLS_CATEGORIES.HEALTH_WELLNESS, level: "intermediate" },
  { id: "nutrition-education", name: "Nutrition Education", category: SKILLS_CATEGORIES.HEALTH_WELLNESS, level: "intermediate" },
  { id: "mental-health-awareness", name: "Mental Health Awareness", category: SKILLS_CATEGORIES.HEALTH_WELLNESS, level: "advanced" },
  
  // Aquatics Skills
  { id: "water-safety", name: "Water Safety", category: SKILLS_CATEGORIES.AQUATICS, level: "essential" },
  { id: "swim-instruction", name: "Swim Instruction", category: SKILLS_CATEGORIES.AQUATICS, level: "intermediate" },
  { id: "lifeguarding", name: "Lifeguarding", category: SKILLS_CATEGORIES.AQUATICS, level: "intermediate" },
  { id: "aquatic-therapy", name: "Aquatic Therapy", category: SKILLS_CATEGORIES.AQUATICS, level: "advanced" },
  
  // Senior Services Skills
  { id: "senior-engagement", name: "Senior Engagement", category: SKILLS_CATEGORIES.SENIOR_SERVICES, level: "essential" },
  { id: "mobility-assistance", name: "Mobility Assistance", category: SKILLS_CATEGORIES.SENIOR_SERVICES, level: "intermediate" },
  { id: "dementia-care", name: "Dementia Care Basics", category: SKILLS_CATEGORIES.SENIOR_SERVICES, level: "advanced" },
  
  // Arts & Music Skills
  { id: "music-therapy", name: "Music Therapy", category: SKILLS_CATEGORIES.ARTS_MUSIC, level: "intermediate" },
  { id: "arts-crafts", name: "Arts & Crafts Instruction", category: SKILLS_CATEGORIES.ARTS_MUSIC, level: "essential" },
  { id: "performance-arts", name: "Performance Arts", category: SKILLS_CATEGORIES.ARTS_MUSIC, level: "advanced" },
  
  // Leadership Skills
  { id: "team-leadership", name: "Team Leadership", category: SKILLS_CATEGORIES.LEADERSHIP, level: "intermediate" },
  { id: "conflict-resolution", name: "Conflict Resolution", category: SKILLS_CATEGORIES.LEADERSHIP, level: "advanced" },
  { id: "public-speaking", name: "Public Speaking", category: SKILLS_CATEGORIES.LEADERSHIP, level: "intermediate" },
  
  // Technology Skills
  { id: "basic-computer", name: "Basic Computer Skills", category: SKILLS_CATEGORIES.TECHNOLOGY, level: "essential" },
  { id: "social-media", name: "Social Media Management", category: SKILLS_CATEGORIES.TECHNOLOGY, level: "intermediate" },
  { id: "database-management", name: "Database Management", category: SKILLS_CATEGORIES.TECHNOLOGY, level: "advanced" }
];

export const VOLUNTEER_SKILLS = [
  { volunteerId: "jane-smith", skillId: "child-safety", proficiency: "expert", lastUpdated: "2025-01-15", certified: true },
  { volunteerId: "jane-smith", skillId: "youth-mentoring", proficiency: "proficient", lastUpdated: "2024-12-10", certified: false },
  { volunteerId: "jane-smith", skillId: "sports-coaching", proficiency: "proficient", lastUpdated: "2024-11-20", certified: true },
  
  { volunteerId: "john-doe", skillId: "food-service", proficiency: "beginner", lastUpdated: "2024-10-05", certified: false },
  { volunteerId: "john-doe", skillId: "event-coordination", proficiency: "proficient", lastUpdated: "2025-01-01", certified: false },
  
  { volunteerId: "alicia-keys", skillId: "cpr-first-aid", proficiency: "expert", lastUpdated: "2025-01-20", certified: true },
  { volunteerId: "alicia-keys", skillId: "fitness-instruction", proficiency: "expert", lastUpdated: "2024-12-15", certified: true },
  { volunteerId: "alicia-keys", skillId: "senior-engagement", proficiency: "proficient", lastUpdated: "2024-11-10", certified: false },
  
  { volunteerId: "taylor-ray", skillId: "youth-mentoring", proficiency: "beginner", lastUpdated: "2024-09-15", certified: false },
  { volunteerId: "taylor-ray", skillId: "basic-computer", proficiency: "proficient", lastUpdated: "2025-01-10", certified: false },
  
  { volunteerId: "sam-patel", skillId: "event-coordination", proficiency: "expert", lastUpdated: "2025-01-25", certified: false },
  { volunteerId: "sam-patel", skillId: "fundraising", proficiency: "proficient", lastUpdated: "2024-12-20", certified: false },
  
  { volunteerId: "rita-ora", skillId: "child-safety", proficiency: "expert", lastUpdated: "2025-01-18", certified: true },
  { volunteerId: "rita-ora", skillId: "early-learning", proficiency: "expert", lastUpdated: "2024-12-05", certified: true },
  { volunteerId: "rita-ora", skillId: "behavior-management", proficiency: "proficient", lastUpdated: "2024-11-25", certified: false },
  
  { volunteerId: "maria-garcia", skillId: "music-therapy", proficiency: "expert", lastUpdated: "2025-01-12", certified: true },
  { volunteerId: "maria-garcia", skillId: "arts-crafts", proficiency: "proficient", lastUpdated: "2024-12-08", certified: false },
  { volunteerId: "maria-garcia", skillId: "youth-mentoring", proficiency: "proficient", lastUpdated: "2024-10-20", certified: false },
  
  { volunteerId: "bob-wilson", skillId: "senior-engagement", proficiency: "expert", lastUpdated: "2025-01-22", certified: false },
  { volunteerId: "bob-wilson", skillId: "mobility-assistance", proficiency: "proficient", lastUpdated: "2024-11-30", certified: true },
  
  { volunteerId: "sarah-johnson", skillId: "senior-engagement", proficiency: "expert", lastUpdated: "2025-01-08", certified: false },
  { volunteerId: "sarah-johnson", skillId: "dementia-care", proficiency: "proficient", lastUpdated: "2024-12-12", certified: true },
  
  { volunteerId: "mike-chen", skillId: "youth-mentoring", proficiency: "expert", lastUpdated: "2025-01-28", certified: false },
  { volunteerId: "mike-chen", skillId: "behavior-management", proficiency: "expert", lastUpdated: "2024-12-18", certified: true },
  { volunteerId: "mike-chen", skillId: "team-leadership", proficiency: "proficient", lastUpdated: "2024-11-15", certified: false }
];

export const TRAINING_PROGRAMS = [
  {
    id: "child-safety-cert",
    name: "Child Safety Certification",
    description: "Comprehensive child protection and safety training",
    skillsAddressed: ["child-safety", "behavior-management"],
    duration: "8 hours",
    format: "In-person",
    cost: 75,
    provider: "YMCA Training Institute",
    nextAvailable: "2025-02-15"
  },
  {
    id: "youth-development-basics",
    name: "Youth Development Fundamentals",
    description: "Core principles of positive youth development",
    skillsAddressed: ["youth-mentoring", "behavior-management"],
    duration: "4 hours",
    format: "Online",
    cost: 25,
    provider: "YMCA Training Institute", 
    nextAvailable: "2025-02-01"
  },
  {
    id: "cpr-first-aid-cert",
    name: "CPR/First Aid Certification",
    description: "American Red Cross CPR and First Aid certification",
    skillsAddressed: ["cpr-first-aid"],
    duration: "6 hours",
    format: "In-person",
    cost: 45,
    provider: "American Red Cross",
    nextAvailable: "2025-02-10"
  },
  {
    id: "swim-instructor-cert",
    name: "Swim Instructor Certification",
    description: "Learn to teach swimming to all ages",
    skillsAddressed: ["swim-instruction", "water-safety"],
    duration: "16 hours",
    format: "In-person",
    cost: 150,
    provider: "YMCA Aquatics",
    nextAvailable: "2025-02-20"
  },
  {
    id: "senior-care-basics",
    name: "Senior Care Fundamentals",
    description: "Understanding and supporting older adults",
    skillsAddressed: ["senior-engagement", "mobility-assistance"],
    duration: "6 hours",
    format: "Hybrid",
    cost: 35,
    provider: "YMCA Training Institute",
    nextAvailable: "2025-02-12"
  },
  {
    id: "music-therapy-intro",
    name: "Introduction to Music Therapy",
    description: "Using music for therapeutic purposes",
    skillsAddressed: ["music-therapy"],
    duration: "12 hours",
    format: "In-person",
    cost: 120,
    provider: "Cincinnati Music Therapy",
    nextAvailable: "2025-02-25"
  }
];