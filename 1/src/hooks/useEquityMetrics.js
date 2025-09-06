import { useMemo } from "react";

export function useEquityMetrics(raw, branchFilter, search) {
  // Filter data based on current filters
  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return raw.filter(r => {
      const matchesBranch = branchFilter === "All" || (r.branch || "").toLowerCase() === branchFilter.toLowerCase();
      const matchesSearch = !q || [r.assignee, r.branch, r.project_tag, r.project_catalog, String(r.hours), r.date]
        .some(v => (v || "").toString().toLowerCase().includes(q));
      return matchesBranch && matchesSearch;
    });
  }, [raw, branchFilter, search]);

  // Participation Parity Metrics
  const participationParity = useMemo(() => {
    // Member vs Non-Member participation
    const memberMap = new Map();
    const nonMemberMap = new Map();
    
    filtered.forEach(r => {
      const branch = (r.branch || "Unknown").trim();
      const assignee = (r.assignee || "").trim().toLowerCase();
      const hours = Number(r.hours) || 0;
      
      if (!assignee) return;
      
      if (r.is_member) {
        if (!memberMap.has(branch)) memberMap.set(branch, { volunteers: new Set(), hours: 0 });
        memberMap.get(branch).volunteers.add(assignee);
        memberMap.get(branch).hours += hours;
      } else {
        if (!nonMemberMap.has(branch)) nonMemberMap.set(branch, { volunteers: new Set(), hours: 0 });
        nonMemberMap.get(branch).volunteers.add(assignee);
        nonMemberMap.get(branch).hours += hours;
      }
    });

    // Calculate parity metrics by branch
    const branches = new Set([...memberMap.keys(), ...nonMemberMap.keys()]);
    const branchParity = Array.from(branches).map(branch => {
      const memberData = memberMap.get(branch) || { volunteers: new Set(), hours: 0 };
      const nonMemberData = nonMemberMap.get(branch) || { volunteers: new Set(), hours: 0 };
      
      const memberVolunteers = memberData.volunteers.size;
      const nonMemberVolunteers = nonMemberData.volunteers.size;
      const totalVolunteers = memberVolunteers + nonMemberVolunteers;
      
      const memberHours = memberData.hours;
      const nonMemberHours = nonMemberData.hours;
      const totalHours = memberHours + nonMemberHours;
      
      // Participation parity ratio (closer to 1.0 is more equitable)
      const volunteerParity = totalVolunteers > 0 ? 
        Math.min(memberVolunteers, nonMemberVolunteers) / Math.max(memberVolunteers, nonMemberVolunteers) : 0;
      
      const hoursParity = totalHours > 0 ? 
        Math.min(memberHours, nonMemberHours) / Math.max(memberHours, nonMemberHours) : 0;

      return {
        branch,
        memberVolunteers,
        nonMemberVolunteers,
        totalVolunteers,
        memberHours: Number(memberHours.toFixed(1)),
        nonMemberHours: Number(nonMemberHours.toFixed(1)),
        totalHours: Number(totalHours.toFixed(1)),
        volunteerParity: Number((volunteerParity || 0).toFixed(3)),
        hoursParity: Number((hoursParity || 0).toFixed(3)),
        memberPercentage: totalVolunteers > 0 ? Number(((memberVolunteers / totalVolunteers) * 100).toFixed(1)) : 0
      };
    });

    return branchParity.sort((a, b) => b.totalVolunteers - a.totalVolunteers);
  }, [filtered]);

  // Access Indicators
  const accessIndicators = useMemo(() => {
    // Project category accessibility (diversity of engagement)
    const categoryAccess = new Map();
    
    filtered.forEach(r => {
      const category = (r.category || r.project_tag || "Unknown").trim();
      const assignee = (r.assignee || "").trim().toLowerCase();
      const branch = (r.branch || "").trim();
      const isMember = r.is_member;
      
      if (!assignee) return;
      
      if (!categoryAccess.has(category)) {
        categoryAccess.set(category, {
          totalVolunteers: new Set(),
          memberVolunteers: new Set(),
          nonMemberVolunteers: new Set(),
          branches: new Set(),
          hours: 0
        });
      }
      
      const data = categoryAccess.get(category);
      data.totalVolunteers.add(`${assignee}||${branch}`);
      data.branches.add(branch);
      data.hours += Number(r.hours) || 0;
      
      if (isMember) {
        data.memberVolunteers.add(`${assignee}||${branch}`);
      } else {
        data.nonMemberVolunteers.add(`${assignee}||${branch}`);
      }
    });

    const categoryMetrics = Array.from(categoryAccess.entries()).map(([category, data]) => {
      const totalVolunteers = data.totalVolunteers.size;
      const memberVolunteers = data.memberVolunteers.size;
      const nonMemberVolunteers = data.nonMemberVolunteers.size;
      const branchDiversity = data.branches.size;
      
      // Access equity score (0-1, higher is more equitable)
      const membershipEquity = totalVolunteers > 0 ? 
        1 - Math.abs((memberVolunteers - nonMemberVolunteers) / totalVolunteers) : 0;
      
      // Geographic access (more branches = better access)
      const geographicAccess = branchDiversity / Math.max(1, participationParity.length);
      
      // Combined access score
      const accessScore = (membershipEquity * 0.6 + geographicAccess * 0.4);
      
      return {
        category,
        totalVolunteers,
        memberVolunteers,
        nonMemberVolunteers,
        branchDiversity,
        hours: Number(data.hours.toFixed(1)),
        membershipEquity: Number(membershipEquity.toFixed(3)),
        geographicAccess: Number(geographicAccess.toFixed(3)),
        accessScore: Number(accessScore.toFixed(3)),
        memberPercentage: totalVolunteers > 0 ? Number(((memberVolunteers / totalVolunteers) * 100).toFixed(1)) : 0
      };
    });

    return categoryMetrics.sort((a, b) => b.accessScore - a.accessScore);
  }, [filtered, participationParity]);

  // Overall Equity Summary
  const equitySummary = useMemo(() => {
    const totalVolunteers = new Set(filtered.map(r => `${r.assignee}||${r.branch}`)).size;
    const totalMemberVolunteers = new Set(filtered.filter(r => r.is_member).map(r => `${r.assignee}||${r.branch}`)).size;
    const totalNonMemberVolunteers = totalVolunteers - totalMemberVolunteers;
    
    // Overall participation parity
    const overallVolunteerParity = totalVolunteers > 0 ? 
      Math.min(totalMemberVolunteers, totalNonMemberVolunteers) / Math.max(totalMemberVolunteers, totalNonMemberVolunteers) : 0;
    
    // Branch coverage equity (how evenly distributed volunteers are across branches)
    const branchVolunteerCounts = participationParity.map(b => b.totalVolunteers);
    const avgVolunteersPerBranch = branchVolunteerCounts.reduce((a, b) => a + b, 0) / branchVolunteerCounts.length;
    const branchEquity = avgVolunteersPerBranch > 0 ? 
      1 - (branchVolunteerCounts.reduce((acc, count) => acc + Math.abs(count - avgVolunteersPerBranch), 0) / 
           (branchVolunteerCounts.length * avgVolunteersPerBranch)) : 0;
    
    // Category access equity (average of all category access scores)
    const avgCategoryAccess = accessIndicators.length > 0 ? 
      accessIndicators.reduce((acc, cat) => acc + cat.accessScore, 0) / accessIndicators.length : 0;
    
    // Overall equity score
    const overallEquityScore = (overallVolunteerParity * 0.4 + branchEquity * 0.3 + avgCategoryAccess * 0.3);
    
    return {
      totalVolunteers,
      memberVolunteers: totalMemberVolunteers,
      nonMemberVolunteers: totalNonMemberVolunteers,
      memberPercentage: totalVolunteers > 0 ? Number(((totalMemberVolunteers / totalVolunteers) * 100).toFixed(1)) : 0,
      overallVolunteerParity: Number((overallVolunteerParity || 0).toFixed(3)),
      branchEquity: Number((branchEquity || 0).toFixed(3)),
      avgCategoryAccess: Number((avgCategoryAccess || 0).toFixed(3)),
      overallEquityScore: Number((overallEquityScore || 0).toFixed(3)),
      equityGrade: getEquityGrade(overallEquityScore)
    };
  }, [filtered, participationParity, accessIndicators]);

  // Equity Insights
  const equityInsights = useMemo(() => {
    const insights = [];
    
    // Overall equity assessment
    if (equitySummary.overallEquityScore >= 0.8) {
      insights.push({
        type: "success",
        title: "Excellent Equity Performance",
        message: `Overall equity score of ${(equitySummary.overallEquityScore * 100).toFixed(1)}% indicates strong inclusive participation`
      });
    } else if (equitySummary.overallEquityScore >= 0.6) {
      insights.push({
        type: "info",
        title: "Good Equity Foundation",
        message: `Equity score of ${(equitySummary.overallEquityScore * 100).toFixed(1)}% shows positive inclusion trends with room for improvement`
      });
    } else {
      insights.push({
        type: "warning",
        title: "Equity Improvement Needed",
        message: `Equity score of ${(equitySummary.overallEquityScore * 100).toFixed(1)}% suggests opportunities to enhance inclusive participation`
      });
    }
    
    // Member participation balance
    const memberPct = equitySummary.memberPercentage;
    if (memberPct >= 40 && memberPct <= 60) {
      insights.push({
        type: "success",
        title: "Balanced Member Participation",
        message: `${memberPct}% member volunteers shows healthy community engagement balance`
      });
    } else if (memberPct > 70) {
      insights.push({
        type: "info",
        title: "High Member Participation",
        message: `${memberPct}% member volunteers. Consider outreach to engage more community members`
      });
    } else if (memberPct < 30) {
      insights.push({
        type: "info",
        title: "High Community Participation",
        message: `${memberPct}% member volunteers shows strong community outreach success`
      });
    }
    
    // Best performing categories for equity
    if (accessIndicators.length > 0) {
      const topCategory = accessIndicators[0];
      if (topCategory.accessScore >= 0.8) {
        insights.push({
          type: "success",
          title: "Equitable Category Access",
          message: `${topCategory.category} shows excellent access equity with ${(topCategory.accessScore * 100).toFixed(1)}% score`
        });
      }
    }
    
    // Branch equity performance
    if (equitySummary.branchEquity >= 0.7) {
      insights.push({
        type: "success",
        title: "Well-Distributed Participation",
        message: `Strong branch equity of ${(equitySummary.branchEquity * 100).toFixed(1)}% shows even volunteer distribution`
      });
    } else {
      insights.push({
        type: "info",
        title: "Uneven Branch Participation",
        message: `Consider strategies to balance volunteer participation across branches`
      });
    }
    
    return insights;
  }, [equitySummary, accessIndicators]);

  return {
    participationParity,
    accessIndicators,
    equitySummary,
    equityInsights
  };
}

function getEquityGrade(score) {
  if (score >= 0.9) return "A+";
  if (score >= 0.8) return "A";
  if (score >= 0.7) return "B+";
  if (score >= 0.6) return "B";
  if (score >= 0.5) return "C+";
  if (score >= 0.4) return "C";
  if (score >= 0.3) return "D";
  return "F";
}