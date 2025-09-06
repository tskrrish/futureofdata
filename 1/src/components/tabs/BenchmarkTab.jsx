import React, { useState } from "react";
import { Calendar, Target, Settings, RefreshCw, Download } from "lucide-react";

import { useBenchmarkData } from "../../hooks/useBenchmarkData";
import { exportCSV } from "../../utils/csvUtils";
import { BenchmarkComparisonChart } from "../charts/BenchmarkComparisonChart";
import { PerformanceSummaryDashboard } from "../charts/PerformanceSummaryDashboard";

/**
 * Main Benchmark Tab Component
 * Displays performance comparison between current and prior periods vs targets
 */
export function BenchmarkTab({ data }) {
  const {
    benchmarkData,
    insights,
    performanceSummary,
    branchBenchmarks,
    availablePeriods,
    currentPeriod,
    priorPeriod,
    priorPeriodOptions,
    setCurrentPeriod,
    setPriorPeriod,
    defaultTargets,
    customTargets,
    activeTargets,
    updateTarget,
    resetTargets,
    isReady
  } = useBenchmarkData(data);

  const [showTargetSettings, setShowTargetSettings] = useState(false);

  // Export benchmark data
  const exportBenchmarkData = () => {
    if (!benchmarkData) return;

    const exportData = Object.entries(benchmarkData.comparisons).map(([metric, comparison]) => ({
      metric,
      current_value: comparison.current,
      prior_value: comparison.prior,
      target_value: comparison.target || '',
      prior_change_percent: comparison.priorChange,
      target_progress_percent: comparison.targetProgress || '',
      status: comparison.status
    }));

    exportCSV('benchmark_comparison.csv', exportData);
  };

  // Export branch benchmarks
  const exportBranchBenchmarks = () => {
    if (!branchBenchmarks.length) return;

    const exportData = branchBenchmarks.map(branch => ({
      branch: branch.branch,
      current_hours: branch.current.totalHours,
      prior_hours: branch.prior.totalHours,
      current_volunteers: branch.current.activeVolunteers,
      prior_volunteers: branch.prior.activeVolunteers,
      hours_change_percent: branch.comparisons.totalHours.priorChange,
      volunteers_change_percent: branch.comparisons.activeVolunteers.priorChange
    }));

    exportCSV('branch_benchmarks.csv', exportData);
  };

  return (
    <div className="space-y-6 mt-4">
      {/* Controls Header */}
      <div className="bg-white rounded-2xl border p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">
              Benchmark Performance Comparison
            </h2>
            <p className="text-sm text-gray-600">
              Compare current period performance to prior period and targets
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowTargetSettings(!showTargetSettings)}
              className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              <Settings className="w-4 h-4 mr-2" />
              Targets
            </button>
            
            {benchmarkData && (
              <button
                onClick={exportBenchmarkData}
                className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                <Download className="w-4 h-4 mr-2" />
                Export
              </button>
            )}
          </div>
        </div>

        {/* Period Selection */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Calendar className="w-4 h-4 inline mr-2" />
              Current Period
            </label>
            <select
              value={currentPeriod}
              onChange={(e) => setCurrentPeriod(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select current period</option>
              {availablePeriods.map(period => (
                <option key={period} value={period}>{period}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Calendar className="w-4 h-4 inline mr-2" />
              Prior Period (for comparison)
            </label>
            <select
              value={priorPeriod}
              onChange={(e) => setPriorPeriod(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={!currentPeriod}
            >
              <option value="">Select prior period</option>
              {priorPeriodOptions.map(period => (
                <option key={period} value={period}>{period}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Target Settings Panel */}
        {showTargetSettings && (
          <TargetSettingsPanel
            targets={activeTargets}
            customTargets={customTargets}
            defaultTargets={defaultTargets}
            onUpdateTarget={updateTarget}
            onResetTargets={resetTargets}
          />
        )}
      </div>

      {/* Performance Summary Dashboard */}
      {isReady && (
        <PerformanceSummaryDashboard 
          performanceSummary={performanceSummary}
          insights={insights}
        />
      )}

      {/* Main Benchmark Comparison Chart */}
      {isReady && (
        <BenchmarkComparisonChart 
          data={benchmarkData}
          title={`Performance Comparison: ${currentPeriod} vs ${priorPeriod}`}
        />
      )}

      {/* Branch-Level Benchmarks */}
      {isReady && branchBenchmarks.length > 0 && (
        <div className="bg-white rounded-2xl border p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-semibold text-gray-900">Branch Performance</h3>
            <button
              onClick={exportBranchBenchmarks}
              className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              <Download className="w-4 h-4 mr-2" />
              Export Branch Data
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-900">Branch</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-900">Current Hours</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-900">Prior Hours</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-900">Hours Change</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-900">Current Volunteers</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-900">Prior Volunteers</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-900">Volunteer Change</th>
                </tr>
              </thead>
              <tbody>
                {branchBenchmarks.map((branch, index) => (
                  <BranchBenchmarkRow key={index} data={branch} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* No Data State */}
      {!isReady && (
        <div className="bg-white rounded-2xl border p-12 text-center">
          <Calendar className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Select Comparison Periods
          </h3>
          <p className="text-gray-600">
            Choose current and prior periods above to view benchmark comparisons
          </p>
        </div>
      )}
    </div>
  );
}

/**
 * Target Settings Panel Component
 */
function TargetSettingsPanel({ targets, customTargets, defaultTargets, onUpdateTarget, onResetTargets }) {
  const targetLabels = {
    totalHours: 'Total Hours Target',
    activeVolunteers: 'Active Volunteers Target',
    memberVolunteers: 'Member Volunteers Target',
    avgHoursPerVolunteer: 'Avg Hours per Volunteer Target',
    memberEngagementRate: 'Member Engagement Rate Target (%)',
    totalProjects: 'Total Projects Target'
  };

  return (
    <div className="mt-6 pt-6 border-t border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h4 className="font-medium text-gray-900">
          <Target className="w-4 h-4 inline mr-2" />
          Target Values
        </h4>
        <button
          onClick={onResetTargets}
          className="inline-flex items-center px-3 py-1 text-xs font-medium text-gray-600 hover:text-gray-900"
        >
          <RefreshCw className="w-3 h-3 mr-1" />
          Reset to Defaults
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(targetLabels).map(([key, label]) => (
          <div key={key}>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              {label}
            </label>
            <div className="relative">
              <input
                type="number"
                value={targets[key] || ''}
                onChange={(e) => onUpdateTarget(key, e.target.value)}
                placeholder={`Default: ${defaultTargets[key] || 'N/A'}`}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {customTargets[key] && (
                <div className="absolute right-2 top-1/2 transform -translate-y-1/2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full" title="Custom target set" />
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Branch Benchmark Table Row Component
 */
function BranchBenchmarkRow({ data }) {
  const { branch, current, prior, comparisons } = data;

  const formatChange = (change) => {
    if (change === 0) return '0%';
    return `${change > 0 ? '+' : ''}${change}%`;
  };

  const getChangeClass = (change) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50">
      <td className="py-3 px-4 font-medium text-gray-900">{branch}</td>
      <td className="py-3 px-4 text-right">{current.totalHours}h</td>
      <td className="py-3 px-4 text-right text-gray-600">{prior.totalHours}h</td>
      <td className={`py-3 px-4 text-right font-medium ${getChangeClass(comparisons.totalHours.priorChange)}`}>
        {formatChange(comparisons.totalHours.priorChange)}
      </td>
      <td className="py-3 px-4 text-right">{current.activeVolunteers}</td>
      <td className="py-3 px-4 text-right text-gray-600">{prior.activeVolunteers}</td>
      <td className={`py-3 px-4 text-right font-medium ${getChangeClass(comparisons.activeVolunteers.priorChange)}`}>
        {formatChange(comparisons.activeVolunteers.priorChange)}
      </td>
    </tr>
  );
}