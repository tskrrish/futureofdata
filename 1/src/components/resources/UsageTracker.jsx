import React, { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { Activity, TrendingUp, Clock, Package } from "lucide-react";
import { KPI } from "../ui/KPI";

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

export function UsageTracker({ resources, assignments, onFetchStats }) {
  const [utilizationStats, setUtilizationStats] = useState(null);
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0]
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchStats();
  }, [dateRange]);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const stats = await onFetchStats(dateRange);
      setUtilizationStats(stats);
    } catch (error) {
      console.error('Failed to fetch utilization stats:', error);
    } finally {
      setLoading(false);
    }
  };

  // Calculate basic stats from assignments
  const basicStats = React.useMemo(() => {
    const totalAssignments = assignments.length;
    const activeAssignments = assignments.filter(a => 
      ['assigned', 'checked_out', 'in_use'].includes(a.status)
    ).length;
    const completedAssignments = assignments.filter(a => a.status === 'returned').length;
    const completionRate = totalAssignments > 0 ? (completedAssignments / totalAssignments * 100).toFixed(1) : 0;

    return {
      totalAssignments,
      activeAssignments,
      completedAssignments,
      completionRate
    };
  }, [assignments]);

  // Resource utilization data
  const resourceUtilization = React.useMemo(() => {
    const resourceUsage = {};
    
    assignments.forEach(assignment => {
      const resource = resources.find(r => r.id === assignment.resource_id);
      if (resource) {
        const key = resource.name;
        if (!resourceUsage[key]) {
          resourceUsage[key] = {
            name: key,
            total: 0,
            active: 0,
            completed: 0
          };
        }
        resourceUsage[key].total += 1;
        if (['assigned', 'checked_out', 'in_use'].includes(assignment.status)) {
          resourceUsage[key].active += 1;
        }
        if (assignment.status === 'returned') {
          resourceUsage[key].completed += 1;
        }
      }
    });

    return Object.values(resourceUsage).sort((a, b) => b.total - a.total);
  }, [resources, assignments]);

  // Status distribution for pie chart
  const statusDistribution = React.useMemo(() => {
    const statusCount = {};
    
    assignments.forEach(assignment => {
      const status = assignment.status;
      statusCount[status] = (statusCount[status] || 0) + 1;
    });

    return Object.entries(statusCount).map(([status, count]) => ({
      name: status.replace('_', ' ').toUpperCase(),
      value: count,
      percentage: ((count / assignments.length) * 100).toFixed(1)
    }));
  }, [assignments]);

  return (
    <div className="space-y-6">
      {/* Date Range Filter */}
      <div className="bg-white rounded-2xl border p-6">
        <div className="flex flex-wrap items-center gap-4 mb-4">
          <h2 className="text-lg font-semibold">Usage Analytics</h2>
          <div className="flex items-center gap-2">
            <label className="text-sm text-neutral-600">From:</label>
            <input
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
              className="px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <label className="text-sm text-neutral-600">To:</label>
            <input
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
              className="px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={fetchStats}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Refresh'}
            </button>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KPI 
            icon={<Activity className="w-5 h-5" />} 
            label="Total Assignments" 
            value={basicStats.totalAssignments} 
          />
          <KPI 
            icon={<Clock className="w-5 h-5" />} 
            label="Active Now" 
            value={basicStats.activeAssignments} 
          />
          <KPI 
            icon={<Package className="w-5 h-5" />} 
            label="Completed" 
            value={basicStats.completedAssignments} 
          />
          <KPI 
            icon={<TrendingUp className="w-5 h-5" />} 
            label="Completion Rate" 
            value={`${basicStats.completionRate}%`} 
          />
        </div>
      </div>

      {/* Charts */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Resource Utilization Chart */}
        <div className="bg-white rounded-2xl border p-6">
          <h3 className="text-lg font-semibold mb-4">Resource Utilization</h3>
          {resourceUtilization.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={resourceUtilization.slice(0, 8)} margin={{ top: 5, right: 30, left: 20, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="name" 
                    angle={-45}
                    textAnchor="end"
                    height={80}
                    fontSize={12}
                  />
                  <YAxis fontSize={12} />
                  <Tooltip />
                  <Bar dataKey="total" fill="#3B82F6" name="Total Assignments" />
                  <Bar dataKey="completed" fill="#10B981" name="Completed" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-neutral-500">
              <div className="text-center">
                <Package className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No utilization data available</p>
              </div>
            </div>
          )}
        </div>

        {/* Status Distribution Pie Chart */}
        <div className="bg-white rounded-2xl border p-6">
          <h3 className="text-lg font-semibold mb-4">Assignment Status Distribution</h3>
          {statusDistribution.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={statusDistribution}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percentage }) => `${name} (${percentage}%)`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {statusDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-neutral-500">
              <div className="text-center">
                <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No status data available</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Detailed Statistics */}
      {utilizationStats && (
        <div className="bg-white rounded-2xl border p-6">
          <h3 className="text-lg font-semibold mb-4">Detailed Statistics</h3>
          <div className="grid md:grid-cols-3 gap-6">
            <div>
              <h4 className="font-medium text-neutral-700 mb-2">Assignment Metrics</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-neutral-600">Total Assignments:</span>
                  <span className="font-medium">{utilizationStats.total_assignments}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-600">Check-out Rate:</span>
                  <span className="font-medium">{utilizationStats.checkout_rate}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-600">Return Rate:</span>
                  <span className="font-medium">{utilizationStats.return_rate}%</span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-neutral-700 mb-2">Usage Duration</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-neutral-600">Average Duration:</span>
                  <span className="font-medium">
                    {Math.floor(utilizationStats.average_usage_duration_minutes / 60)}h{' '}
                    {Math.round(utilizationStats.average_usage_duration_minutes % 60)}m
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-600">Total Checkouts:</span>
                  <span className="font-medium">{utilizationStats.total_checkouts}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-600">Total Returns:</span>
                  <span className="font-medium">{utilizationStats.total_returns}</span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-neutral-700 mb-2">Period Info</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-neutral-600">Date Range:</span>
                  <span className="font-medium">{utilizationStats.period_days} days</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-600">Generated:</span>
                  <span className="font-medium">
                    {new Date(utilizationStats.generated_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Resource-Specific Stats Table */}
      {resourceUtilization.length > 0 && (
        <div className="bg-white rounded-2xl border p-6">
          <h3 className="text-lg font-semibold mb-4">Resource Usage Summary</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-neutral-50">
                <tr>
                  <th className="text-left p-3 font-medium text-neutral-700">Resource</th>
                  <th className="text-center p-3 font-medium text-neutral-700">Total Assignments</th>
                  <th className="text-center p-3 font-medium text-neutral-700">Currently Active</th>
                  <th className="text-center p-3 font-medium text-neutral-700">Completed</th>
                  <th className="text-center p-3 font-medium text-neutral-700">Utilization</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200">
                {resourceUtilization.map((resource, index) => {
                  const utilizationRate = resource.total > 0 
                    ? ((resource.completed / resource.total) * 100).toFixed(1)
                    : 0;
                  
                  return (
                    <tr key={index} className="hover:bg-neutral-50">
                      <td className="p-3 font-medium">{resource.name}</td>
                      <td className="p-3 text-center">{resource.total}</td>
                      <td className="p-3 text-center">{resource.active}</td>
                      <td className="p-3 text-center">{resource.completed}</td>
                      <td className="p-3 text-center">{utilizationRate}%</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}