export async function generateDataStory(volunteerData) {
  const {
    totalHours,
    activeVolunteersCount,
    memberVolunteersCount,
    hoursByBranch,
    trendByMonth,
    leaderboard,
    projectCategoryStats,
    insights,
    enhancedKPIs
  } = volunteerData;

  const cells = [];
  let cellId = 1;

  // Title and Executive Summary
  cells.push({
    id: `cell-${cellId++}`,
    type: "text",
    content: `# Volunteer Impact Analysis

## Executive Summary

This data story analyzes volunteer engagement and impact across ${hoursByBranch.length} YMCA branches. Our analysis reveals ${totalHours.toLocaleString()} total volunteer hours contributed by ${activeVolunteersCount} active volunteers, with ${((memberVolunteersCount / activeVolunteersCount) * 100).toFixed(1)}% being YMCA members.

**Key Highlights:**
- **${hoursByBranch[0]?.branch}** leads in volunteer hours with **${hoursByBranch[0]?.hours} hours**
- Average of **${enhancedKPIs.avgHoursPerVolunteer} hours per volunteer**
- **${enhancedKPIs.memberEngagementRate}%** member engagement rate
- **${enhancedKPIs.totalProjects}** unique projects supported`,
    isEditing: false
  });

  // Branch Performance Visualization
  cells.push({
    id: `cell-${cellId++}`,
    type: "chart",
    content: {
      chartType: "bar",
      dataSource: "hoursByBranch",
      title: "Volunteer Hours by Branch - Top Performers"
    },
    isEditing: false
  });

  // Branch Analysis Text
  const topBranches = hoursByBranch.slice(0, 3);
  cells.push({
    id: `cell-${cellId++}`,
    type: "text",
    content: `## Branch Performance Analysis

The volunteer hour distribution shows clear leadership from our top-performing branches:

${topBranches.map((branch, index) => 
  `${index + 1}. **${branch.branch}**: ${branch.hours} hours`
).join('\n')}

This concentration of volunteer activity indicates strong community engagement at these locations. The top three branches account for **${((topBranches.reduce((sum, b) => sum + b.hours, 0) / totalHours) * 100).toFixed(1)}%** of total volunteer hours.`,
    isEditing: false
  });

  // Volunteer Engagement Chart
  cells.push({
    id: `cell-${cellId++}`,
    type: "chart",
    content: {
      chartType: "bar",
      dataSource: "activesByBranch",
      title: "Active Volunteers by Branch"
    },
    isEditing: false
  });

  // Monthly Trends
  if (trendByMonth.length > 1) {
    cells.push({
      id: `cell-${cellId++}`,
      type: "chart",
      content: {
        chartType: "line",
        dataSource: "trendByMonth",
        title: "Monthly Volunteer Trends"
      },
      isEditing: false
    });

    // Trend Analysis
    const latestMonth = trendByMonth[trendByMonth.length - 1];
    const previousMonth = trendByMonth[trendByMonth.length - 2];
    const hoursTrend = latestMonth.hours - previousMonth.hours;
    const volunteerTrend = latestMonth.active - previousMonth.active;
    
    cells.push({
      id: `cell-${cellId++}`,
      type: "text",
      content: `## Monthly Trend Analysis

Comparing ${previousMonth.month} to ${latestMonth.month}:
- Volunteer hours ${hoursTrend >= 0 ? 'increased' : 'decreased'} by **${Math.abs(hoursTrend).toFixed(1)} hours** (${hoursTrend >= 0 ? '+' : ''}${((hoursTrend / previousMonth.hours) * 100).toFixed(1)}%)
- Active volunteers ${volunteerTrend >= 0 ? 'increased' : 'decreased'} by **${Math.abs(volunteerTrend)} volunteers** (${volunteerTrend >= 0 ? '+' : ''}${((volunteerTrend / previousMonth.active) * 100).toFixed(1)}%)

${hoursTrend >= 0 
  ? "This positive trend indicates growing volunteer engagement." 
  : "This decline presents an opportunity to re-engage volunteers and boost participation."}`,
      isEditing: false
    });
  }

  // Project Categories
  if (projectCategoryStats.length > 0) {
    cells.push({
      id: `cell-${cellId++}`,
      type: "chart",
      content: {
        chartType: "pie",
        dataSource: "projectCategoryStats",
        title: "Volunteer Hours by Project Category"
      },
      isEditing: false
    });

    const topCategory = projectCategoryStats[0];
    cells.push({
      id: `cell-${cellId++}`,
      type: "text",
      content: `## Project Impact Analysis

**${topCategory.project_tag}** emerges as our highest-impact category with **${topCategory.hours} volunteer hours** across **${topCategory.projects} projects** and **${topCategory.volunteers} volunteers**.

### Project Category Breakdown:
${projectCategoryStats.slice(0, 5).map(cat => 
  `- **${cat.project_tag}**: ${cat.hours} hours, ${cat.volunteers} volunteers, ${cat.projects} projects`
).join('\n')}

This distribution reflects our organization's commitment to diverse community programming.`,
      isEditing: false
    });
  }

  // Top Volunteers Recognition
  if (leaderboard.length > 0) {
    cells.push({
      id: `cell-${cellId++}`,
      type: "chart",
      content: {
        chartType: "bar",
        dataSource: "leaderboard",
        title: "Top 10 Volunteers by Hours Contributed"
      },
      isEditing: false
    });

    cells.push({
      id: `cell-${cellId++}`,
      type: "text",
      content: `## Volunteer Recognition

Our top volunteers demonstrate exceptional commitment to the YMCA mission:

### Outstanding Contributors:
${leaderboard.slice(0, 5).map((volunteer, index) => 
  `${index + 1}. **${volunteer.assignee}**: ${volunteer.hours} hours`
).join('\n')}

The dedication of our top 10 volunteers represents **${((leaderboard.slice(0, 10).reduce((sum, v) => sum + v.hours, 0) / totalHours) * 100).toFixed(1)}%** of total volunteer hours, highlighting the significant impact of highly engaged community members.`,
      isEditing: false
    });
  }

  // Insights and Recommendations
  if (insights.length > 0) {
    const insightText = insights.map(insight => {
      const emoji = insight.type === 'success' ? '✅' : insight.type === 'warning' ? '⚠️' : 'ℹ️';
      return `${emoji} **${insight.title}**: ${insight.message}`;
    }).join('\n\n');

    cells.push({
      id: `cell-${cellId++}`,
      type: "text",
      content: `## Key Insights & Recommendations

${insightText}

### Strategic Recommendations:

1. **Expand Successful Programs**: Replicate successful models from top-performing branches
2. **Member Engagement**: ${memberVolunteersCount / activeVolunteersCount < 0.5 
   ? 'Develop targeted campaigns to increase member volunteer participation'
   : 'Maintain strong member engagement through recognition programs'}
3. **Resource Allocation**: Direct support resources to branches with high volunteer activity
4. **Capacity Building**: Provide additional support to emerging volunteer programs`,
      isEditing: false
    });
  }

  // Conclusion
  cells.push({
    id: `cell-${cellId++}`,
    type: "text",
    content: `## Conclusion

This analysis demonstrates the substantial impact of volunteerism across our YMCA network. With **${totalHours.toLocaleString()} hours** of service and **${activeVolunteersCount} dedicated volunteers**, our community continues to strengthen youth development, healthy living, and social responsibility initiatives.

### Next Steps:
- Monitor monthly trends to identify seasonal patterns
- Implement targeted volunteer recruitment strategies
- Recognize and celebrate our top contributors
- Expand successful program models to other locations

*Generated on ${new Date().toLocaleDateString()} | Data reflects current volunteer activity*`,
    isEditing: false
  });

  return cells;
}