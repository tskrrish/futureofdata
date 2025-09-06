export function calculateNormalizedLeaderboards(data) {
  if (!data || data.length === 0) {
    return {
      overallLeaderboard: [],
      branchLeaderboards: [],
      roleLeaderboards: [],
      normalizedOverallLeaderboard: []
    };
  }

  // Calculate branch sizes (total volunteers per branch)
  const branchVolunteers = new Map();
  const branchHours = new Map();
  data.forEach(record => {
    const branch = (record.branch || 'Unknown').trim();
    const volunteer = `${(record.assignee || '').trim().toLowerCase()}||${branch}`;
    
    if (!branchVolunteers.has(branch)) {
      branchVolunteers.set(branch, new Set());
    }
    branchVolunteers.get(branch).add(volunteer);
    
    branchHours.set(branch, (branchHours.get(branch) || 0) + (Number(record.hours) || 0));
  });

  // Calculate role sizes (total volunteers per role/department)
  const roleVolunteers = new Map();
  const roleHours = new Map();
  data.forEach(record => {
    const role = (record.department || record.project_tag || 'Unknown').trim();
    const volunteer = `${(record.assignee || '').trim().toLowerCase()}||${role}`;
    
    if (!roleVolunteers.has(role)) {
      roleVolunteers.set(role, new Set());
    }
    roleVolunteers.get(role).add(volunteer);
    
    roleHours.set(role, (roleHours.get(role) || 0) + (Number(record.hours) || 0));
  });

  // Calculate individual volunteer stats
  const volunteerStats = new Map();
  data.forEach(record => {
    const volunteerId = (record.assignee || '').trim();
    const branch = (record.branch || 'Unknown').trim();
    const role = (record.department || record.project_tag || 'Unknown').trim();
    const hours = Number(record.hours) || 0;
    
    if (!volunteerId) return;

    const key = `${volunteerId}||${branch}`;
    if (!volunteerStats.has(key)) {
      volunteerStats.set(key, {
        name: volunteerId,
        branch: branch,
        role: role,
        totalHours: 0,
        recordCount: 0,
        isMember: record.is_member || false,
        memberBranch: record.member_branch || branch
      });
    }
    
    const stats = volunteerStats.get(key);
    stats.totalHours += hours;
    stats.recordCount += 1;
  });

  // Calculate normalized scores
  const normalizedVolunteers = Array.from(volunteerStats.values()).map(volunteer => {
    const branchSize = branchVolunteers.get(volunteer.branch)?.size || 1;
    const branchTotalHours = branchHours.get(volunteer.branch) || 1;
    const roleSize = roleVolunteers.get(volunteer.role)?.size || 1;
    const roleTotalHours = roleHours.get(volunteer.role) || 1;

    // Size-normalized scoring formula:
    // 1. Branch normalized score: individual hours / (branch total hours / branch size)
    // 2. Role normalized score: individual hours / (role total hours / role size)  
    // 3. Combined normalized score: weighted average of both
    
    const branchNormalizedScore = volunteer.totalHours / (branchTotalHours / branchSize);
    const roleNormalizedScore = volunteer.totalHours / (roleTotalHours / roleSize);
    
    // Weight: 60% branch normalization, 40% role normalization
    const combinedNormalizedScore = (branchNormalizedScore * 0.6) + (roleNormalizedScore * 0.4);
    
    return {
      ...volunteer,
      branchSize,
      roleSize,
      branchNormalizedScore: Number(branchNormalizedScore.toFixed(3)),
      roleNormalizedScore: Number(roleNormalizedScore.toFixed(3)),
      combinedNormalizedScore: Number(combinedNormalizedScore.toFixed(3)),
      efficiencyRating: volunteer.totalHours / volunteer.recordCount // hours per contribution
    };
  });

  // Generate different leaderboard views
  const overallLeaderboard = normalizedVolunteers
    .sort((a, b) => b.totalHours - a.totalHours)
    .slice(0, 20);

  const normalizedOverallLeaderboard = normalizedVolunteers
    .sort((a, b) => b.combinedNormalizedScore - a.combinedNormalizedScore)
    .slice(0, 20);

  // Branch-specific leaderboards
  const branches = Array.from(branchVolunteers.keys());
  const branchLeaderboards = branches.map(branch => ({
    branch,
    volunteers: normalizedVolunteers
      .filter(v => v.branch === branch)
      .sort((a, b) => b.branchNormalizedScore - a.branchNormalizedScore)
      .slice(0, 10),
    branchSize: branchVolunteers.get(branch)?.size || 0,
    totalHours: branchHours.get(branch) || 0
  }));

  // Role-specific leaderboards  
  const roles = Array.from(roleVolunteers.keys());
  const roleLeaderboards = roles.map(role => ({
    role,
    volunteers: normalizedVolunteers
      .filter(v => v.role === role)
      .sort((a, b) => b.roleNormalizedScore - a.roleNormalizedScore)
      .slice(0, 10),
    roleSize: roleVolunteers.get(role)?.size || 0,
    totalHours: roleHours.get(role) || 0
  }));

  return {
    overallLeaderboard,
    normalizedOverallLeaderboard,
    branchLeaderboards: branchLeaderboards.sort((a, b) => b.totalHours - a.totalHours),
    roleLeaderboards: roleLeaderboards.sort((a, b) => b.totalHours - a.totalHours),
    branchStats: Array.from(branchVolunteers.entries()).map(([branch, volunteers]) => ({
      branch,
      volunteerCount: volunteers.size,
      totalHours: branchHours.get(branch) || 0,
      avgHoursPerVolunteer: (branchHours.get(branch) || 0) / volunteers.size
    })),
    roleStats: Array.from(roleVolunteers.entries()).map(([role, volunteers]) => ({
      role,
      volunteerCount: volunteers.size,
      totalHours: roleHours.get(role) || 0,
      avgHoursPerVolunteer: (roleHours.get(role) || 0) / volunteers.size
    }))
  };
}

