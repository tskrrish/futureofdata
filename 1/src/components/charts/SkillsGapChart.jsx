import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const SkillsGapChart = ({ organizationGaps }) => {
  const getGapColor = (severity) => {
    switch (severity) {
      case 'critical': return '#ef4444';
      case 'high': return '#f97316';
      case 'medium': return '#eab308';
      case 'low': return '#22c55e';
      default: return '#6b7280';
    }
  };

  const chartData = organizationGaps
    .map(skill => ({
      name: skill.name.length > 15 ? skill.name.substring(0, 15) + '...' : skill.name,
      fullName: skill.name,
      total: skill.coverage.total,
      expert: skill.coverage.expert,
      proficient: skill.coverage.proficient,
      beginner: skill.coverage.beginner,
      severity: skill.gapSeverity,
      category: skill.category
    }))
    .sort((a, b) => {
      const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
      return severityOrder[b.severity] - severityOrder[a.severity];
    })
    .slice(0, 20); // Show top 20 gaps

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length > 0) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900">{data.fullName}</p>
          <p className="text-sm text-gray-600 mb-2">{data.category}</p>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span>Expert:</span>
              <span className="font-medium text-green-600">{data.expert}</span>
            </div>
            <div className="flex justify-between">
              <span>Proficient:</span>
              <span className="font-medium text-blue-600">{data.proficient}</span>
            </div>
            <div className="flex justify-between">
              <span>Beginner:</span>
              <span className="font-medium text-yellow-600">{data.beginner}</span>
            </div>
            <div className="flex justify-between font-semibold border-t pt-1">
              <span>Total:</span>
              <span>{data.total}</span>
            </div>
            <div className="flex justify-between">
              <span>Gap Level:</span>
              <span className={`font-medium ${
                data.severity === 'critical' ? 'text-red-600' :
                data.severity === 'high' ? 'text-orange-600' :
                data.severity === 'medium' ? 'text-yellow-600' : 'text-green-600'
              }`}>
                {data.severity.charAt(0).toUpperCase() + data.severity.slice(1)}
              </span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Skills Gap Analysis</h3>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-red-500 rounded"></div>
            <span>Critical</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-orange-500 rounded"></div>
            <span>High</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-yellow-500 rounded"></div>
            <span>Medium</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-green-500 rounded"></div>
            <span>Low</span>
          </div>
        </div>
      </div>
      
      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{
              top: 5,
              right: 30,
              left: 20,
              bottom: 80,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="name" 
              angle={-45}
              textAnchor="end"
              height={80}
              fontSize={11}
            />
            <YAxis 
              label={{ value: 'Number of Volunteers', angle: -90, position: 'insideLeft' }}
              fontSize={11}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="total">
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getGapColor(entry.severity)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      
      <div className="mt-4 text-sm text-gray-600">
        <p>Shows the top 20 skills with coverage gaps. Bar height represents total volunteers with the skill.</p>
        <p>Colors indicate gap severity based on skill importance and current coverage levels.</p>
      </div>
    </div>
  );
};

export default SkillsGapChart;