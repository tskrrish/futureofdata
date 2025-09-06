

import { SAMPLE_DATA } from "./data/sampleData";
import { exportCSV } from "./utils/csvUtils";
import { createExportData, EXPORT_TYPES } from "./utils/vaultExportUtils";
import { useVolunteerData } from "./hooks/useVolunteerData";
import { useFileUpload } from "./hooks/useFileUpload";
import { useTelemetry, usePageTracking } from "./hooks/useTelemetry";
import { useFeatureFlag } from "./hooks/useFeatureFlag";

import { Header } from "./components/ui/Header";
import { Controls } from "./components/ui/Controls";
import { KPI } from "./components/ui/KPI";
import { OverviewTab } from "./components/tabs/OverviewTab";
import { BranchesTab } from "./components/tabs/BranchesTab";
import { PeopleTab } from "./components/tabs/PeopleTab";
import { PassportTab } from "./components/tabs/PassportTab";


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

  // Enhanced handlers with telemetry
  const handleBranchFilterChange = (newFilter) => {
    const oldFilter = branchFilter;
    setBranchFilter(newFilter);
    trackUserAction('filter_change', 'branch', { from: oldFilter, to: newFilter });
    metrics.trackFilterUsage('branch', 1, filtered.length);
  };

  const handleSearchChange = (newSearch) => {
    setSearch(newSearch);
    if (newSearch.length > 2) {
      trackUserAction('search', 'volunteer', { queryLength: newSearch.length });
      metrics.trackSearchBehavior(newSearch, filtered.length);
    }
  };

  const handleTabChange = (newTab) => {
    const oldTab = tab;
    setTab(newTab);
    trackUserAction('tab_switch', newTab, { from: oldTab, to: newTab });
    metrics.trackTabSwitch(oldTab, newTab);
  };

  const exportHandlers = {
    hoursByBranch: () => {
      exportCSV("hours_by_branch.csv", hoursByBranch);
      trackUserAction('export', 'hours_by_branch', { recordCount: hoursByBranch.length });
      metrics.trackExportBehavior('hours_by_branch', hoursByBranch.length);
    },
    activesByBranch: () => {
      exportCSV("actives_by_branch.csv", activesByBranch);
      trackUserAction('export', 'actives_by_branch', { recordCount: activesByBranch.length });
      metrics.trackExportBehavior('actives_by_branch', activesByBranch.length);
    },
    memberShare: () => {
      exportCSV("member_share_by_branch.csv", memberShareByBranch);
      trackUserAction('export', 'member_share', { recordCount: memberShareByBranch.length });
      metrics.trackExportBehavior('member_share', memberShareByBranch.length);
    },
    rawCurrentView: () => {
      exportCSV("raw_current_view.csv", filtered);
      trackUserAction('export', 'raw_data', { recordCount: filtered.length });
      metrics.trackExportBehavior('raw_data', filtered.length);
    },
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

  const vaultExportHandlers = {
    hoursByBranch: () => exportToVault(EXPORT_TYPES.HOURS_BY_BRANCH, hoursByBranch),
    activesByBranch: () => exportToVault(EXPORT_TYPES.ACTIVES_BY_BRANCH, activesByBranch),
    memberShare: () => exportToVault(EXPORT_TYPES.MEMBER_SHARE, memberShareByBranch),
    monthlyTrend: () => exportToVault(EXPORT_TYPES.MONTHLY_TREND, trendByMonth),
    leaderboard: () => exportToVault(EXPORT_TYPES.LEADERBOARD, leaderboard),
    rawCurrentView: () => exportToVault(EXPORT_TYPES.RAW_DATA, filtered),
    branchAnalytics: () => exportToVault(EXPORT_TYPES.BRANCH_ANALYTICS, filtered),
    membershipAnalysis: () => exportToVault(EXPORT_TYPES.MEMBERSHIP_ANALYSIS, filtered)
  };

  const exportToVault = async (exportType, data) => {
    if (!vaultExportFunction) {
      alert('Please connect to Google Drive first');
      return;
    }

    try {
      const exportData = createExportData(exportType, data, { branchFilter, search });
      const result = await vaultExportFunction(exportData.data, exportData.filename, exportData.category);
      
      if (result.success) {
        alert(`Successfully exported to Google Drive: ${result.fileName}`);
      }
    } catch (error) {
      console.error('Export to vault failed:', error);
      alert('Failed to export to Google Drive. Please check your connection.');
    }
  };

  return (


      {/* KPI Cards */}
      <div className="max-w-7xl mx-auto px-4 grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPI 
          icon={<Clock className="w-5 h-5" />} 
          label="Total Hours" 
          value={totalHours.toFixed(1)}
          onClick={() => trackUserAction('kpi_click', 'total_hours')}
        />
        <KPI 
          icon={<Users className="w-5 h-5" />} 
          label="Active Volunteers" 
          value={activeVolunteersCount}
          onClick={() => trackUserAction('kpi_click', 'active_volunteers')}
        />
        <KPI
          icon={<UserCheck className="w-5 h-5" />}
          label="Member Volunteers"
          value={memberVolunteersCount}
          sub={`${((memberVolunteersCount / Math.max(activeVolunteersCount, 1)) * 100).toFixed(1)}%`}
          onClick={() => trackUserAction('kpi_click', 'member_volunteers')}
        />
        <KPI
          icon={<Sparkles className="w-5 h-5" />}
          label="Avg Hours / Active"
          value={(totalHours / Math.max(activeVolunteersCount, 1)).toFixed(1)}
          onClick={() => trackUserAction('kpi_click', 'avg_hours')}
          enhanced={enhancedReporting}
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
              onClick={() => handleTabChange(id)}
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
          <PeopleTab 
            leaderboard={leaderboard} 
            badges={badges}

          />
        )}

        {tab === "passport" && <PassportTab />}


  );
}