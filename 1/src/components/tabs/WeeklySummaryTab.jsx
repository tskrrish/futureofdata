import React, { useState } from 'react';
import { Calendar, TrendingUp, Users, Award, FileText, Download, ChevronLeft, ChevronRight } from 'lucide-react';
import { useWeeklySummary } from '../../hooks/useWeeklySummary';

export function WeeklySummaryTab({ data }) {
  const { weeks, currentWeek, getWeekById, weekOptions, stats, hasData } = useWeeklySummary(data);
  const [selectedWeekId, setSelectedWeekId] = useState(currentWeek?.startDate || (weeks[0]?.startDate || null));
  const [viewMode, setViewMode] = useState('summary'); // 'summary' or 'recap'
  
  const selectedWeek = getWeekById(selectedWeekId);

  const handlePreviousWeek = () => {
    const currentIndex = weekOptions.findIndex(w => w.value === selectedWeekId);
    if (currentIndex < weekOptions.length - 1) {
      setSelectedWeekId(weekOptions[currentIndex + 1].value);
    }
  };

  const handleNextWeek = () => {
    const currentIndex = weekOptions.findIndex(w => w.value === selectedWeekId);
    if (currentIndex > 0) {
      setSelectedWeekId(weekOptions[currentIndex - 1].value);
    }
  };

  const exportSummary = () => {
    if (!selectedWeek) return;
    
    const content = viewMode === 'recap' ? selectedWeek.autoRecap : JSON.stringify(selectedWeek, null, 2);
    const filename = `weekly_summary_${selectedWeek.startDate}.${viewMode === 'recap' ? 'md' : 'json'}`;
    
    const blob = new Blob([content], { type: viewMode === 'recap' ? 'text/markdown' : 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!hasData) {
    return (
      <div className="mt-4 p-8 text-center bg-white rounded-2xl border">
        <Calendar className="w-12 h-12 mx-auto text-gray-400 mb-4" />
        <h3 className="text-lg font-semibold text-gray-600 mb-2">No Weekly Data Available</h3>
        <p className="text-gray-500">Upload volunteer data to see automated weekly performance summaries.</p>
      </div>
    );
  }

  return (
    <div className="mt-4 space-y-6">
      {/* Header Controls */}
      <div className="bg-white rounded-2xl border p-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="flex items-center gap-3">
            <Calendar className="w-5 h-5 text-blue-600" />
            <h2 className="text-xl font-semibold">Weekly Performance Summaries</h2>
          </div>
          
          <div className="flex items-center gap-3">
            {/* View Mode Toggle */}
            <div className="inline-flex rounded-lg border bg-gray-50 overflow-hidden">
              <button
                onClick={() => setViewMode('summary')}
                className={`px-3 py-1 text-sm ${viewMode === 'summary' ? 'bg-white shadow-sm' : 'hover:bg-gray-100'}`}
              >
                Data View
              </button>
              <button
                onClick={() => setViewMode('recap')}
                className={`px-3 py-1 text-sm ${viewMode === 'recap' ? 'bg-white shadow-sm' : 'hover:bg-gray-100'}`}
              >
                Auto Recap
              </button>
            </div>
            
            {/* Export Button */}
            <button
              onClick={exportSummary}
              className="inline-flex items-center gap-2 px-3 py-1 text-sm border rounded-lg hover:bg-gray-50"
            >
              <Download className="w-4 h-4" />
              Export
            </button>
          </div>
        </div>

        {/* Week Navigation */}
        <div className="flex items-center justify-between mt-4 p-3 bg-gray-50 rounded-lg">
          <button
            onClick={handlePreviousWeek}
            disabled={weekOptions.findIndex(w => w.value === selectedWeekId) === weekOptions.length - 1}
            className="p-1 rounded-md hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          
          <div className="text-center">
            <h3 className="font-semibold">{selectedWeek?.weekLabel}</h3>
            <p className="text-sm text-gray-600">
              Week {weekOptions.findIndex(w => w.value === selectedWeekId) + 1} of {weekOptions.length}
            </p>
          </div>
          
          <button
            onClick={handleNextWeek}
            disabled={weekOptions.findIndex(w => w.value === selectedWeekId) === 0}
            className="p-1 rounded-md hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>

      {selectedWeek && (
        <>
          {viewMode === 'summary' ? (
            <WeeklySummaryView week={selectedWeek} />
          ) : (
            <WeeklyRecapView week={selectedWeek} />
          )}
        </>
      )}

      {/* Overall Stats */}
      {stats && (
        <div className="bg-white rounded-2xl border p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Overall Trends
          </h3>
          
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{stats.totalWeeks}</div>
              <div className="text-sm text-blue-800">Weeks Tracked</div>
            </div>
            
            <div className="p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{stats.totalHoursAllWeeks}</div>
              <div className="text-sm text-green-800">Total Hours</div>
            </div>
            
            <div className="p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{stats.avgHoursPerWeek}</div>
              <div className="text-sm text-purple-800">Avg Hours/Week</div>
            </div>
            
            <div className="p-4 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">{stats.mostActiveWeek.hours}</div>
              <div className="text-sm text-orange-800">Best Week</div>
              <div className="text-xs text-orange-600">{stats.mostActiveWeek.week}</div>
            </div>
          </div>

          {stats.mostConsistentBranch && (
            <div className="mt-4 p-4 bg-yellow-50 rounded-lg">
              <div className="flex items-center gap-2 text-yellow-800">
                <Award className="w-4 h-4" />
                <span className="font-semibold">Most Consistent Branch:</span>
              </div>
              <div className="text-yellow-900">
                <strong>{stats.mostConsistentBranch.branch}</strong> appeared in {stats.mostConsistentBranch.appearances} of {stats.totalWeeks} weeks ({stats.mostConsistentBranch.percentage}%)
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function WeeklySummaryView({ week }) {
  return (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          icon={<TrendingUp className="w-5 h-5" />}
          label="Total Hours"
          value={week.summary.totalHours}
          color="blue"
          comparison={week.previousWeekComparison ? {
            value: week.previousWeekComparison.hours,
            label: "vs last week"
          } : null}
        />
        
        <MetricCard
          icon={<Users className="w-5 h-5" />}
          label="Volunteers"
          value={week.summary.volunteers}
          color="green"
          comparison={week.previousWeekComparison ? {
            value: week.previousWeekComparison.volunteers,
            label: "vs last week"
          } : null}
        />
        
        <MetricCard
          icon={<Award className="w-5 h-5" />}
          label="Branches Active"
          value={week.summary.branches}
          color="purple"
        />
        
        <MetricCard
          icon={<FileText className="w-5 h-5" />}
          label="Projects"
          value={week.summary.projects}
          color="orange"
        />
      </div>

      {/* Callouts */}
      {week.callouts.length > 0 && (
        <div className="bg-white rounded-2xl border p-6">
          <h3 className="text-lg font-semibold mb-4">Key Highlights</h3>
          <div className="grid gap-4">
            {week.callouts.map((callout, index) => (
              <CalloutCard key={index} callout={callout} />
            ))}
          </div>
        </div>
      )}

      {/* Branch Performance */}
      <div className="bg-white rounded-2xl border p-6">
        <h3 className="text-lg font-semibold mb-4">Branch Performance</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">Branch</th>
                <th className="text-right py-2">Hours</th>
                <th className="text-right py-2">Volunteers</th>
                <th className="text-right py-2">Projects</th>
                <th className="text-right py-2">Member Rate</th>
              </tr>
            </thead>
            <tbody>
              {week.branchPerformance.map((branch, index) => (
                <tr key={branch.branch} className="border-b last:border-b-0">
                  <td className="py-2">
                    <span className="flex items-center gap-2">
                      {index < 3 && (
                        <span className="text-lg">
                          {index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉'}
                        </span>
                      )}
                      {branch.branch}
                    </span>
                  </td>
                  <td className="text-right py-2 font-semibold">{branch.hours}</td>
                  <td className="text-right py-2">{branch.volunteers}</td>
                  <td className="text-right py-2">{branch.projects}</td>
                  <td className="text-right py-2">{branch.memberRate}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Top Volunteers */}
      {week.topVolunteers.length > 0 && (
        <div className="bg-white rounded-2xl border p-6">
          <h3 className="text-lg font-semibold mb-4">Top Contributors</h3>
          <div className="space-y-3">
            {week.topVolunteers.map((volunteer, index) => (
              <div key={volunteer.volunteer} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="text-lg">
                    {index === 0 ? '🏆' : index === 1 ? '🥈' : index === 2 ? '🥉' : '⭐'}
                  </span>
                  <span className="font-medium">{volunteer.volunteer}</span>
                </div>
                <span className="font-bold text-blue-600">{volunteer.hours} hours</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function WeeklyRecapView({ week }) {
  return (
    <div className="bg-white rounded-2xl border p-6">
      <div className="prose max-w-none">
        <div 
          className="whitespace-pre-wrap font-mono text-sm leading-relaxed"
          dangerouslySetInnerHTML={{ 
            __html: week.autoRecap
              .replace(/^# /gm, '<h1 class="text-2xl font-bold mb-4 text-gray-900">')
              .replace(/^## /gm, '<h2 class="text-xl font-semibold mb-3 text-gray-800">')
              .replace(/^### /gm, '<h3 class="text-lg font-semibold mb-2 text-gray-700">')
              .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')
              .replace(/\*(.*?)\*/g, '<em class="italic">$1</em>')
              .replace(/\n\n/g, '</p><p class="mb-3">')
              .replace(/^/, '<p class="mb-3">')
              .replace(/$/, '</p>')
          }}
        />
      </div>
    </div>
  );
}

function MetricCard({ icon, label, value, color, comparison }) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600', 
    purple: 'bg-purple-50 text-purple-600',
    orange: 'bg-orange-50 text-orange-600'
  };

  const comparisonDiff = comparison ? value - comparison.value : 0;
  const comparisonPercentage = comparison && comparison.value > 0 ? 
    ((comparisonDiff / comparison.value) * 100).toFixed(1) : null;

  return (
    <div className={`p-4 rounded-lg ${colorClasses[color]}`}>
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-sm font-medium">{label}</span>
      </div>
      <div className="text-2xl font-bold">{value}</div>
      {comparison && (
        <div className="text-xs mt-1">
          <span className={`${comparisonDiff >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {comparisonDiff >= 0 ? '+' : ''}{comparisonDiff} ({comparisonPercentage}%)
          </span>
          <span className="text-gray-600 ml-1">{comparison.label}</span>
        </div>
      )}
    </div>
  );
}

function CalloutCard({ callout }) {
  const typeStyles = {
    success: 'bg-green-50 border-green-200 text-green-800',
    spotlight: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800',
    warning: 'bg-orange-50 border-orange-200 text-orange-800'
  };

  return (
    <div className={`p-4 rounded-lg border ${typeStyles[callout.type] || typeStyles.info}`}>
      <h4 className="font-semibold text-sm mb-1">{callout.title}</h4>
      <p className="text-sm">{callout.message}</p>
    </div>
  );
}