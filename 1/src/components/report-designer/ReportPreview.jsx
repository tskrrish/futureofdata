import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  ResponsiveContainer, Tooltip, Legend,
  PieChart, Pie, Cell,
  LineChart, Line,
  AreaChart, Area
} from 'recharts';
import { Clock, Users, UserCheck, Sparkles } from 'lucide-react';

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1'];

function PreviewHeader({ element, volunteerData }) {
  const { config } = element;
  
  return (
    <div className="py-6">
      <h1 className="text-3xl font-bold text-neutral-800 mb-3">
        {config.title || 'Custom Report'}
      </h1>
      {config.subtitle && (
        <p className="text-lg text-neutral-600">
          {config.subtitle}
        </p>
      )}
    </div>
  );
}

function PreviewKPI({ volunteerData }) {
  if (!volunteerData) return null;

  const totalHours = volunteerData.totalHours || 0;
  const activeCount = volunteerData.activeVolunteersCount || 0;
  const memberCount = volunteerData.memberVolunteersCount || 0;
  const avgHours = activeCount > 0 ? (totalHours / activeCount) : 0;

  return (
    <div className="py-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg border shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <Clock className="w-6 h-6 text-blue-600" />
            <span className="text-sm font-medium text-neutral-600">Total Hours</span>
          </div>
          <div className="text-2xl font-bold text-neutral-800">
            {totalHours.toFixed(1)}
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <Users className="w-6 h-6 text-green-600" />
            <span className="text-sm font-medium text-neutral-600">Active Volunteers</span>
          </div>
          <div className="text-2xl font-bold text-neutral-800">
            {activeCount}
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <UserCheck className="w-6 h-6 text-purple-600" />
            <span className="text-sm font-medium text-neutral-600">Member Volunteers</span>
          </div>
          <div className="text-2xl font-bold text-neutral-800">
            {memberCount}
          </div>
          <div className="text-sm text-neutral-500">
            {activeCount > 0 ? ((memberCount / activeCount) * 100).toFixed(1) : 0}%
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <Sparkles className="w-6 h-6 text-orange-600" />
            <span className="text-sm font-medium text-neutral-600">Avg Hours / Active</span>
          </div>
          <div className="text-2xl font-bold text-neutral-800">
            {avgHours.toFixed(1)}
          </div>
        </div>
      </div>
    </div>
  );
}

function PreviewDivider() {
  return (
    <div className="py-6">
      <hr className="border-neutral-300" />
    </div>
  );
}

function PreviewMetric({ element, volunteerData }) {
  const { config } = element;
  
  if (!volunteerData) return null;

  let value = '--';
  let label = config.title || 'Metric';

  switch (config.metric) {
    case 'totalHours':
      value = volunteerData.totalHours?.toFixed(1) || '0';
      break;
    case 'activeVolunteers':
      value = volunteerData.activeVolunteersCount?.toString() || '0';
      break;
    case 'memberVolunteers':
      value = volunteerData.memberVolunteersCount?.toString() || '0';
      break;
    case 'averageHours':
      const avg = volunteerData.activeVolunteersCount > 0 
        ? (volunteerData.totalHours / volunteerData.activeVolunteersCount) 
        : 0;
      value = avg.toFixed(1);
      break;
  }

  return (
    <div className="py-6">
      <div className="bg-white p-6 rounded-lg border shadow-sm">
        <div className="text-3xl font-bold text-neutral-800 mb-2">
          {value}
        </div>
        <div className="text-sm font-medium text-neutral-600">
          {label}
        </div>
      </div>
    </div>
  );
}

