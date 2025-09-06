import React from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { 
  TrendingUp, 
  TrendingDown, 
  Target, 
  Award, 
  AlertTriangle,
  CheckCircle,
  XCircle 
} from "lucide-react";

/**
 * Performance Summary Dashboard Component
 * Shows overall performance score and status breakdown
 */
export function PerformanceSummaryDashboard({ performanceSummary, insights = [] }) {
  if (!performanceSummary) {
    return (
      <div className="bg-white rounded-2xl border p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Performance Summary</h3>
        <div className="text-center text-gray-500 py-8">
          No performance data available. Please select comparison periods.
        </div>
      </div>
    );
  }

  const { overallScore, statusCounts, totalMetrics, overallStatus } = performanceSummary;

  // Prepare data for pie chart
  const chartData = Object.entries(statusCounts).map(([status, count]) => ({
    name: formatStatusLabel(status),
    value: count,
    status: status,
    percentage: ((count / totalMetrics) * 100).toFixed(1)
  }));

  // Color mapping for status
  const statusColors = {
    excellent: '#10B981',
    good: '#3B82F6', 
    average: '#F59E0B',
    poor: '#EF4444',
    'below-target': '#F97316'
  };

  const getScoreColor = (score) => {
    if (score >= 85) return 'text-green-600 bg-green-100';
    if (score >= 70) return 'text-blue-600 bg-blue-100';
    if (score >= 55) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getOverallStatusIcon = () => {
    switch (overallStatus) {
      case 'excellent':
        return <Award className="w-6 h-6 text-green-600" />;
      case 'good':
        return <CheckCircle className="w-6 h-6 text-blue-600" />;
      case 'average':
        return <AlertTriangle className="w-6 h-6 text-yellow-600" />;
      case 'poor':
        return <XCircle className="w-6 h-6 text-red-600" />;
      default:
        return <Target className="w-6 h-6 text-gray-600" />;
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Overall Score Card */}
      <div className="bg-white rounded-2xl border p-6">
        <div className="text-center">
          <div className="flex items-center justify-center mb-4">
            {getOverallStatusIcon()}
          </div>
          
          <div className={`inline-flex items-center px-4 py-2 rounded-full text-2xl font-bold mb-2 ${getScoreColor(overallScore)}`}>
            {overallScore}
          </div>
          
          <h3 className="text-lg font-semibold text-gray-900 mb-1">
            Overall Performance
          </h3>
          
          <p className="text-sm text-gray-600 capitalize">
            {overallStatus} Performance
          </p>
        </div>

        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{totalMetrics}</div>
            <div className="text-sm text-gray-600">Metrics Evaluated</div>
          </div>
        </div>
      </div>

      {/* Status Distribution */}
      <div className="bg-white rounded-2xl border p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Status Distribution</h3>
        
        <div className="h-48 mb-4">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                outerRadius={80}
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={statusColors[entry.status]} 
                  />
                ))}
              </Pie>
              <Tooltip 
                formatter={(value, name) => [`${value} metrics`, name]}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="space-y-2">
          {chartData.map((item, index) => (
            <div key={index} className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: statusColors[item.status] }}
                />
                <span className="text-sm text-gray-600">{item.name}</span>
              </div>
              <div className="text-sm font-medium text-gray-900">
                {item.value} ({item.percentage}%)
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Key Insights */}
      <div className="bg-white rounded-2xl border p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Key Insights</h3>
        
        {insights.length > 0 ? (
          <div className="space-y-4">
            {insights.slice(0, 4).map((insight, index) => (
              <InsightCard key={index} insight={insight} />
            ))}
            
            {insights.length > 4 && (
              <div className="text-sm text-gray-500 text-center pt-2 border-t border-gray-200">
                +{insights.length - 4} more insights available
              </div>
            )}
          </div>
        ) : (
          <div className="text-center text-gray-500 py-8">
            <Target className="w-8 h-8 mx-auto mb-2 text-gray-300" />
            <p>No specific insights available</p>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Individual insight card component
 */
function InsightCard({ insight }) {
  const { type, metric, message, priority } = insight;

  const getInsightIcon = () => {
    switch (type) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'info':
        return <TrendingUp className="w-4 h-4 text-blue-500" />;
      default:
        return <Target className="w-4 h-4 text-gray-500" />;
    }
  };

  const getBorderColor = () => {
    switch (type) {
      case 'success': return 'border-l-green-500 bg-green-50';
      case 'warning': return 'border-l-yellow-500 bg-yellow-50';
      case 'info': return 'border-l-blue-500 bg-blue-50';
      default: return 'border-l-gray-500 bg-gray-50';
    }
  };

  const getPriorityBadge = () => {
    if (priority === 'high') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
          High
        </span>
      );
    }
    if (priority === 'medium') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
          Med
        </span>
      );
    }
    return null;
  };

  return (
    <div className={`border-l-4 p-3 rounded-r-lg ${getBorderColor()}`}>
      <div className="flex items-start space-x-3">
        {getInsightIcon()}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <h4 className="text-sm font-medium text-gray-900">{metric}</h4>
            {getPriorityBadge()}
          </div>
          <p className="text-sm text-gray-700">{message}</p>
        </div>
      </div>
    </div>
  );
}

/**
 * Format status labels for display
 */
function formatStatusLabel(status) {
  const labels = {
    excellent: 'Excellent',
    good: 'Good',
    average: 'Average', 
    poor: 'Poor',
    'below-target': 'Below Target'
  };
  
  return labels[status] || status;
}