import { useState, useEffect, useMemo } from 'react';
import { ALERT_LEVELS } from '../data/eventCapacityData';
import { calculateStaffingRatio, determineEventStatus, calculateAlertLevel } from '../utils/staffOptimization';

export const useCapacityAlerts = (events, enableNotifications = true) => {
  const [alerts, setAlerts] = useState([]);
  const [dismissedAlerts, setDismissedAlerts] = useState(new Set());

  const processedEvents = useMemo(() => {
    return events.map(event => {
      const staffingRatio = calculateStaffingRatio(event.requiredStaffRoles, event.requiredStaffRoles);
      const status = determineEventStatus(staffingRatio);
      const alertLevel = calculateAlertLevel(status, staffingRatio);
      
      return {
        ...event,
        staffingRatio,
        status,
        alertLevel
      };
    });
  }, [events]);

  const activeAlerts = useMemo(() => {
    const newAlerts = [];
    
    processedEvents.forEach(event => {
      if (event.alertLevel !== 'none' && !dismissedAlerts.has(event.id)) {
        const shortage = event.requiredStaffRoles.reduce((total, role) => 
          total + Math.max(0, role.required - role.assigned), 0
        );
        
        newAlerts.push({
          id: `alert-${event.id}`,
          eventId: event.id,
          eventName: event.name,
          branch: event.branch,
          date: event.date,
          alertLevel: event.alertLevel,
          status: event.status,
          staffingRatio: event.staffingRatio,
          shortage,
          message: generateAlertMessage(event, shortage),
          priority: ALERT_LEVELS[event.alertLevel].priority,
          timestamp: new Date().toISOString()
        });
      }
    });
    
    return newAlerts.sort((a, b) => b.priority - a.priority);
  }, [processedEvents, dismissedAlerts]);

  const criticalAlertsCount = useMemo(() => {
    return activeAlerts.filter(alert => alert.alertLevel === 'critical').length;
  }, [activeAlerts]);

  const highAlertsCount = useMemo(() => {
    return activeAlerts.filter(alert => alert.alertLevel === 'high').length;
  }, [activeAlerts]);

  const dismissAlert = (alertId) => {
    setDismissedAlerts(prev => new Set([...prev, alertId]));
  };

  const clearAllAlerts = () => {
    const allAlertIds = activeAlerts.map(alert => alert.eventId);
    setDismissedAlerts(prev => new Set([...prev, ...allAlertIds]));
  };

  useEffect(() => {
    if (enableNotifications && 'Notification' in window) {
      const criticalAlerts = activeAlerts.filter(alert => 
        alert.alertLevel === 'critical' && 
        !alerts.some(existing => existing.id === alert.id)
      );
      
      criticalAlerts.forEach(alert => {
        if (Notification.permission === 'granted') {
          new Notification(`Critical Staffing Alert: ${alert.eventName}`, {
            body: alert.message,
            icon: '/vite.svg',
            tag: alert.id
          });
        }
      });
    }
    
    setAlerts(activeAlerts);
  }, [activeAlerts, enableNotifications, alerts]);

  return {
    alerts: activeAlerts,
    criticalAlertsCount,
    highAlertsCount,
    totalAlertsCount: activeAlerts.length,
    dismissAlert,
    clearAllAlerts,
    processedEvents
  };
};

const generateAlertMessage = (event, shortage) => {
  const messages = {
    critically_understaffed: `${event.name} is critically understaffed with ${shortage} staff shortage. Immediate action required.`,
    understaffed: `${event.name} needs ${shortage} additional staff member${shortage > 1 ? 's' : ''}.`,
    overstaffed: `${event.name} has excess staff assigned. Consider reallocating resources.`,
    optimal: `${event.name} has optimal staffing levels.`
  };
  
  return messages[event.status] || 'Staffing status unknown';
};