import React, { useState } from 'react';
import { Save, X } from 'lucide-react';
import { DASHBOARD_VIEW_ROLES } from '../../services/dashboardViewService';

export function SaveDashboardView({ 
  isOpen, 
  onClose, 
  onSave, 
  dashboardState,
  existingView = null 
}) {
  const [name, setName] = useState(existingView?.name || '');
  const [description, setDescription] = useState(existingView?.description || '');
  const [role, setRole] = useState(existingView?.role || DASHBOARD_VIEW_ROLES.PERSONAL);
  const [isDefault, setIsDefault] = useState(existingView?.isDefault || false);
  const [saving, setSaving] = useState(false);

  if (!isOpen) return null;

  const handleSave = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    setSaving(true);
    try {
      const viewData = {
        name: name.trim(),
        description: description.trim(),
        role,
        config: {
          branchFilter: dashboardState.branchFilter,
          search: dashboardState.search,
          activeTab: dashboardState.tab,
          customSettings: dashboardState.customSettings || {}
        },
        isDefault
      };

      await onSave(viewData);
      setName('');
      setDescription('');
      setRole(DASHBOARD_VIEW_ROLES.PERSONAL);
      setIsDefault(false);
      onClose();
    } catch (error) {
      console.error('Error saving view:', error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">
            {existingView ? 'Update View' : 'Save Dashboard View'}
          </h2>
          <button 
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSave} className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              View Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My Dashboard View"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description of this view"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Visibility Level
            </label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={DASHBOARD_VIEW_ROLES.PERSONAL}>
                Personal - Only visible to you
              </option>
              <option value={DASHBOARD_VIEW_ROLES.BRANCH}>
                Branch - Visible to your branch
              </option>
              <option value={DASHBOARD_VIEW_ROLES.ORGANIZATION}>
                Organization - Visible to entire organization
              </option>
            </select>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="isDefault"
              checked={isDefault}
              onChange={(e) => setIsDefault(e.target.checked)}
              className="mr-2"
            />
            <label htmlFor="isDefault" className="text-sm text-gray-700">
              Set as default view for this level
            </label>
          </div>

          <div className="bg-gray-50 p-3 rounded-md">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Current Settings:</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Branch Filter: {dashboardState.branchFilter}</li>
              <li>• Search: {dashboardState.search || 'None'}</li>
              <li>• Active Tab: {dashboardState.tab}</li>
            </ul>
          </div>

          <div className="flex gap-2 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!name.trim() || saving}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <Save className="w-4 h-4" />
              {saving ? 'Saving...' : existingView ? 'Update' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}