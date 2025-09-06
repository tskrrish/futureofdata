import { useState, useEffect, useMemo } from "react";

// API base URL - adjust as needed
const API_BASE = "http://localhost:8000/api";

/**
 * Custom hook for managing resource assignment data
 * Provides CRUD operations and state management for shifts, resources, and assignments
 */
export function useResourceData() {
  const [shifts, setShifts] = useState([]);
  const [resources, setResources] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [usageLogs, setUsageLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // API helper function
  const apiCall = async (endpoint, options = {}) => {
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`API call failed for ${endpoint}:`, error);
      throw error;
    }
  };

  // Fetch all data
  const fetchAllData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [shiftsData, resourcesData, assignmentsData] = await Promise.all([
        apiCall('/shifts'),
        apiCall('/resources'),
        apiCall('/assignments')
      ]);
      
      setShifts(shiftsData.data || []);
      setResources(resourcesData.data || []);
      setAssignments(assignmentsData.data || []);
    } catch (error) {
      setError('Failed to load data');
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Initial data load
  useEffect(() => {
    fetchAllData();
  }, []);

  // Shifts operations
  const createShift = async (shiftData) => {
    try {
      setLoading(true);
      const response = await apiCall('/shifts', {
        method: 'POST',
        body: JSON.stringify(shiftData),
      });
      
      if (response.success) {
        setShifts(prev => [...prev, response.data]);
        return response.data;
      }
      throw new Error('Failed to create shift');
    } catch (error) {
      setError('Failed to create shift');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const updateShift = async (shiftId, updates) => {
    try {
      setLoading(true);
      const response = await apiCall(`/shifts/${shiftId}`, {
        method: 'PUT',
        body: JSON.stringify(updates),
      });
      
      if (response.success) {
        setShifts(prev => prev.map(shift => 
          shift.id === shiftId ? { ...shift, ...updates } : shift
        ));
        return true;
      }
      throw new Error('Failed to update shift');
    } catch (error) {
      setError('Failed to update shift');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Resources operations
  const createResource = async (resourceData) => {
    try {
      setLoading(true);
      const response = await apiCall('/resources', {
        method: 'POST',
        body: JSON.stringify(resourceData),
      });
      
      if (response.success) {
        setResources(prev => [...prev, response.data]);
        return response.data;
      }
      throw new Error('Failed to create resource');
    } catch (error) {
      setError('Failed to create resource');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const updateResource = async (resourceId, updates) => {
    try {
      setLoading(true);
      const response = await apiCall(`/resources/${resourceId}`, {
        method: 'PUT',
        body: JSON.stringify(updates),
      });
      
      if (response.success) {
        setResources(prev => prev.map(resource => 
          resource.id === resourceId ? { ...resource, ...updates } : resource
        ));
        return true;
      }
      throw new Error('Failed to update resource');
    } catch (error) {
      setError('Failed to update resource');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Assignment operations
  const createAssignment = async (assignmentData) => {
    try {
      setLoading(true);
      const response = await apiCall('/assignments', {
        method: 'POST',
        body: JSON.stringify(assignmentData),
      });
      
      if (response.success) {
        setAssignments(prev => [...prev, response.data]);
        await fetchAllData(); // Refresh to get updated relationships
        return response.data;
      }
      throw new Error('Failed to create assignment');
    } catch (error) {
      setError('Failed to create assignment');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const updateAssignmentStatus = async (assignmentId, statusData) => {
    try {
      setLoading(true);
      const response = await apiCall(`/assignments/${assignmentId}/status`, {
        method: 'PUT',
        body: JSON.stringify(statusData),
      });
      
      if (response.success) {
        setAssignments(prev => prev.map(assignment => 
          assignment.id === assignmentId 
            ? { ...assignment, status: statusData.status, ...statusData } 
            : assignment
        ));
        return true;
      }
      throw new Error('Failed to update assignment status');
    } catch (error) {
      setError('Failed to update assignment status');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Usage logs
  const fetchUsageLogs = async (filters = {}) => {
    try {
      setLoading(true);
      const params = new URLSearchParams(filters).toString();
      const response = await apiCall(`/usage-logs${params ? `?${params}` : ''}`);
      setUsageLogs(response.data || []);
      return response.data || [];
    } catch (error) {
      setError('Failed to fetch usage logs');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Analytics
  const fetchUtilizationStats = async (dateRange = null) => {
    try {
      setLoading(true);
      const params = dateRange 
        ? new URLSearchParams({
            start_date: dateRange.start,
            end_date: dateRange.end
          }).toString()
        : '';
      const response = await apiCall(`/analytics/utilization${params ? `?${params}` : ''}`);
      return response.data || {};
    } catch (error) {
      setError('Failed to fetch utilization stats');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Computed values
  const stats = useMemo(() => {
    const totalResources = resources.length;
    const availableResources = resources.filter(r => r.status === 'available').length;
    const activeShifts = shifts.filter(s => s.status === 'active' || s.status === 'scheduled').length;
    const activeAssignments = assignments.filter(a => 
      a.status === 'assigned' || a.status === 'checked_out' || a.status === 'in_use'
    ).length;

    const utilizationRate = totalResources > 0 
      ? ((totalResources - availableResources) / totalResources * 100).toFixed(1)
      : 0;

    return {
      totalResources,
      availableResources,
      activeShifts,
      activeAssignments,
      utilizationRate
    };
  }, [resources, shifts, assignments]);

  // Filter functions
  const getResourcesByBranch = (branch) => {
    return resources.filter(r => r.branch === branch);
  };

  const getShiftsByBranch = (branch) => {
    return shifts.filter(s => s.branch === branch);
  };

  const getAssignmentsByShift = (shiftId) => {
    return assignments.filter(a => a.shift_id === shiftId);
  };

  const getAssignmentsByResource = (resourceId) => {
    return assignments.filter(a => a.resource_id === resourceId);
  };

  // Get unique branches
  const branches = useMemo(() => {
    const branchSet = new Set([
      ...resources.map(r => r.branch),
      ...shifts.map(s => s.branch)
    ]);
    return ['All', ...Array.from(branchSet).sort()];
  }, [resources, shifts]);

  return {
    // Data
    shifts,
    resources,
    assignments,
    usageLogs,
    branches,
    stats,
    
    // State
    loading,
    error,
    
    // Operations
    createShift,
    updateShift,
    createResource,
    updateResource,
    createAssignment,
    updateAssignmentStatus,
    fetchUsageLogs,
    fetchUtilizationStats,
    fetchAllData,
    
    // Filters
    getResourcesByBranch,
    getShiftsByBranch,
    getAssignmentsByShift,
    getAssignmentsByResource,
  };
}