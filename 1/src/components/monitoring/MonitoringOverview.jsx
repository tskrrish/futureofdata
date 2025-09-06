import React from 'react';
import { Activity, Globe, TrendingUp, AlertTriangle } from 'lucide-react';
import { CheckStatus } from '../../types/monitoring';

export function MonitoringOverview({ syntheticChecks, performanceBudgets, alerts }) {
  const calculateSyntheticStats = () => {
    const enabled = syntheticChecks.filter(check => check.enabled);
    const passing = enabled.filter(check => check.status === CheckStatus.SUCCESS);
    const failing = enabled.filter(check => check.status === CheckStatus.FAILURE);
    const warning = enabled.filter(check => check.status === CheckStatus.WARNING);
    
    const avgSuccessRate = enabled.length > 0 
      ? enabled.reduce((sum, check) => sum + (check.successRate || 0), 0) / enabled.length
      : 0;

    return {
      total: enabled.length,
      passing: passing.length,
      failing: failing.length,
      warning: warning.length,
      avgSuccessRate: avgSuccessRate.toFixed(1)
    };
  };

  const calculateBudgetStats = () => {
    const enabled = performanceBudgets.filter(budget => budget.enabled);
    const passing = enabled.filter(budget => budget.overallStatus === 'passing');
    const failing = enabled.filter(budget => budget.overallStatus === 'failing');
    const warning = enabled.filter(budget => budget.overallStatus === 'warning');

    return {
      total: enabled.length,
      passing: passing.length,
      failing: failing.length,
      warning: warning.length
    };
  };

  const calculateAlertStats = () => {
    const active = alerts.filter(alert => !alert.resolved);
    const critical = active.filter(alert => alert.severity === 'error');
    const warnings = active.filter(alert => alert.severity === 'warning');

    return {
      active: active.length,
      critical: critical.length,
      warnings: warnings.length
    };
  };

  const syntheticStats = calculateSyntheticStats();
  const budgetStats = calculateBudgetStats();
  const alertStats = calculateAlertStats();

  const StatCard = ({ icon, title, value, subtitle, status }) => {
    const getStatusColor = () => {
      switch (status) {
        case 'success':
          return 'border-green-200 bg-green-50';
        case 'warning':
          return 'border-yellow-200 bg-yellow-50';
        case 'error':
          return 'border-red-200 bg-red-50';
        default:
          return 'border-gray-200 bg-white';
      }
    };

    return (
      <div className={`p-4 rounded-lg border ${getStatusColor()}`}>
        <div className="flex items-center gap-2 mb-2">
          {icon}
          <h3 className="font-medium text-gray-900">{title}</h3>
        </div>
        <div className="text-2xl font-bold text-gray-900 mb-1">{value}</div>
        {subtitle && <div className="text-sm text-gray-600">{subtitle}</div>}
      </div>
    );
  };

  const getOverallStatus = () => {
    if (alertStats.critical > 0 || syntheticStats.failing > 0 || budgetStats.failing > 0) {
      return 'error';
    }
    if (alertStats.warnings > 0 || syntheticStats.warning > 0 || budgetStats.warning > 0) {
      return 'warning';
    }
    return 'success';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">Monitoring Overview</h2>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${
          getOverallStatus() === 'success' ? 'bg-green-100 text-green-800' :
          getOverallStatus() === 'warning' ? 'bg-yellow-100 text-yellow-800' :
          'bg-red-100 text-red-800'
        }`}>
          System {getOverallStatus() === 'success' ? 'Healthy' : 
                 getOverallStatus() === 'warning' ? 'Degraded' : 'Critical'}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Activity className="w-5 h-5 text-blue-500" />}
          title="Synthetic Checks"
          value={`${syntheticStats.passing}/${syntheticStats.total}`}
          subtitle={`${syntheticStats.avgSuccessRate}% avg success rate`}
          status={syntheticStats.failing > 0 ? 'error' : syntheticStats.warning > 0 ? 'warning' : 'success'}
        />

        <StatCard
          icon={<TrendingUp className="w-5 h-5 text-green-500" />}
          title="Performance Budgets"
          value={`${budgetStats.passing}/${budgetStats.total}`}
          subtitle={`${budgetStats.failing} failing budgets`}
          status={budgetStats.failing > 0 ? 'error' : budgetStats.warning > 0 ? 'warning' : 'success'}
        />

        <StatCard
          icon={<AlertTriangle className="w-5 h-5 text-yellow-500" />}
          title="Active Alerts"
          value={alertStats.active}
          subtitle={`${alertStats.critical} critical, ${alertStats.warnings} warnings`}
          status={alertStats.critical > 0 ? 'error' : alertStats.warnings > 0 ? 'warning' : 'success'}
        />

        <StatCard
          icon={<Globe className="w-5 h-5 text-purple-500" />}
          title="Endpoints Monitored"
          value={syntheticStats.total + budgetStats.total}
          subtitle="Across synthetic & performance"
          status="default"
        />
      </div>

      {(syntheticStats.failing > 0 || budgetStats.failing > 0 || alertStats.active > 0) && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-5 h-5 text-yellow-600" />
            <h3 className="font-medium text-yellow-800">Attention Required</h3>
          </div>
          <ul className="text-sm text-yellow-700 space-y-1">
            {syntheticStats.failing > 0 && (
              <li>• {syntheticStats.failing} synthetic check{syntheticStats.failing !== 1 ? 's' : ''} failing</li>
            )}
            {budgetStats.failing > 0 && (
              <li>• {budgetStats.failing} performance budget{budgetStats.failing !== 1 ? 's' : ''} exceeded</li>
            )}
            {alertStats.active > 0 && (
              <li>• {alertStats.active} active alert{alertStats.active !== 1 ? 's' : ''} need attention</li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}