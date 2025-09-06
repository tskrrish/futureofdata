export const SAMPLE_DATA = [
  { 
    branch: "Blue Ash", hours: 42.5, assignee: "Jane Smith", is_member: true, date: "2025-07-15",
    member_branch: "Blue Ash", project_tag: "Youth Development", project_catalog: "Youth Sports", 
    project: "Summer Basketball Camp", category: "Sports", department: "Youth Development"
  },
  { 
    branch: "Campbell County", hours: 18, assignee: "John Doe", is_member: false, date: "2025-07-22",
    member_branch: "", project_tag: "Community Services", project_catalog: "Food Service", 
    project: "Food Bank Volunteer", category: "Community", department: "Community Services"
  },
  { 
    branch: "Blue Ash", hours: 3.5, assignee: "Jane Smith", is_member: true, date: "2025-08-01",
    member_branch: "Blue Ash", project_tag: "Youth Development", project_catalog: "Childcare", 
    project: "After School Program", category: "Childcare", department: "Youth Development"
  },
  { 
    branch: "Clippard", hours: 12, assignee: "Alicia Keys", is_member: true, date: "2025-08-05",
    member_branch: "Clippard", project_tag: "Health & Wellness", project_catalog: "Senior Programs", 
    project: "Senior Fitness Class", category: "Senior", department: "Wellness"
  },
  { 
    branch: "Campbell County", hours: 6, assignee: "Taylor Ray", is_member: false, date: "2025-08-21",
    member_branch: "", project_tag: "YDE - Community Services", project_catalog: "Educational Support", 
    project: "Tutoring Program", category: "Education", department: "Youth Development"
  },
  { 
    branch: "Blue Ash", hours: 10, assignee: "Sam Patel", is_member: false, date: "2025-08-17",
    member_branch: "", project_tag: "Community Services", project_catalog: "Event Support", 
    project: "Community Health Fair", category: "Events", department: "Community Services"
  },
  { 
    branch: "Clippard", hours: 7, assignee: "Rita Ora", is_member: true, date: "2025-08-11",
    member_branch: "Clippard", project_tag: "YDE - Early Learning Centers", project_catalog: "Childcare Support", 
    project: "Preschool Assistant", category: "Childcare", department: "Early Learning"
  },
  { 
    branch: "Campbell County", hours: 2, assignee: "John Doe", is_member: false, date: "2025-08-28",
    member_branch: "", project_tag: "Competitive Swim", project_catalog: "Aquatics", 
    project: "Swim Meet Volunteer", category: "Sports", department: "Aquatics"
  },
  { 
    branch: "Music Resource Center", hours: 15, assignee: "Maria Garcia", is_member: true, date: "2025-08-10",
    member_branch: "Blue Ash", project_tag: "YDE - Community Services", project_catalog: "Music Programs", 
    project: "Music Therapy Sessions", category: "Arts", department: "Youth Development"
  },
  { 
    branch: "Clippard Senior Center", hours: 8, assignee: "Bob Wilson", is_member: true, date: "2025-08-15",
    member_branch: "Clippard", project_tag: "Senior Services", project_catalog: "Senior Activities", 
    project: "Senior Center Support", category: "Senior", department: "Senior Services"
  },
  { 
    branch: "Kentucky Senior Center", hours: 12, assignee: "Sarah Johnson", is_member: true, date: "2025-08-20",
    member_branch: "R.C. Durre YMCA", project_tag: "Senior Services", project_catalog: "Senior Activities", 
    project: "Senior Transportation", category: "Senior", department: "Senior Services"
  },
  { 
    branch: "R.C. Durre YMCA", hours: 25, assignee: "Mike Chen", is_member: true, date: "2025-08-12",
    member_branch: "R.C. Durre YMCA", project_tag: "YDE - Out of School Time", project_catalog: "After School", 
    project: "After School Programming", category: "Education", department: "Youth Development"
  }
];

export const CERTIFICATION_DATA = [
  {
    id: "cert-001",
    volunteer: "Jane Smith",
    branch: "Blue Ash",
    certification: "Youth Protection Training",
    type: "Safety",
    expiry_date: "2025-09-15",
    issue_date: "2023-09-15",
    criticality: "critical",
    status: "active",
    renewal_required: true
  },
  {
    id: "cert-002", 
    volunteer: "Jane Smith",
    branch: "Blue Ash",
    certification: "CPR/AED",
    type: "Safety",
    expiry_date: "2025-10-20",
    issue_date: "2023-10-20",
    criticality: "high",
    status: "active",
    renewal_required: true
  },
  {
    id: "cert-003",
    volunteer: "John Doe",
    branch: "Campbell County",
    certification: "Food Safety Certification",
    type: "Food Service",
    expiry_date: "2025-09-30",
    issue_date: "2022-09-30",
    criticality: "critical",
    status: "active",
    renewal_required: true
  },
  {
    id: "cert-004",
    volunteer: "Alicia Keys",
    branch: "Clippard",
    certification: "Senior Fitness Instructor",
    type: "Fitness",
    expiry_date: "2025-11-12",
    issue_date: "2024-11-12",
    criticality: "medium",
    status: "active",
    renewal_required: true
  },
  {
    id: "cert-005",
    volunteer: "Taylor Ray",
    branch: "Campbell County",
    certification: "Background Check",
    type: "Safety",
    expiry_date: "2025-09-08",
    issue_date: "2024-09-08",
    criticality: "critical",
    status: "active",
    renewal_required: true
  },
  {
    id: "cert-006",
    volunteer: "Sam Patel",
    branch: "Blue Ash",
    certification: "First Aid",
    type: "Safety",
    expiry_date: "2025-12-01",
    issue_date: "2024-12-01",
    criticality: "high",
    status: "active",
    renewal_required: true
  },
  {
    id: "cert-007",
    volunteer: "Rita Ora",
    branch: "Clippard",
    certification: "Child Development Associate",
    type: "Education",
    expiry_date: "2026-03-15",
    issue_date: "2021-03-15",
    criticality: "high",
    status: "active",
    renewal_required: false
  },
  {
    id: "cert-008",
    volunteer: "Maria Garcia",
    branch: "Music Resource Center",
    certification: "Music Therapy Certification",
    type: "Therapy",
    expiry_date: "2025-09-22",
    issue_date: "2023-09-22",
    criticality: "medium",
    status: "active",
    renewal_required: true
  },
  {
    id: "cert-009",
    volunteer: "Bob Wilson",
    branch: "Clippard Senior Center",
    certification: "Senior Care Training",
    type: "Care",
    expiry_date: "2025-10-05",
    issue_date: "2024-10-05",
    criticality: "high",
    status: "active",
    renewal_required: true
  },
  {
    id: "cert-010",
    volunteer: "Sarah Johnson",
    branch: "Kentucky Senior Center",
    certification: "Transportation Safety",
    type: "Safety",
    expiry_date: "2025-09-12",
    issue_date: "2024-09-12",
    criticality: "critical",
    status: "active",
    renewal_required: true
  },
  {
    id: "cert-011",
    volunteer: "Mike Chen",
    branch: "R.C. Durre YMCA",
    certification: "Youth Program Leader",
    type: "Leadership",
    expiry_date: "2025-11-30",
    issue_date: "2022-11-30",
    criticality: "medium",
    status: "active",
    renewal_required: true
  },
  {
    id: "cert-012",
    volunteer: "Jane Smith",
    branch: "Blue Ash",
    certification: "Aquatics Safety",
    type: "Safety",
    expiry_date: "2025-09-25",
    issue_date: "2024-09-25",
    criticality: "high",
    status: "active",
    renewal_required: true
  }
];