import React from 'react';
import { CheckCircle, XCircle, AlertTriangle, Clock, Globe, Activity } from 'lucide-react';
import { CheckStatus, CheckTypes } from '../../types/monitoring';

const StatusIcon = ({ status }) => {
  switch (status) {
    case CheckStatus.SUCCESS:
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    case CheckStatus.FAILURE:
      return <XCircle className="w-5 h-5 text-red-500" />;
    case CheckStatus.WARNING:
      return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
    default:
      return <Clock className="w-5 h-5 text-gray-500" />;
  }
};

const TypeIcon = ({ type }) => {
  switch (type) {
    case CheckTypes.PAGE_LOAD:
      return <Globe className="w-4 h-4" />;
    case CheckTypes.API_RESPONSE:
      return <Activity className="w-4 h-4" />;
    default:
      return <Globe className="w-4 h-4" />;
  }
};

export function SyntheticCheckCard({ check, onEdit, onToggle, onDelete }) {
  const getStatusColor = (status) => {
    switch (status) {
      case CheckStatus.SUCCESS:
        return 'border-green-200 bg-green-50';
      case CheckStatus.FAILURE:
        return 'border-red-200 bg-red-50';
      case CheckStatus.WARNING:
        return 'border-yellow-200 bg-yellow-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  const formatDuration = (ms) => {
    return ms ? `${ms}ms` : 'N/A';
  };

  const formatInterval = (ms) => {
    const minutes = Math.floor(ms / 60000);
    return `${minutes}m`;
  };

  const formatLastRun = (timestamp) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  return (
    <div className={`border rounded-lg p-4 ${getStatusColor(check.status)}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <StatusIcon status={check.status} />
          <div>
            <h3 className="font-medium text-gray-900">{check.name}</h3>
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <TypeIcon type={check.type} />
              <span className="capitalize">{check.type.replace('_', ' ')}</span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-1">
          <button
            onClick={() => onToggle(check.id)}
            className={`text-xs px-2 py-1 rounded ${
              check.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
            }`}
          >
            {check.enabled ? 'Enabled' : 'Disabled'}
          </button>
          <button
            onClick={() => onEdit(check)}
            className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-700 hover:bg-blue-200"
          >
            Edit
          </button>
          <button
            onClick={() => onDelete(check.id)}
            className="text-xs px-2 py-1 rounded bg-red-100 text-red-700 hover:bg-red-200"
          >
            Delete
          </button>
        </div>
      </div>

      <div className="text-sm text-gray-600 mb-3">
        <div className="font-mono bg-gray-100 px-2 py-1 rounded text-xs mb-2">
          {check.method} {check.url}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
        <div>
          <span className="text-gray-500">Last Duration</span>
          <div className="font-medium">{formatDuration(check.lastDuration)}</div>
        </div>
        <div>
          <span className="text-gray-500">Success Rate</span>
          <div className="font-medium">{check.successRate?.toFixed(1)}%</div>
        </div>
        <div>
          <span className="text-gray-500">Interval</span>
          <div className="font-medium">{formatInterval(check.interval)}</div>
        </div>
        <div>
          <span className="text-gray-500">Last Run</span>
          <div className="font-medium">{formatLastRun(check.lastRun)}</div>
        </div>
      </div>
    </div>
  );
}