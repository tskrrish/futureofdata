import React, { useState, useEffect } from 'react';
import { AlertTriangle, TrendingUp, Users, Calendar, Download, Bell, BellOff, Filter, X } from 'lucide-react';
import { useCapacityPlanning } from '../../hooks/useCapacityPlanning';
import { useCapacityAlerts } from '../../hooks/useCapacityAlerts';
import { EventCard } from '../capacity/EventCard';
import { CapacityAlert } from '../capacity/CapacityAlert';
import { StaffUtilizationChart } from '../capacity/StaffUtilizationChart';
import { exportCSV } from '../../utils/csvUtils';

export const CapacityTab = () => {
  const {
    events,
    staff,
    loading,
    getEventRecommendations,
    getStaffUtilization,
    getEventsByStatus,
    exportCapacityReport,
    assignStaffToEvent
  } = useCapacityPlanning();

  const [enableNotifications, setEnableNotifications] = useState(false);
  const {
    alerts,
    totalAlertsCount,
    dismissAlert,
    clearAllAlerts
  } = useCapacityAlerts(events, enableNotifications);

  const [filters, setFilters] = useState({
    branch: 'All',
    status: 'All',
    alertLevel: 'All'
  });
  const [showFilters, setShowFilters] = useState(false);

  const eventStats = getEventsByStatus();
  const staffUtilization = getStaffUtilization();

  const filteredEvents = events.filter(event => {
    if (filters.branch !== 'All' && event.branch !== filters.branch) return false;
    if (filters.status !== 'All' && event.status !== filters.status) return false;
    if (filters.alertLevel !== 'All' && event.alertLevel !== filters.alertLevel) return false;
    return true;
  });

  const branches = [...new Set(events.map(e => e.branch))];
  const statuses = ['optimal', 'understaffed', 'critically_understaffed', 'overstaffed'];
  const alertLevels = ['none', 'low', 'medium', 'high', 'critical'];

  useEffect(() => {
    if ('Notification' in window && enableNotifications) {
      Notification.requestPermission();
    }
  }, [enableNotifications]);

  const handleExportReport = () => {
    const report = exportCapacityReport();
    const csvData = report.events.map(event => ({
      'Event Name': event.name,
      'Branch': event.branch,
      'Date': event.date,
      'Status': event.status,
      'Alert Level': event.alertLevel,
      'Staffing Ratio': `${Math.round(event.staffingRatio * 100)}%`,
      'Recommendations': event.recommendations.map(r => r.type === 'shortage' 
        ? `Need ${r.shortage} ${r.role}` 
        : `Excess ${r.excess} ${r.role}`
      ).join('; ')
    }));
    
    exportCSV('capacity_planning_report.csv', csvData);
  };

  const handleStaffAssignment = async (eventId, roleType) => {
    try {
      await assignStaffToEvent(eventId, 'staff-001', roleType);
    } catch (error) {
      console.error('Failed to assign staff:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with Stats */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-2xl font-bold text-gray-900">Event Capacity Planning</h2>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setEnableNotifications(!enableNotifications)}
              className={`p-2 rounded-lg ${enableNotifications ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600'}`}
              title={enableNotifications ? 'Disable notifications' : 'Enable notifications'}
            >
              {enableNotifications ? <Bell className="w-4 h-4" /> : <BellOff className="w-4 h-4" />}
            </button>
            {totalAlertsCount > 0 && (
              <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs font-medium">
                {totalAlertsCount} alerts
              </span>
            )}
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-md text-sm"
          >
            <Filter className="w-4 h-4" />
            Filters
          </button>
          <button
            onClick={handleExportReport}
            className="flex items-center gap-2 px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white rounded-md text-sm"
          >
            <Download className="w-4 h-4" />
            Export Report
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Events</p>
              <p className="text-2xl font-bold text-gray-900">{eventStats.total}</p>
            </div>
            <Calendar className="w-8 h-8 text-blue-500" />
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Critical Alerts</p>
              <p className="text-2xl font-bold text-red-600">{eventStats.critical}</p>
            </div>
            <AlertTriangle className="w-8 h-8 text-red-500" />
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Staff Utilization</p>
              <p className="text-2xl font-bold text-gray-900">
                {Math.round(staffUtilization.reduce((sum, s) => sum + s.utilizationRate, 0) / staffUtilization.length * 100)}%
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-green-500" />
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Available Staff</p>
              <p className="text-2xl font-bold text-gray-900">{staff.length}</p>
            </div>
            <Users className="w-8 h-8 text-blue-500" />
          </div>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="bg-white p-4 rounded-lg border">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium">Filters</h3>
            <button
              onClick={() => setShowFilters(false)}
              className="p-1 hover:bg-gray-100 rounded"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Branch</label>
              <select
                value={filters.branch}
                onChange={(e) => setFilters(prev => ({ ...prev, branch: e.target.value }))}
                className="w-full p-2 border rounded-md"
              >
                <option value="All">All Branches</option>
                {branches.map(branch => (
                  <option key={branch} value={branch}>{branch}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Status</label>
              <select
                value={filters.status}
                onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                className="w-full p-2 border rounded-md"
              >
                <option value="All">All Statuses</option>
                {statuses.map(status => (
                  <option key={status} value={status}>
                    {status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Alert Level</label>
              <select
                value={filters.alertLevel}
                onChange={(e) => setFilters(prev => ({ ...prev, alertLevel: e.target.value }))}
                className="w-full p-2 border rounded-md"
              >
                <option value="All">All Alert Levels</option>
                {alertLevels.map(level => (
                  <option key={level} value={level}>
                    {level.replace(/\b\w/g, l => l.toUpperCase())}
                  </option>
                ))}
              </select>
            </div>
          </div>
          
          <button
            onClick={() => setFilters({ branch: 'All', status: 'All', alertLevel: 'All' })}
            className="mt-3 px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
          >
            Clear Filters
          </button>
        </div>
      )}

      {/* Alerts Section */}
      {alerts.length > 0 && (
        <div className="bg-white p-4 rounded-lg border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Active Alerts ({alerts.length})</h3>
            <button
              onClick={clearAllAlerts}
              className="text-sm text-gray-600 hover:text-gray-800"
            >
              Dismiss All
            </button>
          </div>
          
          <div className="space-y-3">
            {alerts.slice(0, 3).map(alert => (
              <CapacityAlert
                key={alert.id}
                alert={alert}
                onDismiss={dismissAlert}
              />
            ))}
            {alerts.length > 3 && (
              <p className="text-sm text-gray-500 text-center">
                And {alerts.length - 3} more alerts...
              </p>
            )}
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <StaffUtilizationChart staffUtilization={staffUtilization} />
        
        <div className="bg-white p-4 rounded-lg border">
          <h3 className="font-semibold text-gray-900 mb-4">Event Status Breakdown</h3>
          <div className="space-y-3">
            {Object.entries(eventStats.statusCounts).map(([status, count]) => (
              <div key={status} className="flex items-center justify-between">
                <span className="text-sm capitalize">{status.replace('_', ' ')}</span>
                <div className="flex items-center gap-2">
                  <div className="w-24 bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        status === 'optimal' ? 'bg-green-500' :
                        status === 'understaffed' ? 'bg-yellow-500' :
                        status === 'critically_understaffed' ? 'bg-red-500' :
                        'bg-blue-500'
                      }`}
                      style={{ width: `${(count / eventStats.total) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium w-8">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Events Grid */}
      <div className="space-y-4">
        <h3 className="font-semibold text-gray-900">
          Events ({filteredEvents.length})
          {filters.branch !== 'All' || filters.status !== 'All' || filters.alertLevel !== 'All' ? 
            ' - Filtered' : ''
          }
        </h3>
        
        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
        ) : filteredEvents.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No events match the selected filters.
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {filteredEvents.map(event => (
              <EventCard
                key={event.id}
                event={event}
                recommendations={getEventRecommendations(event.id)}
                onAssignStaff={handleStaffAssignment}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};