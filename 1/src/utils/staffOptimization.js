import { CAPACITY_THRESHOLDS, ALERT_LEVELS } from '../data/eventCapacityData';

export const calculateStaffingRatio = (requiredStaff) => {
  const totalRequired = requiredStaff.reduce((sum, role) => sum + role.required, 0);
  const totalAssigned = requiredStaff.reduce((sum, role) => sum + role.assigned, 0);
  return totalRequired > 0 ? totalAssigned / totalRequired : 1;
};

export const determineEventStatus = (staffingRatio) => {
  if (staffingRatio < CAPACITY_THRESHOLDS.understaffed * 0.7) {
    return 'critically_understaffed';
  } else if (staffingRatio < CAPACITY_THRESHOLDS.understaffed) {
    return 'understaffed';
  } else if (staffingRatio <= CAPACITY_THRESHOLDS.overstaffed) {
    return 'optimal';
  } else {
    return 'overstaffed';
  }
};

export const calculateAlertLevel = (status, staffingRatio) => {
  switch (status) {
    case 'critically_understaffed':
      return 'critical';
    case 'understaffed':
      return staffingRatio < 0.75 ? 'high' : 'medium';
    case 'overstaffed':
      return staffingRatio > 1.3 ? 'medium' : 'low';
    default:
      return 'none';
  }
};

export const optimizeStaffAssignment = (events, staffAvailability) => {
  const optimizedEvents = [...events];
  const availableStaff = [...staffAvailability];

  optimizedEvents.forEach(event => {
    event.requiredStaffRoles.forEach(role => {
      if (role.assigned < role.required) {
        const shortage = role.required - role.assigned;
        const suitableStaff = availableStaff.filter(staff => 
          staff.roles.includes(role.role) &&
          staff.availability[event.date]?.available &&
          staff.totalHoursThisWeek < staff.maxHoursPerDay * 5
        );

        suitableStaff
          .sort((a, b) => a.totalHoursThisWeek - b.totalHoursThisWeek)
          .slice(0, shortage)
          .forEach(staff => {
            role.assigned++;
            staff.totalHoursThisWeek += calculateEventDuration(event);
          });
      }
    });

    const staffingRatio = calculateStaffingRatio(event.requiredStaffRoles, event.requiredStaffRoles);
    event.status = determineEventStatus(staffingRatio);
    event.alertLevel = calculateAlertLevel(event.status, staffingRatio);
    event.staffingRatio = staffingRatio;
  });

  return optimizedEvents;
};

export const calculateEventDuration = (event) => {
  const start = new Date(`${event.date}T${event.startTime}`);
  const end = new Date(`${event.date}T${event.endTime}`);
  return (end - start) / (1000 * 60 * 60);
};

export const generateStaffingRecommendations = (event) => {
  const recommendations = [];
  
  event.requiredStaffRoles.forEach(role => {
    if (role.assigned < role.required) {
      recommendations.push({
        type: 'shortage',
        role: role.role,
        shortage: role.required - role.assigned,
        priority: role.required - role.assigned > 2 ? 'high' : 'medium'
      });
    } else if (role.assigned > role.required) {
      recommendations.push({
        type: 'excess',
        role: role.role,
        excess: role.assigned - role.required,
        priority: 'low'
      });
    }
  });

  return recommendations;
};

export const predictCapacityNeeds = (events, historicalData = []) => {
  const predictions = {};
  
  events.forEach(event => {
    const historical = historicalData.filter(h => 
      h.category === event.category && 
      h.branch === event.branch
    );
    
    if (historical.length > 0) {
      const avgAttendanceRatio = historical.reduce((sum, h) => 
        sum + (h.actualAttendees / h.estimatedAttendees), 0
      ) / historical.length;
      
      const adjustedAttendees = Math.round(event.estimatedAttendees * avgAttendanceRatio);
      const staffingMultiplier = adjustedAttendees / event.estimatedAttendees;
      
      predictions[event.id] = {
        adjustedAttendees,
        recommendedStaffAdjustment: staffingMultiplier,
        confidence: Math.min(historical.length / 5, 1)
      };
    }
  });
  
  return predictions;
};