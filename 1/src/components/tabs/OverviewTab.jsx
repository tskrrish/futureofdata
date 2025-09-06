import { HoursByBranchChart } from "../charts/HoursByBranchChart";
import { MonthlyTrendChart } from "../charts/MonthlyTrendChart";

export function OverviewTab({ hoursByBranch, trendByMonth, onExportHours }) {
  return (
    <div className="grid lg:grid-cols-3 gap-6 mt-4">
      <HoursByBranchChart data={hoursByBranch} onExport={onExportHours} />
      <MonthlyTrendChart data={trendByMonth} />
    </div>
  );
}