class VoiceQueryProcessor {
  constructor(volunteerData) {
    this.volunteerData = volunteerData;
    this.commandPatterns = this.initializeCommandPatterns();
  }

  initializeCommandPatterns() {
    return [
      {
        patterns: [
          /show me.*hours.*for\s+(.+)/i,
          /how many hours.*did\s+(.+)\s+work/i,
          /(.+)\s+hours/i,
          /hours for\s+(.+)/i
        ],
        intent: 'get_volunteer_hours',
        extractEntity: (match) => match[1]?.trim()
      },
      {
        patterns: [
          /who.*worked.*at\s+(.+)/i,
          /volunteers.*at\s+(.+)/i,
          /show me.*(.+)\s+branch/i,
          /(.+)\s+volunteers/i
        ],
        intent: 'get_branch_volunteers',
        extractEntity: (match) => match[1]?.trim()
      },
      {
        patterns: [
          /total.*hours/i,
          /how many.*hours.*total/i,
          /overall.*hours/i,
          /sum.*hours/i
        ],
        intent: 'get_total_hours',
        extractEntity: () => null
      },
      {
        patterns: [
          /active.*volunteers/i,
          /how many.*volunteers/i,
          /volunteer.*count/i,
          /number.*volunteers/i
        ],
        intent: 'get_volunteer_count',
        extractEntity: () => null
      },
      {
        patterns: [
          /top.*volunteers/i,
          /best.*volunteers/i,
          /leading.*volunteers/i,
          /most.*hours/i,
          /leaderboard/i
        ],
        intent: 'get_top_volunteers',
        extractEntity: () => null
      },
      {
        patterns: [
          /projects.*for\s+(.+)/i,
          /what.*projects.*(.+)/i,
          /(.+)\s+projects/i,
          /show.*projects.*(.+)/i
        ],
        intent: 'get_volunteer_projects',
        extractEntity: (match) => match[1]?.trim()
      },
      {
        patterns: [
          /branches/i,
          /all.*branches/i,
          /list.*branches/i,
          /show.*branches/i
        ],
        intent: 'list_branches',
        extractEntity: () => null
      },
      {
        patterns: [
          /update.*hours.*for\s+(.+)\s+to\s+(\d+)/i,
          /set.*(.+)\s+hours.*to\s+(\d+)/i,
          /change.*(.+)\s+hours.*(\d+)/i
        ],
        intent: 'update_volunteer_hours',
        extractEntity: (match) => ({
          volunteer: match[1]?.trim(),
          hours: parseInt(match[2])
        })
      },
      {
        patterns: [
          /add.*volunteer.*(.+)/i,
          /new.*volunteer.*(.+)/i,
          /create.*volunteer.*(.+)/i
        ],
        intent: 'add_volunteer',
        extractEntity: (match) => match[1]?.trim()
      },
      {
        patterns: [
          /filter.*by\s+(.+)/i,
          /show.*only\s+(.+)/i,
          /search.*for\s+(.+)/i
        ],
        intent: 'filter_data',
        extractEntity: (match) => match[1]?.trim()
      }
    ];
  }

  processQuery(transcript) {
    const cleanTranscript = transcript.toLowerCase().trim();
    
    for (const command of this.commandPatterns) {
      for (const pattern of command.patterns) {
        const match = cleanTranscript.match(pattern);
        if (match) {
          const entity = command.extractEntity(match);
          return {
            intent: command.intent,
            entity,
            originalText: transcript,
            confidence: this.calculateConfidence(match, pattern)
          };
        }
      }
    }
    
    return {
      intent: 'unknown',
      entity: null,
      originalText: transcript,
      confidence: 0
    };
  }

  calculateConfidence(match, pattern) {
    // Simple confidence calculation based on match quality
    const matchLength = match[0].length;
    const totalLength = match.input.length;
    return Math.min(0.9, matchLength / totalLength * 1.2);
  }

  executeQuery(query) {
    switch (query.intent) {
      case 'get_volunteer_hours':
        return this.getVolunteerHours(query.entity);
      
      case 'get_branch_volunteers':
        return this.getBranchVolunteers(query.entity);
      
      case 'get_total_hours':
        return this.getTotalHours();
      
      case 'get_volunteer_count':
        return this.getVolunteerCount();
      
      case 'get_top_volunteers':
        return this.getTopVolunteers();
      
      case 'get_volunteer_projects':
        return this.getVolunteerProjects(query.entity);
      
      case 'list_branches':
        return this.listBranches();
      
      case 'filter_data':
        return this.filterData(query.entity);
      
      default:
        return {
          success: false,
          message: "I didn't understand that command. Try asking about volunteer hours, branches, or projects."
        };
    }
  }

