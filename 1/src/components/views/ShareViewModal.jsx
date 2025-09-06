import React, { useState } from 'react';
import { X, Share2, UserPlus, Trash2, Eye, Edit, Trash, Share } from 'lucide-react';
import { DASHBOARD_VIEW_PERMISSIONS } from '../../services/dashboardViewService';

export function ShareViewModal({ view, isOpen, onClose, onShare, onUnshare }) {
  const [newUserEmail, setNewUserEmail] = useState('');
  const [selectedPermissions, setSelectedPermissions] = useState([DASHBOARD_VIEW_PERMISSIONS.READ]);
  const [isSharing, setIsSharing] = useState(false);

  if (!isOpen || !view) return null;

  const handleShare = async (e) => {
    e.preventDefault();
    if (!newUserEmail.trim()) return;

    setIsSharing(true);
    try {
      await onShare(view.id, [newUserEmail.trim()], selectedPermissions);
      setNewUserEmail('');
      setSelectedPermissions([DASHBOARD_VIEW_PERMISSIONS.READ]);
    } catch (error) {
      console.error('Error sharing view:', error);
    } finally {
      setIsSharing(false);
    }
  };

  const handleUnshare = async (userEmail) => {
    try {
      await onUnshare(view.id, userEmail);
    } catch (error) {
      console.error('Error unsharing view:', error);
    }
  };

  const togglePermission = (permission) => {
    setSelectedPermissions(prev => {
      if (prev.includes(permission)) {
        return prev.filter(p => p !== permission);
      } else {
        return [...prev, permission];
      }
    });
  };

  const getPermissionIcon = (permission) => {
    switch (permission) {
      case DASHBOARD_VIEW_PERMISSIONS.READ:
        return <Eye className="w-3 h-3" />;
      case DASHBOARD_VIEW_PERMISSIONS.WRITE:
        return <Edit className="w-3 h-3" />;
      case DASHBOARD_VIEW_PERMISSIONS.SHARE:
        return <Share className="w-3 h-3" />;
      case DASHBOARD_VIEW_PERMISSIONS.DELETE:
        return <Trash className="w-3 h-3" />;
      default:
        return null;
    }
  };

  const getPermissionLabel = (permission) => {
    switch (permission) {
      case DASHBOARD_VIEW_PERMISSIONS.READ:
        return 'View';
      case DASHBOARD_VIEW_PERMISSIONS.WRITE:
        return 'Edit';
      case DASHBOARD_VIEW_PERMISSIONS.SHARE:
        return 'Share';
      case DASHBOARD_VIEW_PERMISSIONS.DELETE:
        return 'Delete';
      default:
        return permission;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[80vh] overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-2">
            <Share2 className="w-5 h-5" />
            <h2 className="text-lg font-semibold">Share Dashboard View</h2>
          </div>
          <button 
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 space-y-6 overflow-y-auto max-h-[60vh]">
          <div>
            <h3 className="font-medium text-gray-900 mb-2">{view.name}</h3>
            <p className="text-sm text-gray-600">
              {view.description || 'No description provided'}
            </p>
            <div className="text-xs text-gray-500 mt-1">
              Created by {view.owner} • {view.role} level view
            </div>
          </div>

          <form onSubmit={handleShare} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Share with user (email)
              </label>
              <div className="flex gap-2">
                <input
                  type="email"
                  value={newUserEmail}
                  onChange={(e) => setNewUserEmail(e.target.value)}
                  placeholder="user@example.com"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="submit"
                  disabled={!newUserEmail.trim() || isSharing}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <UserPlus className="w-4 h-4" />
                  {isSharing ? 'Sharing...' : 'Share'}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Permissions
              </label>
              <div className="grid grid-cols-2 gap-2">
                {Object.values(DASHBOARD_VIEW_PERMISSIONS).map(permission => (
                  <label
                    key={permission}
                    className="flex items-center gap-2 p-2 border rounded-md cursor-pointer hover:bg-gray-50"
                  >
                    <input
                      type="checkbox"
                      checked={selectedPermissions.includes(permission)}
                      onChange={() => togglePermission(permission)}
                      className="rounded"
                    />
                    <div className="flex items-center gap-1">
                      {getPermissionIcon(permission)}
                      <span className="text-sm">{getPermissionLabel(permission)}</span>
                    </div>
                  </label>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Select the permissions this user will have for this view
              </p>
            </div>
          </form>

          {view.sharedWith && view.sharedWith.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">
                Currently shared with ({view.sharedWith.length})
              </h4>
              <div className="space-y-2">
                {view.sharedWith.map((share, index) => (
                  <div 
                    key={`${share.user}-${index}`} 
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-md"
                  >
                    <div className="flex-1">
                      <div className="font-medium text-sm">{share.user}</div>
                      <div className="text-xs text-gray-600 flex items-center gap-2">
                        <span>Shared on {new Date(share.sharedAt).toLocaleDateString()}</span>
                        <span>•</span>
                        <div className="flex items-center gap-1">
                          {share.permissions.map(permission => (
                            <div 
                              key={permission}
                              className="flex items-center gap-1 bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs"
                            >
                              {getPermissionIcon(permission)}
                              <span>{getPermissionLabel(permission)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => handleUnshare(share.user)}
                      className="p-1 hover:bg-gray-200 rounded text-red-600"
                      title="Remove access"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="bg-blue-50 p-3 rounded-md">
            <h4 className="text-sm font-medium text-blue-900 mb-1">
              Sharing Guidelines
            </h4>
            <ul className="text-xs text-blue-800 space-y-1">
              <li>• Users with <strong>View</strong> permission can apply and see the view</li>
              <li>• Users with <strong>Edit</strong> permission can modify the view settings</li>
              <li>• Users with <strong>Share</strong> permission can share the view with others</li>
              <li>• Users with <strong>Delete</strong> permission can delete the view</li>
            </ul>
          </div>
        </div>

        <div className="p-4 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default ShareViewModal;