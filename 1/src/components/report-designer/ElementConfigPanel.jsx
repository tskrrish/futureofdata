import React from 'react';

function HeaderConfig({ config, onUpdate }) {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-1">
          Title
        </label>
        <input
          type="text"
          value={config.title || ''}
          onChange={(e) => onUpdate({ title: e.target.value })}
          className="w-full px-3 py-2 border border-neutral-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Enter header title"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-1">
          Subtitle (optional)
        </label>
        <input
          type="text"
          value={config.subtitle || ''}
          onChange={(e) => onUpdate({ subtitle: e.target.value })}
          className="w-full px-3 py-2 border border-neutral-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Enter subtitle"
        />
      </div>
    </div>
  );
}

function MetricConfig({ config, onUpdate }) {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-1">
          Title
        </label>
        <input
          type="text"
          value={config.title || ''}
          onChange={(e) => onUpdate({ title: e.target.value })}
          className="w-full px-3 py-2 border border-neutral-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Enter metric title"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-1">
          Metric Type
        </label>
        <select
          value={config.metric || ''}
          onChange={(e) => onUpdate({ metric: e.target.value })}
          className="w-full px-3 py-2 border border-neutral-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">Select metric</option>
          <option value="totalHours">Total Hours</option>
          <option value="activeVolunteers">Active Volunteers</option>
          <option value="memberVolunteers">Member Volunteers</option>
          <option value="averageHours">Average Hours per Volunteer</option>
        </select>
      </div>
    </div>
  );
}

function ChartConfig({ config, onUpdate }) {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-1">
          Chart Title
        </label>
        <input
          type="text"
          value={config.title || ''}
          onChange={(e) => onUpdate({ title: e.target.value })}
          className="w-full px-3 py-2 border border-neutral-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Enter chart title"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-1">
          Chart Type
        </label>
        <select
          value={config.chartType || ''}
          onChange={(e) => onUpdate({ chartType: e.target.value })}
          className="w-full px-3 py-2 border border-neutral-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">Select chart type</option>
          <option value="bar">Bar Chart</option>
          <option value="line">Line Chart</option>
          <option value="pie">Pie Chart</option>
          <option value="area">Area Chart</option>
        </select>
      </div>
      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-1">
          Data Source
        </label>
        <select
          value={config.dataSource || ''}
          onChange={(e) => onUpdate({ dataSource: e.target.value })}
          className="w-full px-3 py-2 border border-neutral-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">Select data source</option>
          <option value="hoursByBranch">Hours by Branch</option>
          <option value="activesByBranch">Active Volunteers by Branch</option>
          <option value="memberShareByBranch">Member Share by Branch</option>
          <option value="trendByMonth">Monthly Trend</option>
        </select>
      </div>
    </div>
  );
}

function FilterConfig({ config, onUpdate }) {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-1">
          Filter Label
        </label>
        <input
          type="text"
          value={config.title || ''}
          onChange={(e) => onUpdate({ title: e.target.value })}
          className="w-full px-3 py-2 border border-neutral-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Enter filter label"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-1">
          Filter Type
        </label>
        <select
          value={config.filterType || ''}
          onChange={(e) => onUpdate({ filterType: e.target.value })}
          className="w-full px-3 py-2 border border-neutral-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">Select filter type</option>
          <option value="select">Dropdown Select</option>
          <option value="dateRange">Date Range</option>
          <option value="search">Text Search</option>
          <option value="multiSelect">Multi-select</option>
        </select>
      </div>
      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-1">
          Field to Filter
        </label>
        <select
          value={config.field || ''}
          onChange={(e) => onUpdate({ field: e.target.value })}
          className="w-full px-3 py-2 border border-neutral-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">Select field</option>
          <option value="branch">Branch</option>
          <option value="name">Volunteer Name</option>
          <option value="date">Date</option>
          <option value="hours">Hours</option>
          <option value="member">Member Status</option>
        </select>
      </div>
    </div>
  );
}

export function ElementConfigPanel({ element, onUpdate, onClose }) {
  const handleUpdate = (newConfig) => {
    onUpdate(element.id, newConfig);
  };

  return (
    <div className="border-t border-neutral-200 bg-neutral-50 p-4">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-sm font-semibold text-neutral-800">
          Configuration
        </h4>
        <button
          onClick={onClose}
          className="text-xs text-neutral-500 hover:text-neutral-700"
        >
          Close
        </button>
      </div>

      {element.type === 'header' && (
        <HeaderConfig config={element.config} onUpdate={handleUpdate} />
      )}

      {element.type === 'metric' && (
        <MetricConfig config={element.config} onUpdate={handleUpdate} />
      )}

      {element.type === 'chart' && (
        <ChartConfig config={element.config} onUpdate={handleUpdate} />
      )}

      {element.type === 'filter' && (
        <FilterConfig config={element.config} onUpdate={handleUpdate} />
      )}

      {element.type === 'kpi' && (
        <div className="text-sm text-neutral-600">
          KPI cards will automatically display key metrics from your data.
        </div>
      )}

      {element.type === 'divider' && (
        <div className="text-sm text-neutral-600">
          Dividers provide visual separation between sections.
        </div>
      )}
    </div>
  );
}