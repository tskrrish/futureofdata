import React from 'react';
import { AlertTriangle, X, Users, Calendar } from 'lucide-react';
import { ALERT_LEVELS } from '../../data/eventCapacityData';

export const CapacityAlert = ({ alert, onDismiss, compact = false }) => {
  const alertConfig = ALERT_LEVELS[alert.alertLevel];
  const bgColor = {
    critical: 'bg-red-50 border-red-200',
    high: 'bg-red-50 border-red-200',
    medium: 'bg-yellow-50 border-yellow-200',
    low: 'bg-blue-50 border-blue-200'
  }[alert.alertLevel];

  const textColor = {
    critical: 'text-red-800',
    high: 'text-red-700',
    medium: 'text-yellow-700',
    low: 'text-blue-700'
  }[alert.alertLevel];

  const iconColor = {
    critical: 'text-red-500',
    high: 'text-red-500',
    medium: 'text-yellow-500',
    low: 'text-blue-500'
  }[alert.alertLevel];

  if (compact) {
    return (
      <div className={`flex items-center gap-2 p-2 rounded-lg border ${bgColor}`}>
        <AlertTriangle className={`w-4 h-4 ${iconColor}`} />
        <span className={`text-sm ${textColor} flex-1`}>
          {alert.eventName}: {alert.shortage} staff needed
        </span>
      </div>
    );
  }

  return (
    <div className={`p-4 rounded-lg border ${bgColor} relative`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 flex-1">
          <AlertTriangle className={`w-5 h-5 ${iconColor} mt-0.5`} />
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h4 className={`font-semibold ${textColor}`}>
                {alert.eventName}
              </h4>
              <span className={`px-2 py-1 rounded-full text-xs font-medium bg-${alertConfig.color}-100 text-${alertConfig.color}-800`}>
                {alert.alertLevel.toUpperCase()}
              </span>
            </div>
            
            <div className="flex items-center gap-4 text-sm text-gray-600 mb-2">
              <div className="flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                {new Date(alert.date).toLocaleDateString()}
              </div>
              <div className="flex items-center gap-1">
                <Users className="w-4 h-4" />
                {alert.branch}
              </div>
            </div>
            
            <p className={`text-sm ${textColor}`}>
              {alert.message}
            </p>
            
            <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
              <span>Staffing: {Math.round(alert.staffingRatio * 100)}%</span>
              <span>Status: {alert.status.replace('_', ' ')}</span>
            </div>
          </div>
        </div>
        
        {onDismiss && (
          <button
            onClick={() => onDismiss(alert.eventId)}
            className={`p-1 rounded hover:bg-${alertConfig.color}-100 ${textColor}`}
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};