  getVolunteerHours(volunteerName) {
    if (!volunteerName) {
      return {
        success: false,
        message: "Please specify which volunteer you'd like to know about."
      };
    }

    const volunteer = this.findVolunteer(volunteerName);
    if (volunteer.length === 0) {
      return {
        success: false,
        message: `I couldn't find a volunteer named ${volunteerName}.`
      };
    }

    const totalHours = volunteer.reduce((sum, record) => sum + record.hours, 0);
    const projects = volunteer.length;
    
    return {
      success: true,
      message: `${volunteerName} has worked ${totalHours.toFixed(1)} hours across ${projects} projects.`,
      data: { totalHours, projects, records: volunteer }
    };
  }

  getBranchVolunteers(branchName) {
    if (!branchName) {
      return {
        success: false,
        message: "Please specify which branch you'd like to know about."
      };
    }

    const branchData = this.volunteerData.filter(record => 
      record.branch.toLowerCase().includes(branchName.toLowerCase())
    );

    if (branchData.length === 0) {
      return {
        success: false,
        message: `I couldn't find any volunteers for ${branchName} branch.`
      };
    }

    const uniqueVolunteers = [...new Set(branchData.map(record => record.assignee))];
    const totalHours = branchData.reduce((sum, record) => sum + record.hours, 0);

    return {
      success: true,
      message: `${branchName} branch has ${uniqueVolunteers.length} volunteers who worked ${totalHours.toFixed(1)} hours total.`,
      data: { volunteers: uniqueVolunteers, totalHours, records: branchData }
    };
  }

  getTotalHours() {
    const totalHours = this.volunteerData.reduce((sum, record) => sum + record.hours, 0);
    const activeVolunteers = [...new Set(this.volunteerData.map(record => record.assignee))].length;

    return {
      success: true,
      message: `Total volunteer hours: ${totalHours.toFixed(1)} hours from ${activeVolunteers} active volunteers.`,
      data: { totalHours, activeVolunteers }
    };
  }

  getVolunteerCount() {
    const activeVolunteers = [...new Set(this.volunteerData.map(record => record.assignee))].length;
    const memberVolunteers = [...new Set(
      this.volunteerData.filter(record => record.is_member).map(record => record.assignee)
    )].length;

    return {
      success: true,
      message: `We have ${activeVolunteers} active volunteers, including ${memberVolunteers} YMCA members.`,
      data: { activeVolunteers, memberVolunteers }
    };
  }

  getTopVolunteers() {
    const volunteerHours = {};
    this.volunteerData.forEach(record => {
      volunteerHours[record.assignee] = (volunteerHours[record.assignee] || 0) + record.hours;
    });

    const topVolunteers = Object.entries(volunteerHours)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5);

    const message = `Top volunteers: ${topVolunteers.map(([name, hours]) => 
      `${name} with ${hours.toFixed(1)} hours`).join(', ')}.`;

    return {
      success: true,
      message,
      data: { topVolunteers }
    };
  }

  getVolunteerProjects(volunteerName) {
    if (!volunteerName) {
      return {
        success: false,
        message: "Please specify which volunteer you'd like to know about."
      };
    }

    const volunteer = this.findVolunteer(volunteerName);
    if (volunteer.length === 0) {
      return {
        success: false,
        message: `I couldn't find a volunteer named ${volunteerName}.`
      };
    }

    const projects = volunteer.map(record => record.project);
    const uniqueProjects = [...new Set(projects)];

    return {
      success: true,
      message: `${volunteerName} has worked on ${uniqueProjects.length} projects: ${uniqueProjects.join(', ')}.`,
      data: { projects: uniqueProjects, records: volunteer }
    };
  }

  listBranches() {
    const branches = [...new Set(this.volunteerData.map(record => record.branch))];
    
    return {
      success: true,
      message: `Available branches: ${branches.join(', ')}.`,
      data: { branches }
    };
  }

  filterData(filterTerm) {
    const filtered = this.volunteerData.filter(record => 
      Object.values(record).some(value => 
        value && value.toString().toLowerCase().includes(filterTerm.toLowerCase())
      )
    );

    return {
      success: true,
      message: `Found ${filtered.length} records matching "${filterTerm}".`,
      data: { filtered, filterTerm }
    };
  }

  findVolunteer(volunteerName) {
    return this.volunteerData.filter(record => 
      record.assignee.toLowerCase().includes(volunteerName.toLowerCase())
    );
  }

  updateData(newData) {
    this.volunteerData = newData;
  }
}

export default VoiceQueryProcessor;