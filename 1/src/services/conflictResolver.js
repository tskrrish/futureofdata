export class ConflictResolver {
  constructor(options = {}) {
    this.strategy = options.strategy || 'latest_wins';
    this.customResolver = options.customResolver;
    this.conflictLog = [];
  }

  resolveConflicts(localChanges, remoteChanges, strategy = this.strategy) {
    const resolution = {
      resolved: [],
      conflicts: [],
      strategy: strategy,
      timestamp: new Date().toISOString()
    };

    // Find overlapping changes (conflicts)
    const localIds = new Set(localChanges.map(change => change.id));
    const remoteIds = new Set(remoteChanges.map(change => change.id));
    const conflictIds = new Set([...localIds].filter(id => remoteIds.has(id)));

    // Resolve conflicts based on strategy
    conflictIds.forEach(id => {
      const localChange = localChanges.find(c => c.id === id);
      const remoteChange = remoteChanges.find(c => c.id === id);
      
      const conflict = {
        id,
        local: localChange,
        remote: remoteChange,
        resolved: null,
        strategy: strategy
      };

      conflict.resolved = this.resolveConflict(localChange, remoteChange, strategy);
      
      if (conflict.resolved) {
        resolution.resolved.push(conflict);
      } else {
        resolution.conflicts.push(conflict);
      }
    });

    // Add non-conflicting changes
    localChanges.forEach(change => {
      if (!conflictIds.has(change.id)) {
        resolution.resolved.push({
          id: change.id,
          local: change,
          remote: null,
          resolved: change,
          strategy: 'local_only'
        });
      }
    });

    remoteChanges.forEach(change => {
      if (!conflictIds.has(change.id)) {
        resolution.resolved.push({
          id: change.id,
          local: null,
          remote: change,
          resolved: change,
          strategy: 'remote_only'
        });
      }
    });

    // Log conflicts for analysis
    this.logConflicts(resolution.conflicts);

    return resolution;
  }

  resolveConflict(localChange, remoteChange, strategy) {
    switch (strategy) {
      case 'latest_wins':
        return this.resolveLatestWins(localChange, remoteChange);
      
      case 'remote_wins':
        return remoteChange;
      
      case 'local_wins':
        return localChange;
      
      case 'merge_fields':
        return this.mergeFields(localChange, remoteChange);
      
      case 'hours_sum':
        return this.resolveHoursSum(localChange, remoteChange);
      
      case 'custom':
        return this.customResolver ? 
          this.customResolver(localChange, remoteChange) : 
          this.resolveLatestWins(localChange, remoteChange);
      
      default:
        return this.resolveLatestWins(localChange, remoteChange);
    }
  }

  resolveLatestWins(localChange, remoteChange) {
    // Compare timestamps if available
    const localTimestamp = this.extractTimestamp(localChange);
    const remoteTimestamp = this.extractTimestamp(remoteChange);
    
    if (localTimestamp && remoteTimestamp) {
      return localTimestamp > remoteTimestamp ? localChange : remoteChange;
    }
    
    // Fallback to remote wins if no timestamps
    return remoteChange;
  }

  mergeFields(localChange, remoteChange) {
    // Intelligent field merging for volunteer data
    const merged = { ...remoteChange };
    
    // Merge strategy per field type
    const mergeStrategies = {
      hours: 'sum', // Sum hours if different
      assignee: 'remote', // Remote wins for assignee
      date: 'latest', // Latest date
      project: 'remote', // Remote wins for project info
      branch: 'remote', // Remote wins for branch
      is_member: 'local' // Local wins for member status
    };

    Object.keys(mergeStrategies).forEach(field => {
      const strategy = mergeStrategies[field];
      const localValue = localChange.data?.[field];
      const remoteValue = remoteChange.data?.[field];
      
      if (localValue !== undefined && remoteValue !== undefined) {
        switch (strategy) {
          case 'sum':
            if (field === 'hours') {
              merged.data[field] = (parseFloat(localValue) || 0) + (parseFloat(remoteValue) || 0);
            }
            break;
          case 'latest':
            if (field === 'date') {
              const localDate = new Date(localValue);
              const remoteDate = new Date(remoteValue);
              merged.data[field] = localDate > remoteDate ? localValue : remoteValue;
            }
            break;
          case 'local':
            merged.data[field] = localValue;
            break;
          case 'remote':
          default:
            merged.data[field] = remoteValue;
            break;
        }
      }
    });

    return merged;
  }

  resolveHoursSum(localChange, remoteChange) {
    // Special strategy for summing hours when conflicts occur
    const resolved = { ...remoteChange };
    
    if (localChange.data?.hours && remoteChange.data?.hours) {
      const localHours = parseFloat(localChange.data.hours) || 0;
      const remoteHours = parseFloat(remoteChange.data.hours) || 0;
      resolved.data.hours = localHours + remoteHours;
    }
    
    return resolved;
  }

  extractTimestamp(change) {
    // Try to extract timestamp from various sources
    if (change.timestamp) return new Date(change.timestamp);
    if (change.data?.date) return new Date(change.data.date);
    if (change.data?.modified_date) return new Date(change.data.modified_date);
    return null;
  }

  logConflicts(conflicts) {
    conflicts.forEach(conflict => {
      this.conflictLog.push({
        ...conflict,
        timestamp: new Date().toISOString()
      });
    });

    // Keep only recent conflicts (last 100)
    if (this.conflictLog.length > 100) {
      this.conflictLog = this.conflictLog.slice(-100);
    }
  }

  getConflictHistory() {
    return [...this.conflictLog];
  }

  getConflictStats() {
    const stats = {
      totalConflicts: this.conflictLog.length,
      recentConflicts: this.conflictLog.filter(c => 
        new Date(c.timestamp) > new Date(Date.now() - 24 * 60 * 60 * 1000)
      ).length,
      strategiesUsed: {}
    };

    this.conflictLog.forEach(conflict => {
      const strategy = conflict.strategy || 'unknown';
      stats.strategiesUsed[strategy] = (stats.strategiesUsed[strategy] || 0) + 1;
    });

    return stats;
  }

  // Validate resolved data
  validateResolution(resolvedData) {
    const validation = {
      isValid: true,
      errors: [],
      warnings: []
    };

    resolvedData.forEach((item, index) => {
      if (!item.resolved?.data) {
        validation.errors.push(`Item ${index}: Missing resolved data`);
        validation.isValid = false;
        return;
      }

      const data = item.resolved.data;

      // Validate required fields for volunteer data
      const requiredFields = ['assignee', 'hours', 'date'];
      requiredFields.forEach(field => {
        if (!data[field]) {
          validation.warnings.push(`Item ${index}: Missing ${field}`);
        }
      });

      // Validate data types
      if (data.hours && isNaN(parseFloat(data.hours))) {
        validation.errors.push(`Item ${index}: Invalid hours value`);
        validation.isValid = false;
      }

      if (data.date && isNaN(new Date(data.date).getTime())) {
        validation.warnings.push(`Item ${index}: Invalid date format`);
      }
    });

    return validation;
  }

  // Clear conflict history
  clearHistory() {
    this.conflictLog = [];
  }

  // Set custom resolver function
  setCustomResolver(resolverFunction) {
    this.customResolver = resolverFunction;
  }
}