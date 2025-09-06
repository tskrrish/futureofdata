export function createExportData(type, data, options = {}) {
  const timestamp = new Date().toISOString().slice(0, 10);
  const { branchFilter, search } = options;

  const exportMetadata = {
    exportType: type,
    exportDate: new Date().toISOString(),
    filters: {
      branch: branchFilter || 'All',
      search: search || 'None'
    },
    recordCount: data.length,
    generatedBy: 'YMCA Dashboard'
  };

  let exportData, filename;

  switch (type) {
    case 'hoursByBranch':
      exportData = data.map(item => ({
        Branch: item.branch,
        'Total Hours': item.hours,
        'Active Volunteers': item.activeCount || 0,
        'Average Hours per Volunteer': item.avgHours || 0
      }));
      filename = `Hours_by_Branch_${timestamp}`;
      break;

    case 'activesByBranch':
      exportData = data.map(item => ({
        Branch: item.branch,
        'Active Volunteers': item.count,
        'Percentage of Total': `${item.percentage}%`
      }));
      filename = `Active_Volunteers_by_Branch_${timestamp}`;
      break;

    case 'memberShare':
      exportData = data.map(item => ({
        Branch: item.branch,
        'Member Volunteers': item.members,
        'Non-Member Volunteers': item.nonMembers,
        'Member Percentage': `${item.memberPercentage}%`,
        'Total Volunteers': item.total
      }));
      filename = `Member_Share_by_Branch_${timestamp}`;
      break;

    case 'monthlyTrend':
      exportData = data.map(item => ({
        Month: item.month,
        'Total Hours': item.hours,
        'Active Volunteers': item.volunteers,
        'Average Hours per Volunteer': (item.hours / Math.max(item.volunteers, 1)).toFixed(1)
      }));
      filename = `Monthly_Trend_Analysis_${timestamp}`;
      break;

    case 'leaderboard':
      exportData = data.map((item, index) => ({
        Rank: index + 1,
        Name: item.name,
        Branch: item.branch,
        'Total Hours': item.hours,
        'Is Member': item.isMember ? 'Yes' : 'No',
        'Projects Completed': item.projectCount || 0
      }));
      filename = `Volunteer_Leaderboard_${timestamp}`;
      break;

    case 'rawData':
      exportData = data.map(item => ({
        Branch: item.branch,
        'Volunteer Name': item.assignee,
        Hours: item.hours,
        Date: item.date,
        'Is Member': item.is_member ? 'Yes' : 'No',
        'Member Branch': item.member_branch,
        Project: item.project,
        'Project Tag': item.project_tag,
        'Project Catalog': item.project_catalog,
        Category: item.category,
        Department: item.department
      }));
      filename = `Raw_Volunteer_Data_${timestamp}`;
      break;

    case 'branchAnalytics':
      const branchStats = calculateBranchAnalytics(data);
      exportData = branchStats.map(branch => ({
        Branch: branch.name,
        'Total Hours': branch.totalHours,
        'Active Volunteers': branch.activeVolunteers,
        'Member Volunteers': branch.memberVolunteers,
        'Member Percentage': `${branch.memberPercentage}%`,
        'Average Hours per Volunteer': branch.avgHoursPerVolunteer,
        'Top Project': branch.topProject,
        'Most Active Volunteer': branch.mostActiveVolunteer,
        'Unique Projects': branch.uniqueProjects
      }));
      filename = `Branch_Analytics_Report_${timestamp}`;
      break;

    case 'membershipAnalysis':
      const membershipStats = calculateMembershipAnalysis(data);
      exportData = [
        {
          Metric: 'Total Volunteers',
          Value: membershipStats.totalVolunteers
        },
        {
          Metric: 'Member Volunteers',
          Value: membershipStats.memberVolunteers
        },
        {
          Metric: 'Non-Member Volunteers',
          Value: membershipStats.nonMemberVolunteers
        },
        {
          Metric: 'Member Percentage',
          Value: `${membershipStats.memberPercentage}%`
        },
        {
          Metric: 'Member Hours Total',
          Value: membershipStats.memberHours
        },
        {
          Metric: 'Non-Member Hours Total',
          Value: membershipStats.nonMemberHours
        },
        {
          Metric: 'Average Hours per Member',
          Value: membershipStats.avgHoursPerMember
        },
        {
          Metric: 'Average Hours per Non-Member',
          Value: membershipStats.avgHoursPerNonMember
        }
      ];
      filename = `Membership_Analysis_${timestamp}`;
      break;

    default:
      exportData = data;
      filename = `Export_${timestamp}`;
  }

  return {
    data: exportData,
    filename,
    metadata: exportMetadata,
    category: getExportCategory(type)
  };
}

