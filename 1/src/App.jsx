import React, { useState, useEffect, useCallback, useMemo } from "react";
import { Users, Clock, UserCheck, Sparkles, Save, BookOpen, Settings } from "lucide-react";

import { SAMPLE_DATA } from "./data/sampleData";
import { exportCSV } from "./utils/csvUtils";
import { useVolunteerData } from "./hooks/useVolunteerData";
import { useFileUpload } from "./hooks/useFileUpload";
import { useDashboardViews } from "./hooks/useDashboardViews";

import { Header } from "./components/ui/Header";
import { Controls } from "./components/ui/Controls";
import { KPI } from "./components/ui/KPI";
import { OverviewTab } from "./components/tabs/OverviewTab";
import { BranchesTab } from "./components/tabs/BranchesTab";
import { PeopleTab } from "./components/tabs/PeopleTab";
import { PassportTab } from "./components/tabs/PassportTab";
import { SaveDashboardView } from "./components/views/SaveDashboardView";
import { DashboardViewManager } from "./components/views/DashboardViewManager";
import { ShareViewModal } from "./components/views/ShareViewModal";

export default function App() {
  const [raw, setRaw] = useState(SAMPLE_DATA);
  const [branchFilter, setBranchFilter] = useState("All");
  const [search, setSearch] = useState("");
  const [tab, setTab] = useState("overview");
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [showViewManager, setShowViewManager] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [editingView, setEditingView] = useState(null);
  const [sharingView, setSharingView] = useState(null);
  const [customSettings, setCustomSettings] = useState({});

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

  const dashboardViews = useDashboardViews();
  const {
    personalViews,
    branchViews,
    organizationViews,
    currentView,
    actions: viewActions
  } = dashboardViews;

  const exportHandlers = {
    hoursByBranch: () => exportCSV("hours_by_branch.csv", hoursByBranch),
    activesByBranch: () => exportCSV("actives_by_branch.csv", activesByBranch),
    memberShare: () => exportCSV("member_share_by_branch.csv", memberShareByBranch),
    rawCurrentView: () => exportCSV("raw_current_view.csv", filtered),
  };

  const currentDashboardState = useMemo(() => ({
    branchFilter,
    search,
    tab,
    customSettings
  }), [branchFilter, search, tab, customSettings]);

  const handleSaveView = async (viewData) => {
    if (editingView) {
      await viewActions.updateView(editingView.id, viewData);
      setEditingView(null);
    } else {
      await viewActions.saveView(viewData);
    }
  };

  const handleApplyView = useCallback(async (view) => {
    const newState = viewActions.applyView(view, currentDashboardState);
    setBranchFilter(newState.branchFilter);
    setSearch(newState.search);
    setTab(newState.tab);
    setCustomSettings(newState.customSettings);
    viewActions.setCurrentView(view);
    setShowViewManager(false);
  }, [viewActions, currentDashboardState]);

  const handleEditView = (view) => {
    setEditingView(view);
    setShowSaveModal(true);
  };

  const handleShareView = (view) => {
    setSharingView(view);
    setShowShareModal(true);
  };

  const handleDeleteView = async (viewId) => {
    await viewActions.deleteView(viewId);
  };

  const handleShare = async (viewId, users, permissions) => {
    await viewActions.shareView(viewId, users, permissions);
  };

  const handleUnshare = async (viewId, user) => {
    await viewActions.unshareView(viewId, user);
  };

  const handleSetDefault = async (viewId, role) => {
    await viewActions.setDefaultView(viewId, role);
  };

  useEffect(() => {
    const defaultView = viewActions.getDefaultView('personal');
    if (defaultView && !currentView) {
      handleApplyView(defaultView);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [personalViews]);

  return (
    <div className="min-h-screen bg-neutral-50">
      <Header onFileUpload={handleFile} onExportRaw={exportHandlers.rawCurrentView} />
      
      {/* Dashboard View Controls */}
      <div className="max-w-7xl mx-auto px-4 py-2">
        <div className="flex justify-between items-center bg-white rounded-lg border border-gray-200 px-4 py-2">
          <div className="flex items-center gap-2 text-sm">
            {currentView ? (
              <span className="text-gray-700">
                Current view: <span className="font-medium text-blue-600">{currentView.name}</span>
                <span className="text-gray-500 ml-2">({currentView.role})</span>
              </span>
            ) : (
              <span className="text-gray-500">No view selected</span>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setShowSaveModal(true)}
              className="flex items-center gap-1 px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              <Save className="w-4 h-4" />
              Save View
            </button>
            <button
              onClick={() => setShowViewManager(true)}
              className="flex items-center gap-1 px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              <BookOpen className="w-4 h-4" />
              Manage Views
            </button>
          </div>
        </div>
      </div>
      
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
      
      {/* Modals */}
      <SaveDashboardView
        isOpen={showSaveModal}
        onClose={() => {
          setShowSaveModal(false);
          setEditingView(null);
        }}
        onSave={handleSaveView}
        dashboardState={currentDashboardState}
        existingView={editingView}
      />
      
      {showViewManager && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl mx-4 max-h-[80vh] overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">Dashboard View Manager</h2>
              <button 
                onClick={() => setShowViewManager(false)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <Settings className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 overflow-y-auto max-h-[70vh]">
              <DashboardViewManager
                personalViews={personalViews}
                branchViews={branchViews}
                organizationViews={organizationViews}
                currentView={currentView}
                onApplyView={handleApplyView}
                onEditView={handleEditView}
                onDeleteView={handleDeleteView}
                onShareView={handleShareView}
                onSetDefault={handleSetDefault}
                canEditView={viewActions.canEditView}
                canShareView={viewActions.canShareView}
                canDeleteView={viewActions.canDeleteView}
              />
            </div>
            <div className="p-4 border-t bg-gray-50">
              <button
                onClick={() => setShowViewManager(false)}
                className="w-full px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
      
      <ShareViewModal
        view={sharingView}
        isOpen={showShareModal}
        onClose={() => {
          setShowShareModal(false);
          setSharingView(null);
        }}
        onShare={handleShare}
        onUnshare={handleUnshare}
      />
    </div>
  );
}