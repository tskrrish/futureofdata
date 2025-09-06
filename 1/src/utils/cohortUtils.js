export function getCohortMonth(dateStr) {
  if (!dateStr) return null;
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return null;
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

export function calculateCohortRetention(volunteerData) {
  // Group volunteers by their first activity month (cohort)
  const volunteerFirstActivity = new Map();
  const volunteerActivities = new Map();

  // Process all volunteer data
  volunteerData.forEach(record => {
    const assignee = (record.assignee || "").trim();
    const month = getCohortMonth(record.date);
    
    if (!assignee || !month) return;

    // Track first activity month for each volunteer
    if (!volunteerFirstActivity.has(assignee)) {
      volunteerFirstActivity.set(assignee, month);
    } else {
      const currentFirst = volunteerFirstActivity.get(assignee);
      if (month < currentFirst) {
        volunteerFirstActivity.set(assignee, month);
      }
    }

    // Track all months volunteer was active
    if (!volunteerActivities.has(assignee)) {
      volunteerActivities.set(assignee, new Set());
    }
    volunteerActivities.get(assignee).add(month);
  });

  // Group volunteers by cohort
  const cohorts = new Map();
  volunteerFirstActivity.forEach((firstMonth, volunteer) => {
    if (!cohorts.has(firstMonth)) {
      cohorts.set(firstMonth, []);
    }
    cohorts.get(firstMonth).push(volunteer);
  });

  // Calculate retention for each cohort
  const retentionData = [];
  const sortedCohortMonths = Array.from(cohorts.keys()).sort();

  sortedCohortMonths.forEach(cohortMonth => {
    const cohortVolunteers = cohorts.get(cohortMonth);
    const cohortSize = cohortVolunteers.length;
    
    if (cohortSize === 0) return;

    const retentionRow = {
      cohortMonth,
      cohortSize,
      months: {}
    };

    // Calculate retention for each subsequent month
    const cohortDate = new Date(cohortMonth + '-01');
    for (let i = 0; i <= 12; i++) {
      const checkDate = new Date(cohortDate);
      checkDate.setMonth(cohortDate.getMonth() + i);
      const checkMonth = `${checkDate.getFullYear()}-${String(checkDate.getMonth() + 1).padStart(2, '0')}`;
      
      const activeInMonth = cohortVolunteers.filter(volunteer => 
        volunteerActivities.get(volunteer)?.has(checkMonth)
      ).length;
      
      const retentionPct = cohortSize > 0 ? (activeInMonth / cohortSize * 100) : 0;
      
      retentionRow.months[`month${i}`] = {
        active: activeInMonth,
        retentionPct: Math.round(retentionPct * 10) / 10
      };
    }

    retentionData.push(retentionRow);
  });

  return retentionData;
}

export function formatCohortData(retentionData) {
  if (!retentionData || retentionData.length === 0) return [];

  return retentionData.map(cohort => ({
    cohort: cohort.cohortMonth,
    cohortSize: cohort.cohortSize,
    month0: cohort.months.month0?.retentionPct || 0,
    month1: cohort.months.month1?.retentionPct || 0,
    month2: cohort.months.month2?.retentionPct || 0,
    month3: cohort.months.month3?.retentionPct || 0,
    month6: cohort.months.month6?.retentionPct || 0,
    month12: cohort.months.month12?.retentionPct || 0
  }));
}

export function getCohortInsights(retentionData) {
  if (!retentionData || retentionData.length === 0) return [];

  const insights = [];
  
  // Calculate average retention rates
  const avgRetention = {
    month1: 0,
    month3: 0,
    month6: 0,
    month12: 0
  };

  let validCohorts = 0;
  retentionData.forEach(cohort => {
    if (cohort.months.month1) {
      avgRetention.month1 += cohort.months.month1.retentionPct;
      validCohorts++;
    }
    if (cohort.months.month3) avgRetention.month3 += cohort.months.month3.retentionPct;
    if (cohort.months.month6) avgRetention.month6 += cohort.months.month6.retentionPct;
    if (cohort.months.month12) avgRetention.month12 += cohort.months.month12.retentionPct;
  });

  if (validCohorts > 0) {
    avgRetention.month1 = Math.round((avgRetention.month1 / validCohorts) * 10) / 10;
    avgRetention.month3 = Math.round((avgRetention.month3 / validCohorts) * 10) / 10;
    avgRetention.month6 = Math.round((avgRetention.month6 / validCohorts) * 10) / 10;
    avgRetention.month12 = Math.round((avgRetention.month12 / validCohorts) * 10) / 10;
  }

  // Generate insights
  if (avgRetention.month1 > 50) {
    insights.push({
      type: "success",
      title: "Strong 1-Month Retention",
      message: `${avgRetention.month1}% of volunteers return after their first month`
    });
  } else if (avgRetention.month1 > 0 && avgRetention.month1 < 30) {
    insights.push({
      type: "warning", 
      title: "Low 1-Month Retention",
      message: `Only ${avgRetention.month1}% of volunteers return after their first month. Consider onboarding improvements.`
    });
  }

  if (avgRetention.month6 > 25) {
    insights.push({
      type: "success",
      title: "Solid Long-term Engagement",
      message: `${avgRetention.month6}% of volunteers remain active after 6 months`
    });
  }

  // Find best performing cohort
  if (retentionData.length > 1) {
    const bestCohort = retentionData.reduce((best, current) => {
      const currentMonth3 = current.months.month3?.retentionPct || 0;
      const bestMonth3 = best.months.month3?.retentionPct || 0;
      return currentMonth3 > bestMonth3 ? current : best;
    });

    insights.push({
      type: "info",
      title: "Top Performing Cohort",
      message: `${bestCohort.cohortMonth} cohort shows ${bestCohort.months.month3?.retentionPct || 0}% retention at 3 months`
    });
  }

  return insights;
}