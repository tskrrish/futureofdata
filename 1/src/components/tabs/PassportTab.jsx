import { ArrowRight, Download } from "lucide-react";
import { useState } from "react";
import { exportMultipleVolunteersPDF, exportVolunteerPassportPDF } from "../../utils/pdfExport.js";
import { useVolunteerData } from "../../hooks/useVolunteerData.js";

export function PassportTab() {
  const { volunteers } = useVolunteerData();
  const [isExporting, setIsExporting] = useState(false);

  const handleExportAll = async () => {
    if (!volunteers || volunteers.length === 0) return;
    
    setIsExporting(true);
    try {
      await exportMultipleVolunteersPDF(volunteers);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Failed to export PDF. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="rounded-2xl border bg-white p-4 mt-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Belonging Passport — Growth Pathways</h3>
        <div className="flex gap-2">
          <button 
            className="inline-flex items-center gap-2 rounded-xl border px-3 py-1.5 text-sm hover:bg-neutral-50"
            onClick={handleExportAll}
            disabled={isExporting || !volunteers?.length}
          >
            <Download className="w-4 h-4" />
            {isExporting ? 'Generating PDF...' : 'Export All Passports'}
          </button>
          <button className="inline-flex items-center gap-2 rounded-xl border px-3 py-1.5 text-sm hover:bg-neutral-50">
            Open App <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
      <p className="text-sm text-neutral-600">
        Recognize contributions and create belonging pathways. Earn badges at 10/25/50/100 hours, unlock roles
        (Greeter → Lead Volunteer → Mentor), and surface perks (guest pass, merch, training credits).
      </p>
      <div className="grid md:grid-cols-3 gap-4">
        <div className="rounded-2xl border p-4 bg-white">
          <div className="font-medium mb-1">Next Step</div>
          <div className="text-sm text-neutral-600">
            Complete <b>Safety Training</b> to unlock <b>Greeter</b> role.
          </div>
        </div>
        <div className="rounded-2xl border p-4 bg-white">
          <div className="font-medium mb-1">Perk Unlocked</div>
          <div className="text-sm text-neutral-600">
            25+ hours — Free <b>Guest Pass</b> this month.
          </div>
        </div>
        <div className="rounded-2xl border p-4 bg-white">
          <div className="font-medium mb-1">Connection</div>
          <div className="text-sm text-neutral-600">
            Join the <b>Family Night</b> volunteer squad at your branch.
          </div>
        </div>
      </div>
      <div className="rounded-2xl border p-4 bg-neutral-50">
        <div className="font-medium mb-2">Implementation notes</div>
        <ul className="list-disc pl-5 text-sm text-neutral-600 space-y-1">
          <li>Active Volunteers = unique pairs of (assignee, branch).</li>
          <li>Member Volunteers = same pairs, counted if any record for the pair has <code>is_member = true</code>.</li>
          <li>Branch – Hours = sum of <code>hours</code> (no deduplication).</li>
          <li>Upload CSV/JSON with: <code>branch, hours, assignee, is_member, date</code>.</li>
        </ul>
      </div>
    </div>
  );
}