import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import { TrendingUp, TrendingDown, Users, MessageSquare, ThumbsUp, AlertTriangle } from 'lucide-react';
import { calculateNPS, NPS_CATEGORIES } from '../../data/npsData';

export function NPSAnalytics({ surveyResponses, onExport }) {
  // Calculate overall NPS score
  const overallNPS = calculateNPS(surveyResponses);
  
  // Category breakdown
  const categoryData = Object.keys(NPS_CATEGORIES).map(category => {
    const categoryResponses = surveyResponses.filter(r => r.category === category);
    return {
      name: category,
      count: categoryResponses.length,
      percentage: Math.round((categoryResponses.length / surveyResponses.length) * 100),
      color: NPS_CATEGORIES[category].color
    };
  });

  // Branch breakdown
  const branchData = surveyResponses.reduce((acc, response) => {
    const branch = response.branch;
    if (!acc[branch]) {
      acc[branch] = { branch, responses: [], totalScore: 0 };
    }
    acc[branch].responses.push(response);
    acc[branch].totalScore += response.npsScore;
    return acc;
  }, {});

  const branchNPSData = Object.values(branchData).map(branch => ({
    branch: branch.branch,
    nps: calculateNPS(branch.responses),
    avgScore: Math.round((branch.totalScore / branch.responses.length) * 10) / 10,
    responseCount: branch.responses.length
  }));

  // Time trend (mock monthly data)
  const trendData = [
    { month: 'Jan', nps: 45 },
    { month: 'Feb', nps: 52 },
    { month: 'Mar', nps: 48 },
    { month: 'Apr', nps: 55 },
    { month: 'May', nps: 62 },
    { month: 'Jun', nps: 58 },
    { month: 'Jul', nps: overallNPS }
  ];

  // Common improvement areas
  const improvementAreas = surveyResponses.reduce((acc, response) => {
    response.improvementAreas.forEach(area => {
      acc[area] = (acc[area] || 0) + 1;
    });
    return acc;
  }, {});

  const topImprovements = Object.entries(improvementAreas)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 5)
    .map(([area, count]) => ({ area, count }));

  // Response rate and engagement metrics
  const avgResponseTime = Math.round(
    surveyResponses.reduce((sum, r) => sum + r.responseTime, 0) / surveyResponses.length
  );

  const volunteerAgainRate = Math.round(
    (surveyResponses.filter(r => r.wouldVolunteerAgain).length / surveyResponses.length) * 100
  );

  return (
    <div className="space-y-8">
      {/* Header Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-xl border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Overall NPS Score</p>
              <p className="text-3xl font-bold text-gray-900">{overallNPS}</p>
            </div>
            <div className={`p-3 rounded-full ${overallNPS >= 50 ? 'bg-green-100' : overallNPS >= 0 ? 'bg-yellow-100' : 'bg-red-100'}`}>
              {overallNPS >= 50 ? (
                <TrendingUp className="w-6 h-6 text-green-600" />
              ) : (
                <TrendingDown className="w-6 h-6 text-red-600" />
              )}
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            {overallNPS >= 50 ? 'Excellent' : overallNPS >= 0 ? 'Good' : 'Needs Improvement'}
          </p>
        </div>

        <div className="bg-white p-6 rounded-xl border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Survey Responses</p>
              <p className="text-3xl font-bold text-gray-900">{surveyResponses.length}</p>
            </div>
            <div className="p-3 rounded-full bg-blue-100">
              <Users className="w-6 h-6 text-blue-600" />
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-2">From {new Set(surveyResponses.map(r => r.branch)).size} branches</p>
        </div>

        <div className="bg-white p-6 rounded-xl border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Response Time</p>
              <p className="text-3xl font-bold text-gray-900">{Math.floor(avgResponseTime / 60)}m {avgResponseTime % 60}s</p>
            </div>
            <div className="p-3 rounded-full bg-purple-100">
              <MessageSquare className="w-6 h-6 text-purple-600" />
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-2">Time to complete survey</p>
        </div>

        <div className="bg-white p-6 rounded-xl border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Would Volunteer Again</p>
              <p className="text-3xl font-bold text-gray-900">{volunteerAgainRate}%</p>
            </div>
            <div className="p-3 rounded-full bg-green-100">
              <ThumbsUp className="w-6 h-6 text-green-600" />
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-2">Volunteer retention indicator</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* NPS Category Distribution */}
        <div className="bg-white p-6 rounded-xl border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">NPS Category Distribution</h3>
            <button
              onClick={() => onExport('nps_categories')}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Export
            </button>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={categoryData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="count"
              >
                {categoryData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value, name, props) => [`${value} (${props.payload.percentage}%)`, props.payload.name]} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-4 mt-4">
            {categoryData.map((category) => (
              <div key={category.name} className="flex items-center">
                <div
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: category.color }}
                ></div>
                <span className="text-sm text-gray-600">
                  {category.name} ({category.count})
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Branch Performance */}
        <div className="bg-white p-6 rounded-xl border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">NPS by Branch</h3>
            <button
              onClick={() => onExport('branch_nps')}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Export
            </button>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={branchNPSData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="branch" fontSize={12} />
              <YAxis />
              <Tooltip formatter={(value) => [`${value}`, 'NPS Score']} />
              <Bar dataKey="nps" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* NPS Trend Over Time */}
        <div className="bg-white p-6 rounded-xl border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">NPS Trend Over Time</h3>
            <button
              onClick={() => onExport('nps_trend')}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Export
            </button>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip formatter={(value) => [`${value}`, 'NPS Score']} />
              <Line type="monotone" dataKey="nps" stroke="#3b82f6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Top Improvement Areas */}
        <div className="bg-white p-6 rounded-xl border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Top Improvement Areas</h3>
            <button
              onClick={() => onExport('improvement_areas')}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Export
            </button>
          </div>
          <div className="space-y-3">
            {topImprovements.map((item) => (
              <div key={item.area} className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-6 h-6 bg-red-100 rounded-full flex items-center justify-center mr-3">
                    <AlertTriangle className="w-3 h-3 text-red-600" />
                  </div>
                  <span className="text-sm font-medium">{item.area}</span>
                </div>
                <div className="flex items-center">
                  <span className="text-sm text-gray-600 mr-2">{item.count} mentions</span>
                  <div className="w-16 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-red-500 h-2 rounded-full"
                      style={{ width: `${(item.count / Math.max(...topImprovements.map(i => i.count))) * 100}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Feedback */}
      <div className="bg-white p-6 rounded-xl border">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Recent Feedback</h3>
          <button
            onClick={() => onExport('recent_feedback')}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            Export All
          </button>
        </div>
        <div className="grid gap-4">
          {surveyResponses.slice(0, 3).map((response) => (
            <div key={response.id} className="border-l-4 border-gray-200 pl-4 py-2">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <p className="font-medium text-sm">{response.volunteerName}</p>
                  <p className="text-xs text-gray-500">{response.projectName} • {response.branch}</p>
                </div>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  response.npsScore >= 9 ? 'bg-green-100 text-green-800' :
                  response.npsScore >= 7 ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {response.npsScore}/10
                </span>
              </div>
              <p className="text-sm text-gray-700 italic">"{response.feedback}"</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}