import React from 'react';
import { AlertTriangle, CheckCircle, Info, X } from 'lucide-react';

const SeverityIcon = ({ severity }) => {
  switch (severity) {
    case 'error':
      return <X className="w-5 h-5 text-red-500" />;
    case 'warning':
      return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
    case 'info':
      return <Info className="w-5 h-5 text-blue-500" />;
    default:
      return <AlertTriangle className="w-5 h-5 text-gray-500" />;
  }
};

export function AlertsPanel({ alerts, onResolveAlert, onDismissAlert }) {
  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'error':
        return 'border-l-red-500 bg-red-50';
      case 'warning':
        return 'border-l-yellow-500 bg-yellow-50';
      case 'info':
        return 'border-l-blue-500 bg-blue-50';
      default:
        return 'border-l-gray-500 bg-gray-50';
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const activeAlerts = alerts.filter(alert => !alert.resolved);
  const resolvedAlerts = alerts.filter(alert => alert.resolved);

  if (alerts.length === 0) {
    return (
      <div className="bg-white rounded-lg border p-6 text-center">
        <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">All Clear!</h3>
        <p className="text-gray-600">No active alerts at this time.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {activeAlerts.length > 0 && (
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-3">
            Active Alerts ({activeAlerts.length})
          </h3>
          <div className="space-y-3">
            {activeAlerts.map((alert) => (
              <div
                key={alert.id}
                className={`border-l-4 p-4 rounded-r-lg ${getSeverityColor(alert.severity)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <SeverityIcon severity={alert.severity} />
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">{alert.title}</h4>
                      <p className="text-sm text-gray-700 mt-1">{alert.message}</p>
                      
                      {(alert.threshold && alert.actual) && (
                        <div className="mt-2 text-xs text-gray-600">
                          <span className="font-medium">Threshold:</span> {alert.threshold}ms • 
                          <span className="font-medium"> Actual:</span> {alert.actual}ms
                        </div>
                      )}
                      
                      <div className="text-xs text-gray-500 mt-2">
                        {formatTimestamp(alert.timestamp)}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex gap-2">
                    <button
                      onClick={() => onResolveAlert(alert.id)}
                      className="text-xs px-2 py-1 rounded bg-green-100 text-green-700 hover:bg-green-200"
                    >
                      Resolve
                    </button>
                    <button
                      onClick={() => onDismissAlert(alert.id)}
                      className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-700 hover:bg-gray-200"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {resolvedAlerts.length > 0 && (
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-3">
            Recent Resolved ({resolvedAlerts.slice(0, 5).length})
          </h3>
          <div className="space-y-2">
            {resolvedAlerts.slice(0, 5).map((alert) => (
              <div
                key={alert.id}
                className="border rounded-lg p-3 bg-gray-50 opacity-75"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-green-500 mt-0.5" />
                    <div>
                      <h4 className="text-sm font-medium text-gray-700">{alert.title}</h4>
                      <p className="text-xs text-gray-600">{alert.message}</p>
                      <div className="text-xs text-gray-500 mt-1">
                        Resolved • {formatTimestamp(alert.timestamp)}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}