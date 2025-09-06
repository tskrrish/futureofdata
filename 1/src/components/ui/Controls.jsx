import React from 'react';
import { AdvancedFilters } from '../features/AdvancedFilters';

export function Controls({ 
  branches, 
  branchFilter, 
  onBranchChange, 
  search, 
  onSearchChange, 
  showAdvancedFiltering = false 
}) {
  return (
    <div className="max-w-7xl mx-auto px-4 py-4">
      <div className="grid md:grid-cols-3 gap-3 mb-4">
        <div>
          <div className="text-xs mb-1">Branch</div>
          <select
            className="w-full rounded-2xl border p-2 bg-white"
            value={branchFilter}
            onChange={(e) => onBranchChange(e.target.value)}
          >
            {branches.map((b) => (
              <option key={b}>{b}</option>
            ))}
          </select>
        </div>
        <div className="md:col-span-2">
          <div className="text-xs mb-1">Search</div>
          <input
            className="w-full rounded-2xl border p-2 bg-white"
            placeholder="Find name, branch, date…"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
          />
        </div>
      </div>
      
      <AdvancedFilters 
        showAdvancedFiltering={showAdvancedFiltering}
        onFiltersChange={(filters) => {
          console.log('Advanced filters changed:', filters);
          // In a real implementation, you'd apply these filters
        }}
      />
    </div>
  );
}