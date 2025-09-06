import { useState, useCallback } from 'react';

export const useVoiceCommands = (volunteerData, updateFilters) => {
  const [commandHistory, setCommandHistory] = useState([]);

  const executeCommand = useCallback((intent, entity, originalText) => {
    const command = {
      id: Date.now(),
      intent,
      entity,
      originalText,
      timestamp: new Date().toISOString(),
    };

    setCommandHistory(prev => [...prev, command]);

    switch (intent) {
      case 'get_volunteer_hours':
        return getVolunteerHours(entity);
      
      case 'get_branch_volunteers':
        return getBranchVolunteers(entity);
      
      case 'get_total_hours':
        return getTotalHours();
      
      case 'get_volunteer_count':
        return getVolunteerCount();
      
      case 'get_top_volunteers':
        return getTopVolunteers();
      
      case 'get_volunteer_projects':
        return getVolunteerProjects(entity);
      
      case 'list_branches':
        return listBranches();
      
      case 'filter_data':
        return filterData(entity);
      
      case 'get_recent_activity':
        return getRecentActivity();
      
      case 'get_project_stats':
        return getProjectStats(entity);
      
      case 'compare_branches':
        return compareBranches(entity);
      
      case 'get_member_stats':
        return getMemberStats();
      
      case 'export_data':
        return exportData(entity);
      
      default:
        return {
          success: false,
          message: "I didn't understand that command. Try asking about volunteer hours, branches, or projects.",
          suggestions: [
            "Show me total hours",
            "Who worked at Blue Ash?",
            "List all branches",
            "Get top volunteers"
          ]
        };
    }
  }, [volunteerData]);

  const getVolunteerHours = (volunteerName) => {
    if (!volunteerName) {
      return {
        success: false,
        message: "Please specify which volunteer you'd like to know about.",
      };
    }

    const volunteer = findVolunteer(volunteerName);
    if (volunteer.length === 0) {
      return {
        success: false,
        message: `I couldn't find a volunteer named ${volunteerName}.`,
        suggestions: getVolunteerNameSuggestions(volunteerName)
      };
    }

    const totalHours = volunteer.reduce((sum, record) => sum + record.hours, 0);
    const projects = volunteer.length;
    const avgHoursPerProject = totalHours / projects;
    const recentProject = volunteer.sort((a, b) => new Date(b.date) - new Date(a.date))[0];
    
    return {
      success: true,
      message: `${volunteerName} has worked ${totalHours.toFixed(1)} hours across ${projects} projects, averaging ${avgHoursPerProject.toFixed(1)} hours per project. Their most recent project was ${recentProject.project}.`,
      data: { 
        totalHours, 
        projects, 
        avgHoursPerProject,
        recentProject,
        records: volunteer 
      }
    };
  };

  const getBranchVolunteers = (branchName) => {
    if (!branchName) {
      return {
        success: false,
        message: "Please specify which branch you'd like to know about.",
        suggestions: getAllBranches().slice(0, 3)
      };
    }

    const branchData = volunteerData.filter(record => 
      record.branch.toLowerCase().includes(branchName.toLowerCase())
    );

    if (branchData.length === 0) {
      return {
        success: false,
        message: `I couldn't find any volunteers for ${branchName} branch.`,
        suggestions: getBranchSuggestions(branchName)
      };
    }

    const uniqueVolunteers = [...new Set(branchData.map(record => record.assignee))];
    const totalHours = branchData.reduce((sum, record) => sum + record.hours, 0);
    const avgHoursPerVolunteer = totalHours / uniqueVolunteers.length;
    const topVolunteer = getTopVolunteerForBranch(branchData);

    return {
      success: true,
      message: `${branchName} branch has ${uniqueVolunteers.length} volunteers who worked ${totalHours.toFixed(1)} hours total, averaging ${avgHoursPerVolunteer.toFixed(1)} hours per volunteer. Top contributor is ${topVolunteer.name} with ${topVolunteer.hours.toFixed(1)} hours.`,
      data: { 
        volunteers: uniqueVolunteers, 
        totalHours, 
        avgHoursPerVolunteer,
        topVolunteer,
        records: branchData 
      }
    };
  };

  const getTotalHours = () => {
    const totalHours = volunteerData.reduce((sum, record) => sum + record.hours, 0);
    const activeVolunteers = [...new Set(volunteerData.map(record => record.assignee))].length;
    const totalProjects = [...new Set(volunteerData.map(record => record.project))].length;
    const avgHoursPerVolunteer = totalHours / activeVolunteers;

    return {
      success: true,
      message: `Total volunteer hours: ${totalHours.toFixed(1)} hours from ${activeVolunteers} active volunteers across ${totalProjects} projects, averaging ${avgHoursPerVolunteer.toFixed(1)} hours per volunteer.`,
      data: { totalHours, activeVolunteers, totalProjects, avgHoursPerVolunteer }
    };
  };

  const getVolunteerCount = () => {
    const activeVolunteers = [...new Set(volunteerData.map(record => record.assignee))].length;
    const memberVolunteers = [...new Set(
      volunteerData.filter(record => record.is_member).map(record => record.assignee)
    )].length;
    const nonMemberVolunteers = activeVolunteers - memberVolunteers;
    const memberPercentage = (memberVolunteers / activeVolunteers * 100);

    return {
      success: true,
      message: `We have ${activeVolunteers} active volunteers: ${memberVolunteers} YMCA members (${memberPercentage.toFixed(1)}%) and ${nonMemberVolunteers} non-members.`,
      data: { activeVolunteers, memberVolunteers, nonMemberVolunteers, memberPercentage }
    };
  };

  const getTopVolunteers = () => {
    const volunteerHours = {};
    volunteerData.forEach(record => {
      volunteerHours[record.assignee] = (volunteerHours[record.assignee] || 0) + record.hours;
    });

    const topVolunteers = Object.entries(volunteerHours)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5);

    const totalTopHours = topVolunteers.reduce((sum, [, hours]) => sum + hours, 0);
    const overallTotal = Object.values(volunteerHours).reduce((sum, hours) => sum + hours, 0);
    const topPercentage = (totalTopHours / overallTotal * 100);

    const message = `Top 5 volunteers: ${topVolunteers.map(([name, hours]) => 
      `${name} with ${hours.toFixed(1)} hours`).join(', ')}. These volunteers contributed ${topPercentage.toFixed(1)}% of total hours.`;

    return {
      success: true,
      message,
      data: { topVolunteers, totalTopHours, topPercentage }
    };
  };

  const getVolunteerProjects = (volunteerName) => {
    if (!volunteerName) {
      return {
        success: false,
        message: "Please specify which volunteer you'd like to know about.",
      };
    }

    const volunteer = findVolunteer(volunteerName);
    if (volunteer.length === 0) {
      return {
        success: false,
        message: `I couldn't find a volunteer named ${volunteerName}.`,
        suggestions: getVolunteerNameSuggestions(volunteerName)
      };
    }

    const projects = volunteer.map(record => ({
      name: record.project,
      hours: record.hours,
      date: record.date,
      category: record.category
    }));
    const uniqueProjects = [...new Set(projects.map(p => p.name))];
    const categories = [...new Set(projects.map(p => p.category))];
    const totalHours = projects.reduce((sum, p) => sum + p.hours, 0);

    return {
      success: true,
      message: `${volunteerName} has worked on ${uniqueProjects.length} projects across ${categories.length} categories, totaling ${totalHours.toFixed(1)} hours. Projects include: ${uniqueProjects.join(', ')}.`,
      data: { projects: uniqueProjects, categories, totalHours, records: volunteer }
    };
  };

  const listBranches = () => {
    const branches = [...new Set(volunteerData.map(record => record.branch))];
    const branchStats = branches.map(branch => {
      const branchData = volunteerData.filter(record => record.branch === branch);
      const volunteers = [...new Set(branchData.map(record => record.assignee))].length;
      const hours = branchData.reduce((sum, record) => sum + record.hours, 0);
      return { branch, volunteers, hours };
    }).sort((a, b) => b.hours - a.hours);
    
    const topBranch = branchStats[0];
    
    return {
      success: true,
      message: `We have ${branches.length} branches: ${branches.join(', ')}. ${topBranch.branch} is the most active with ${topBranch.volunteers} volunteers and ${topBranch.hours.toFixed(1)} hours.`,
      data: { branches, branchStats }
    };
  };

  const filterData = (filterTerm) => {
    const filtered = volunteerData.filter(record => 
      Object.values(record).some(value => 
        value && value.toString().toLowerCase().includes(filterTerm.toLowerCase())
      )
    );

    if (updateFilters) {
      updateFilters({ search: filterTerm, filtered });
    }

    return {
      success: true,
      message: `Found ${filtered.length} records matching "${filterTerm}". Data has been filtered in the dashboard.`,
      data: { filtered, filterTerm }
    };
  };

  const getRecentActivity = () => {
    const sortedData = [...volunteerData].sort((a, b) => new Date(b.date) - new Date(a.date));
    const recentRecords = sortedData.slice(0, 5);
    const lastWeekData = volunteerData.filter(record => {
      const recordDate = new Date(record.date);
      const lastWeek = new Date();
      lastWeek.setDate(lastWeek.getDate() - 7);
      return recordDate >= lastWeek;
    });

    return {
      success: true,
      message: `Recent activity: ${recentRecords.length} recent entries, ${lastWeekData.length} activities in the last week. Latest: ${recentRecords[0].assignee} worked ${recentRecords[0].hours} hours on ${recentRecords[0].project}.`,
      data: { recentRecords, lastWeekData }
    };
  };

  const getProjectStats = (projectName) => {
    if (!projectName) {
      const projects = [...new Set(volunteerData.map(record => record.project))];
      return {
        success: true,
        message: `We have ${projects.length} active projects. Top projects by participation: ${getTopProjects().slice(0, 3).join(', ')}.`,
        data: { projects }
      };
    }

    const projectData = volunteerData.filter(record => 
      record.project.toLowerCase().includes(projectName.toLowerCase())
    );

    if (projectData.length === 0) {
      return {
        success: false,
        message: `I couldn't find a project named ${projectName}.`,
        suggestions: getProjectSuggestions(projectName)
      };
    }

    const volunteers = [...new Set(projectData.map(record => record.assignee))].length;
    const totalHours = projectData.reduce((sum, record) => sum + record.hours, 0);
    const avgHoursPerSession = totalHours / projectData.length;

    return {
      success: true,
      message: `${projectName} has ${volunteers} volunteers contributing ${totalHours.toFixed(1)} hours across ${projectData.length} sessions, averaging ${avgHoursPerSession.toFixed(1)} hours per session.`,
      data: { volunteers, totalHours, sessions: projectData.length, avgHoursPerSession }
    };
  };

  // Helper functions
  const findVolunteer = (volunteerName) => {
    return volunteerData.filter(record => 
      record.assignee.toLowerCase().includes(volunteerName.toLowerCase())
    );
  };

  const getAllBranches = () => {
    return [...new Set(volunteerData.map(record => record.branch))];
  };

  const getVolunteerNameSuggestions = (searchName) => {
    const allNames = [...new Set(volunteerData.map(record => record.assignee))];
    return allNames.filter(name => 
      name.toLowerCase().includes(searchName.toLowerCase()) ||
      searchName.toLowerCase().includes(name.toLowerCase())
    ).slice(0, 3);
  };

  const getBranchSuggestions = (searchBranch) => {
    const branches = getAllBranches();
    return branches.filter(branch =>
      branch.toLowerCase().includes(searchBranch.toLowerCase()) ||
      searchBranch.toLowerCase().includes(branch.toLowerCase())
    ).slice(0, 3);
  };

  const getProjectSuggestions = (searchProject) => {
    const projects = [...new Set(volunteerData.map(record => record.project))];
    return projects.filter(project =>
      project.toLowerCase().includes(searchProject.toLowerCase()) ||
      searchProject.toLowerCase().includes(project.toLowerCase())
    ).slice(0, 3);
  };

  const getTopVolunteerForBranch = (branchData) => {
    const volunteerHours = {};
    branchData.forEach(record => {
      volunteerHours[record.assignee] = (volunteerHours[record.assignee] || 0) + record.hours;
    });
    
    const topEntry = Object.entries(volunteerHours).sort(([,a], [,b]) => b - a)[0];
    return { name: topEntry[0], hours: topEntry[1] };
  };

  const getTopProjects = () => {
    const projectCounts = {};
    volunteerData.forEach(record => {
      projectCounts[record.project] = (projectCounts[record.project] || 0) + 1;
    });
    
    return Object.entries(projectCounts)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5)
      .map(([project]) => project);
  };

  return {
    executeCommand,
    commandHistory,
    clearHistory: () => setCommandHistory([])
  };
};