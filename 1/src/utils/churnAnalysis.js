import { toMonth } from './dateUtils';

/**
 * Calculates churn risk metrics for volunteers
 */
export function calculateChurnRisk(data, currentDate = new Date()) {
  const currentMonth = toMonth(currentDate.toISOString().split('T')[0]);
  const oneMonthAgo = toMonth(new Date(currentDate.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]);
  const twoMonthsAgo = toMonth(new Date(currentDate.getTime() - 60 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]);
  
  // Group volunteers by assignee and branch
  const volunteerStats = new Map();
  
  data.forEach(record => {
    const key = `${record.assignee}||${record.branch}`;
    const recordMonth = toMonth(record.date);
    
    if (!volunteerStats.has(key)) {
      volunteerStats.set(key, {
        assignee: record.assignee,
        branch: record.branch,
        is_member: record.is_member,
        member_branch: record.member_branch,
        totalHours: 0,
        monthlyHours: new Map(),
        lastActiveMonth: null,
        activeDuration: 0,
        projects: new Set()
      });
    }
    
    const volunteer = volunteerStats.get(key);
    volunteer.totalHours += Number(record.hours) || 0;
    volunteer.monthlyHours.set(recordMonth, (volunteer.monthlyHours.get(recordMonth) || 0) + (Number(record.hours) || 0));
    volunteer.projects.add(record.project);
    
    if (!volunteer.lastActiveMonth || new Date(recordMonth) > new Date(volunteer.lastActiveMonth)) {
      volunteer.lastActiveMonth = recordMonth;
    }
  });
  
  // Calculate churn risk for each volunteer
  const churnRisks = [];
  
  volunteerStats.forEach((volunteer, key) => {
    const lastActiveDate = new Date(volunteer.lastActiveMonth);
    const currentDateObj = new Date(currentMonth);
    const monthsSinceActive = Math.floor((currentDateObj - lastActiveDate) / (30 * 24 * 60 * 60 * 1000));
    
    // Risk factors
    let riskScore = 0;
    const riskFactors = [];
    
    // 1. Time since last activity
    if (monthsSinceActive >= 2) {
      riskScore += 40;
      riskFactors.push(`Inactive for ${monthsSinceActive} months`);
    } else if (monthsSinceActive >= 1) {
      riskScore += 20;
      riskFactors.push(`Inactive for ${monthsSinceActive} month(s)`);
    }
    
    // 2. Declining hours trend
    const currentMonthHours = volunteer.monthlyHours.get(currentMonth) || 0;
    const oneMonthAgoHours = volunteer.monthlyHours.get(oneMonthAgo) || 0;
    const twoMonthsAgoHours = volunteer.monthlyHours.get(twoMonthsAgo) || 0;
    
    if (currentMonthHours === 0 && oneMonthAgoHours > 0) {
      riskScore += 25;
      riskFactors.push('No activity this month');
    }
    
    if (oneMonthAgoHours < twoMonthsAgoHours && twoMonthsAgoHours > 0) {
      riskScore += 15;
      riskFactors.push('Declining hours trend');
    }
    
    // 3. Low total engagement
    if (volunteer.totalHours < 10) {
      riskScore += 20;
      riskFactors.push('Low total engagement (< 10 hours)');
    }
    
    // 4. Limited project diversity
    if (volunteer.projects.size === 1) {
      riskScore += 10;
      riskFactors.push('Limited to single project');
    }
    
    // 5. Non-member status
    if (!volunteer.is_member) {
      riskScore += 15;
      riskFactors.push('Not a YMCA member');
    }
    
    // Determine risk level
    let riskLevel;
    if (riskScore >= 60) {
      riskLevel = 'High';
    } else if (riskScore >= 30) {
      riskLevel = 'Medium';
    } else {
      riskLevel = 'Low';
    }
    
    churnRisks.push({
      assignee: volunteer.assignee,
      branch: volunteer.branch,
      is_member: volunteer.is_member,
      member_branch: volunteer.member_branch,
      totalHours: Number(volunteer.totalHours.toFixed(1)),
      lastActiveMonth: volunteer.lastActiveMonth,
      monthsSinceActive,
      riskScore,
      riskLevel,
      riskFactors,
      projectCount: volunteer.projects.size
    });
  });
  
  return churnRisks.sort((a, b) => b.riskScore - a.riskScore);
}

