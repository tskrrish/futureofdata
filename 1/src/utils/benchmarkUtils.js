/**
 * Benchmark Performance Comparison Utilities
 * Compares current period to prior period and target values
 */

import { toMonth } from './dateUtils';

/**
 * Calculate benchmark comparison for metrics
 * @param {Array} data - Raw volunteer data
 * @param {string} currentPeriod - Current period (e.g., "Aug 2025")
 * @param {string} priorPeriod - Prior period to compare against
 * @param {Object} targets - Target values for metrics
 * @returns {Object} Benchmark comparison data
 */
export function calculateBenchmarkComparison(data, currentPeriod, priorPeriod, targets = {}) {
  const currentData = filterDataByPeriod(data, currentPeriod);
  const priorData = filterDataByPeriod(data, priorPeriod);
  
  const currentMetrics = calculatePeriodMetrics(currentData);
  const priorMetrics = calculatePeriodMetrics(priorData);
  
  return {
    current: currentMetrics,
    prior: priorMetrics,
    targets,
    comparisons: {
      totalHours: calculateComparison(currentMetrics.totalHours, priorMetrics.totalHours, targets.totalHours),
      activeVolunteers: calculateComparison(currentMetrics.activeVolunteers, priorMetrics.activeVolunteers, targets.activeVolunteers),
      memberVolunteers: calculateComparison(currentMetrics.memberVolunteers, priorMetrics.memberVolunteers, targets.memberVolunteers),
      avgHoursPerVolunteer: calculateComparison(currentMetrics.avgHoursPerVolunteer, priorMetrics.avgHoursPerVolunteer, targets.avgHoursPerVolunteer),
      memberEngagementRate: calculateComparison(currentMetrics.memberEngagementRate, priorMetrics.memberEngagementRate, targets.memberEngagementRate),
      totalProjects: calculateComparison(currentMetrics.totalProjects, priorMetrics.totalProjects, targets.totalProjects)
    }
  };
}

/**
 * Filter data by specific time period
 */
function filterDataByPeriod(data, period) {
  if (!period) return data;
  
  return data.filter(record => {
    const recordMonth = toMonth(record.date);
    return recordMonth === period;
  });
}

/**
 * Calculate key metrics for a specific period
 */
function calculatePeriodMetrics(data) {
  const totalHours = data.reduce((sum, record) => sum + (Number(record.hours) || 0), 0);
  
  // Count unique volunteers (deduplicated by assignee + branch)
  const volunteerSet = new Set();
  const memberSet = new Set();
  
  data.forEach(record => {
    const assignee = (record.assignee || '').trim().toLowerCase();
    const branch = (record.branch || '').trim().toLowerCase();
    
    if (assignee) {
      const volunteerKey = `${assignee}||${branch}`;
      volunteerSet.add(volunteerKey);
      
      if (record.is_member) {
        const memberBranch = (record.member_branch || record.branch || '').trim().toLowerCase();
        memberSet.add(`${assignee}||${memberBranch}`);
      }
    }
  });
  
  const activeVolunteers = volunteerSet.size;
  const memberVolunteers = memberSet.size;
  const avgHoursPerVolunteer = activeVolunteers > 0 ? totalHours / activeVolunteers : 0;
  const memberEngagementRate = activeVolunteers > 0 ? (memberVolunteers / activeVolunteers) * 100 : 0;
  
  // Count unique projects
  const projectSet = new Set();
  data.forEach(record => {
    const project = (record.project || '').trim();
    const branch = (record.branch || '').trim();
    if (project) {
      projectSet.add(`${project}||${branch}`);
    }
  });
  
  return {
    totalHours: Number(totalHours.toFixed(1)),
    activeVolunteers,
    memberVolunteers,
    avgHoursPerVolunteer: Number(avgHoursPerVolunteer.toFixed(1)),
    memberEngagementRate: Number(memberEngagementRate.toFixed(1)),
    totalProjects: projectSet.size
  };
}

/**
 * Calculate comparison between current, prior, and target values
 */
function calculateComparison(current, prior, target) {
  const priorChange = prior !== 0 ? ((current - prior) / prior) * 100 : 0;
  const targetGap = target ? current - target : null;
  const targetProgress = target ? (current / target) * 100 : null;
  
  return {
    current,
    prior,
    target,
    priorChange: Number(priorChange.toFixed(1)),
    targetGap: targetGap ? Number(targetGap.toFixed(1)) : null,
    targetProgress: targetProgress ? Number(targetProgress.toFixed(1)) : null,
    status: getPerformanceStatus(priorChange, targetProgress)
  };
}

/**
 * Determine performance status based on changes and target progress
 */
function getPerformanceStatus(priorChange, targetProgress) {
  if (targetProgress !== null) {
    if (targetProgress >= 100) return 'excellent';
    if (targetProgress >= 90) return 'good';
    if (targetProgress >= 75) return 'average';
    return 'below-target';
  }
  
  if (priorChange >= 10) return 'excellent';
  if (priorChange >= 0) return 'good';
  if (priorChange >= -10) return 'average';
  return 'poor';
}

