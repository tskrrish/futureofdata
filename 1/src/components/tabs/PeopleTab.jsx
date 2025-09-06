import { Trophy, Award, Crown, Star } from "lucide-react";
import { useState } from "react";
import BadgeDashboard from "../BadgeDashboard";

export function PeopleTab({ leaderboard, badges, volunteers = [] }) {
  const [viewMode, setViewMode] = useState('classic');

  return (
    <div className="mt-4">
      {/* View Mode Toggle */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold">People & Badges</h2>
          <p className="text-neutral-600">Volunteer achievements and recognition system</p>
        </div>
        <div className="flex rounded-lg border bg-white overflow-hidden">
          <button
            className={`px-4 py-2 text-sm font-medium ${
              viewMode === 'classic' 
                ? 'bg-blue-500 text-white' 
                : 'text-neutral-600 hover:bg-neutral-50'
            }`}
            onClick={() => setViewMode('classic')}
          >
            <Trophy className="w-4 h-4 mr-2 inline" />
            Classic View
          </button>
          <button
            className={`px-4 py-2 text-sm font-medium ${
              viewMode === 'badges2' 
                ? 'bg-blue-500 text-white' 
                : 'text-neutral-600 hover:bg-neutral-50'
            }`}
            onClick={() => setViewMode('badges2')}
          >
            <Star className="w-4 h-4 mr-2 inline" />
            Badge System 2.0
          </button>
        </div>
      </div>

      {viewMode === 'classic' ? (
        /* Classic View - Original Implementation */
        <div className="grid lg:grid-cols-2 gap-6">
          <div className="rounded-2xl border bg-white p-4">
            <h3 className="font-semibold mb-3">Top Volunteers (Hours)</h3>
            <ul className="space-y-2">
              {leaderboard.map((row, i) => (
                <li key={row.assignee} className="flex items-center justify-between p-2 rounded-xl border bg-white">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-xl bg-neutral-100 grid place-items-center font-semibold">{i + 1}</div>
                    <div>
                      <div className="font-medium">{row.assignee}</div>
                      <div className="text-xs text-neutral-500">{row.hours} hours</div>
                    </div>
                  </div>
                  <Trophy className="w-4 h-4" />
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-2xl border bg-white p-4">
            <h3 className="font-semibold mb-3">Badges Earned</h3>
            <div className="grid sm:grid-cols-2 gap-3">
              {badges.map((b) => (
                <div key={b.assignee} className="p-3 rounded-xl border bg-white">
                  <div className="font-medium mb-1">{b.assignee}</div>
                  <div className="text-xs text-neutral-500 mb-2">{b.hours} total hours</div>
                  <div className="flex flex-wrap gap-2">
                    {b.badges.map((m) => (
                      <span key={m} className="px-2 py-1 rounded-full text-xs border">{m}+ hrs</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        /* Badge System 2.0 View */
        <div className="badge-system-2-container">
          <div className="upgrade-notice mb-6 p-4 bg-gradient-to-r from-purple-100 to-blue-100 rounded-2xl border border-purple-200">
            <div className="flex items-start gap-3">
              <Crown className="w-6 h-6 text-purple-600 mt-1" />
              <div>
                <h4 className="font-semibold text-purple-900 mb-1">Badge System 2.0 is Live!</h4>
                <p className="text-purple-700 text-sm mb-3">
                  Enhanced role-specific badges with rarity tiers, achievement tracking, and personalized progression paths.
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-purple-200 text-purple-800">
                    <Star className="w-3 h-3 mr-1" /> 5 Rarity Tiers
                  </span>
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-200 text-blue-800">
                    <Award className="w-3 h-3 mr-1" /> Role Progression
                  </span>
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-200 text-green-800">
                    <Trophy className="w-3 h-3 mr-1" /> Storyworld Badges
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Enhanced Badge Dashboard */}
          <BadgeDashboard volunteers={volunteers} />
        </div>
      )}
    </div>
  );
}