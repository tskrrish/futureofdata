import React, { useState, useEffect } from "react";
import { 
  Shield, 
  Clock, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  RefreshCw,
  Calendar,
  User,
  FileText,
  Bell,
  Settings
} from "lucide-react";

export function BackgroundCheckTab() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [dashboardStats, setDashboardStats] = useState({});
  const [backgroundChecks, setBackgroundChecks] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedUserId, setSelectedUserId] = useState("");

  useEffect(() => {
    loadDashboardData();
  }, [selectedUserId]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // Load dashboard stats
      const statsResponse = await fetch(`/api/background-checks/dashboard/${selectedUserId || ''}`);
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setDashboardStats(statsData.stats || {});
      }

      // Load background checks for user if selected
      if (selectedUserId) {
        const checksResponse = await fetch(`/api/background-checks/user/${selectedUserId}`);
        if (checksResponse.ok) {
          const checksData = await checksResponse.json();
          setBackgroundChecks(checksData.background_checks || []);
        }

        // Load workflows for user
        const workflowsResponse = await fetch(`/api/recheck-workflows/user/${selectedUserId}`);
        if (workflowsResponse.ok) {
          const workflowsData = await workflowsResponse.json();
          setWorkflows(workflowsData.workflows || []);
        }
      }

      // Load alerts
      const alertsResponse = await fetch('/api/background-checks/alerts');
      if (alertsResponse.ok) {
        const alertsData = await alertsResponse.json();
        setAlerts(alertsData.alerts || []);
      }

    } catch (error) {
      console.error('Error loading background check data:', error);
    }
    setLoading(false);
  };

  const processAlerts = async () => {
    try {
      const response = await fetch('/api/background-checks/process-alerts', {
        method: 'POST'
      });
      if (response.ok) {
        await loadDashboardData();
        alert('Alerts processed successfully');
      }
    } catch (error) {
      console.error('Error processing alerts:', error);
    }
  };

  const resolveAlert = async (alertId) => {
    try {
      const response = await fetch(`/api/background-checks/alerts/${alertId}/resolve`, {
        method: 'PUT'
      });
      if (response.ok) {
        await loadDashboardData();
      }
    } catch (error) {
      console.error('Error resolving alert:', error);
    }
  };

  const updateCheckStatus = async (checkId, status, result = null) => {
    try {
      const response = await fetch(`/api/background-checks/${checkId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          status, 
          result,
          completion_date: status === 'completed' ? new Date().toISOString() : null
        })
      });
      if (response.ok) {
        await loadDashboardData();
      }
    } catch (error) {
      console.error('Error updating check status:', error);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString();
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-600" />;
      case 'expired':
        return <XCircle className="w-4 h-4 text-red-600" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Clock className="w-4 h-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'expired':
        return 'bg-red-100 text-red-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const isExpiringSoon = (expirationDate) => {
    if (!expirationDate) return false;
    const expiry = new Date(expirationDate);
    const now = new Date();
    const daysUntilExpiry = (expiry - now) / (1000 * 60 * 60 * 24);
    return daysUntilExpiry <= 30 && daysUntilExpiry > 0;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-2 text-lg">Loading background check data...</span>
      </div>
    );
  }

  return (
    <div className="mt-6">
      {/* Header */}
      <div className="bg-white rounded-2xl border p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Shield className="w-8 h-8 text-blue-600" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Background Check Tracking</h2>
              <p className="text-gray-600">Manage volunteer background checks, expiration alerts, and renewal workflows</p>
            </div>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={processAlerts}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
            >
              <Bell className="w-4 h-4" />
              <span>Process Alerts</span>
            </button>
            <button
              onClick={loadDashboardData}
              className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* User Selection */}
        <div className="mt-4">
          <label htmlFor="userSelect" className="block text-sm font-medium text-gray-700 mb-2">
            Filter by User (Optional)
          </label>
          <input
            id="userSelect"
            type="text"
            placeholder="Enter User ID to filter results"
            value={selectedUserId}
            onChange={(e) => setSelectedUserId(e.target.value)}
            className="w-full max-w-md px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white rounded-2xl border mb-6">
        <div className="flex border-b">
          {[
            ['dashboard', 'Dashboard', Settings],
            ['checks', 'Background Checks', Shield],
            ['alerts', 'Alerts', AlertTriangle],
            ['workflows', 'Workflows', RefreshCw],
          ].map(([id, label, Icon]) => (
            <button
              key={id}
              className={`flex items-center space-x-2 px-6 py-3 border-b-2 ${
                activeTab === id 
                  ? 'border-blue-500 text-blue-600' 
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
              onClick={() => setActiveTab(id)}
            >
              <Icon className="w-4 h-4" />
              <span>{label}</span>
            </button>
          ))}
        </div>

        <div className="p-6">
          {/* Dashboard Tab */}
          {activeTab === 'dashboard' && (
            <div>
              <h3 className="text-lg font-semibold mb-4">Dashboard Overview</h3>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-blue-600 font-medium">Total Checks</p>
                      <p className="text-2xl font-bold text-blue-900">{dashboardStats.total_checks || 0}</p>
                    </div>
                    <Shield className="w-8 h-8 text-blue-600" />
                  </div>
                </div>
                
                <div className="bg-yellow-50 p-4 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-yellow-600 font-medium">Pending</p>
                      <p className="text-2xl font-bold text-yellow-900">{dashboardStats.pending_checks || 0}</p>
                    </div>
                    <Clock className="w-8 h-8 text-yellow-600" />
                  </div>
                </div>
                
                <div className="bg-red-50 p-4 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-red-600 font-medium">Expiring Soon</p>
                      <p className="text-2xl font-bold text-red-900">{dashboardStats.expiring_soon || 0}</p>
                    </div>
                    <AlertTriangle className="w-8 h-8 text-red-600" />
                  </div>
                </div>
                
                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-green-600 font-medium">Completed</p>
                      <p className="text-2xl font-bold text-green-900">{dashboardStats.completed_checks || 0}</p>
                    </div>
                    <CheckCircle className="w-8 h-8 text-green-600" />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-orange-50 p-4 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-orange-600 font-medium">Active Workflows</p>
                      <p className="text-2xl font-bold text-orange-900">{dashboardStats.active_workflows || 0}</p>
                    </div>
                    <RefreshCw className="w-8 h-8 text-orange-600" />
                  </div>
                </div>
                
                <div className="bg-purple-50 p-4 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-purple-600 font-medium">Pending Alerts</p>
                      <p className="text-2xl font-bold text-purple-900">{dashboardStats.pending_alerts || 0}</p>
                    </div>
                    <Bell className="w-8 h-8 text-purple-600" />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Background Checks Tab */}
          {activeTab === 'checks' && (
            <div>
              <h3 className="text-lg font-semibold mb-4">Background Checks</h3>
              
              {backgroundChecks.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  {selectedUserId ? 'No background checks found for this user.' : 'Select a user to view their background checks.'}
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full table-auto">
                    <thead>
                      <tr className="border-b bg-gray-50">
                        <th className="text-left p-3 font-medium">Check Type</th>
                        <th className="text-left p-3 font-medium">Provider</th>
                        <th className="text-left p-3 font-medium">Status</th>
                        <th className="text-left p-3 font-medium">Submitted</th>
                        <th className="text-left p-3 font-medium">Expires</th>
                        <th className="text-left p-3 font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {backgroundChecks.map((check) => (
                        <tr key={check.id} className="border-b hover:bg-gray-50">
                          <td className="p-3">
                            <span className="capitalize font-medium">{check.check_type}</span>
                          </td>
                          <td className="p-3">
                            <span className="text-gray-600">{check.check_provider || 'N/A'}</span>
                          </td>
                          <td className="p-3">
                            <div className="flex items-center space-x-2">
                              {getStatusIcon(check.status)}
                              <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(check.status)}`}>
                                {check.status}
                              </span>
                              {isExpiringSoon(check.expiration_date) && (
                                <AlertTriangle className="w-4 h-4 text-orange-500" title="Expiring Soon" />
                              )}
                            </div>
                          </td>
                          <td className="p-3 text-gray-600">
                            {formatDate(check.submission_date)}
                          </td>
                          <td className="p-3 text-gray-600">
                            {formatDate(check.expiration_date)}
                          </td>
                          <td className="p-3">
                            {check.status === 'pending' && (
                              <div className="flex space-x-2">
                                <button
                                  onClick={() => updateCheckStatus(check.id, 'completed', 'clear')}
                                  className="text-green-600 hover:text-green-800 text-sm"
                                >
                                  Mark Clear
                                </button>
                                <button
                                  onClick={() => updateCheckStatus(check.id, 'failed', 'disqualified')}
                                  className="text-red-600 hover:text-red-800 text-sm"
                                >
                                  Mark Failed
                                </button>
                              </div>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Alerts Tab */}
          {activeTab === 'alerts' && (
            <div>
              <h3 className="text-lg font-semibold mb-4">Background Check Alerts</h3>
              
              {alerts.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No pending alerts.</p>
              ) : (
                <div className="space-y-3">
                  {alerts.map((alert) => (
                    <div key={alert.id} className="border rounded-lg p-4 bg-white shadow-sm">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <AlertTriangle className="w-5 h-5 text-orange-500" />
                            <span className="font-medium capitalize">{alert.alert_type.replace('_', ' ')}</span>
                            <span className="text-gray-500 text-sm">
                              {formatDate(alert.alert_date)}
                            </span>
                          </div>
                          
                          {alert.background_checks && (
                            <div className="text-sm text-gray-600 mb-2">
                              <p><strong>User:</strong> {alert.background_checks.users?.first_name} {alert.background_checks.users?.last_name}</p>
                              <p><strong>Check Type:</strong> {alert.background_checks.check_type}</p>
                              <p><strong>Expiration:</strong> {formatDate(alert.background_checks.expiration_date)}</p>
                            </div>
                          )}
                          
                          {alert.notes && (
                            <p className="text-sm text-gray-700">{alert.notes}</p>
                          )}
                        </div>
                        
                        <button
                          onClick={() => resolveAlert(alert.id)}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                        >
                          Resolve
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Workflows Tab */}
          {activeTab === 'workflows' && (
            <div>
              <h3 className="text-lg font-semibold mb-4">Re-check Workflows</h3>
              
              {workflows.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  {selectedUserId ? 'No workflows found for this user.' : 'Select a user to view their workflows.'}
                </p>
              ) : (
                <div className="space-y-3">
                  {workflows.map((workflow) => (
                    <div key={workflow.id} className="border rounded-lg p-4 bg-white shadow-sm">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <RefreshCw className="w-5 h-5 text-blue-500" />
                            <span className="font-medium">Workflow #{workflow.id.slice(0, 8)}</span>
                            <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(workflow.workflow_status)}`}>
                              {workflow.workflow_status}
                            </span>
                          </div>
                          
                          <div className="text-sm text-gray-600 mb-2">
                            <p><strong>Initiated:</strong> {formatDate(workflow.created_at)}</p>
                            <p><strong>Due Date:</strong> {formatDate(workflow.due_date)}</p>
                            <p><strong>Initiated By:</strong> {workflow.initiated_by}</p>
                            {workflow.reminder_count > 0 && (
                              <p><strong>Reminders Sent:</strong> {workflow.reminder_count}</p>
                            )}
                          </div>
                          
                          {workflow.notes && (
                            <p className="text-sm text-gray-700">{workflow.notes}</p>
                          )}
                        </div>
                        
                        <div className="flex flex-col space-y-2">
                          {workflow.workflow_status === 'initiated' && (
                            <button
                              onClick={() => {/* Send reminder logic */}}
                              className="bg-yellow-600 hover:bg-yellow-700 text-white px-3 py-1 rounded text-sm"
                            >
                              Send Reminder
                            </button>
                          )}
                          <button
                            onClick={() => {/* Update status logic */}}
                            className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                          >
                            Mark Complete
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}