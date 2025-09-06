import React, { useState, useEffect } from "react";
import { X, Calendar } from "lucide-react";

const CATEGORIES = [
  'Youth Programs',
  'Senior Services',
  'Community Services',
  'Health & Wellness',
  'Aquatics',
  'Sports',
  'Maintenance',
  'Events',
  'Education',
  'Other'
];

export function ShiftForm({ shift, branches, onSubmit, onClose }) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    branch: branches[0] || '',
    category: 'Youth Programs',
    start_time: '',
    end_time: '',
    max_volunteers: 1
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Populate form when editing
  useEffect(() => {
    if (shift) {
      // Format datetime for input fields
      const formatForInput = (dateString) => {
        const date = new Date(dateString);
        return date.toISOString().slice(0, 16); // YYYY-MM-DDTHH:MM
      };

      setFormData({
        name: shift.name || '',
        description: shift.description || '',
        branch: shift.branch || branches[0] || '',
        category: shift.category || 'Youth Programs',
        start_time: shift.start_time ? formatForInput(shift.start_time) : '',
        end_time: shift.end_time ? formatForInput(shift.end_time) : '',
        max_volunteers: shift.max_volunteers || 1
      });
    }
  }, [shift, branches]);

  const validateForm = () => {
    const newErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.branch) {
      newErrors.branch = 'Branch is required';
    }

    if (!formData.start_time) {
      newErrors.start_time = 'Start time is required';
    }

    if (!formData.end_time) {
      newErrors.end_time = 'End time is required';
    }

    if (formData.start_time && formData.end_time) {
      const startDate = new Date(formData.start_time);
      const endDate = new Date(formData.end_time);
      
      if (startDate >= endDate) {
        newErrors.end_time = 'End time must be after start time';
      }

      // Check if start time is in the past
      const now = new Date();
      if (startDate < now && !shift) { // Only check for new shifts
        newErrors.start_time = 'Start time cannot be in the past';
      }
    }

    if (formData.max_volunteers < 1) {
      newErrors.max_volunteers = 'Must allow at least 1 volunteer';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    
    try {
      // Convert datetime-local format to ISO string
      const submitData = {
        ...formData,
        start_time: new Date(formData.start_time).toISOString(),
        end_time: new Date(formData.end_time).toISOString()
      };
      
      await onSubmit(submitData);
    } catch (error) {
      console.error('Failed to save shift:', error);
      setErrors({ submit: 'Failed to save shift. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  // Auto-fill end time when start time is set (default to 2 hours later)
  const handleStartTimeChange = (e) => {
    const startTime = e.target.value;
    setFormData(prev => {
      const newData = { ...prev, start_time: startTime };
      
      // If no end time set and we have a start time, default to 2 hours later
      if (startTime && !prev.end_time) {
        const start = new Date(startTime);
        const end = new Date(start.getTime() + 2 * 60 * 60 * 1000); // Add 2 hours
        newData.end_time = end.toISOString().slice(0, 16);
      }
      
      return newData;
    });
    
    // Clear start time error
    if (errors.start_time) {
      setErrors(prev => ({ ...prev, start_time: '' }));
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
              <Calendar className="w-4 h-4 text-green-600" />
            </div>
            <h2 className="text-lg font-semibold">
              {shift ? 'Edit Shift' : 'Add New Shift'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 rounded-lg"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {errors.submit && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-600">{errors.submit}</p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Shift Name *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.name ? 'border-red-300' : 'border-neutral-300'
                }`}
                placeholder="e.g., Morning Pool Maintenance"
              />
              {errors.name && <p className="text-sm text-red-600 mt-1">{errors.name}</p>}
            </div>

            {/* Category */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Category
              </label>
              <select
                name="category"
                value={formData.category}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {CATEGORIES.map(category => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>
            </div>

            {/* Branch */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Branch *
              </label>
              <select
                name="branch"
                value={formData.branch}
                onChange={handleChange}
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.branch ? 'border-red-300' : 'border-neutral-300'
                }`}
              >
                {branches.map(branch => (
                  <option key={branch} value={branch}>{branch}</option>
                ))}
              </select>
              {errors.branch && <p className="text-sm text-red-600 mt-1">{errors.branch}</p>}
            </div>

            {/* Max Volunteers */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Max Volunteers *
              </label>
              <input
                type="number"
                name="max_volunteers"
                value={formData.max_volunteers}
                onChange={handleChange}
                min="1"
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.max_volunteers ? 'border-red-300' : 'border-neutral-300'
                }`}
              />
              {errors.max_volunteers && <p className="text-sm text-red-600 mt-1">{errors.max_volunteers}</p>}
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">
              Description
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={3}
              className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Brief description of the shift..."
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Start Time */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Start Time *
              </label>
              <input
                type="datetime-local"
                name="start_time"
                value={formData.start_time}
                onChange={handleStartTimeChange}
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.start_time ? 'border-red-300' : 'border-neutral-300'
                }`}
              />
              {errors.start_time && <p className="text-sm text-red-600 mt-1">{errors.start_time}</p>}
            </div>

            {/* End Time */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                End Time *
              </label>
              <input
                type="datetime-local"
                name="end_time"
                value={formData.end_time}
                onChange={handleChange}
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.end_time ? 'border-red-300' : 'border-neutral-300'
                }`}
              />
              {errors.end_time && <p className="text-sm text-red-600 mt-1">{errors.end_time}</p>}
            </div>
          </div>

          {/* Duration Display */}
          {formData.start_time && formData.end_time && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-sm text-blue-600">
                Duration: {(() => {
                  const start = new Date(formData.start_time);
                  const end = new Date(formData.end_time);
                  const diff = end - start;
                  const hours = Math.floor(diff / (1000 * 60 * 60));
                  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                  return `${hours}h ${minutes}m`;
                })()}
              </p>
            </div>
          )}

          {/* Form Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-neutral-600 bg-neutral-100 rounded-lg hover:bg-neutral-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Saving...' : shift ? 'Update Shift' : 'Add Shift'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}