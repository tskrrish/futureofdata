import React, { useState, useEffect } from 'react';
import { Share2, Users, Eye, Edit, Trash2, Plus, X, Check } from 'lucide-react';

const DashboardSharing = ({ dashboardId, isOwner, onClose }) => {
  const [permissions, setPermissions] = useState([]);
  const [shareEmail, setShareEmail] = useState('');
  const [sharePermission, setSharePermission] = useState('view');
  const [isSharing, setIsSharing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (isOwner) {
      loadPermissions();
    }
  }, [dashboardId, isOwner]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadPermissions = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/dashboards/${dashboardId}/permissions`, {
        headers: {
          'Authorization': `Bearer ${getCurrentUserToken()}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setPermissions(data);
      }
    } catch {
      setError('Failed to load dashboard permissions');
    } finally {
      setLoading(false);
    }
  };

  const getCurrentUserToken = () => {
    // In a real app, this would get the JWT token from localStorage or context
    // For demo purposes, using a placeholder
    return localStorage.getItem('user_token') || 'demo-user-id';
  };

  const handleShare = async (e) => {
    e.preventDefault();
    setIsSharing(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch(`/api/dashboards/${dashboardId}/share`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getCurrentUserToken()}`,
        },
        body: JSON.stringify({
          user_email: shareEmail,
          permission_type: sharePermission,
        }),
      });

      if (response.ok) {
        setSuccess(`Dashboard shared with ${shareEmail} successfully!`);
        setShareEmail('');
        setSharePermission('view');
        await loadPermissions(); // Reload permissions list
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to share dashboard');
      }
    } catch {
      setError('Failed to share dashboard');
    } finally {
      setIsSharing(false);
    }
  };

  const handleRevoke = async (userId) => {
    if (!window.confirm('Are you sure you want to revoke access for this user?')) {
      return;
    }

    try {
      const response = await fetch(`/api/dashboards/${dashboardId}/share/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${getCurrentUserToken()}`,
        },
      });

      if (response.ok) {
        setSuccess('Access revoked successfully');
        await loadPermissions(); // Reload permissions list
      } else {
        setError('Failed to revoke access');
      }
    } catch {
      setError('Failed to revoke access');
    }
  };

  const formatUserName = (user) => {
    if (user && user.first_name && user.last_name) {
      return `${user.first_name} ${user.last_name}`;
    }
    return 'Unknown User';
  };

  const getPermissionIcon = (permission) => {
    return permission === 'edit' ? (
      <Edit className="w-4 h-4 text-blue-500" />
    ) : (
      <Eye className="w-4 h-4 text-green-500" />
    );
  };

  const getPermissionColor = (permission) => {
    return permission === 'edit' ? 'text-blue-600' : 'text-green-600';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-2">
            <Share2 className="w-5 h-5 text-blue-600" />
            <h2 className="text-xl font-semibold">Dashboard Sharing</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Error/Success Messages */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md">
              {error}
            </div>
          )}
          {success && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-700 rounded-md">
              {success}
            </div>
          )}

          {isOwner ? (
            <>
              {/* Share New User Form */}
              <div className="mb-6">
                <h3 className="text-lg font-medium mb-4">Share with New User</h3>
                <form onSubmit={handleShare} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email Address
                    </label>
                    <input
                      type="email"
                      value={shareEmail}
                      onChange={(e) => setShareEmail(e.target.value)}
                      placeholder="Enter user's email address"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Permission Level
                    </label>
                    <select
                      value={sharePermission}
                      onChange={(e) => setSharePermission(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="view">View Only - Can see the dashboard</option>
                      <option value="edit">Editor - Can modify dashboard settings</option>
                    </select>
                  </div>
                  <button
                    type="submit"
                    disabled={isSharing}
                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Plus className="w-4 h-4" />
                    <span>{isSharing ? 'Sharing...' : 'Share Dashboard'}</span>
                  </button>
                </form>
              </div>

              {/* Current Permissions */}
              <div>
                <h3 className="text-lg font-medium mb-4 flex items-center space-x-2">
                  <Users className="w-5 h-5" />
                  <span>Current Shared Access ({permissions.length} users)</span>
                </h3>
                
                {loading ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-2 text-gray-600">Loading permissions...</p>
                  </div>
                ) : permissions.length > 0 ? (
                  <div className="space-y-3">
                    {permissions.map((permission) => (
                      <div
                        key={permission.id}
                        className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                      >
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                            <span className="text-sm font-medium text-blue-600">
                              {formatUserName(permission.user)
                                .split(' ')
                                .map((n) => n[0])
                                .join('')}
                            </span>
                          </div>
                          <div>
                            <p className="font-medium text-gray-900">
                              {formatUserName(permission.user)}
                            </p>
                            <p className="text-sm text-gray-600">{permission.user?.email}</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="flex items-center space-x-1">
                            {getPermissionIcon(permission.permission_type)}
                            <span className={`text-sm font-medium ${getPermissionColor(permission.permission_type)}`}>
                              {permission.permission_type === 'edit' ? 'Editor' : 'Viewer'}
                            </span>
                          </div>
                          <button
                            onClick={() => handleRevoke(permission.user_id)}
                            className="text-red-600 hover:text-red-800 p-1"
                            title="Revoke access"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <Users className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p>This dashboard hasn't been shared with anyone yet.</p>
                    <p className="text-sm">Use the form above to share it with other users.</p>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="text-center py-8">
              <Eye className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Shared Dashboard</h3>
              <p className="text-gray-600">
                This dashboard has been shared with you. You can view the data and insights.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t px-6 py-4">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default DashboardSharing;