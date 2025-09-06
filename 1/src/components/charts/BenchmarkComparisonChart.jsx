import React from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { TrendingUp, TrendingDown, Target, ArrowUpCircle, ArrowDownCircle } from "lucide-react";

/**
 * Chart component for displaying benchmark performance comparisons
 */
export function BenchmarkComparisonChart({ data, title = "Performance Comparison", height = 400 }) {
  if (!data || !data.comparisons) {
    return (
      <div className="bg-white rounded-2xl border p-6">
        <h3 className="font-semibold text-gray-900 mb-4">{title}</h3>
        <div className="text-center text-gray-500 py-8">
          No benchmark data available. Please select comparison periods.
        </div>
      </div>
    );
  }

  // Transform comparison data for chart display
  const chartData = Object.entries(data.comparisons).map(([key, comparison]) => ({
    metric: formatMetricLabel(key),
    current: comparison.current,
    prior: comparison.prior,
    target: comparison.target || null,
    priorChange: comparison.priorChange,
    status: comparison.status
  }));

  // Color mapping for performance status
  const getStatusColor = (status) => {
    switch (status) {
      case 'excellent': return '#10B981';
      case 'good': return '#3B82F6';
      case 'average': return '#F59E0B';
      case 'poor': return '#EF4444';
      case 'below-target': return '#F97316';
      default: return '#6B7280';
    }
  };

  return (
    <div className="bg-white rounded-2xl border p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="font-semibold text-gray-900">{title}</h3>
        <div className="text-sm text-gray-500">
          {data.current && data.prior ? 
            `Comparing current period to prior period` : 
            'Select periods to compare'
          }
        </div>
      </div>

      <div className="mb-6">
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="metric" 
              tick={{ fontSize: 12 }}
              interval={0}
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip 
              content={<CustomTooltip />}
              cursor={{ fill: 'rgba(0, 0, 0, 0.05)' }}
            />
            <Bar 
              dataKey="prior" 
              name="Prior Period" 
              fill="#E5E7EB"
              radius={[4, 4, 0, 0]}
            />
            <Bar 
              dataKey="current" 
              name="Current Period" 
              radius={[4, 4, 0, 0]}
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getStatusColor(entry.status)} />
              ))}
            </Bar>
            <Bar 
              dataKey="target" 
              name="Target" 
              fill="rgba(239, 68, 68, 0.3)"
              stroke="#EF4444"
              strokeWidth={2}
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Performance indicators */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {chartData.map((item, index) => (
          <MetricCard key={index} data={item} />
        ))}
      </div>
    </div>
  );
}

/**
 * Individual metric performance card
 */
function MetricCard({ data }) {
  const { metric, current, target, priorChange, status } = data;
  
  const getStatusIcon = () => {
    switch (status) {
      case 'excellent':
      case 'good':
        return <ArrowUpCircle className="w-4 h-4 text-green-500" />;
      case 'poor':
        return <ArrowDownCircle className="w-4 h-4 text-red-500" />;
      case 'below-target':
        return <Target className="w-4 h-4 text-orange-500" />;
      default:
        return <TrendingUp className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusMessage = () => {
    if (priorChange > 0) {
      return `+${priorChange}% vs prior`;
    } else if (priorChange < 0) {
      return `${priorChange}% vs prior`;
    }
    return 'No change vs prior';
  };

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-medium text-gray-700">{metric}</h4>
        {getStatusIcon()}
      </div>
      
      <div className="space-y-1">
        <div className="text-lg font-semibold text-gray-900">
          {formatValue(current, metric)}
        </div>
        
        <div className="text-xs text-gray-500">
          {getStatusMessage()}
        </div>
        
        {target && (
          <div className="text-xs text-gray-500">
            Target: {formatValue(target, metric)}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Custom tooltip for the chart
 */
function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    
    return (
      <div className="bg-white border rounded-lg shadow-lg p-3">
        <p className="font-medium text-gray-900 mb-2">{label}</p>
        
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center justify-between space-x-4">
            <div className="flex items-center space-x-2">
              <div 
                className="w-3 h-3 rounded"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-sm text-gray-600">{entry.name}:</span>
            </div>
            <span className="text-sm font-medium">
              {formatValue(entry.value, label)}
            </span>
          </div>
        ))}
        
        {data.priorChange !== 0 && (
          <div className="mt-2 pt-2 border-t border-gray-200">
            <div className="flex items-center space-x-2">
              {data.priorChange > 0 ? 
                <TrendingUp className="w-3 h-3 text-green-500" /> : 
                <TrendingDown className="w-3 h-3 text-red-500" />
              }
              <span className="text-xs text-gray-500">
                {data.priorChange > 0 ? '+' : ''}{data.priorChange}% change
              </span>
            </div>
          </div>
        )}
      </div>
    );
  }
  
  return null;
}

/**
 * Format metric labels for display
 */
function formatMetricLabel(key) {
  const labels = {
    totalHours: 'Total Hours',
    activeVolunteers: 'Active Volunteers',
    memberVolunteers: 'Member Volunteers', 
    avgHoursPerVolunteer: 'Avg Hours/Volunteer',
    memberEngagementRate: 'Member Rate (%)',
    totalProjects: 'Total Projects'
  };
  
  return labels[key] || key;
}

/**
 * Format values for display based on metric type
 */
function formatValue(value, metric) {
  if (typeof value !== 'number') return 'N/A';
  
  if (metric.includes('Rate') || metric.includes('%')) {
    return `${value}%`;
  }
  
  if (metric.includes('Hours')) {
    return `${value}h`;
  }
  
  return value.toString();
}