export function getLeaderboardInsights(leaderboardData) {
  const insights = [];
  const { overallLeaderboard, normalizedOverallLeaderboard, branchStats, roleStats } = leaderboardData;

  if (overallLeaderboard.length === 0) return insights;

  // Compare top performers in raw vs normalized rankings
  const topRawPerformer = overallLeaderboard[0];
  const topNormalizedPerformer = normalizedOverallLeaderboard[0];
  
  if (topRawPerformer.name !== topNormalizedPerformer.name) {
    insights.push({
      type: "info",
      title: "Fair Competition Impact",
      message: `Size normalization reveals ${topNormalizedPerformer.name} as the top performer when accounting for branch/role size, while ${topRawPerformer.name} leads in raw hours.`
    });
  }

  // Branch size disparities
  const sortedBranchStats = branchStats.sort((a, b) => b.volunteerCount - a.volunteerCount);
  if (sortedBranchStats.length >= 2) {
    const largest = sortedBranchStats[0];
    const smallest = sortedBranchStats[sortedBranchStats.length - 1];
    const sizeRatio = largest.volunteerCount / smallest.volunteerCount;
    
    if (sizeRatio > 3) {
      insights.push({
        type: "warning", 
        title: "Branch Size Imbalance",
        message: `${largest.branch} has ${sizeRatio.toFixed(1)}x more volunteers than ${smallest.branch}. Size normalization ensures fair competition across branches.`
      });
    }
  }

  // High efficiency performers
  const highEfficiencyVolunteers = normalizedOverallLeaderboard
    .filter(v => v.efficiencyRating > 15) // more than 15 hours per contribution
    .slice(0, 3);
    
  if (highEfficiencyVolunteers.length > 0) {
    insights.push({
      type: "success",
      title: "High-Impact Volunteers",
      message: `${highEfficiencyVolunteers.map(v => v.name).join(', ')} demonstrate exceptional commitment with ${highEfficiencyVolunteers[0].efficiencyRating.toFixed(1)}+ hours per volunteer session.`
    });
  }

  return insights;
}