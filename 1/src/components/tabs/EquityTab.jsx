import React from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";
import { TrendingUp, Users, Target, Award, AlertTriangle, CheckCircle, Info } from "lucide-react";

export function EquityTab({ participationParity, accessIndicators, equitySummary, equityInsights }) {
  
  const getInsightIcon = (type) => {
    switch (type) {
      case "success": return <CheckCircle className="w-5 h-5 text-green-600" />;
      case "warning": return <AlertTriangle className="w-5 h-5 text-orange-500" />;
      case "info": return <Info className="w-5 h-5 text-blue-500" />;
      default: return <Info className="w-5 h-5 text-gray-500" />;
    }
  };

  const getScoreColor = (score) => {
    if (score >= 0.8) return "text-green-600";
    if (score >= 0.6) return "text-blue-600";
    if (score >= 0.4) return "text-orange-500";
    return "text-red-500";
  };

  const getGradeColor = (grade) => {
    if (grade.startsWith('A')) return "bg-green-100 text-green-800 border-green-200";
    if (grade.startsWith('B')) return "bg-blue-100 text-blue-800 border-blue-200";
    if (grade.startsWith('C')) return "bg-orange-100 text-orange-800 border-orange-200";
    return "bg-red-100 text-red-800 border-red-200";
  };

  return (
    <div className="space-y-6 pt-6">
      {/* Equity Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-2xl p-6 border">
          <div className="flex items-center justify-between mb-2">
            <Target className="w-5 h-5 text-purple-600" />
            <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getGradeColor(equitySummary.equityGrade)}`}>
              {equitySummary.equityGrade}
            </span>
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {(equitySummary.overallEquityScore * 100).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-600">Overall Equity Score</div>
        </div>

        <div className="bg-white rounded-2xl p-6 border">
          <div className="flex items-center mb-2">
            <Users className="w-5 h-5 text-blue-600" />
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {(equitySummary.overallVolunteerParity * 100).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-600">Participation Parity</div>
        </div>

        <div className="bg-white rounded-2xl p-6 border">
          <div className="flex items-center mb-2">
            <TrendingUp className="w-5 h-5 text-green-600" />
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {(equitySummary.branchEquity * 100).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-600">Branch Distribution</div>
        </div>

        <div className="bg-white rounded-2xl p-6 border">
          <div className="flex items-center mb-2">
            <Award className="w-5 h-5 text-orange-600" />
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {(equitySummary.avgCategoryAccess * 100).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-600">Category Access</div>
        </div>
      </div>

      {/* Equity Insights */}
      {equityInsights.length > 0 && (
        <div className="bg-white rounded-2xl p-6 border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Equity & Inclusion Insights</h3>
          <div className="space-y-3">
            {equityInsights.map((insight, idx) => (
              <div key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-gray-50">
                {getInsightIcon(insight.type)}
                <div>
                  <div className="font-medium text-gray-900">{insight.title}</div>
                  <div className="text-sm text-gray-600">{insight.message}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Member vs Non-Member Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl p-6 border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Member vs Community Participation</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={[
                  { name: "YMCA Members", value: equitySummary.memberVolunteers, color: "#8b5cf6" },
                  { name: "Community Members", value: equitySummary.nonMemberVolunteers, color: "#06b6d4" }
                ]}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                dataKey="value"
                startAngle={90}
                endAngle={-270}
              >
                {[
                  { name: "YMCA Members", value: equitySummary.memberVolunteers, color: "#8b5cf6" },
                  { name: "Community Members", value: equitySummary.nonMemberVolunteers, color: "#06b6d4" }
                ].map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-2xl p-6 border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Participation Parity by Branch</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={participationParity.slice(0, 8)} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="branch" 
                angle={-45}
                textAnchor="end"
                height={80}
                fontSize={12}
              />
              <YAxis />
              <Tooltip 
                formatter={(value, name) => [
                  name === 'volunteerParity' ? `${(value * 100).toFixed(1)}%` : value,
                  name === 'volunteerParity' ? 'Parity Score' : 
                  name === 'memberVolunteers' ? 'Member Volunteers' : 'Community Volunteers'
                ]}
              />
              <Bar dataKey="memberVolunteers" fill="#8b5cf6" name="memberVolunteers" />
              <Bar dataKey="nonMemberVolunteers" fill="#06b6d4" name="nonMemberVolunteers" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Category Access Indicators */}
      <div className="bg-white rounded-2xl p-6 border">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Program Category Access Equity</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-3 font-medium text-gray-900">Category</th>
                <th className="text-right py-3 font-medium text-gray-900">Total Volunteers</th>
                <th className="text-right py-3 font-medium text-gray-900">Member %</th>
                <th className="text-right py-3 font-medium text-gray-900">Branch Coverage</th>
                <th className="text-right py-3 font-medium text-gray-900">Access Score</th>
                <th className="text-right py-3 font-medium text-gray-900">Hours</th>
              </tr>
            </thead>
            <tbody>
              {accessIndicators.slice(0, 10).map((category, idx) => (
                <tr key={idx} className="border-b hover:bg-gray-50">
                  <td className="py-3 font-medium text-gray-900">{category.category}</td>
                  <td className="text-right py-3">{category.totalVolunteers}</td>
                  <td className="text-right py-3">{category.memberPercentage}%</td>
                  <td className="text-right py-3">{category.branchDiversity}</td>
                  <td className={`text-right py-3 font-medium ${getScoreColor(category.accessScore)}`}>
                    {(category.accessScore * 100).toFixed(1)}%
                  </td>
                  <td className="text-right py-3">{category.hours}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detailed Branch Equity Metrics */}
      <div className="bg-white rounded-2xl p-6 border">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Branch-Level Equity Metrics</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-3 font-medium text-gray-900">Branch</th>
                <th className="text-right py-3 font-medium text-gray-900">Total Volunteers</th>
                <th className="text-right py-3 font-medium text-gray-900">Members</th>
                <th className="text-right py-3 font-medium text-gray-900">Community</th>
                <th className="text-right py-3 font-medium text-gray-900">Member %</th>
                <th className="text-right py-3 font-medium text-gray-900">Volunteer Parity</th>
                <th className="text-right py-3 font-medium text-gray-900">Hours Parity</th>
                <th className="text-right py-3 font-medium text-gray-900">Total Hours</th>
              </tr>
            </thead>
            <tbody>
              {participationParity.map((branch, idx) => (
                <tr key={idx} className="border-b hover:bg-gray-50">
                  <td className="py-3 font-medium text-gray-900">{branch.branch}</td>
                  <td className="text-right py-3">{branch.totalVolunteers}</td>
                  <td className="text-right py-3">{branch.memberVolunteers}</td>
                  <td className="text-right py-3">{branch.nonMemberVolunteers}</td>
                  <td className="text-right py-3">{branch.memberPercentage}%</td>
                  <td className={`text-right py-3 font-medium ${getScoreColor(branch.volunteerParity)}`}>
                    {(branch.volunteerParity * 100).toFixed(1)}%
                  </td>
                  <td className={`text-right py-3 font-medium ${getScoreColor(branch.hoursParity)}`}>
                    {(branch.hoursParity * 100).toFixed(1)}%
                  </td>
                  <td className="text-right py-3">{branch.totalHours}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}