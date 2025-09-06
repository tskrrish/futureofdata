// Sample announcement data structure
export const SAMPLE_ANNOUNCEMENTS = [
  {
    id: "ann-001",
    title: "Welcome New Volunteers!",
    message: "We're excited to have new volunteers joining our YMCA community. Please take a moment to review the updated safety protocols and sign in procedures.",
    type: "info", // info, warning, success, urgent
    priority: "medium", // low, medium, high
    targetBranches: ["All"], // ["All"] or specific branch names
    targetRoles: ["All"], // ["All"] or ["member", "volunteer", "staff"]
    targetDepartments: ["All"], // ["All"] or specific departments
    createdAt: "2025-09-06T12:00:00Z",
    expiresAt: "2025-09-20T23:59:59Z",
    isActive: true,
    readReceipts: [], // Array of {userId, readAt, branch} objects
    createdBy: "admin",
    dismissible: true
  },
  {
    id: "ann-002", 
    title: "System Maintenance Scheduled",
    message: "Our volunteer tracking system will undergo maintenance on Sunday, September 15th from 2-4 AM. Please ensure all hours are logged before this time.",
    type: "warning",
    priority: "high",
    targetBranches: ["All"],
    targetRoles: ["All"],
    targetDepartments: ["All"],
    createdAt: "2025-09-05T10:00:00Z",
    expiresAt: "2025-09-15T06:00:00Z",
    isActive: true,
    readReceipts: [
      { userId: "user-001", readAt: "2025-09-06T14:30:00Z", branch: "Blue Ash" }
    ],
    createdBy: "admin",
    dismissible: false
  },
  {
    id: "ann-003",
    title: "Blue Ash Branch - New Equipment Available",
    message: "We've received new fitness equipment for our youth programs! Volunteers helping with youth sports can now utilize the updated facilities.",
    type: "success",
    priority: "low",
    targetBranches: ["Blue Ash"],
    targetRoles: ["volunteer"],
    targetDepartments: ["Youth Development", "Sports"],
    createdAt: "2025-09-04T09:00:00Z",
    expiresAt: "2025-09-18T23:59:59Z",
    isActive: true,
    readReceipts: [],
    createdBy: "branch-manager-blue-ash",
    dismissible: true
  },
  {
    id: "ann-004",
    title: "COVID-19 Protocol Update",
    message: "Updated health and safety protocols are now in effect. Please review the new guidelines before your next volunteer shift.",
    type: "urgent",
    priority: "high", 
    targetBranches: ["All"],
    targetRoles: ["All"],
    targetDepartments: ["All"],
    createdAt: "2025-09-03T08:00:00Z",
    expiresAt: "2025-09-30T23:59:59Z",
    isActive: true,
    readReceipts: [
      { userId: "user-001", readAt: "2025-09-06T11:00:00Z", branch: "Blue Ash" },
      { userId: "user-002", readAt: "2025-09-05T16:45:00Z", branch: "Clippard" }
    ],
    createdBy: "admin",
    dismissible: false
  }
];

