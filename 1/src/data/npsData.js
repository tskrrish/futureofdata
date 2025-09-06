// NPS Survey Data Structure and Sample Data
export const NPS_SURVEY_RESPONSES = [
  {
    id: "nps-001",
    volunteerId: "volunteer-001",
    volunteerName: "Jane Smith",
    branch: "Blue Ash",
    projectId: "project-001",
    projectName: "Summer Basketball Camp",
    eventDate: "2025-07-15",
    surveyDate: "2025-07-16",
    npsScore: 9,
    category: "Promoter",
    feedback: "Great experience! The coordination was excellent and I felt my contribution was valued.",
    recommendationText: "Would definitely volunteer again. The staff was very supportive.",
    improvementAreas: ["Better communication beforehand"],
    wouldVolunteerAgain: true,
    responseTime: 120, // seconds to complete survey
    isPostEvent: true
  },
  {
    id: "nps-002",
    volunteerId: "volunteer-002",
    volunteerName: "John Doe",
    branch: "Campbell County",
    projectId: "project-002",
    projectName: "Food Bank Volunteer",
    eventDate: "2025-07-22",
    surveyDate: "2025-07-23",
    npsScore: 7,
    category: "Passive",
    feedback: "Good experience overall, but could use better organization.",
    recommendationText: "It was okay, might volunteer again if schedule allows.",
    improvementAreas: ["Better organization", "Clearer instructions"],
    wouldVolunteerAgain: true,
    responseTime: 95,
    isPostEvent: true
  },
  {
    id: "nps-003",
    volunteerId: "volunteer-003",
    volunteerName: "Alicia Keys",
    branch: "Clippard",
    projectId: "project-003",
    projectName: "Senior Fitness Class",
    eventDate: "2025-08-05",
    surveyDate: "2025-08-06",
    npsScore: 10,
    category: "Promoter",
    feedback: "Amazing experience! The seniors were so grateful and it was very fulfilling.",
    recommendationText: "Absolutely recommend this to other volunteers. Very rewarding work.",
    improvementAreas: [],
    wouldVolunteerAgain: true,
    responseTime: 180,
    isPostEvent: true
  },
  {
    id: "nps-004",
    volunteerId: "volunteer-004",
    volunteerName: "Taylor Ray",
    branch: "Campbell County",
    projectId: "project-004",
    projectName: "Tutoring Program",
    eventDate: "2025-08-21",
    surveyDate: "2025-08-22",
    npsScore: 4,
    category: "Detractor",
    feedback: "Disappointing experience. Lack of materials and poor coordination.",
    recommendationText: "Would not recommend unless major improvements are made.",
    improvementAreas: ["Provide adequate materials", "Better staff coordination", "Clear expectations"],
    wouldVolunteerAgain: false,
    responseTime: 240,
    isPostEvent: true
  },
  {
    id: "nps-005",
    volunteerId: "volunteer-005",
    volunteerName: "Sam Patel",
    branch: "Blue Ash",
    projectId: "project-005",
    projectName: "Community Health Fair",
    eventDate: "2025-08-17",
    surveyDate: "2025-08-18",
    npsScore: 8,
    category: "Promoter",
    feedback: "Great community impact! Well organized event with clear roles.",
    recommendationText: "Would recommend to others interested in community health initiatives.",
    improvementAreas: ["More volunteer orientation"],
    wouldVolunteerAgain: true,
    responseTime: 150,
    isPostEvent: true
  }
];

// NPS Categories and scoring logic
export const NPS_CATEGORIES = {
  PROMOTER: { min: 9, max: 10, label: "Promoter", color: "#16a34a" },
  PASSIVE: { min: 7, max: 8, label: "Passive", color: "#eab308" },
  DETRACTOR: { min: 0, max: 6, label: "Detractor", color: "#dc2626" }
};

// Function to categorize NPS score
export function categorizeNPSScore(score) {
  if (score >= NPS_CATEGORIES.PROMOTER.min) return "Promoter";
  if (score >= NPS_CATEGORIES.PASSIVE.min) return "Passive";
  return "Detractor";
}

// Function to calculate NPS score from responses
export function calculateNPS(responses) {
  if (!responses || responses.length === 0) return 0;
  
  const promoters = responses.filter(r => r.npsScore >= 9).length;
  const detractors = responses.filter(r => r.npsScore <= 6).length;
  const total = responses.length;
  
  return Math.round(((promoters - detractors) / total) * 100);
}

// Survey prompts and questions
export const SURVEY_PROMPTS = {
  npsQuestion: "On a scale of 0-10, how likely are you to recommend volunteering at this YMCA to a friend or colleague?",
  feedbackPrompt: "What did you enjoy most about your volunteer experience?",
  improvementPrompt: "What could we improve to make your volunteer experience better?",
  recommendationPrompt: "Any additional thoughts or recommendations for future volunteers?",
  volunteerAgainPrompt: "Would you be interested in volunteering with us again?"
};

// User prompts for different scenarios
export const USER_PROMPTS = {
  postEvent: {
    title: "How was your volunteer experience?",
    subtitle: "Your feedback helps us improve volunteer experiences for everyone.",
    thankYou: "Thank you for your valuable time and feedback!"
  },
  followUp: {
    title: "Quick follow-up on your volunteer experience",
    subtitle: "We'd love to hear about your experience to help improve our programs.",
    thankYou: "Thank you for helping us serve our community better!"
  },
  reminder: {
    title: "We'd love your feedback!",
    subtitle: "Your volunteer experience feedback is important to us.",
    thankYou: "Thank you for taking the time to share your thoughts!"
  }
};