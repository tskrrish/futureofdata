import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export const StaffUtilizationChart = ({ staffUtilization }) => {
  const chartData = staffUtilization.map(staff => ({
    name: staff.name.split(' ')[0],
    utilization: Math.round(staff.utilizationRate * 100),
    hours: staff.assignedHours,
    maxHours: staff.maxHours,
    roles: staff.roles.join(', ')
  }));

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 rounded-lg shadow-lg border">
          <p className="font-semibold">{label}</p>
          <p className="text-sm text-gray-600">Utilization: {data.utilization}%</p>
          <p className="text-sm text-gray-600">Hours: {data.hours}/{data.maxHours}</p>
          <p className="text-sm text-gray-600">Roles: {data.roles}</p>
        </div>
      );
    }
    return null;
  };

  const getBarColor = (utilization) => {
    if (utilization >= 90) return '#ef4444'; // red-500
    if (utilization >= 80) return '#f59e0b'; // amber-500
    if (utilization >= 60) return '#10b981'; // emerald-500
    return '#6b7280'; // gray-500
  };

  return (
    <div className="bg-white p-4 rounded-lg border">
      <h3 className="font-semibold text-gray-900 mb-4">Staff Utilization</h3>
      
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="name" 
            tick={{ fontSize: 12 }}
          />
          <YAxis 
            domain={[0, 100]}
            tick={{ fontSize: 12 }}
            label={{ value: 'Utilization %', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar 
            dataKey="utilization" 
            fill={(entry) => getBarColor(entry.utilization)}
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
      
      <div className="mt-4 flex items-center justify-center gap-6 text-xs">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-gray-500 rounded"></div>
          <span>Under 60%</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-emerald-500 rounded"></div>
          <span>60-79%</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-amber-500 rounded"></div>
          <span>80-89%</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-red-500 rounded"></div>
          <span>90%+</span>
        </div>
      </div>
    </div>
  );
};