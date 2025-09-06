import { Trophy, Download } from "lucide-react";
import { useState } from "react";
import { exportVolunteerPassportPDF } from "../../utils/pdfExport.js";

export function PeopleTab({ leaderboard, badges }) {
  const [exportingVolunteer, setExportingVolunteer] = useState(null);

  const handleExportVolunteer = async (volunteer) => {
    setExportingVolunteer(volunteer.assignee);
    try {
      await exportVolunteerPassportPDF(volunteer);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Failed to export PDF. Please try again.');
    } finally {
      setExportingVolunteer(null);
    }
  };
  return (
    <div className="grid lg:grid-cols-2 gap-6 mt-4">
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
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleExportVolunteer(row)}
                  disabled={exportingVolunteer === row.assignee}
                  className="w-6 h-6 rounded-lg bg-neutral-100 hover:bg-neutral-200 grid place-items-center text-neutral-600 hover:text-neutral-800 disabled:opacity-50"
                  title="Export Passport PDF"
                >
                  {exportingVolunteer === row.assignee ? '...' : <Download className="w-3 h-3" />}
                </button>
                <Trophy className="w-4 h-4" />
              </div>
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-2xl border bg-white p-4">
        <h3 className="font-semibold mb-3">Badges Earned</h3>
        <div className="grid sm:grid-cols-2 gap-3">
          {badges.map((b) => (
            <div key={b.assignee} className="p-3 rounded-xl border bg-white">
              <div className="flex justify-between items-start mb-1">
                <div className="font-medium">{b.assignee}</div>
                <button
                  onClick={() => handleExportVolunteer(b)}
                  disabled={exportingVolunteer === b.assignee}
                  className="w-5 h-5 rounded grid place-items-center text-neutral-400 hover:text-neutral-600 disabled:opacity-50"
                  title="Export Passport PDF"
                >
                  {exportingVolunteer === b.assignee ? '...' : <Download className="w-3 h-3" />}
                </button>
              </div>
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
  );
}