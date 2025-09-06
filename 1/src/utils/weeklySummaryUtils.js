// Weekly summary utilities for generating auto-written performance recaps

export function getWeekDateRange(date) {
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - day;
  
  const sunday = new Date(d.setDate(diff));
  const saturday = new Date(d.setDate(diff + 6));
  
  return {
    start: new Date(sunday),
    end: new Date(saturday),
    weekLabel: `${sunday.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${saturday.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
  };
}

export function getWeeksFromData(data) {
  const weeks = new Map();
  
  data.forEach(record => {
    const date = new Date(record.date);
    if (isNaN(date.getTime())) return;
    
    const { start, weekLabel } = getWeekDateRange(date);
    const weekKey = start.toISOString().split('T')[0];
    
    if (!weeks.has(weekKey)) {
      weeks.set(weekKey, {
        weekKey,
        weekLabel,
        startDate: start,
        endDate: getWeekDateRange(date).end,
        records: []
      });
    }
    
    weeks.get(weekKey).records.push(record);
  });
  
  return Array.from(weeks.values()).sort((a, b) => b.startDate - a.startDate);
}

export function generateWeeklySummary(weekData, allData) {
  const { records, weekLabel, startDate, endDate } = weekData;
  
  // Basic metrics
  const totalHours = records.reduce((sum, r) => sum + (Number(r.hours) || 0), 0);
  const uniqueVolunteers = new Set(records.map(r => `${r.assignee}||${r.branch}`)).size;
  const uniqueBranches = new Set(records.map(r => r.branch)).size;
  const uniqueProjects = new Set(records.map(r => `${r.project}||${r.branch}`)).size;
  
  // Branch performance
  const branchMetrics = new Map();
  records.forEach(r => {
    const branch = r.branch || 'Unknown';
    if (!branchMetrics.has(branch)) {
      branchMetrics.set(branch, {
        branch,
        hours: 0,
        volunteers: new Set(),
        projects: new Set(),
        members: new Set()
      });
    }
    
    const metrics = branchMetrics.get(branch);
    metrics.hours += Number(r.hours) || 0;
    metrics.volunteers.add(`${r.assignee}||${r.branch}`);
    metrics.projects.add(`${r.project}||${r.branch}`);
    if (r.is_member) {
      metrics.members.add(`${r.assignee}||${r.member_branch || r.branch}`);
    }
  });
  
  const branchPerformance = Array.from(branchMetrics.values()).map(m => ({
    branch: m.branch,
    hours: Number(m.hours.toFixed(1)),
    volunteers: m.volunteers.size,
    projects: m.projects.size,
    members: m.members.size,
    memberRate: m.volunteers.size > 0 ? ((m.members.size / m.volunteers.size) * 100).toFixed(1) : 0
  })).sort((a, b) => b.hours - a.hours);
  
  // Top performers
  const volunteerHours = new Map();
  records.forEach(r => {
    const volunteer = r.assignee || 'Unknown';
    volunteerHours.set(volunteer, (volunteerHours.get(volunteer) || 0) + (Number(r.hours) || 0));
  });
  
  const topVolunteers = Array.from(volunteerHours.entries())
    .map(([volunteer, hours]) => ({ volunteer, hours: Number(hours.toFixed(1)) }))
    .sort((a, b) => b.hours - a.hours)
    .slice(0, 5);
  
  // Project categories
  const projectCategories = new Map();
  records.forEach(r => {
    const category = r.project_tag || 'Unknown';
    if (!projectCategories.has(category)) {
      projectCategories.set(category, { hours: 0, volunteers: new Set() });
    }
    projectCategories.get(category).hours += Number(r.hours) || 0;
    projectCategories.get(category).volunteers.add(`${r.assignee}||${r.branch}`);
  });
  
  const categoryStats = Array.from(projectCategories.entries())
    .map(([category, stats]) => ({
      category,
      hours: Number(stats.hours.toFixed(1)),
      volunteers: stats.volunteers.size
    }))
    .sort((a, b) => b.hours - a.hours);
  
  // Generate callouts (key insights)
  const callouts = generateCallouts(branchPerformance, topVolunteers, categoryStats, totalHours, uniqueVolunteers);
  
  // Calculate previous week comparison if data exists
  const previousWeekData = getPreviousWeekComparison(startDate, allData);
  
  return {
    weekLabel,
    startDate: startDate.toISOString().split('T')[0],
    endDate: endDate.toISOString().split('T')[0],
    summary: {
      totalHours: Number(totalHours.toFixed(1)),
      volunteers: uniqueVolunteers,
      branches: uniqueBranches,
      projects: uniqueProjects,
      avgHoursPerVolunteer: uniqueVolunteers > 0 ? Number((totalHours / uniqueVolunteers).toFixed(1)) : 0
    },
    branchPerformance,
    topVolunteers,
    categoryStats,
    callouts,
    previousWeekComparison: previousWeekData,
    generatedAt: new Date().toISOString()
  };
}

function generateCallouts(branchPerformance, topVolunteers, categoryStats, totalHours, uniqueVolunteers) {
  const callouts = [];
  
  // Top performing branch
  if (branchPerformance.length > 0) {
    const topBranch = branchPerformance[0];
    if (topBranch.hours > 20) {
      callouts.push({
        type: 'success',
        title: '🏆 Top Branch Performance',
        message: `${topBranch.branch} led the week with ${topBranch.hours} volunteer hours across ${topBranch.volunteers} volunteers`
      });
    }
  }
  
  // High-impact volunteer
  if (topVolunteers.length > 0 && topVolunteers[0].hours > 15) {
    callouts.push({
      type: 'spotlight',
      title: '⭐ Volunteer Spotlight',
      message: `${topVolunteers[0].volunteer} contributed ${topVolunteers[0].hours} hours this week - outstanding dedication!`
    });
  }
  
  // Strong participation
  if (uniqueVolunteers > 15) {
    callouts.push({
      type: 'success',
      title: '👥 Strong Participation',
      message: `${uniqueVolunteers} volunteers participated this week, showing excellent community engagement`
    });
  }
  
  // Category highlight
  if (categoryStats.length > 0) {
    const topCategory = categoryStats[0];
    if (topCategory.hours > totalHours * 0.3) {
      callouts.push({
        type: 'info',
        title: '📊 Category Focus',
        message: `${topCategory.category} dominated the week with ${topCategory.hours} hours (${((topCategory.hours/totalHours)*100).toFixed(1)}% of total activity)`
      });
    }
  }
  
  // Multiple branches active
  const activeBranches = branchPerformance.filter(b => b.hours > 0).length;
  if (activeBranches >= 4) {
    callouts.push({
      type: 'success',
      title: '🌟 Network-wide Impact',
      message: `${activeBranches} branches were active this week, showing strong network-wide volunteer engagement`
    });
  }
  
  // Member engagement
  const totalMembers = branchPerformance.reduce((sum, b) => sum + Number(b.members), 0);
  const memberRate = uniqueVolunteers > 0 ? ((totalMembers / uniqueVolunteers) * 100).toFixed(1) : 0;
  if (memberRate > 60) {
    callouts.push({
      type: 'success',
      title: '💪 Strong Member Engagement',
      message: `${memberRate}% of volunteers were YMCA members, indicating strong member community involvement`
    });
  }
  
  return callouts.slice(0, 4); // Limit to top 4 callouts
}

function getPreviousWeekComparison(currentWeekStart, allData) {
  const previousWeekStart = new Date(currentWeekStart);
  previousWeekStart.setDate(previousWeekStart.getDate() - 7);
  
  const previousWeekEnd = new Date(currentWeekStart);
  previousWeekEnd.setDate(previousWeekEnd.getDate() - 1);
  
  const previousWeekRecords = allData.filter(record => {
    const recordDate = new Date(record.date);
    return recordDate >= previousWeekStart && recordDate <= previousWeekEnd;
  });
  
  if (previousWeekRecords.length === 0) return null;
  
  const prevHours = previousWeekRecords.reduce((sum, r) => sum + (Number(r.hours) || 0), 0);
  const prevVolunteers = new Set(previousWeekRecords.map(r => `${r.assignee}||${r.branch}`)).size;
  
  return {
    hours: Number(prevHours.toFixed(1)),
    volunteers: prevVolunteers,
    weekLabel: `${previousWeekStart.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${previousWeekEnd.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
  };
}

export function generateAutoWrittenRecap(weeklySummary) {
  const { summary, branchPerformance, topVolunteers, categoryStats, callouts, weekLabel, previousWeekComparison } = weeklySummary;
  
  let recap = `# Weekly Volunteer Impact Summary\n## ${weekLabel}\n\n`;
  
  // Executive Summary
  recap += `### 📈 Week at a Glance\n`;
  recap += `This week brought **${summary.totalHours} volunteer hours** from **${summary.volunteers} dedicated volunteers** across **${summary.branches} branches**. `;
  
  if (previousWeekComparison) {
    const hourChange = summary.totalHours - previousWeekComparison.hours;
    const volunteerChange = summary.volunteers - previousWeekComparison.volunteers;
    const hourChangeText = hourChange > 0 ? `up ${hourChange.toFixed(1)} hours` : `down ${Math.abs(hourChange).toFixed(1)} hours`;
    const volunteerChangeText = volunteerChange > 0 ? `${volunteerChange} more volunteers` : `${Math.abs(volunteerChange)} fewer volunteers`;
    
    recap += `Compared to last week, we're ${hourChangeText} with ${volunteerChangeText} participating.\n\n`;
  } else {
    recap += `With an average of ${summary.avgHoursPerVolunteer} hours per volunteer, our community showed strong commitment to service.\n\n`;
  }
  
  // Key Callouts
  if (callouts.length > 0) {
    recap += `### 🌟 This Week's Highlights\n`;
    callouts.forEach(callout => {
      recap += `**${callout.title}**: ${callout.message}\n\n`;
    });
  }
  
  // Branch Performance
  recap += `### 🏢 Branch Performance Breakdown\n`;
  branchPerformance.slice(0, 5).forEach((branch, index) => {
    const position = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`;
    recap += `${position} **${branch.branch}**: ${branch.hours} hours • ${branch.volunteers} volunteers • ${branch.projects} projects`;
    if (branch.members > 0) {
      recap += ` • ${branch.memberRate}% member rate`;
    }
    recap += '\n';
  });
  recap += '\n';
  
  // Top Contributors
  if (topVolunteers.length > 0) {
    recap += `### 👏 Top Contributors\n`;
    topVolunteers.forEach((volunteer, index) => {
      const medal = index === 0 ? '🏆' : index === 1 ? '🥈' : index === 2 ? '🥉' : '⭐';
      recap += `${medal} ${volunteer.volunteer} - ${volunteer.hours} hours\n`;
    });
    recap += '\n';
  }
  
  // Project Categories
  if (categoryStats.length > 0) {
    recap += `### 📊 Impact Areas\n`;
    categoryStats.slice(0, 3).forEach(category => {
      const percentage = ((category.hours / summary.totalHours) * 100).toFixed(1);
      recap += `• **${category.category}**: ${category.hours} hours (${percentage}%) • ${category.volunteers} volunteers\n`;
    });
    recap += '\n';
  }
  
  // Closing
  recap += `### 💙 Looking Forward\n`;
  recap += `Thank you to all ${summary.volunteers} volunteers who made this week impactful! `;
  recap += `Your collective ${summary.totalHours} hours of service strengthened our community and advanced the YMCA mission. `;
  recap += `Keep up the amazing work! 🙌\n\n`;
  recap += `*This summary was automatically generated on ${new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}.*`;
  
  return recap;
}