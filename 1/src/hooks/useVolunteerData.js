import { useMemo } from "react";
import { toMonth } from "../utils/dateUtils";
import { calculateNormalizedLeaderboards, getLeaderboardInsights } from "../utils/leaderboardUtils";

export function useVolunteerData(raw, branchFilter, search, monthFilter = "All") {
  const branches = useMemo(() => {
    const s = new Set(raw.map(r => (r.branch || "Unknown").trim() || "Unknown"));
    return ["All", ...Array.from(s).sort()];
  }, [raw]);

  const months = useMemo(() => {
    const s = new Set(raw.map(r => toMonth(r.date)).filter(Boolean));
    return ["All", ...Array.from(s).sort((a, b) => new Date(a) - new Date(b))];
  }, [raw]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return raw.filter(r => {
      const matchesBranch = branchFilter === "All" || (r.branch || "").toLowerCase() === branchFilter.toLowerCase();
      const matchesMonth = monthFilter === "All" || toMonth(r.date) === monthFilter;
      const matchesSearch = !q || [r.assignee, r.branch, r.project_tag, r.project_catalog, String(r.hours), r.date]
        .some(v => (v || "").toString().toLowerCase().includes(q));
      return matchesBranch && matchesMonth && matchesSearch;
    });
  }, [raw, branchFilter, search, monthFilter]);

  const totalHours = useMemo(() =>
    filtered.reduce((acc, r) => acc + (Number(r.hours) || 0), 0), [filtered]);

  // PROJECT CATEGORY STATISTICS (Page 1 Requirements)
  const projectCategoryStats = useMemo(() => {
    // Hours by Project Tag (no deduplication)
    const hoursByTag = new Map();
    filtered.forEach(r => {
      const tag = (r.project_tag || "Unknown").trim();
      hoursByTag.set(tag, (hoursByTag.get(tag) || 0) + (Number(r.hours) || 0));
    });

    // Volunteers by Project Catalog (deduplicated by ASSIGNEE, PROJECT CATALOG, BRANCH)
    const volunteersByProjectCatalog = new Map();
    const volunteerDedupeSet = new Set();
    filtered.forEach(r => {
      const catalog = (r.project_catalog || "Unknown").trim();
      const assignee = (r.assignee || "").trim().toLowerCase();
      const branch = (r.branch || "").trim().toLowerCase();
      if (!assignee) return;
      
      const key = `${assignee}||${catalog}||${branch}`;
      if (!volunteerDedupeSet.has(key)) {
        volunteerDedupeSet.add(key);
        volunteersByProjectCatalog.set(catalog, (volunteersByProjectCatalog.get(catalog) || 0) + 1);
      }
    });

    // Projects by Project Tag (deduplicated by PROJECT, PROJECT CATALOG, BRANCH)
    const projectsByTag = new Map();
    const projectDedupeSet = new Set();
    filtered.forEach(r => {
      const tag = (r.project_tag || "Unknown").trim();
      const project = (r.project || "").trim();
      const catalog = (r.project_catalog || "").trim();
      const branch = (r.branch || "").trim();
      if (!project) return;
      
      const key = `${project}||${catalog}||${branch}`;
      if (!projectDedupeSet.has(key)) {
        projectDedupeSet.add(key);
        projectsByTag.set(tag, (projectsByTag.get(tag) || 0) + 1);
      }
    });

    const allTags = new Set([...hoursByTag.keys(), ...projectsByTag.keys()]);
    return Array.from(allTags).map(tag => ({
      project_tag: tag,
      hours: Number((hoursByTag.get(tag) || 0).toFixed(1)),
      volunteers: volunteersByProjectCatalog.get(tag) || 0,
      projects: projectsByTag.get(tag) || 0
    })).sort((a, b) => b.hours - a.hours);
  }, [filtered]);

  // Enhanced Active Volunteers Count (deduplicated by ASSIGNEE, BRANCH)
  const activeVolunteersCount = useMemo(() => {
    const keyset = new Set();
    filtered.forEach(r => {
      const a = (r.assignee || "").trim().toLowerCase();
      const b = (r.branch || "").trim().toLowerCase();
      if (a) keyset.add(`${a}||${b}`);
    });
    return keyset.size;
  }, [filtered]);

  // Member Volunteers Count (using MEMBER BRANCH and ARE YOU A YMCA MEMBER)
  const memberVolunteersCount = useMemo(() => {
    const memberDedupeSet = new Set();
    filtered.forEach(r => {
      if (!r.is_member) return;
      const a = (r.assignee || "").trim().toLowerCase();
      const memberBranch = (r.member_branch || r.branch || "").trim().toLowerCase();
      if (a) memberDedupeSet.add(`${a}||${memberBranch}`);
    });
    return memberDedupeSet.size;
  }, [filtered]);

  // ENHANCED BRANCH ANALYTICS (Pages 2-5 Requirements)
  const hoursByBranch = useMemo(() => {
    const m = new Map();
    filtered.forEach(r => {
      const b = (r.branch || "Unknown").trim() || "Unknown";
      m.set(b, (m.get(b) || 0) + (Number(r.hours) || 0));
    });
    return Array.from(m.entries())
      .map(([branch, hours]) => ({ branch, hours: Number(hours.toFixed(1)) }))
      .sort((a, b) => b.hours - a.hours);
  }, [filtered]);

  const activesByBranch = useMemo(() => {
    const map = new Map();
    filtered.forEach(r => {
      const b = (r.branch || "Unknown").trim() || "Unknown";
      const a = (r.assignee || "").trim().toLowerCase();
      if (!a) return;
      if (!map.has(b)) map.set(b, new Set());
      map.get(b).add(`${a}||${b}`); // Include branch in deduplication key
    });
    return Array.from(map.entries())
      .map(([branch, set]) => ({ branch, active: set.size }))
      .sort((a, b) => b.active - a.active);
  }, [filtered]);

  const memberShareByBranch = useMemo(() => {
    const total = new Map();
    const mem = new Map();
    filtered.forEach(r => {
      const memberBranch = (r.member_branch || "Unknown").trim() || "Unknown";
      const a = (r.assignee || "").trim().toLowerCase();
      if (!a || !r.is_member) return;
      
      if (!total.has(memberBranch)) total.set(memberBranch, new Set());
      total.get(memberBranch).add(`${a}||${memberBranch}`);
      
      if (!mem.has(memberBranch)) mem.set(memberBranch, new Set());
      mem.get(memberBranch).add(`${a}||${memberBranch}`);
    });
    
    const rows = Array.from(total.keys()).map(b => {
      const t = total.get(b).size;
      const m = (mem.get(b) || new Set()).size;
      return { branch: b, members: m, active: t, pct: t ? Number(((m / t) * 100).toFixed(1)) : 100 };
    });
    return rows.sort((a, b) => b.members - a.members);
  }, [filtered]);

  // YDE SPECIAL REPORTING (Page 6 Requirements)
  const ydeStats = useMemo(() => {
    const ydeFiltered = filtered.filter(r => {
      const tag = (r.project_tag || "").toLowerCase();
      return tag.includes("yde") || r.branch === "Music Resource Center";
    });

    const categories = ["YDE - Community Services", "YDE - Early Learning Centers", "YDE - Out of School Time"];
    return categories.map(category => {
      const categoryData = ydeFiltered.filter(r => 
        (r.project_tag || "").includes(category) || 
        (category === "YDE - Community Services" && r.branch === "Music Resource Center")
      );
      
      const hours = categoryData.reduce((acc, r) => acc + (Number(r.hours) || 0), 0);
      const volunteers = new Set(categoryData.map(r => `${r.assignee}||${r.branch}`)).size;
      const projects = new Set(categoryData.map(r => `${r.project}||${r.branch}`)).size;
      
      return {
        category,
        hours: Number(hours.toFixed(1)),
        volunteers,
        projects
      };
    });
  }, [filtered]);

  // SENIOR CENTERS COMBINED REPORTING (Page 7 Requirements)
  const seniorCentersStats = useMemo(() => {
    const combinations = [
      {
        name: "Clippard YMCA + Clippard Senior Center",
        branches: ["Clippard", "Clippard Senior Center"]
      },
      {
        name: "R.C. Durre YMCA + Kentucky Senior Center", 
        branches: ["R.C. Durre YMCA", "Kentucky Senior Center"]
      }
    ];

    return combinations.map(combo => {
      const comboData = filtered.filter(r => combo.branches.includes(r.branch));
      const hours = comboData.reduce((acc, r) => acc + (Number(r.hours) || 0), 0);
      const volunteers = new Set(comboData.map(r => `${r.assignee}||${r.branch}`)).size;
      const members = new Set(comboData.filter(r => r.is_member).map(r => `${r.assignee}||${r.member_branch}`)).size;
      
      return {
        name: combo.name,
        hours: Number(hours.toFixed(1)),
        volunteers,
        members
      };
    });
  }, [filtered]);

  const trendByMonth = useMemo(() => {
    const map = new Map();
    filtered.forEach(r => {
      const mo = toMonth(r.date);
      if (!map.has(mo)) map.set(mo, { hours: 0, active: new Set(), members: new Set() });
      map.get(mo).hours += Number(r.hours) || 0;
      const a = (r.assignee || "").trim().toLowerCase();
      const b = (r.branch || "").trim().toLowerCase();
      if (a) {
        map.get(mo).active.add(`${a}||${b}`);
        if (r.is_member) map.get(mo).members.add(`${a}||${b}`);
      }
    });
    const months = Array.from(map.keys());
    months.sort((a, b) => new Date(a) - new Date(b));
    return months.map(m => ({
      month: m,
      hours: Number((map.get(m).hours || 0).toFixed(1)),
      active: map.get(m).active.size,
      members: map.get(m).members.size
    }));
  }, [filtered]);

  const leaderboard = useMemo(() => {
    const map = new Map();
    filtered.forEach(r => {
      const a = (r.assignee || "Unknown").trim();
      map.set(a, (map.get(a) || 0) + (Number(r.hours) || 0));
    });
    return Array.from(map.entries())
      .map(([assignee, hours]) => ({ assignee, hours: Number(hours.toFixed(1)) }))
      .sort((a, b) => b.hours - a.hours)
      .slice(0, 15);
  }, [filtered]);

  // Enhanced normalized leaderboards for fair competition
  const normalizedLeaderboards = useMemo(() => {
    return calculateNormalizedLeaderboards(filtered);
  }, [filtered]);

  const leaderboardInsights = useMemo(() => {
    return getLeaderboardInsights(normalizedLeaderboards);
  }, [normalizedLeaderboards]);

  const badges = useMemo(() => {
    const milestones = [10, 25, 50, 100, 200, 500];
    const sums = new Map();
    filtered.forEach(r => {
      const a = (r.assignee || "Unknown").trim();
      sums.set(a, (sums.get(a) || 0) + (Number(r.hours) || 0));
    });
    return Array.from(sums.entries()).map(([assignee, hrs]) => {
      const reached = milestones.filter(m => hrs >= m);
      return { assignee, hours: Number(hrs.toFixed(1)), badges: reached };
    }).filter(x => x.badges.length > 0)
      .sort((a, b) => b.hours - a.hours)
      .slice(0, 20);
  }, [filtered]);

  // INTELLIGENT INSIGHTS
  const insights = useMemo(() => {
    const insights = [];
    
    // Top performing branch
    if (hoursByBranch.length > 0) {
      const topBranch = hoursByBranch[0];
      insights.push({
        type: "success",
        title: "Top Performing Branch",
        message: `${topBranch.branch} leads with ${topBranch.hours} volunteer hours`
      });
    }

    // Member engagement
    const memberRate = activeVolunteersCount > 0 ? ((memberVolunteersCount / activeVolunteersCount) * 100).toFixed(1) : 0;
    if (memberRate > 60) {
      insights.push({
        type: "success",
        title: "Strong Member Engagement", 
        message: `${memberRate}% of volunteers are YMCA members`
      });
    } else if (memberRate < 30) {
      insights.push({
        type: "warning",
        title: "Low Member Engagement",
        message: `Only ${memberRate}% of volunteers are members. Consider member recruitment strategies.`
      });
    }

    // YDE Impact
    const ydeHours = ydeStats.reduce((acc, stat) => acc + stat.hours, 0);
    if (ydeHours > totalHours * 0.3) {
      insights.push({
        type: "info",
        title: "YDE Strong Impact",
        message: `Youth Development & Education programs account for ${((ydeHours/totalHours)*100).toFixed(1)}% of volunteer hours`
      });
    }

    // High-impact volunteers
    const highImpactVolunteers = leaderboard.filter(v => v.hours > 50).length;
    if (highImpactVolunteers > 0) {
      insights.push({
        type: "success",
        title: "Dedicated Volunteers",
        message: `${highImpactVolunteers} volunteers contributed 50+ hours each`
      });
    }

    return insights;
  }, [hoursByBranch, activeVolunteersCount, memberVolunteersCount, ydeStats, totalHours, leaderboard]);

  // Enhanced KPIs
  const enhancedKPIs = useMemo(() => ({
    totalProjects: new Set(filtered.map(r => `${r.project}||${r.branch}`)).size,
    avgHoursPerVolunteer: activeVolunteersCount > 0 ? (totalHours / activeVolunteersCount).toFixed(1) : 0,
    memberEngagementRate: activeVolunteersCount > 0 ? ((memberVolunteersCount / activeVolunteersCount) * 100).toFixed(1) : 0,
    topProjectCategory: projectCategoryStats.length > 0 ? projectCategoryStats[0].project_tag : "N/A",
    ydeImpactPct: totalHours > 0 ? ((ydeStats.reduce((acc, stat) => acc + stat.hours, 0) / totalHours) * 100).toFixed(1) : 0
  }), [filtered, activeVolunteersCount, totalHours, memberVolunteersCount, projectCategoryStats, ydeStats]);

  return {
    branches,
    months,
    filtered,
    totalHours,
    activeVolunteersCount,
    memberVolunteersCount,
    hoursByBranch,
    activesByBranch,
    memberShareByBranch,
    trendByMonth,
    leaderboard,
    badges,
    projectCategoryStats,
    ydeStats,
    seniorCentersStats,
    insights,
    enhancedKPIs,
    normalizedLeaderboards,
    leaderboardInsights
  };
}