import { HoursByBranchChart } from "../charts/HoursByBranchChart";
import { MonthlyTrendChart } from "../charts/MonthlyTrendChart";
import { ProjectsList } from "../ui/ProjectsList";

export function OverviewTab({ hoursByBranch, trendByMonth, onExportHours, rawData }) {
  return (
    <div className="space-y-6 mt-4">
      <div className="grid lg:grid-cols-3 gap-6">
        <HoursByBranchChart data={hoursByBranch} onExport={onExportHours} />
        <MonthlyTrendChart data={trendByMonth} />
        <ProjectsList data={rawData || []} title="Recent Projects" />
      </div>
    </div>
  );
}