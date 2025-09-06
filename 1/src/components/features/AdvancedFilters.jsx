import React, { useState } from 'react';
import { Filter, Calendar, MapPin, Clock } from 'lucide-react';

export function AdvancedFilters({ 
  onFiltersChange, 
  showAdvancedFiltering = false 
}) {
  const [filters, setFilters] = useState({
    dateRange: 'all',
    hoursRange: 'all',
    memberStatus: 'all',
    location: 'all'
  });

  const [isExpanded, setIsExpanded] = useState(false);

  if (!showAdvancedFiltering) {
    return null;
  }

  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    if (onFiltersChange) {
      onFiltersChange(newFilters);
    }
  };

  return (
    <div className="bg-white rounded-lg border p-4 mb-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900 w-full justify-between"
      >
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4" />
          Advanced Filters
        </div>
        <span className={`transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
          ▼
        </span>
      </button>

      {isExpanded && (
        <div className="mt-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Date Range Filter */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-2">
                <Calendar className="w-3 h-3 inline mr-1" />
                Date Range
              </label>
              <select
                value={filters.dateRange}
                onChange={(e) => handleFilterChange('dateRange', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Time</option>
                <option value="last7">Last 7 days</option>
                <option value="last30">Last 30 days</option>
                <option value="last90">Last 90 days</option>
                <option value="ytd">Year to date</option>
                <option value="custom">Custom range</option>
              </select>
            </div>

            {/* Hours Range Filter */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-2">
                <Clock className="w-3 h-3 inline mr-1" />
                Hours Range
              </label>
              <select
                value={filters.hoursRange}
                onChange={(e) => handleFilterChange('hoursRange', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Hours</option>
                <option value="0-10">0-10 hours</option>
                <option value="11-25">11-25 hours</option>
                <option value="26-50">26-50 hours</option>
                <option value="51-100">51-100 hours</option>
                <option value="100+">100+ hours</option>
              </select>
            </div>

            {/* Member Status Filter */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-2">
                Member Status
              </label>
              <select
                value={filters.memberStatus}
                onChange={(e) => handleFilterChange('memberStatus', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Status</option>
                <option value="member">Members Only</option>
                <option value="non-member">Non-Members Only</option>
              </select>
            </div>

            {/* Location Filter */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-2">
                <MapPin className="w-3 h-3 inline mr-1" />
                Location
              </label>
              <select
                value={filters.location}
                onChange={(e) => handleFilterChange('location', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Locations</option>
                <option value="downtown">Downtown</option>
                <option value="westside">West Side</option>
                <option value="eastside">East Side</option>
                <option value="northside">North Side</option>
              </select>
            </div>
          </div>

          {/* Active Filters Display */}
          {Object.values(filters).some(v => v !== 'all') && (
            <div className="border-t pt-3">
              <p className="text-xs text-gray-500 mb-2">Active filters:</p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(filters)
                  .filter(([, value]) => value !== 'all')
                  .map(([key, value]) => (
                    <span
                      key={key}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                    >
                      {key}: {value}
                      <button
                        onClick={() => handleFilterChange(key, 'all')}
                        className="hover:text-blue-600"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                <button
                  onClick={() => {
                    const resetFilters = Object.keys(filters).reduce((acc, key) => ({
                      ...acc,
                      [key]: 'all'
                    }), {});
                    setFilters(resetFilters);
                    if (onFiltersChange) onFiltersChange(resetFilters);
                  }}
                  className="text-xs text-gray-500 hover:text-gray-700 underline"
                >
                  Clear all
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}