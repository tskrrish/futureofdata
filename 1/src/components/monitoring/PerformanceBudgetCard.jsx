import React from 'react';
import { CheckCircle, XCircle, AlertTriangle, TrendingUp, Globe } from 'lucide-react';
import { BudgetMetrics } from '../../types/monitoring';

const MetricNames = {
  [BudgetMetrics.RESPONSE_TIME]: 'Response Time',
  [BudgetMetrics.PAGE_LOAD_TIME]: 'Page Load Time',
  [BudgetMetrics.FIRST_CONTENTFUL_PAINT]: 'First Contentful Paint',
  [BudgetMetrics.LARGEST_CONTENTFUL_PAINT]: 'Largest Contentful Paint',
  [BudgetMetrics.CUMULATIVE_LAYOUT_SHIFT]: 'Cumulative Layout Shift',
  [BudgetMetrics.TOTAL_BLOCKING_TIME]: 'Total Blocking Time'
};

const StatusIcon = ({ status }) => {
  switch (status) {
    case 'passing':
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    case 'failing':
      return <XCircle className="w-4 h-4 text-red-500" />;
    case 'warning':
      return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
    default:
      return <AlertTriangle className="w-4 h-4 text-gray-500" />;
  }
};

export function PerformanceBudgetCard({ budget, onEdit, onToggle, onDelete }) {
  const getOverallStatusColor = (status) => {
    switch (status) {
      case 'passing':
        return 'border-green-200 bg-green-50';
      case 'failing':
        return 'border-red-200 bg-red-50';
      case 'warning':
        return 'border-yellow-200 bg-yellow-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  const formatMetricValue = (metric, value) => {
    if (metric === BudgetMetrics.CUMULATIVE_LAYOUT_SHIFT) {
      return value?.toFixed(3) || '0.000';
    }
    return `${value || 0}ms`;
  };

  const formatLastCheck = (timestamp) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  const enabledMetrics = Object.entries(budget.metrics).filter(([, metric]) => metric.enabled);
  const passingCount = enabledMetrics.filter(([, metric]) => metric.status === 'passing').length;
  const failingCount = enabledMetrics.filter(([, metric]) => metric.status === 'failing').length;

  return (
    <div className={`border rounded-lg p-4 ${getOverallStatusColor(budget.overallStatus)}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <StatusIcon status={budget.overallStatus} />
          <div>
            <h3 className="font-medium text-gray-900">{budget.name}</h3>
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <Globe className="w-4 h-4" />
              <span className="font-mono text-xs">{budget.url}</span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-1">
          <button
            onClick={() => onToggle(budget.id)}
            className={`text-xs px-2 py-1 rounded ${
              budget.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
            }`}
          >
            {budget.enabled ? 'Enabled' : 'Disabled'}
          </button>
          <button
            onClick={() => onEdit(budget)}
            className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-700 hover:bg-blue-200"
          >
            Edit
          </button>
          <button
            onClick={() => onDelete(budget.id)}
            className="text-xs px-2 py-1 rounded bg-red-100 text-red-700 hover:bg-red-200"
          >
            Delete
          </button>
        </div>
      </div>

      <div className="mb-3 flex items-center gap-4 text-sm">
        <div className="flex items-center gap-1">
          <CheckCircle className="w-4 h-4 text-green-500" />
          <span className="text-green-700">{passingCount} passing</span>
        </div>
        {failingCount > 0 && (
          <div className="flex items-center gap-1">
            <XCircle className="w-4 h-4 text-red-500" />
            <span className="text-red-700">{failingCount} failing</span>
          </div>
        )}
        <div className="text-gray-500 text-xs ml-auto">
          Last check: {formatLastCheck(budget.lastCheck)}
        </div>
      </div>

      <div className="space-y-2">
        {enabledMetrics.slice(0, 4).map(([metricKey, metric]) => (
          <div key={metricKey} className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <StatusIcon status={metric.status} />
              <span className="text-gray-700">{MetricNames[metricKey]}</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-gray-500">
                {formatMetricValue(metricKey, metric.current)} / {formatMetricValue(metricKey, metric.threshold)}
              </span>
              <TrendingUp className="w-3 h-3 text-gray-400" />
            </div>
          </div>
        ))}
        
        {enabledMetrics.length > 4 && (
          <div className="text-xs text-gray-500 text-center pt-2">
            +{enabledMetrics.length - 4} more metrics
          </div>
        )}
      </div>
    </div>
  );
}