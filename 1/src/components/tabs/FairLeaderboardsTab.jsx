import { Trophy, Users, TrendingUp, Award, BarChart3 } from "lucide-react";

export function FairLeaderboardsTab({ 
  normalizedLeaderboards, 
  leaderboardInsights,
  leaderboard,
  badges 
}) {
  const {
    overallLeaderboard,
    normalizedOverallLeaderboard,
    branchLeaderboards,
    roleLeaderboards,
    branchStats,
    roleStats
  } = normalizedLeaderboards;

  return (
    <div className="space-y-6 mt-4">
      {/* Insights Section */}
      {leaderboardInsights.length > 0 && (
        <div className="rounded-2xl border bg-white p-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Fair Competition Insights
          </h3>
          <div className="space-y-2">
            {leaderboardInsights.map((insight, i) => (
              <div 
                key={i} 
                className={`p-3 rounded-xl border-l-4 ${
                  insight.type === 'success' ? 'bg-green-50 border-green-400' :
                  insight.type === 'warning' ? 'bg-yellow-50 border-yellow-400' :
                  'bg-blue-50 border-blue-400'
                }`}
              >
                <div className="font-medium text-sm">{insight.title}</div>
                <div className="text-sm text-neutral-600">{insight.message}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Traditional Hours Leaderboard */}
        <div className="rounded-2xl border bg-white p-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Trophy className="w-4 h-4" />
            Top Volunteers (Total Hours)
          </h3>
          <div className="text-xs text-neutral-500 mb-3">
            Traditional ranking by raw volunteer hours
          </div>
          <ul className="space-y-2">
            {leaderboard.slice(0, 10).map((row, i) => (
              <li key={row.assignee} className="flex items-center justify-between p-2 rounded-xl border bg-white">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-xl bg-neutral-100 grid place-items-center font-semibold text-sm">{i + 1}</div>
                  <div>
                    <div className="font-medium">{row.assignee}</div>
                    <div className="text-xs text-neutral-500">{row.hours} hours</div>
                  </div>
                </div>
                <Trophy className="w-4 h-4 text-yellow-500" />
              </li>
            ))}
          </ul>
        </div>

        {/* Normalized Fair Competition Leaderboard */}
        <div className="rounded-2xl border bg-gradient-to-r from-blue-50 to-purple-50 p-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Award className="w-4 h-4" />
            Fair Competition Leaders
          </h3>
          <div className="text-xs text-neutral-600 mb-3">
            Size-normalized scoring for fair competition across branches & roles
          </div>
          <ul className="space-y-2">
            {normalizedOverallLeaderboard.slice(0, 10).map((volunteer, i) => (
              <li key={`${volunteer.name}-${volunteer.branch}`} className="flex items-center justify-between p-2 rounded-xl border bg-white/80">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 text-white grid place-items-center font-semibold text-sm">{i + 1}</div>
                  <div>
                    <div className="font-medium">{volunteer.name}</div>
                    <div className="text-xs text-neutral-600">
                      {volunteer.totalHours} hrs • {volunteer.branch}
                    </div>
                    <div className="text-xs text-neutral-500">
                      Score: {volunteer.combinedNormalizedScore}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <Award className="w-4 h-4 text-purple-500 mb-1" />
                  <div className="text-xs text-neutral-500">
                    {volunteer.efficiencyRating.toFixed(1)} hrs/session
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Branch Leaderboards */}
      <div className="rounded-2xl border bg-white p-4">
        <h3 className="font-semibold mb-3 flex items-center gap-2">
          <Users className="w-4 h-4" />
          Branch Competition
        </h3>
        <div className="text-xs text-neutral-500 mb-4">
          Top performers within each branch (normalized by branch size)
        </div>
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
          {branchLeaderboards.slice(0, 6).map((branchData) => (
            <div key={branchData.branch} className="p-3 rounded-xl border bg-neutral-50">
              <div className="font-medium text-sm mb-2">{branchData.branch}</div>
              <div className="text-xs text-neutral-500 mb-3">
                {branchData.branchSize} volunteers • {branchData.totalHours.toFixed(1)} total hours
              </div>
              <ul className="space-y-1">
                {branchData.volunteers.slice(0, 3).map((volunteer, i) => (
                  <li key={`${volunteer.name}-${volunteer.branch}`} className="flex items-center justify-between p-1 rounded text-xs">
                    <div className="flex items-center gap-2">
                      <div className="w-5 h-5 rounded bg-blue-100 text-blue-700 grid place-items-center font-semibold text-xs">{i + 1}</div>
                      <div>
                        <div className="font-medium">{volunteer.name}</div>
                        <div className="text-neutral-500">{volunteer.totalHours} hrs</div>
                      </div>
                    </div>
                    <div className="text-neutral-600 font-medium">
                      {volunteer.branchNormalizedScore}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Role/Department Leaderboards */}
      <div className="rounded-2xl border bg-white p-4">
        <h3 className="font-semibold mb-3 flex items-center gap-2">
          <BarChart3 className="w-4 h-4" />
          Role Competition
        </h3>
        <div className="text-xs text-neutral-500 mb-4">
          Top performers within each role/department (normalized by role size)
        </div>
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
          {roleLeaderboards.slice(0, 6).map((roleData) => (
            <div key={roleData.role} className="p-3 rounded-xl border bg-neutral-50">
              <div className="font-medium text-sm mb-2">{roleData.role}</div>
              <div className="text-xs text-neutral-500 mb-3">
                {roleData.roleSize} volunteers • {roleData.totalHours.toFixed(1)} total hours
              </div>
              <ul className="space-y-1">
                {roleData.volunteers.slice(0, 3).map((volunteer, i) => (
                  <li key={`${volunteer.name}-${volunteer.role}`} className="flex items-center justify-between p-1 rounded text-xs">
                    <div className="flex items-center gap-2">
                      <div className="w-5 h-5 rounded bg-green-100 text-green-700 grid place-items-center font-semibold text-xs">{i + 1}</div>
                      <div>
                        <div className="font-medium">{volunteer.name}</div>
                        <div className="text-neutral-500">{volunteer.totalHours} hrs</div>
                      </div>
                    </div>
                    <div className="text-neutral-600 font-medium">
                      {volunteer.roleNormalizedScore}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Statistics Overview */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="rounded-2xl border bg-white p-4">
          <h3 className="font-semibold mb-3">Branch Statistics</h3>
          <div className="space-y-2">
            {branchStats.slice(0, 5).map((stat) => (
              <div key={stat.branch} className="flex items-center justify-between p-2 rounded-xl bg-neutral-50">
                <div>
                  <div className="font-medium text-sm">{stat.branch}</div>
                  <div className="text-xs text-neutral-500">{stat.volunteerCount} volunteers</div>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-sm">{stat.totalHours.toFixed(1)} hrs</div>
                  <div className="text-xs text-neutral-500">{stat.avgHoursPerVolunteer.toFixed(1)} avg</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border bg-white p-4">
          <h3 className="font-semibold mb-3">Role Statistics</h3>
          <div className="space-y-2">
            {roleStats.slice(0, 5).map((stat) => (
              <div key={stat.role} className="flex items-center justify-between p-2 rounded-xl bg-neutral-50">
                <div>
                  <div className="font-medium text-sm">{stat.role}</div>
                  <div className="text-xs text-neutral-500">{stat.volunteerCount} volunteers</div>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-sm">{stat.totalHours.toFixed(1)} hrs</div>
                  <div className="text-xs text-neutral-500">{stat.avgHoursPerVolunteer.toFixed(1)} avg</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}