/**
 * Get available periods from data for benchmark selection
 */
export function getAvailablePeriods(data) {
  const periods = new Set();
  data.forEach(record => {
    const period = toMonth(record.date);
    if (period !== 'Unknown') {
      periods.add(period);
    }
  });
  
  return Array.from(periods).sort((a, b) => new Date(a) - new Date(b));
}

/**
 * Get default target values based on historical performance
 */
export function calculateDefaultTargets(data) {
  const allPeriods = getAvailablePeriods(data);
  if (allPeriods.length < 2) return {};
  
  // Calculate average performance across all periods
  const periodMetrics = allPeriods.map(period => {
    const periodData = filterDataByPeriod(data, period);
    return calculatePeriodMetrics(periodData);
  });
  
  // Set targets as 10% above historical average
  const avgTotalHours = periodMetrics.reduce((sum, m) => sum + m.totalHours, 0) / periodMetrics.length;
  const avgActiveVolunteers = periodMetrics.reduce((sum, m) => sum + m.activeVolunteers, 0) / periodMetrics.length;
  const avgMemberVolunteers = periodMetrics.reduce((sum, m) => sum + m.memberVolunteers, 0) / periodMetrics.length;
  const avgHoursPerVolunteer = periodMetrics.reduce((sum, m) => sum + m.avgHoursPerVolunteer, 0) / periodMetrics.length;
  const avgMemberEngagementRate = periodMetrics.reduce((sum, m) => sum + m.memberEngagementRate, 0) / periodMetrics.length;
  const avgTotalProjects = periodMetrics.reduce((sum, m) => sum + m.totalProjects, 0) / periodMetrics.length;
  
  return {
    totalHours: Number((avgTotalHours * 1.1).toFixed(1)),
    activeVolunteers: Math.ceil(avgActiveVolunteers * 1.1),
    memberVolunteers: Math.ceil(avgMemberVolunteers * 1.1),
    avgHoursPerVolunteer: Number((avgHoursPerVolunteer * 1.05).toFixed(1)),
    memberEngagementRate: Number((avgMemberEngagementRate * 1.05).toFixed(1)),
    totalProjects: Math.ceil(avgTotalProjects * 1.1)
  };
}

/**
 * Generate benchmark insights based on comparison data
 */
export function generateBenchmarkInsights(benchmark) {
  const insights = [];
  const { comparisons } = benchmark;
  
  // Total Hours Insights
  if (comparisons.totalHours.status === 'excellent') {
    insights.push({
      type: 'success',
      metric: 'Total Hours',
      message: `Outstanding performance! Hours increased by ${comparisons.totalHours.priorChange}% vs prior period.`,
      priority: 'high'
    });
  } else if (comparisons.totalHours.status === 'poor') {
    insights.push({
      type: 'warning',
      metric: 'Total Hours',
      message: `Hours declined by ${Math.abs(comparisons.totalHours.priorChange)}% vs prior period. Focus on volunteer engagement.`,
      priority: 'high'
    });
  }
  
  // Active Volunteers Insights
  if (comparisons.activeVolunteers.status === 'excellent') {
    insights.push({
      type: 'success',
      metric: 'Active Volunteers',
      message: `Great volunteer recruitment! Active volunteers increased by ${comparisons.activeVolunteers.priorChange}%.`,
      priority: 'medium'
    });
  } else if (comparisons.activeVolunteers.status === 'poor') {
    insights.push({
      type: 'warning',
      metric: 'Active Volunteers',
      message: `Volunteer count decreased by ${Math.abs(comparisons.activeVolunteers.priorChange)}%. Consider recruitment campaigns.`,
      priority: 'high'
    });
  }
  
  // Member Engagement Insights
  if (comparisons.memberEngagementRate.targetProgress && comparisons.memberEngagementRate.targetProgress >= 100) {
    insights.push({
      type: 'success',
      metric: 'Member Engagement',
      message: `Member engagement target achieved at ${comparisons.memberEngagementRate.targetProgress}%!`,
      priority: 'medium'
    });
  } else if (comparisons.memberEngagementRate.status === 'below-target') {
    insights.push({
      type: 'info',
      metric: 'Member Engagement',
      message: `Member engagement at ${comparisons.memberEngagementRate.targetProgress}% of target. Focus on member volunteer programs.`,
      priority: 'medium'
    });
  }
  
  // Efficiency Insights
  if (comparisons.avgHoursPerVolunteer.priorChange > 0) {
    insights.push({
      type: 'success',
      metric: 'Volunteer Efficiency',
      message: `Average hours per volunteer improved by ${comparisons.avgHoursPerVolunteer.priorChange}%.`,
      priority: 'low'
    });
  }
  
  return insights.sort((a, b) => {
    const priorityOrder = { high: 3, medium: 2, low: 1 };
    return priorityOrder[b.priority] - priorityOrder[a.priority];
  });
}