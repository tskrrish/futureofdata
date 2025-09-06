

import { SAMPLE_DATA } from "./data/sampleData";
import { exportCSV } from "./utils/csvUtils";
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
import DashboardManager from "./components/DashboardManager";


export default function App() {
  const [raw, setRaw] = useState(SAMPLE_DATA);
  const [branchFilter, setBranchFilter] = useState("All");
  const [search, setSearch] = useState("");
  const [tab, setTab] = useState("overview");
  const [showDashboardManager, setShowDashboardManager] = useState(false);
  const [currentDashboard, setCurrentDashboard] = useState(null);

  // Telemetry and feature flags
  const { trackUserAction } = useTelemetry();
  const { isEnabled: enhancedReporting } = useFeatureFlag('enhancedReporting');
  const { isEnabled: advancedFiltering } = useFeatureFlag('advancedFiltering');
  const { isEnabled: exportEnhancements } = useFeatureFlag('exportEnhancements');
  
  usePageTracking('dashboard');

  // Initialize services
  useEffect(() => {
    featureFlags.setUserAttributes({
      userId: 'dashboard_user',
      role: 'admin',
      timestamp: new Date().toISOString()
    });
    
    telemetry.setUserId('dashboard_user');
    metrics.trackPageView('dashboard');
  }, []);

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

      />

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
            ["monitoring", "E2E Monitoring"],
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
            enhancedReporting={enhancedReporting}
          />
        )}

        {tab === "branches" && (
          <BranchesTab
            activesByBranch={activesByBranch}
            memberShareByBranch={memberShareByBranch}
            onExportActives={exportHandlers.activesByBranch}
            onExportMemberShare={exportHandlers.memberShare}
            exportEnhancements={exportEnhancements}
          />
        )}

        {tab === "people" && (
          <PeopleTab 
            leaderboard={leaderboard} 
            badges={badges}
            enhancedReporting={enhancedReporting}
          />
        )}

        {tab === "passport" && <PassportTab />}
        
        {tab === "monitoring" && <MonitoringTab />}
      </div>

      <footer className="max-w-7xl mx-auto px-4 py-10 text-xs text-neutral-500">
        Built for YMCA Cincinnati — Hackathon: Platform for Belonging. Upload VolunteerMatters CSV/JSON above to power the dashboard.
      </footer>


    </div>
  );
}