import React, { useState } from 'react';
import { Plus, Edit2, Trash2, Eye, Users, Calendar, Target } from 'lucide-react';
import { useAnnouncements } from '../../hooks/useAnnouncements';

const AnnouncementAdmin = () => {
  const { 
    announcements, 
    addAnnouncement, 
    updateAnnouncement, 
    deleteAnnouncement,
    getReadReceiptStats
  } = useAnnouncements();
  
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingAnnouncement, setEditingAnnouncement] = useState(null);
  const [viewingStats, setViewingStats] = useState(null);

  const branches = ['All', 'Blue Ash', 'Campbell County', 'Clippard', 'Music Resource Center', 'Clippard Senior Center', 'Kentucky Senior Center', 'R.C. Durre YMCA'];
  const roles = ['All', 'volunteer', 'member', 'staff', 'admin'];
  const departments = ['All', 'Youth Development', 'Sports', 'Community Services', 'Senior Services', 'Wellness', 'Early Learning', 'Aquatics', 'Arts'];

  const AnnouncementForm = ({ announcement, onSubmit, onCancel }) => {
    const [formData, setFormData] = useState(announcement || {
      title: '',
      message: '',
      type: 'info',
      priority: 'medium',
      targetBranches: ['All'],
      targetRoles: ['All'],
      targetDepartments: ['All'],
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 16),
      dismissible: true
    });

    const handleSubmit = (e) => {
      e.preventDefault();
      onSubmit(formData);
    };

    const handleMultiSelect = (field, value, isChecked) => {
      setFormData(prev => ({
        ...prev,
        [field]: isChecked 
          ? [...prev[field].filter(item => item !== 'All'), value]
          : prev[field].filter(item => item !== value)
      }));
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold">
              {announcement ? 'Edit Announcement' : 'Create New Announcement'}
            </h3>
          </div>

          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
              <input
                type="text"
                required
                value={formData.title}
                onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Message</label>
              <textarea
                required
                rows="4"
                value={formData.message}
                onChange={(e) => setFormData(prev => ({ ...prev, message: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData(prev => ({ ...prev, type: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="info">Info</option>
                  <option value="warning">Warning</option>
                  <option value="success">Success</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                <select
                  value={formData.priority}
                  onChange={(e) => setFormData(prev => ({ ...prev, priority: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Expires At</label>
              <input
                type="datetime-local"
                required
                value={formData.expiresAt}
                onChange={(e) => setFormData(prev => ({ ...prev, expiresAt: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Target Branches</label>
              <div className="space-y-2 max-h-32 overflow-y-auto border border-gray-200 rounded p-3">
                {branches.map(branch => (
                  <label key={branch} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.targetBranches.includes(branch)}
                      onChange={(e) => handleMultiSelect('targetBranches', branch, e.target.checked)}
                      className="mr-2"
                    />
                    <span className="text-sm">{branch}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Target Roles</label>
              <div className="space-y-2 max-h-32 overflow-y-auto border border-gray-200 rounded p-3">
                {roles.map(role => (
                  <label key={role} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.targetRoles.includes(role)}
                      onChange={(e) => handleMultiSelect('targetRoles', role, e.target.checked)}
                      className="mr-2"
                    />
                    <span className="text-sm">{role}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Target Departments</label>
              <div className="space-y-2 max-h-32 overflow-y-auto border border-gray-200 rounded p-3">
                {departments.map(department => (
                  <label key={department} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.targetDepartments.includes(department)}
                      onChange={(e) => handleMultiSelect('targetDepartments', department, e.target.checked)}
                      className="mr-2"
                    />
                    <span className="text-sm">{department}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.dismissible}
                  onChange={(e) => setFormData(prev => ({ ...prev, dismissible: e.target.checked }))}
                  className="mr-2"
                />
                <span className="text-sm font-medium text-gray-700">Allow users to dismiss</span>
              </label>
            </div>

            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onCancel}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                {announcement ? 'Update' : 'Create'} Announcement
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  const StatsModal = ({ announcement, onClose }) => {
    const stats = getReadReceiptStats(announcement.id);
    
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg max-w-lg w-full">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold">Read Receipt Stats</h3>
            <p className="text-sm text-gray-600">{announcement.title}</p>
          </div>
          
          <div className="p-6">
            <div className="mb-4">
              <div className="text-2xl font-bold text-blue-600">{stats.totalReads}</div>
              <div className="text-sm text-gray-600">Total Reads</div>
            </div>
            
            {stats.readReceipts.length > 0 && (
              <div>
                <h4 className="font-medium mb-2">Recent Reads:</h4>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {stats.readReceipts.slice(-10).reverse().map((receipt, index) => (
                    <div key={index} className="flex justify-between text-sm">
                      <span>{receipt.userId}</span>
                      <span className="text-gray-500">{receipt.branch}</span>
                      <span className="text-gray-400">
                        {new Date(receipt.readAt).toLocaleDateString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
          
          <div className="px-6 py-4 border-t">
            <button
              onClick={onClose}
              className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  };

  const handleCreateSubmit = (formData) => {
    addAnnouncement(formData);
    setIsCreateModalOpen(false);
  };

  const handleEditSubmit = (formData) => {
    updateAnnouncement(editingAnnouncement.id, formData);
    setEditingAnnouncement(null);
  };

  const handleDelete = (announcementId) => {
    if (confirm('Are you sure you want to delete this announcement?')) {
      deleteAnnouncement(announcementId);
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Announcement Management</h2>
          <p className="text-gray-600">Create and manage targeted announcements</p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Announcement
        </button>
      </div>

      <div className="grid gap-4">
        {announcements.map(announcement => {
          const stats = getReadReceiptStats(announcement.id);
          const isExpired = new Date(announcement.expiresAt) < new Date();
          
          return (
            <div key={announcement.id} className={`border rounded-lg p-4 ${isExpired ? 'bg-gray-50 opacity-75' : 'bg-white'}`}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <h3 className="font-medium text-gray-900">{announcement.title}</h3>
                    <span className={`px-2 py-1 text-xs rounded-md ${
                      announcement.type === 'urgent' ? 'bg-red-100 text-red-800' :
                      announcement.type === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                      announcement.type === 'success' ? 'bg-green-100 text-green-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {announcement.priority.toUpperCase()}
                    </span>
                    {isExpired && <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-md">EXPIRED</span>}
                  </div>
                  
                  <p className="text-gray-600 text-sm mb-3">{announcement.message}</p>
                  
                  <div className="flex items-center space-x-4 text-xs text-gray-500">
                    <div className="flex items-center">
                      <Target className="w-3 h-3 mr-1" />
                      {announcement.targetBranches.includes('All') ? 'All Branches' : `${announcement.targetBranches.length} branches`}
                    </div>
                    <div className="flex items-center">
                      <Users className="w-3 h-3 mr-1" />
                      {stats.totalReads} reads
                    </div>
                    <div className="flex items-center">
                      <Calendar className="w-3 h-3 mr-1" />
                      Expires: {new Date(announcement.expiresAt).toLocaleDateString()}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setViewingStats(announcement)}
                    className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                    title="View stats"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setEditingAnnouncement(announcement)}
                    className="p-2 text-gray-400 hover:text-yellow-600 hover:bg-yellow-50 rounded"
                    title="Edit"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(announcement.id)}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {isCreateModalOpen && (
        <AnnouncementForm
          onSubmit={handleCreateSubmit}
          onCancel={() => setIsCreateModalOpen(false)}
        />
      )}

      {editingAnnouncement && (
        <AnnouncementForm
          announcement={editingAnnouncement}
          onSubmit={handleEditSubmit}
          onCancel={() => setEditingAnnouncement(null)}
        />
      )}

      {viewingStats && (
        <StatsModal
          announcement={viewingStats}
          onClose={() => setViewingStats(null)}
        />
      )}
    </div>
  );
};

export default AnnouncementAdmin;