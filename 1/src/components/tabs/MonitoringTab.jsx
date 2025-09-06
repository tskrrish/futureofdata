import React, { useState } from 'react';
import { Plus, Activity, TrendingUp, AlertTriangle } from 'lucide-react';
import { MonitoringOverview } from '../monitoring/MonitoringOverview';
import { SyntheticCheckCard } from '../monitoring/SyntheticCheckCard';
import { PerformanceBudgetCard } from '../monitoring/PerformanceBudgetCard';
import { AlertsPanel } from '../monitoring/AlertsPanel';
import { 
  SAMPLE_SYNTHETIC_CHECKS, 
  SAMPLE_PERFORMANCE_BUDGETS, 
  SAMPLE_MONITORING_ALERTS 
} from '../../data/monitoringData';
import { createDefaultSyntheticCheck, createDefaultPerformanceBudget } from '../../types/monitoring';

export function MonitoringTab() {
  const [syntheticChecks, setSyntheticChecks] = useState(SAMPLE_SYNTHETIC_CHECKS);
  const [performanceBudgets, setPerformanceBudgets] = useState(SAMPLE_PERFORMANCE_BUDGETS);
  const [alerts, setAlerts] = useState(SAMPLE_MONITORING_ALERTS);
  const [activeSection, setActiveSection] = useState('overview');
  const [_isAddingCheck, _setIsAddingCheck] = useState(false);
  const [_isAddingBudget, _setIsAddingBudget] = useState(false);

  const handleToggleCheck = (checkId) => {
    setSyntheticChecks(checks => 
      checks.map(check => 
        check.id === checkId ? { ...check, enabled: !check.enabled } : check
      )
    );
  };

  const handleDeleteCheck = (checkId) => {
    setSyntheticChecks(checks => checks.filter(check => check.id !== checkId));
  };

  const handleToggleBudget = (budgetId) => {
    setPerformanceBudgets(budgets =>
      budgets.map(budget =>
        budget.id === budgetId ? { ...budget, enabled: !budget.enabled } : budget
      )
    );
  };

  const handleDeleteBudget = (budgetId) => {
    setPerformanceBudgets(budgets => budgets.filter(budget => budget.id !== budgetId));
  };

  const handleResolveAlert = (alertId) => {
    setAlerts(alerts =>
      alerts.map(alert =>
        alert.id === alertId ? { ...alert, resolved: true } : alert
      )
    );
  };

  const handleDismissAlert = (alertId) => {
    setAlerts(alerts => alerts.filter(alert => alert.id !== alertId));
  };

  const handleAddCheck = () => {
    const newCheck = createDefaultSyntheticCheck();
    newCheck.name = `New Check ${syntheticChecks.length + 1}`;
    newCheck.url = 'https://example.com';
    setSyntheticChecks([...syntheticChecks, newCheck]);
  };

  const handleAddBudget = () => {
    const newBudget = createDefaultPerformanceBudget();
    newBudget.name = `New Budget ${performanceBudgets.length + 1}`;
    newBudget.url = 'https://example.com';
    newBudget.overallStatus = 'passing';
    setPerformanceBudgets([...performanceBudgets, newBudget]);
  };

  const TabButton = ({ id, label, icon, count }) => (
    <button
      className={`flex items-center gap-2 px-4 py-2 text-sm ${
        activeSection === id ? 'bg-neutral-100' : 'hover:bg-neutral-50'
      }`}
      onClick={() => setActiveSection(id)}
    >
      {icon}
      {label}
      {count !== undefined && (
        <span className="bg-gray-200 text-gray-700 text-xs px-1.5 py-0.5 rounded-full">
          {count}
        </span>
      )}
    </button>
  );

  const activeAlerts = alerts.filter(alert => !alert.resolved);

  return (
    <div className="bg-white rounded-2xl border mt-6 overflow-hidden">
      {/* Tab Navigation */}
      <div className="border-b">
        <div className="flex">
          <TabButton
            id="overview"
            label="Overview"
            icon={<Activity className="w-4 h-4" />}
          />
          <TabButton
            id="synthetic"
            label="Synthetic Checks"
            icon={<Activity className="w-4 h-4" />}
            count={syntheticChecks.length}
          />
          <TabButton
            id="budgets"
            label="Performance Budgets"
            icon={<TrendingUp className="w-4 h-4" />}
            count={performanceBudgets.length}
          />
          <TabButton
            id="alerts"
            label="Alerts"
            icon={<AlertTriangle className="w-4 h-4" />}
            count={activeAlerts.length}
          />
        </div>
      </div>

      <div className="p-6">
        {activeSection === 'overview' && (
          <MonitoringOverview
            syntheticChecks={syntheticChecks}
            performanceBudgets={performanceBudgets}
            alerts={alerts}
          />
        )}

        {activeSection === 'synthetic' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">Synthetic Checks</h2>
              <button
                onClick={handleAddCheck}
                className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus className="w-4 h-4" />
                Add Check
              </button>
            </div>

            <div className="grid gap-4">
              {syntheticChecks.map((check) => (
                <SyntheticCheckCard
                  key={check.id}
                  check={check}
                  onEdit={() => {}} // TODO: Implement edit modal
                  onToggle={handleToggleCheck}
                  onDelete={handleDeleteCheck}
                />
              ))}
            </div>

            {syntheticChecks.length === 0 && (
              <div className="text-center py-12">
                <Activity className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Synthetic Checks</h3>
                <p className="text-gray-600 mb-4">Create your first synthetic check to monitor your endpoints.</p>
                <button
                  onClick={handleAddCheck}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Add Your First Check
                </button>
              </div>
            )}
          </div>
        )}

        {activeSection === 'budgets' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">Performance Budgets</h2>
              <button
                onClick={handleAddBudget}
                className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus className="w-4 h-4" />
                Add Budget
              </button>
            </div>

            <div className="grid gap-4">
              {performanceBudgets.map((budget) => (
                <PerformanceBudgetCard
                  key={budget.id}
                  budget={budget}
                  onEdit={() => {}} // TODO: Implement edit modal
                  onToggle={handleToggleBudget}
                  onDelete={handleDeleteBudget}
                />
              ))}
            </div>

            {performanceBudgets.length === 0 && (
              <div className="text-center py-12">
                <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Performance Budgets</h3>
                <p className="text-gray-600 mb-4">Set performance budgets to track your site's performance metrics.</p>
                <button
                  onClick={handleAddBudget}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Add Your First Budget
                </button>
              </div>
            )}
          </div>
        )}

        {activeSection === 'alerts' && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-gray-900">Monitoring Alerts</h2>
            <AlertsPanel
              alerts={alerts}
              onResolveAlert={handleResolveAlert}
              onDismissAlert={handleDismissAlert}
            />
          </div>
        )}
      </div>
    </div>
  );
}