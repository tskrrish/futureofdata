import React, { useMemo } from "react";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from "recharts";

const CHART_COLORS = ["#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6", "#06B6D4"];

export function ChartCell({ content, isEditing, volunteerData, onChange }) {
  const chartOptions = [
    { value: "bar", label: "Bar Chart" },
    { value: "line", label: "Line Chart" },
    { value: "pie", label: "Pie Chart" }
  ];

  const dataOptions = [
    { value: "hoursByBranch", label: "Hours by Branch" },
    { value: "activesByBranch", label: "Active Volunteers by Branch" },
    { value: "memberShareByBranch", label: "Member Share by Branch" },
    { value: "trendByMonth", label: "Monthly Trends" },
    { value: "projectCategoryStats", label: "Project Category Statistics" },
    { value: "leaderboard", label: "Top Volunteers" }
  ];

  const chartData = useMemo(() => {
    if (!content.dataSource || !volunteerData) return [];

    switch (content.dataSource) {
      case "hoursByBranch":
        return volunteerData.hoursByBranch?.slice(0, 10) || [];
      
      case "activesByBranch":
        return volunteerData.activesByBranch?.slice(0, 10) || [];
      
      case "memberShareByBranch":
        return volunteerData.memberShareByBranch?.slice(0, 8) || [];
      
      case "trendByMonth":
        return volunteerData.trendByMonth || [];
      
      case "projectCategoryStats":
        return volunteerData.projectCategoryStats?.slice(0, 8) || [];
      
      case "leaderboard":
        return volunteerData.leaderboard?.slice(0, 10) || [];
      
      default:
        return [];
    }
  }, [content.dataSource, volunteerData]);

  const renderChart = () => {
    if (!chartData.length) {
      return (
        <div className="h-64 flex items-center justify-center text-gray-500">
          No data available for selected source
        </div>
      );
    }

    const chartProps = {
      data: chartData,
      height: 300
    };

    switch (content.chartType) {
      case "bar":
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart {...chartProps}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey={getXAxisKey(content.dataSource)} 
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis />
              <Tooltip />
              <Legend />
              {getYAxisKeys(content.dataSource).map((key, index) => (
                <Bar 
                  key={key} 
                  dataKey={key} 
                  fill={CHART_COLORS[index % CHART_COLORS.length]} 
                  name={formatKeyName(key)}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );

      case "line":
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart {...chartProps}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={getXAxisKey(content.dataSource)} />
              <YAxis />
              <Tooltip />
              <Legend />
              {getYAxisKeys(content.dataSource).map((key, index) => (
                <Line 
                  key={key}
                  type="monotone" 
                  dataKey={key} 
                  stroke={CHART_COLORS[index % CHART_COLORS.length]}
                  name={formatKeyName(key)}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );

      case "pie": {
        const pieData = chartData.slice(0, 8).map((item, index) => ({
          name: item[getXAxisKey(content.dataSource)],
          value: item[getYAxisKeys(content.dataSource)[0]],
          fill: CHART_COLORS[index % CHART_COLORS.length]
        }));

        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                outerRadius={80}
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        );
      }

      default:
        return <div className="h-64 flex items-center justify-center">Select a chart type</div>;
    }
  };

  if (isEditing) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Chart Type</label>
            <select
              value={content.chartType || "bar"}
              onChange={(e) => onChange({ ...content, chartType: e.target.value })}
              className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {chartOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Data Source</label>
            <select
              value={content.dataSource || ""}
              onChange={(e) => onChange({ ...content, dataSource: e.target.value })}
              className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select data source...</option>
              {dataOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Title</label>
          <input
            type="text"
            value={content.title || ""}
            onChange={(e) => onChange({ ...content, title: e.target.value })}
            placeholder="Chart title..."
            className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="border rounded-lg p-4 bg-gray-50">
          <h4 className="font-medium mb-2">Preview:</h4>
          {renderChart()}
        </div>
      </div>
    );
  }

  return (
    <div>
      {content.title && (
        <h3 className="text-lg font-semibold mb-4">{content.title}</h3>
      )}
      {renderChart()}
      {chartData.length > 0 && (
        <p className="text-sm text-gray-500 mt-2">
          Showing {chartData.length} data points
        </p>
      )}
    </div>
  );
}

function getXAxisKey(dataSource) {
  const keyMap = {
    hoursByBranch: "branch",
    activesByBranch: "branch", 
    memberShareByBranch: "branch",
    trendByMonth: "month",
    projectCategoryStats: "project_tag",
    leaderboard: "assignee"
  };
  return keyMap[dataSource] || "name";
}

function getYAxisKeys(dataSource) {
  const keyMap = {
    hoursByBranch: ["hours"],
    activesByBranch: ["active"],
    memberShareByBranch: ["members", "active"],
    trendByMonth: ["hours", "active"],
    projectCategoryStats: ["hours", "volunteers"],
    leaderboard: ["hours"]
  };
  return keyMap[dataSource] || ["value"];
}

function formatKeyName(key) {
  const nameMap = {
    hours: "Hours",
    active: "Active Volunteers",
    members: "Member Volunteers", 
    volunteers: "Volunteers",
    assignee: "Volunteer",
    branch: "Branch",
    project_tag: "Project Category"
  };
  return nameMap[key] || key;
}