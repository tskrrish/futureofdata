import React, { useState } from "react";
import { Users, Clock, UserCheck, Sparkles, Calculator } from "lucide-react";

import { SAMPLE_DATA } from "./data/sampleData";
import { exportCSV } from "./utils/csvUtils";
import { useVolunteerData } from "./hooks/useVolunteerData";
import { useFileUpload } from "./hooks/useFileUpload";
import { useCustomKPIs } from "./hooks/useCustomKPIs";

import { Header } from "./components/ui/Header";
import { Controls } from "./components/ui/Controls";
import { KPI } from "./components/ui/KPI";
import { KPIBuilder } from "./components/ui/KPIBuilder";
import { CustomKPIGrid } from "./components/ui/CustomKPI";
import { OverviewTab } from "./components/tabs/OverviewTab";
import { BranchesTab } from "./components/tabs/BranchesTab";
import { PeopleTab } from "./components/tabs/PeopleTab";
import { PassportTab } from "./components/tabs/PassportTab";

export default function App() {
  const [raw, setRaw] = useState(SAMPLE_DATA);
  const [branchFilter, setBranchFilter] = useState("All");
  const [search, setSearch] = useState("");
  const [tab, setTab] = useState("overview");
  const [showKPIBuilder, setShowKPIBuilder] = useState(false);

  const {
    branches,
    filtered,
    totalHours,
    activeVolunteersCount,
    memberVolunteersCount,
    hoursByBranch,
    activesByBranch,
    memberShareByBranch,
    trendByMonth,
    leaderboard,
    badges
  } = useVolunteerData(raw, branchFilter, search);

  const { customKPIs, saveKPI } = useCustomKPIs();
  const handleFile = useFileUpload(setRaw);

  const exportHandlers = {
    hoursByBranch: () => exportCSV("hours_by_branch.csv", hoursByBranch),
    activesByBranch: () => exportCSV("actives_by_branch.csv", activesByBranch),
    memberShare: () => exportCSV("member_share_by_branch.csv", memberShareByBranch),
    rawCurrentView: () => exportCSV("raw_current_view.csv", filtered),
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      <Header onFileUpload={handleFile} onExportRaw={exportHandlers.rawCurrentView} />
      
      <Controls
        branches={branches}
        branchFilter={branchFilter}
        onBranchChange={setBranchFilter}
        search={search}
        onSearchChange={setSearch}
      />

      {/* KPI Cards */}
      <div className="max-w-7xl mx-auto px-4">
        {/* Default KPIs */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <KPI icon={<Clock className="w-5 h-5" />} label="Total Hours" value={totalHours.toFixed(1)} />
          <KPI icon={<Users className="w-5 h-5" />} label="Active Volunteers" value={activeVolunteersCount} />
          <KPI
            icon={<UserCheck className="w-5 h-5" />}
            label="Member Volunteers"
            value={memberVolunteersCount}
            sub={`${((memberVolunteersCount / Math.max(activeVolunteersCount, 1)) * 100).toFixed(1)}%`}
          />
          <KPI
            icon={<Sparkles className="w-5 h-5" />}
            label="Avg Hours / Active"
            value={(totalHours / Math.max(activeVolunteersCount, 1)).toFixed(1)}
          />
        </div>

        {/* Custom KPI Builder Button & Custom KPIs */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-800">Custom KPIs</h3>
          <button
            onClick={() => setShowKPIBuilder(true)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            <Calculator className="w-4 h-4" />
            Create Custom KPI
          </button>
        </div>
        
        {customKPIs.length > 0 ? (
          <CustomKPIGrid 
            kpis={customKPIs} 
            volunteerData={{
              totalHours,
              activeVolunteersCount,
              memberVolunteersCount,
              filtered
            }}
            className="mb-6"
          />
        ) : (
          <div className="bg-gray-50 border-2 border-dashed border-gray-200 rounded-lg p-8 text-center mb-6">
            <Calculator className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-600 mb-2">No Custom KPIs Yet</h3>
            <p className="text-gray-500 mb-4">
              Create custom KPIs with formulas and filters to track metrics that matter to your organization.
            </p>
            <button
              onClick={() => setShowKPIBuilder(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              <Calculator className="w-4 h-4" />
              Create Your First Custom KPI
            </button>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="inline-flex rounded-2xl border bg-white overflow-hidden text-sm">
          {[
            ["overview", "Overview"],
            ["branches", "Branch Breakdown"],
            ["people", "People & Badges"],
            ["passport", "Belonging Passport"],
          ].map(([id, label]) => (
            <button
              key={id}
              className={`px-4 py-2 ${tab === id ? "bg-neutral-100" : "hover:bg-neutral-50"}`}
              onClick={() => setTab(id)}
            >
              {label}
            </button>
          ))}
        </div>

        {tab === "overview" && (
          <OverviewTab 
            hoursByBranch={hoursByBranch} 
            trendByMonth={trendByMonth} 
            onExportHours={exportHandlers.hoursByBranch}
          />
        )}

        {tab === "branches" && (
          <BranchesTab
            activesByBranch={activesByBranch}
            memberShareByBranch={memberShareByBranch}
            onExportActives={exportHandlers.activesByBranch}
            onExportMemberShare={exportHandlers.memberShare}
          />
        )}

        {tab === "people" && (
          <PeopleTab leaderboard={leaderboard} badges={badges} />
        )}

        {tab === "passport" && <PassportTab />}
      </div>

      <footer className="max-w-7xl mx-auto px-4 py-10 text-xs text-neutral-500">
        Built for YMCA Cincinnati — Hackathon: Platform for Belonging. Upload VolunteerMatters CSV/JSON above to power the dashboard.
      </footer>

      {/* KPI Builder Modal */}
      <KPIBuilder
        isOpen={showKPIBuilder}
        onClose={() => setShowKPIBuilder(false)}
        volunteerData={{
          totalHours,
          activeVolunteersCount,
          memberVolunteersCount,
          filtered
        }}
        onSaveKPI={saveKPI}
        customKPIs={customKPIs}
      />
    </div>
  );
}