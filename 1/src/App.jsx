import React, { useState } from "react";
import { Users, Clock, UserCheck, Sparkles } from "lucide-react";

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
import { ImpactTab } from "./components/tabs/ImpactTab";

export default function App() {
  const [raw, setRaw] = useState(SAMPLE_DATA);
  const [branchFilter, setBranchFilter] = useState("All");
  const [search, setSearch] = useState("");
  const [tab, setTab] = useState("overview");

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
            ["impact", "Impact Dashboard"],
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

        {tab === "impact" && (
          <ImpactTab totalHours={totalHours} activeVolunteersCount={activeVolunteersCount} />
        )}

        {tab === "passport" && <PassportTab />}
      </div>

      <footer className="max-w-7xl mx-auto px-4 py-10 text-xs text-neutral-500">
        Built for YMCA Cincinnati — Hackathon: Platform for Belonging. Upload VolunteerMatters CSV/JSON above to power the dashboard.
      </footer>
    </div>
  );
}