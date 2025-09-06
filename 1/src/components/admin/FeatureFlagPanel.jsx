import React, { useState, useEffect } from 'react';
import { Settings, ToggleLeft, ToggleRight, TrendingUp, Users, Activity } from 'lucide-react';
import featureFlags from '../../services/featureFlags.js';
import metrics from '../../services/metrics.js';

export function FeatureFlagPanel() {
  const [flags, setFlags] = useState({});
  const [metrics_data, setMetricsData] = useState({});
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    const allFlags = featureFlags.getAllFlags();
    const flagMetrics = metrics.getFeatureFlagMetrics();
    setFlags(allFlags);
    setMetricsData(flagMetrics);
  };

  const handleToggle = (flagName) => {
    const flag = flags[flagName];
    if (flag.isEnabled) {
      featureFlags.forceDisable(flagName);
    } else {
      featureFlags.forceEnable(flagName);
    }
    loadData();
  };

  const handleRolloutChange = (flagName, percentage) => {
    featureFlags.setRollout(flagName, parseInt(percentage));
    loadData();
  };

  // Admin panel toggle (accessible via keyboard shortcut)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'F') {
        e.preventDefault();
        setIsVisible(!isVisible);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isVisible]);

  if (!isVisible) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={() => setIsVisible(true)}
          className="bg-gray-800 text-white p-2 rounded-full shadow-lg hover:bg-gray-700"
          title="Feature Flags Admin (Ctrl+Shift+F)"
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Settings className="w-6 h-6 text-blue-600" />
              <h2 className="text-2xl font-bold text-gray-900">Feature Flags & Telemetry</h2>
            </div>
            <button
              onClick={() => setIsVisible(false)}
              className="text-gray-400 hover:text-gray-600 text-2xl"
            >
              ×
            </button>
          </div>
          <p className="text-gray-600 mt-2">Manage feature rollouts and monitor metrics</p>
        </div>

        <div className="p-6 space-y-6">
          {/* Feature Flags */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Feature Flags</h3>
            <div className="space-y-4">
              {Object.entries(flags).map(([flagName, flag]) => {
                const flagMetrics = metrics_data[flagName] || { enabled: 0, disabled: 0, total: 0 };
                
                return (
                  <div key={flagName} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => handleToggle(flagName)}
                          className="flex items-center gap-2"
                        >
                          {flag.isEnabled ? (
                            <ToggleRight className="w-6 h-6 text-green-600" />
                          ) : (
                            <ToggleLeft className="w-6 h-6 text-gray-400" />
                          )}
                        </button>
                        <div>
                          <h4 className="font-semibold text-gray-900">{flagName}</h4>
                          <p className="text-sm text-gray-600">
                            {flag.isEnabled ? 'Enabled' : 'Disabled'} • Rollout: {flag.rollout}%
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 text-sm">
                        <div className="flex items-center gap-1 text-green-600">
                          <Users className="w-4 h-4" />
                          {flagMetrics.enabled}
                        </div>
                        <div className="flex items-center gap-1 text-gray-500">
                          <Users className="w-4 h-4" />
                          {flagMetrics.disabled}
                        </div>
                      </div>
                    </div>

                    {flag.enabled && (
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-700">
                          Rollout Percentage: {flag.rollout}%
                        </label>
                        <div className="flex items-center gap-3">
                          <input
                            type="range"
                            min="0"
                            max="100"
                            value={flag.rollout}
                            onChange={(e) => handleRolloutChange(flagName, e.target.value)}
                            className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none slider"
                          />
                          <input
                            type="number"
                            min="0"
                            max="100"
                            value={flag.rollout}
                            onChange={(e) => handleRolloutChange(flagName, e.target.value)}
                            className="w-16 px-2 py-1 border border-gray-300 rounded text-sm"
                          />
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${flag.rollout}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {flagMetrics.total > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-100">
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <span>Success Rate: {((flagMetrics.enabled / flagMetrics.total) * 100).toFixed(1)}%</span>
                          <span>Total Evaluations: {flagMetrics.total}</span>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Metrics Summary */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Telemetry Metrics</h3>
            <TelemetryMetrics />
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t border-gray-200">
            <button
              onClick={() => metrics.exportMetrics()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              <TrendingUp className="w-4 h-4" />
              Export Metrics
            </button>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
            >
              Reload App
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function TelemetryMetrics() {
  const [summary, setSummary] = useState({});

  useEffect(() => {
    const loadSummary = () => {
      const data = metrics.getSummaryMetrics();
      setSummary(data);
    };

    loadSummary();
    const interval = setInterval(loadSummary, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="bg-blue-50 p-4 rounded-lg">
        <div className="flex items-center gap-2 mb-2">
          <Activity className="w-5 h-5 text-blue-600" />
          <h4 className="font-semibold text-blue-900">Session</h4>
        </div>
        <p className="text-2xl font-bold text-blue-800">
          {Math.round((summary.sessionDuration || 0) / 1000)}s
        </p>
        <p className="text-sm text-blue-600">Active session</p>
      </div>

      <div className="bg-green-50 p-4 rounded-lg">
        <div className="flex items-center gap-2 mb-2">
          <Users className="w-5 h-5 text-green-600" />
          <h4 className="font-semibold text-green-900">Interactions</h4>
        </div>
        <p className="text-2xl font-bold text-green-800">
          {Object.values(summary.userBehavior || {}).reduce((a, b) => a + b, 0)}
        </p>
        <p className="text-sm text-green-600">Total actions</p>
      </div>

      <div className="bg-purple-50 p-4 rounded-lg">
        <div className="flex items-center gap-2 mb-2">
          <TrendingUp className="w-5 h-5 text-purple-600" />
          <h4 className="font-semibold text-purple-900">Page Views</h4>
        </div>
        <p className="text-2xl font-bold text-purple-800">
          {Object.keys(summary.pageViews || {}).length}
        </p>
        <p className="text-sm text-purple-600">Unique pages</p>
      </div>
    </div>
  );
}