import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

const SkillsCategoryChart = ({ categoryStats, viewMode = 'coverage' }) => {
  const COLORS = ['#3b82f6', '#ef4444', '#f97316', '#eab308', '#22c55e', '#8b5cf6', '#ec4899', '#06b6d4'];

  const pieData = categoryStats.map((stat, index) => ({
    name: stat.category,
    value: Math.round(stat.averageCoverage * 10) / 10,
    volunteers: stat.volunteersWithSkills,
    totalSkills: stat.totalSkills,
    criticalGaps: stat.criticalGaps,
    highGaps: stat.highGaps,
    color: COLORS[index % COLORS.length]
  }));

  const barData = categoryStats.map((stat) => ({
    name: stat.category.length > 12 ? stat.category.substring(0, 12) + '...' : stat.category,
    fullName: stat.category,
    coverage: Math.round(stat.averageCoverage * 10) / 10,
    volunteers: stat.volunteersWithSkills,
    critical: stat.criticalGaps,
    high: stat.highGaps,
    totalSkills: stat.totalSkills
  }));

  const CustomPieTooltip = ({ active, payload }) => {
    if (active && payload && payload.length > 0) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900">{data.name}</p>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span>Average Coverage:</span>
              <span className="font-medium">{data.value}%</span>
            </div>
            <div className="flex justify-between">
              <span>Volunteers:</span>
              <span className="font-medium">{data.volunteers}</span>
            </div>
            <div className="flex justify-between">
              <span>Total Skills:</span>
              <span className="font-medium">{data.totalSkills}</span>
            </div>
            <div className="flex justify-between">
              <span>Critical Gaps:</span>
              <span className="font-medium text-red-600">{data.criticalGaps}</span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  const CustomBarTooltip = ({ active, payload }) => {
    if (active && payload && payload.length > 0) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900">{data.fullName}</p>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span>Coverage:</span>
              <span className="font-medium">{data.coverage}%</span>
            </div>
            <div className="flex justify-between">
              <span>Volunteers:</span>
              <span className="font-medium">{data.volunteers}</span>
            </div>
            <div className="flex justify-between">
              <span>Critical Gaps:</span>
              <span className="font-medium text-red-600">{data.critical}</span>
            </div>
            <div className="flex justify-between">
              <span>High Priority Gaps:</span>
              <span className="font-medium text-orange-600">{data.high}</span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  if (viewMode === 'coverage') {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold mb-4">Skills Coverage by Category</h3>
        
        <div className="flex items-center justify-center">
          <div className="w-full h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomPieTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
          {pieData.map((entry) => (
            <div key={entry.name} className="flex items-center gap-2">
              <div 
                className="w-3 h-3 rounded"
                style={{ backgroundColor: entry.color }}
              ></div>
              <span className="text-gray-600">{entry.name}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <h3 className="text-lg font-semibold mb-4">Skills Gap Analysis by Category</h3>
      
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={barData}
            margin={{
              top: 5,
              right: 30,
              left: 20,
              bottom: 60,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="name"
              angle={-45}
              textAnchor="end"
              height={60}
              fontSize={11}
            />
            <YAxis 
              label={{ value: 'Number of Gaps', angle: -90, position: 'insideLeft' }}
              fontSize={11}
            />
            <Tooltip content={<CustomBarTooltip />} />
            <Bar dataKey="critical" stackId="gaps" fill="#ef4444" />
            <Bar dataKey="high" stackId="gaps" fill="#f97316" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 flex items-center gap-4 text-xs">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-red-500 rounded"></div>
          <span>Critical Priority Gaps</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-orange-500 rounded"></div>
          <span>High Priority Gaps</span>
        </div>
      </div>
    </div>
  );
};

export default SkillsCategoryChart;