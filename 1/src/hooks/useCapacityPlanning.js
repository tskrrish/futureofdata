import { useState, useCallback, useMemo } from 'react';
import { EVENT_CAPACITY_DATA, STAFF_AVAILABILITY } from '../data/eventCapacityData';
import { optimizeStaffAssignment, generateStaffingRecommendations, predictCapacityNeeds } from '../utils/staffOptimization';

export const useCapacityPlanning = () => {
  const [events, setEvents] = useState(EVENT_CAPACITY_DATA);
  const [staff, setStaff] = useState(STAFF_AVAILABILITY);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const optimizedEvents = useMemo(() => {
    return optimizeStaffAssignment(events, staff);
  }, [events, staff]);

  const addEvent = useCallback((eventData) => {
    const newEvent = {
      ...eventData,
      id: `event-${Date.now()}`,
      status: 'pending',
      alertLevel: 'none'
    };
    setEvents(prev => [...prev, newEvent]);
    return newEvent;
  }, []);

  const updateEvent = useCallback((eventId, updates) => {
    setEvents(prev => prev.map(event => 
      event.id === eventId ? { ...event, ...updates } : event
    ));
  }, []);

  const deleteEvent = useCallback((eventId) => {
    setEvents(prev => prev.filter(event => event.id !== eventId));
  }, []);

  const addStaffMember = useCallback((staffData) => {
    const newStaff = {
      ...staffData,
      id: `staff-${Date.now()}`
    };
    setStaff(prev => [...prev, newStaff]);
    return newStaff;
  }, []);

  const updateStaffAvailability = useCallback((staffId, availability) => {
    setStaff(prev => prev.map(member => 
      member.id === staffId 
        ? { ...member, availability: { ...member.availability, ...availability }}
        : member
    ));
  }, []);

  const assignStaffToEvent = useCallback(async (eventId, staffId, roleType) => {
    setLoading(true);
    setError(null);
    
    try {
      const event = events.find(e => e.id === eventId);
      const staffMember = staff.find(s => s.id === staffId);
      
      if (!event || !staffMember) {
        throw new Error('Event or staff member not found');
      }
      
      if (!staffMember.roles.includes(roleType)) {
        throw new Error(`Staff member is not qualified for role: ${roleType}`);
      }
      
      const eventDate = event.date;
      if (!staffMember.availability[eventDate]?.available) {
        throw new Error('Staff member is not available on this date');
      }
      
      updateEvent(eventId, {
        requiredStaffRoles: event.requiredStaffRoles.map(role => 
          role.role === roleType 
            ? { ...role, assigned: role.assigned + 1 }
            : role
        )
      });
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [events, staff, updateEvent]);

  const getEventRecommendations = useCallback((eventId) => {
    const event = optimizedEvents.find(e => e.id === eventId);
    return event ? generateStaffingRecommendations(event) : [];
  }, [optimizedEvents]);

  const getCapacityPredictions = useCallback((historicalData = []) => {
    return predictCapacityNeeds(optimizedEvents, historicalData);
  }, [optimizedEvents]);

  const getStaffUtilization = useMemo(() => {
    const utilization = staff.map(member => {
      const assignedHours = member.totalHoursThisWeek;
      const maxHours = member.maxHoursPerDay * 5;
      const utilizationRate = maxHours > 0 ? assignedHours / maxHours : 0;
      
      return {
        ...member,
        assignedHours,
        maxHours,
        utilizationRate,
        availableDays: Object.keys(member.availability).filter(
          date => member.availability[date].available
        ).length
      };
    });
    
    return utilization.sort((a, b) => b.utilizationRate - a.utilizationRate);
  }, [staff]);

  const getEventsByStatus = useMemo(() => {
    const statusCounts = optimizedEvents.reduce((acc, event) => {
      acc[event.status] = (acc[event.status] || 0) + 1;
      return acc;
    }, {});
    
    return {
      statusCounts,
      total: optimizedEvents.length,
      critical: optimizedEvents.filter(e => e.alertLevel === 'critical').length,
      high: optimizedEvents.filter(e => e.alertLevel === 'high').length
    };
  }, [optimizedEvents]);

  const exportCapacityReport = useCallback(() => {
    const report = {
      generatedAt: new Date().toISOString(),
      summary: getEventsByStatus,
      events: optimizedEvents.map(event => ({
        id: event.id,
        name: event.name,
        branch: event.branch,
        date: event.date,
        status: event.status,
        alertLevel: event.alertLevel,
        staffingRatio: event.staffingRatio,
        recommendations: getEventRecommendations(event.id)
      })),
      staffUtilization: getStaffUtilization
    };
    
    return report;
  }, [optimizedEvents, getEventsByStatus, getEventRecommendations, getStaffUtilization]);

  return {
    events: optimizedEvents,
    staff,
    loading,
    error,
    addEvent,
    updateEvent,
    deleteEvent,
    addStaffMember,
    updateStaffAvailability,
    assignStaffToEvent,
    getEventRecommendations,
    getCapacityPredictions,
    getStaffUtilization,
    getEventsByStatus,
    exportCapacityReport
  };
};