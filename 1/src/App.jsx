import React, { useState } from "react";
import { Users, Clock, UserCheck, Sparkles, Save } from "lucide-react";

import { SAMPLE_DATA } from "./data/sampleData";
import { exportCSV } from "./utils/csvUtils";
import { useVolunteerData } from "./hooks/useVolunteerData";
import { useFileUpload } from "./hooks/useFileUpload";

import { Header } from "./components/ui/Header";
import { Controls } from "./components/ui/Controls";
import { KPI } from "./components/ui/KPI";
import { OverviewTab } from "./components/tabs/OverviewTab";
import { BranchesTab } from "./components/tabs/BranchesTab";
import { PeopleTab } from "./components/tabs/PeopleTab";
import { PassportTab } from "./components/tabs/PassportTab";
import DashboardManager from "./components/DashboardManager";

export default function App() {
  const [raw, setRaw] = useState(SAMPLE_DATA);
  const [branchFilter, setBranchFilter] = useState("All");
  const [search, setSearch] = useState("");
  const [tab, setTab] = useState("overview");
  const [showDashboardManager, setShowDashboardManager] = useState(false);
  const [currentDashboard, setCurrentDashboard] = useState(null);

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

  const handleFile = useFileUpload(setRaw);

  const exportHandlers = {
    hoursByBranch: () => exportCSV("hours_by_branch.csv", hoursByBranch),
    activesByBranch: () => exportCSV("actives_by_branch.csv", activesByBranch),
    memberShare: () => exportCSV("member_share_by_branch.csv", memberShareByBranch),
    rawCurrentView: () => exportCSV("raw_current_view.csv", filtered),
  };

  // Dashboard management functions
  const getCurrentDashboardState = () => ({
    raw,
    branchFilter,
    search,
    tab,
    timestamp: new Date().toISOString()
  });

  const handleLoadDashboard = (dashboardData) => {
    if (dashboardData.raw) setRaw(dashboardData.raw);
    if (dashboardData.branchFilter) setBranchFilter(dashboardData.branchFilter);
    if (dashboardData.search) setSearch(dashboardData.search);
    if (dashboardData.tab) setTab(dashboardData.tab);
  };

  const handleSaveDashboard = (dashboard) => {
    setCurrentDashboard(dashboard);
  };

  // Check if user has edit permissions for current dashboard
  const canEditDashboard = () => {
    if (!currentDashboard) return true; // No dashboard loaded, full access
    const permission = currentDashboard.permission;
    return permission === 'owner' || permission === 'edit';
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      <Header onFileUpload={handleFile} onExportRaw={exportHandlers.rawCurrentView} />
      
      {/* Dashboard Management Bar */}
      <div className="max-w-7xl mx-auto px-4 py-2">
        <div className="flex items-center justify-between bg-white rounded-lg border p-3">
          <div className="flex items-center space-x-4">
            {currentDashboard && (
              <div className="text-sm">
                <span className="font-medium text-gray-900">{currentDashboard.title}</span>
                <span className="text-gray-500 ml-2">
                  ({currentDashboard.permission === 'owner' ? 'Owner' : 
                    currentDashboard.permission === 'edit' ? 'Editor' : 'Viewer'})
                </span>
              </div>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowDashboardManager(true)}
              className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
            >
              <Save className="w-4 h-4" />
              <span>Dashboard Manager</span>
            </button>
          </div>
        </div>
      </div>
      
      <Controls
        branches={branches}
        branchFilter={branchFilter}
        onBranchChange={canEditDashboard() ? setBranchFilter : undefined}
        search={search}
        onSearchChange={canEditDashboard() ? setSearch : undefined}
        readOnly={!canEditDashboard()}
      />

      {/* KPI Cards */}
      <div className="max-w-7xl mx-auto px-4 grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
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

      {/* Dashboard Manager Modal */}
      {showDashboardManager && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-semibold">Dashboard Manager</h2>
                <button
                  onClick={() => setShowDashboardManager(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <span className="sr-only">Close</span>
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <DashboardManager
                currentDashboardState={getCurrentDashboardState()}
                onLoadDashboard={handleLoadDashboard}
                onSaveDashboard={handleSaveDashboard}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}