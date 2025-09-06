import React, { useState, useEffect } from 'react';
import { Save, FolderOpen, Share2, Trash2, Plus, Eye, Edit, Globe, Lock } from 'lucide-react';
import DashboardSharing from './DashboardSharing';

const DashboardManager = ({ 
  currentDashboardState, 
  onLoadDashboard, 
  onSaveDashboard,
  currentUser = 'demo-user-id' // In production, get from auth context
}) => {
  const [dashboards, setDashboards] = useState([]);
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [showSharingModal, setShowSharingModal] = useState(false);
  const [selectedDashboardId, setSelectedDashboardId] = useState(null);
  const [saveForm, setSaveForm] = useState({
    title: '',
    description: '',
    isPublic: false
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    loadDashboards();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const getCurrentUserToken = () => {
    return localStorage.getItem('user_token') || currentUser;
  };

  const loadDashboards = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/dashboards', {
        headers: {
          'Authorization': `Bearer ${getCurrentUserToken()}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setDashboards(data);
      } else {
        setError('Failed to load dashboards');
      }
    } catch {
      setError('Failed to connect to dashboard service');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveDashboard = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const dashboardData = {
        title: saveForm.title,
        description: saveForm.description,
        is_public: saveForm.isPublic,
        dashboard_data: {
          ...currentDashboardState,
          savedAt: new Date().toISOString()
        }
      };

      const response = await fetch('/api/dashboards', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getCurrentUserToken()}`,
        },
        body: JSON.stringify(dashboardData),
      });

      if (response.ok) {
        const newDashboard = await response.json();
        setSuccess('Dashboard saved successfully!');
        setShowSaveModal(false);
        setSaveForm({ title: '', description: '', isPublic: false });
        await loadDashboards();
        
        // Notify parent component
        if (onSaveDashboard) {
          onSaveDashboard(newDashboard);
        }
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to save dashboard');
      }
    } catch {
      setError('Failed to save dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleLoadDashboard = async (dashboard) => {
    try {
      const response = await fetch(`/api/dashboards/${dashboard.id}`, {
        headers: {
          'Authorization': `Bearer ${getCurrentUserToken()}`,
        },
      });

      if (response.ok) {
        const dashboardData = await response.json();
        
        // Notify parent component to load the dashboard state
        if (onLoadDashboard && dashboardData.dashboard_data) {
          onLoadDashboard(dashboardData.dashboard_data);
          setSuccess(`Loaded dashboard: ${dashboardData.title}`);
        }
      } else {
        setError('Failed to load dashboard');
      }
    } catch {
      setError('Failed to load dashboard');
    }
  };

  const handleDeleteDashboard = async (dashboardId) => {
    if (!window.confirm('Are you sure you want to delete this dashboard?')) {
      return;
    }

    try {
      const response = await fetch(`/api/dashboards/${dashboardId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${getCurrentUserToken()}`,
        },
      });

      if (response.ok) {
        setSuccess('Dashboard deleted successfully');
        await loadDashboards();
      } else {
        setError('Failed to delete dashboard');
      }
    } catch {
      setError('Failed to delete dashboard');
    }
  };

  const handleShareDashboard = (dashboardId) => {
    setSelectedDashboardId(dashboardId);
    setShowSharingModal(true);
  };

  const getPermissionBadge = (permission) => {
    const badges = {
      owner: { icon: Edit, label: 'Owner', color: 'bg-purple-100 text-purple-800' },
      edit: { icon: Edit, label: 'Editor', color: 'bg-blue-100 text-blue-800' },
      view: { icon: Eye, label: 'Viewer', color: 'bg-green-100 text-green-800' }
    };
    
    const badge = badges[permission] || badges.view;
    const Icon = badge.icon;
    
    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${badge.color}`}>
        <Icon className="w-3 h-3 mr-1" />
        {badge.label}
      </span>
    );
  };

  const getVisibilityIcon = (isPublic) => {
    return isPublic ? (
      <Globe className="w-4 h-4 text-green-600" title="Public dashboard" />
    ) : (
      <Lock className="w-4 h-4 text-gray-600" title="Private dashboard" />
    );
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-4">
      {/* Action Buttons */}
      <div className="flex items-center space-x-3">
        <button
          onClick={() => setShowSaveModal(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <Save className="w-4 h-4" />
          <span>Save Dashboard</span>
        </button>
        <button
          onClick={loadDashboards}
          disabled={loading}
          className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50"
        >
          <FolderOpen className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Messages */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-md">
          {error}
        </div>
      )}
      {success && (
        <div className="p-3 bg-green-50 border border-green-200 text-green-700 rounded-md">
          {success}
        </div>
      )}

      {/* Dashboard List */}
      <div className="bg-white rounded-lg border">
        <div className="p-4 border-b">
          <h3 className="text-lg font-medium">My Dashboards</h3>
        </div>
        
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading dashboards...</p>
          </div>
        ) : dashboards.length > 0 ? (
          <div className="divide-y">
            {dashboards.map((dashboard) => (
              <div key={dashboard.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3">
                      <h4 className="text-lg font-medium text-gray-900 truncate">
                        {dashboard.title}
                      </h4>
                      {getPermissionBadge(dashboard.permission)}
                      {getVisibilityIcon(dashboard.is_public)}
                    </div>
                    {dashboard.description && (
                      <p className="text-sm text-gray-600 mt-1">{dashboard.description}</p>
                    )}
                    <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                      <span>Updated: {formatDate(dashboard.updated_at)}</span>
                      {dashboard.shared_at && (
                        <span>Shared: {formatDate(dashboard.shared_at)}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => handleLoadDashboard(dashboard)}
                      className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded"
                      title="Load dashboard"
                    >
                      <FolderOpen className="w-4 h-4" />
                    </button>
                    {dashboard.permission === 'owner' && (
                      <>
                        <button
                          onClick={() => handleShareDashboard(dashboard.id)}
                          className="p-2 text-gray-600 hover:text-green-600 hover:bg-green-50 rounded"
                          title="Share dashboard"
                        >
                          <Share2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteDashboard(dashboard.id)}
                          className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded"
                          title="Delete dashboard"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center text-gray-500">
            <FolderOpen className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p className="text-lg mb-2">No dashboards found</p>
            <p className="text-sm">Create your first dashboard by clicking "Save Dashboard" above.</p>
          </div>
        )}
      </div>

      {/* Save Dashboard Modal */}
      {showSaveModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6">
              <h3 className="text-lg font-medium mb-4">Save Dashboard</h3>
              <form onSubmit={handleSaveDashboard} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Dashboard Title
                  </label>
                  <input
                    type="text"
                    value={saveForm.title}
                    onChange={(e) => setSaveForm({...saveForm, title: e.target.value})}
                    placeholder="Enter dashboard title"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description (optional)
                  </label>
                  <textarea
                    value={saveForm.description}
                    onChange={(e) => setSaveForm({...saveForm, description: e.target.value})}
                    placeholder="Describe this dashboard..."
                    rows="3"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="isPublic"
                    checked={saveForm.isPublic}
                    onChange={(e) => setSaveForm({...saveForm, isPublic: e.target.checked})}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="isPublic" className="ml-2 text-sm text-gray-700">
                    Make this dashboard publicly viewable
                  </label>
                </div>
                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowSaveModal(false)}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {loading ? 'Saving...' : 'Save Dashboard'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Dashboard Sharing Modal */}
      {showSharingModal && selectedDashboardId && (
        <DashboardSharing
          dashboardId={selectedDashboardId}
          isOwner={dashboards.find(d => d.id === selectedDashboardId)?.permission === 'owner'}
          onClose={() => {
            setShowSharingModal(false);
            setSelectedDashboardId(null);
            loadDashboards(); // Refresh list in case permissions changed
          }}
        />
      )}
    </div>
  );
};

export default DashboardManager;