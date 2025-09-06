import { ActivesByBranchChart } from "../charts/ActivesByBranchChart";
import { MemberShareChart } from "../charts/MemberShareChart";

export function BranchesTab({ activesByBranch, memberShareByBranch, onExportActives, onExportMemberShare }) {
  return (
    <div className="grid lg:grid-cols-2 gap-6 mt-4">
      <ActivesByBranchChart data={activesByBranch} onExport={onExportActives} />
      <MemberShareChart data={memberShareByBranch} onExport={onExportMemberShare} />
    </div>
  );
}