function calculateBranchAnalytics(data) {
  const branches = {};
  
  data.forEach(item => {
    if (!branches[item.branch]) {
      branches[item.branch] = {
        name: item.branch,
        totalHours: 0,
        volunteers: new Set(),
        memberVolunteers: new Set(),
        projects: new Set(),
        volunteerHours: {}
      };
    }
    
    const branch = branches[item.branch];
    branch.totalHours += item.hours;
    branch.volunteers.add(item.assignee);
    branch.projects.add(item.project);
    
    if (item.is_member) {
      branch.memberVolunteers.add(item.assignee);
    }
    
    if (!branch.volunteerHours[item.assignee]) {
      branch.volunteerHours[item.assignee] = 0;
    }
    branch.volunteerHours[item.assignee] += item.hours;
  });

  return Object.values(branches).map(branch => {
    const activeVolunteers = branch.volunteers.size;
    const memberVolunteers = branch.memberVolunteers.size;
    const memberPercentage = activeVolunteers > 0 ? ((memberVolunteers / activeVolunteers) * 100).toFixed(1) : 0;
    const avgHoursPerVolunteer = activeVolunteers > 0 ? (branch.totalHours / activeVolunteers).toFixed(1) : 0;
    
    const volunteerHoursArray = Object.entries(branch.volunteerHours);
    const mostActiveVolunteer = volunteerHoursArray.length > 0 
      ? volunteerHoursArray.reduce((max, current) => current[1] > max[1] ? current : max)[0]
      : 'N/A';

    const projectCounts = {};
    data.filter(item => item.branch === branch.name).forEach(item => {
      projectCounts[item.project] = (projectCounts[item.project] || 0) + item.hours;
    });
    const topProject = Object.keys(projectCounts).length > 0
      ? Object.entries(projectCounts).reduce((max, current) => current[1] > max[1] ? current : max)[0]
      : 'N/A';

    return {
      ...branch,
      activeVolunteers,
      memberVolunteers,
      memberPercentage,
      avgHoursPerVolunteer,
      mostActiveVolunteer,
      topProject,
      uniqueProjects: branch.projects.size
    };
  });
}

function calculateMembershipAnalysis(data) {
  const volunteers = new Set();
  const memberVolunteers = new Set();
  let memberHours = 0;
  let nonMemberHours = 0;

  data.forEach(item => {
    volunteers.add(item.assignee);
    if (item.is_member) {
      memberVolunteers.add(item.assignee);
      memberHours += item.hours;
    } else {
      nonMemberHours += item.hours;
    }
  });

  const totalVolunteers = volunteers.size;
  const memberCount = memberVolunteers.size;
  const nonMemberCount = totalVolunteers - memberCount;
  const memberPercentage = totalVolunteers > 0 ? ((memberCount / totalVolunteers) * 100).toFixed(1) : 0;
  const avgHoursPerMember = memberCount > 0 ? (memberHours / memberCount).toFixed(1) : 0;
  const avgHoursPerNonMember = nonMemberCount > 0 ? (nonMemberHours / nonMemberCount).toFixed(1) : 0;

  return {
    totalVolunteers,
    memberVolunteers: memberCount,
    nonMemberVolunteers: nonMemberCount,
    memberPercentage,
    memberHours,
    nonMemberHours,
    avgHoursPerMember,
    avgHoursPerNonMember
  };
}

function getExportCategory(type) {
  const categoryMap = {
    'hoursByBranch': 'Branch_Analytics',
    'activesByBranch': 'Branch_Analytics',
    'memberShare': 'Member_Reports',
    'monthlyTrend': 'Reports',
    'leaderboard': 'Volunteer_Data',
    'rawData': 'Volunteer_Data',
    'branchAnalytics': 'Branch_Analytics',
    'membershipAnalysis': 'Member_Reports'
  };
  
  return categoryMap[type] || 'Reports';
}

export const EXPORT_TYPES = {
  HOURS_BY_BRANCH: 'hoursByBranch',
  ACTIVES_BY_BRANCH: 'activesByBranch',
  MEMBER_SHARE: 'memberShare',
  MONTHLY_TREND: 'monthlyTrend',
  LEADERBOARD: 'leaderboard',
  RAW_DATA: 'rawData',
  BRANCH_ANALYTICS: 'branchAnalytics',
  MEMBERSHIP_ANALYSIS: 'membershipAnalysis'
};