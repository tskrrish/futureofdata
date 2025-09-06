export const EVENT_CAPACITY_DATA = [
  {
    id: "event-001",
    name: "Summer Basketball Camp",
    branch: "Blue Ash",
    date: "2025-09-15",
    startTime: "09:00",
    endTime: "16:00",
    estimatedAttendees: 50,
    requiredStaffRoles: [
      { role: "Youth Coach", required: 4, assigned: 3 },
      { role: "Safety Monitor", required: 2, assigned: 2 },
      { role: "Registration Assistant", required: 1, assigned: 1 }
    ],
    department: "Youth Development",
    category: "Sports",
    status: "understaffed",
    alertLevel: "high"
  },
  {
    id: "event-002",
    name: "Senior Fitness Class",
    branch: "Clippard",
    date: "2025-09-16",
    startTime: "10:00",
    endTime: "11:00",
    estimatedAttendees: 25,
    requiredStaffRoles: [
      { role: "Fitness Instructor", required: 1, assigned: 1 },
      { role: "Medical Assistant", required: 1, assigned: 1 }
    ],
    department: "Wellness",
    category: "Senior",
    status: "optimal",
    alertLevel: "none"
  },
  {
    id: "event-003",
    name: "Community Health Fair",
    branch: "Campbell County",
    date: "2025-09-20",
    startTime: "08:00",
    endTime: "17:00",
    estimatedAttendees: 200,
    requiredStaffRoles: [
      { role: "Event Coordinator", required: 2, assigned: 1 },
      { role: "Health Screener", required: 6, assigned: 4 },
      { role: "Registration Volunteer", required: 4, assigned: 3 },
      { role: "Setup/Breakdown", required: 8, assigned: 5 }
    ],
    department: "Community Services",
    category: "Events",
    status: "critically_understaffed",
    alertLevel: "critical"
  },
  {
    id: "event-004",
    name: "After School Program",
    branch: "Blue Ash",
    date: "2025-09-17",
    startTime: "15:30",
    endTime: "18:00",
    estimatedAttendees: 35,
    requiredStaffRoles: [
      { role: "Program Leader", required: 2, assigned: 2 },
      { role: "Homework Helper", required: 3, assigned: 4 },
      { role: "Activity Assistant", required: 2, assigned: 2 }
    ],
    department: "Youth Development",
    category: "Education",
    status: "overstaffed",
    alertLevel: "none"
  },
  {
    id: "event-005",
    name: "Swim Meet",
    branch: "R.C. Durre YMCA",
    date: "2025-09-21",
    startTime: "07:00",
    endTime: "15:00",
    estimatedAttendees: 150,
    requiredStaffRoles: [
      { role: "Meet Official", required: 4, assigned: 3 },
      { role: "Lifeguard", required: 6, assigned: 6 },
      { role: "Timer", required: 8, assigned: 6 },
      { role: "Scorer", required: 2, assigned: 1 }
    ],
    department: "Aquatics",
    category: "Sports",
    status: "understaffed",
    alertLevel: "medium"
  }
];

export const STAFF_AVAILABILITY = [
  {
    id: "staff-001",
    name: "Jane Smith",
    roles: ["Youth Coach", "Program Leader"],
    branch: "Blue Ash",
    availability: {
      "2025-09-15": { available: true, hours: "08:00-17:00" },
      "2025-09-16": { available: false },
      "2025-09-17": { available: true, hours: "15:00-19:00" }
    },
    maxHoursPerDay: 8,
    totalHoursThisWeek: 12
  },
  {
    id: "staff-002",
    name: "Mike Chen",
    roles: ["Youth Coach", "Activity Assistant"],
    branch: "R.C. Durre YMCA",
    availability: {
      "2025-09-15": { available: true, hours: "09:00-16:00" },
      "2025-09-21": { available: true, hours: "06:00-16:00" }
    },
    maxHoursPerDay: 8,
    totalHoursThisWeek: 20
  },
  {
    id: "staff-003",
    name: "Sarah Johnson",
    roles: ["Health Screener", "Registration Volunteer"],
    branch: "Kentucky Senior Center",
    availability: {
      "2025-09-20": { available: true, hours: "08:00-18:00" }
    },
    maxHoursPerDay: 10,
    totalHoursThisWeek: 15
  }
];

export const CAPACITY_THRESHOLDS = {
  understaffed: 0.85,
  optimal: 1.0,
  overstaffed: 1.15
};

export const ALERT_LEVELS = {
  none: { color: "green", priority: 0 },
  low: { color: "yellow", priority: 1 },
  medium: { color: "orange", priority: 2 },
  high: { color: "red", priority: 3 },
  critical: { color: "red", priority: 4 }
};