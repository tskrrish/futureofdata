import React, { useState, useEffect } from "react";
import { X, Package } from "lucide-react";

const RESOURCE_TYPES = [
  'equipment',
  'supplies', 
  'facility',
  'vehicle',
  'tool',
  'technology',
  'furniture',
  'other'
];

const CONDITIONS = [
  'excellent',
  'good',
  'fair', 
  'poor',
  'maintenance'
];

export function ResourceForm({ resource, branches, onSubmit, onClose }) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    resource_type: 'equipment',
    branch: branches[0] || '',
    serial_number: '',
    model: '',
    manufacturer: '',
    purchase_date: '',
    condition: 'good',
    max_concurrent_assignments: 1,
    requires_training: false,
    maintenance_schedule_days: 30
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Populate form when editing
  useEffect(() => {
    if (resource) {
      setFormData({
        name: resource.name || '',
        description: resource.description || '',
        resource_type: resource.resource_type || 'equipment',
        branch: resource.branch || branches[0] || '',
        serial_number: resource.serial_number || '',
        model: resource.model || '',
        manufacturer: resource.manufacturer || '',
        purchase_date: resource.purchase_date || '',
        condition: resource.condition || 'good',
        max_concurrent_assignments: resource.max_concurrent_assignments || 1,
        requires_training: resource.requires_training || false,
        maintenance_schedule_days: resource.maintenance_schedule_days || 30
      });
    }
  }, [resource, branches]);

  const validateForm = () => {
    const newErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.resource_type) {
      newErrors.resource_type = 'Resource type is required';
    }

    if (!formData.branch) {
      newErrors.branch = 'Branch is required';
    }

    if (formData.max_concurrent_assignments < 1) {
      newErrors.max_concurrent_assignments = 'Must allow at least 1 assignment';
    }

    if (formData.maintenance_schedule_days < 1) {
      newErrors.maintenance_schedule_days = 'Maintenance schedule must be at least 1 day';
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
      await onSubmit(formData);
    } catch (error) {
      console.error('Failed to save resource:', error);
      setErrors({ submit: 'Failed to save resource. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
              <Package className="w-4 h-4 text-blue-600" />
            </div>
            <h2 className="text-lg font-semibold">
              {resource ? 'Edit Resource' : 'Add New Resource'}
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
                Resource Name *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.name ? 'border-red-300' : 'border-neutral-300'
                }`}
                placeholder="e.g., Pool Vacuum System"
              />
              {errors.name && <p className="text-sm text-red-600 mt-1">{errors.name}</p>}
            </div>

            {/* Resource Type */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Type *
              </label>
              <select
                name="resource_type"
                value={formData.resource_type}
                onChange={handleChange}
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.resource_type ? 'border-red-300' : 'border-neutral-300'
                }`}
              >
                {RESOURCE_TYPES.map(type => (
                  <option key={type} value={type}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </option>
                ))}
              </select>
              {errors.resource_type && <p className="text-sm text-red-600 mt-1">{errors.resource_type}</p>}
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

            {/* Condition */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Condition
              </label>
              <select
                name="condition"
                value={formData.condition}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {CONDITIONS.map(condition => (
                  <option key={condition} value={condition}>
                    {condition.charAt(0).toUpperCase() + condition.slice(1)}
                  </option>
                ))}
              </select>
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
              placeholder="Brief description of the resource..."
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Serial Number */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Serial Number
              </label>
              <input
                type="text"
                name="serial_number"
                value={formData.serial_number}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="S/N"
              />
            </div>

            {/* Model */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Model
              </label>
              <input
                type="text"
                name="model"
                value={formData.model}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Model"
              />
            </div>

            {/* Manufacturer */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Manufacturer
              </label>
              <input
                type="text"
                name="manufacturer"
                value={formData.manufacturer}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Manufacturer"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Purchase Date */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Purchase Date
              </label>
              <input
                type="date"
                name="purchase_date"
                value={formData.purchase_date}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Max Concurrent Assignments */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Max Assignments *
              </label>
              <input
                type="number"
                name="max_concurrent_assignments"
                value={formData.max_concurrent_assignments}
                onChange={handleChange}
                min="1"
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.max_concurrent_assignments ? 'border-red-300' : 'border-neutral-300'
                }`}
              />
              {errors.max_concurrent_assignments && (
                <p className="text-sm text-red-600 mt-1">{errors.max_concurrent_assignments}</p>
              )}
            </div>

            {/* Maintenance Schedule */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Maintenance Interval (days) *
              </label>
              <input
                type="number"
                name="maintenance_schedule_days"
                value={formData.maintenance_schedule_days}
                onChange={handleChange}
                min="1"
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.maintenance_schedule_days ? 'border-red-300' : 'border-neutral-300'
                }`}
              />
              {errors.maintenance_schedule_days && (
                <p className="text-sm text-red-600 mt-1">{errors.maintenance_schedule_days}</p>
              )}
            </div>
          </div>

          {/* Requires Training */}
          <div className="flex items-center">
            <input
              type="checkbox"
              name="requires_training"
              checked={formData.requires_training}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-neutral-300 rounded"
            />
            <label className="ml-2 block text-sm text-neutral-700">
              Requires training before use
            </label>
          </div>

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
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Saving...' : resource ? 'Update Resource' : 'Add Resource'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}