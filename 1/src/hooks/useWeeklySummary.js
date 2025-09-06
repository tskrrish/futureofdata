import { useMemo } from 'react';
import { getWeeksFromData, generateWeeklySummary, generateAutoWrittenRecap } from '../utils/weeklySummaryUtils';

export function useWeeklySummary(data) {
  const weeks = useMemo(() => {
    return getWeeksFromData(data);
  }, [data]);

  const weeklySummaries = useMemo(() => {
    return weeks.map(weekData => {
      const summary = generateWeeklySummary(weekData, data);
      const autoRecap = generateAutoWrittenRecap(summary);
      return { ...summary, autoRecap };
    });
  }, [weeks, data]);

  const currentWeekSummary = useMemo(() => {
    if (weeklySummaries.length === 0) return null;
    
    const today = new Date();
    const currentWeek = weeklySummaries.find(summary => {
      const startDate = new Date(summary.startDate);
      const endDate = new Date(summary.endDate);
      return today >= startDate && today <= endDate;
    });
    
    return currentWeek || weeklySummaries[0]; // Return most recent if current week not found
  }, [weeklySummaries]);

  const getWeekById = useMemo(() => {
    const weekMap = new Map();
    weeklySummaries.forEach(week => {
      weekMap.set(week.startDate, week);
    });
    return (weekId) => weekMap.get(weekId);
  }, [weeklySummaries]);

  const weekOptions = useMemo(() => {
    return weeklySummaries.map(week => ({
      value: week.startDate,
      label: week.weekLabel
    }));
  }, [weeklySummaries]);

  const stats = useMemo(() => {
    if (weeklySummaries.length === 0) return null;

    const totalWeeks = weeklySummaries.length;
    const totalHoursAllWeeks = weeklySummaries.reduce((sum, week) => sum + week.summary.totalHours, 0);
    const avgHoursPerWeek = totalWeeks > 0 ? (totalHoursAllWeeks / totalWeeks).toFixed(1) : 0;
    
    // Most active week
    const mostActiveWeek = weeklySummaries.reduce((max, week) => 
      week.summary.totalHours > max.summary.totalHours ? week : max
    );

    // Most consistent branch (appears in most weeks)
    const branchConsistency = new Map();
    weeklySummaries.forEach(week => {
      week.branchPerformance.forEach(branch => {
        if (branch.hours > 0) {
          branchConsistency.set(branch.branch, (branchConsistency.get(branch.branch) || 0) + 1);
        }
      });
    });

    const mostConsistentBranch = Array.from(branchConsistency.entries())
      .sort((a, b) => b[1] - a[1])[0];

    return {
      totalWeeks,
      totalHoursAllWeeks: Number(totalHoursAllWeeks.toFixed(1)),
      avgHoursPerWeek: Number(avgHoursPerWeek),
      mostActiveWeek: {
        week: mostActiveWeek.weekLabel,
        hours: mostActiveWeek.summary.totalHours
      },
      mostConsistentBranch: mostConsistentBranch ? {
        branch: mostConsistentBranch[0],
        appearances: mostConsistentBranch[1],
        percentage: ((mostConsistentBranch[1] / totalWeeks) * 100).toFixed(1)
      } : null
    };
  }, [weeklySummaries]);

  return {
    weeks: weeklySummaries,
    currentWeek: currentWeekSummary,
    getWeekById,
    weekOptions,
    stats,
    hasData: weeklySummaries.length > 0
  };
}