/**
 * Processes natural language queries about churn risk
 */
export function processNaturalLanguageQuery(query, churnData) {
  const lowerQuery = query.toLowerCase().trim();
  
  // Extract branch name if mentioned
  const branchMatch = lowerQuery.match(/(?:in|at|from)\s+(.+?)(?:\s|$)/);
  let targetBranch = null;
  if (branchMatch) {
    targetBranch = branchMatch[1].replace(/[^\w\s]/g, '').trim();
  }
  
  // Determine query type
  let queryType = 'general';
  let riskLevel = null;
  
  if (lowerQuery.includes('churn risk') || lowerQuery.includes('at risk')) {
    queryType = 'churn_risk';
    
    if (lowerQuery.includes('high risk') || lowerQuery.includes('most at risk')) {
      riskLevel = 'High';
    } else if (lowerQuery.includes('medium risk')) {
      riskLevel = 'Medium';
    } else if (lowerQuery.includes('low risk')) {
      riskLevel = 'Low';
    }
  } else if (lowerQuery.includes('inactive') || lowerQuery.includes('not active')) {
    queryType = 'inactive';
  } else if (lowerQuery.includes('declining') || lowerQuery.includes('decreasing')) {
    queryType = 'declining';
  } else if (lowerQuery.includes('new') || lowerQuery.includes('recent')) {
    queryType = 'new';
  }
  
  // Filter data based on query
  let filteredData = churnData;
  
  // Apply branch filter
  if (targetBranch) {
    filteredData = filteredData.filter(volunteer => 
      volunteer.branch.toLowerCase().includes(targetBranch.toLowerCase()) ||
      targetBranch.toLowerCase().includes(volunteer.branch.toLowerCase())
    );
  }
  
  // Apply query type filters
  switch (queryType) {
    case 'churn_risk':
      if (riskLevel) {
        filteredData = filteredData.filter(v => v.riskLevel === riskLevel);
      } else {
        filteredData = filteredData.filter(v => v.riskLevel !== 'Low');
      }
      break;
    case 'inactive':
      filteredData = filteredData.filter(v => v.monthsSinceActive >= 1);
      break;
    case 'declining':
      filteredData = filteredData.filter(v => 
        v.riskFactors.some(factor => factor.includes('declining') || factor.includes('No activity'))
      );
      break;
    case 'new':
      filteredData = filteredData.filter(v => v.totalHours < 20);
      break;
  }
  
  // Generate response
  const response = generateQueryResponse(query, filteredData, queryType, targetBranch, riskLevel);
  
  return {
    results: filteredData.slice(0, 10), // Limit to top 10 results
    summary: response,
    totalFound: filteredData.length,
    queryType,
    targetBranch,
    riskLevel
  };
}

function generateQueryResponse(originalQuery, results, queryType, branch, riskLevel) {
  const count = results.length;
  const branchText = branch ? ` in ${branch}` : '';
  
  if (count === 0) {
    return `No volunteers found matching your query${branchText}.`;
  }
  
  let response = '';
  
  switch (queryType) {
    case 'churn_risk':
      const levelText = riskLevel ? ` at ${riskLevel.toLowerCase()} risk` : ' at churn risk';
      response = `Found ${count} volunteer${count !== 1 ? 's' : ''}${levelText}${branchText}. `;
      
      if (results.length > 0) {
        const avgRisk = (results.reduce((sum, v) => sum + v.riskScore, 0) / results.length).toFixed(1);
        response += `Average risk score: ${avgRisk}/100.`;
      }
      break;
      
    case 'inactive':
      response = `Found ${count} inactive volunteer${count !== 1 ? 's' : ''}${branchText}. `;
      const avgInactive = results.length > 0 ? 
        (results.reduce((sum, v) => sum + v.monthsSinceActive, 0) / results.length).toFixed(1) : 0;
      response += `Average months since last activity: ${avgInactive}.`;
      break;
      
    case 'declining':
      response = `Found ${count} volunteer${count !== 1 ? 's' : ''} with declining engagement${branchText}.`;
      break;
      
    case 'new':
      response = `Found ${count} new/low-engagement volunteer${count !== 1 ? 's' : ''}${branchText} (< 20 hours).`;
      break;
      
    default:
      response = `Found ${count} volunteer${count !== 1 ? 's' : ''}${branchText} matching your query.`;
  }
  
  return response;
}