function PreviewChart({ element, volunteerData }) {
  const { config } = element;
  
  if (!volunteerData) return null;

  let data = [];
  let chartTitle = config.title || 'Chart';

  // Get data based on data source
  switch (config.dataSource) {
    case 'hoursByBranch':
      data = volunteerData.hoursByBranch || [];
      break;
    case 'activesByBranch':
      data = volunteerData.activesByBranch || [];
      break;
    case 'memberShareByBranch':
      data = volunteerData.memberShareByBranch || [];
      break;
    case 'trendByMonth':
      data = volunteerData.trendByMonth || [];
      break;
    default:
      data = [];
  }

  const renderChart = () => {
    switch (config.chartType) {
      case 'bar':
        return (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="branch" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="hours" name="Hours" fill="#8884d8" />
            <Bar dataKey="active" name="Active" fill="#82ca9d" />
          </BarChart>
        );

      case 'line':
        return (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="hours" stroke="#8884d8" />
          </LineChart>
        );

      case 'pie':
        return (
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        );

      case 'area':
        return (
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Area type="monotone" dataKey="hours" stroke="#8884d8" fill="#8884d8" />
          </AreaChart>
        );

      default:
        return (
          <div className="h-64 bg-neutral-50 rounded flex items-center justify-center">
            <div className="text-neutral-400 text-center">
              <div className="text-sm">No chart type selected</div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="py-6">
      <div className="bg-white p-6 rounded-lg border shadow-sm">
        <h3 className="font-semibold text-lg text-neutral-800 mb-6">
          {chartTitle}
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            {renderChart()}
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

function PreviewFilter({ element }) {
  const { config } = element;
  
  const renderFilterInput = () => {
    switch (config.filterType) {
      case 'select':
        return (
          <select className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option>All {config.field || 'items'}</option>
            <option>Option 1</option>
            <option>Option 2</option>
          </select>
        );

      case 'dateRange':
        return (
          <div className="flex gap-3">
            <input
              type="date"
              className="flex-1 px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              type="date"
              className="flex-1 px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        );

      case 'search':
        return (
          <input
            type="text"
            placeholder={`Search ${config.field || 'records'}...`}
            className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        );

      case 'multiSelect':
        return (
          <div className="space-y-2">
            {['Option 1', 'Option 2', 'Option 3'].map((option, index) => (
              <label key={index} className="flex items-center gap-2">
                <input type="checkbox" className="rounded" />
                <span className="text-sm">{option}</span>
              </label>
            ))}
          </div>
        );

      default:
        return (
          <div className="w-full px-3 py-2 border border-neutral-300 rounded-md bg-neutral-50 text-neutral-400">
            No filter type selected
          </div>
        );
    }
  };

  return (
    <div className="py-6">
      <div className="bg-white p-6 rounded-lg border shadow-sm">
        <label className="block text-sm font-medium text-neutral-700 mb-3">
          {config.title || 'Filter'}
        </label>
        {renderFilterInput()}
      </div>
    </div>
  );
}

export function ReportPreview({ elements, volunteerData }) {
  if (elements.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-neutral-400 mb-4">
          <div className="w-16 h-16 mx-auto mb-4 bg-neutral-100 rounded-full flex items-center justify-center">
            📊
          </div>
          <h3 className="text-lg font-medium mb-2">No Elements to Preview</h3>
          <p className="text-neutral-500">
            Add some elements to your report to see the preview.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto bg-white min-h-full">
      <div className="px-8 py-6">
        {elements.map((element) => {
          switch (element.type) {
            case 'header':
              return (
                <PreviewHeader
                  key={element.id}
                  element={element}
                  volunteerData={volunteerData}
                />
              );
            case 'kpi':
              return (
                <PreviewKPI
                  key={element.id}
                  volunteerData={volunteerData}
                />
              );
            case 'divider':
              return <PreviewDivider key={element.id} />;
            case 'metric':
              return (
                <PreviewMetric
                  key={element.id}
                  element={element}
                  volunteerData={volunteerData}
                />
              );
            case 'chart':
              return (
                <PreviewChart
                  key={element.id}
                  element={element}
                  volunteerData={volunteerData}
                />
              );
            case 'filter':
              return (
                <PreviewFilter
                  key={element.id}
                  element={element}
                />
              );
            default:
              return null;
          }
        })}
      </div>
    </div>
  );
}