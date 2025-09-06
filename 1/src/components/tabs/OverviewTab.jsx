import { FileText, Loader2 } from "lucide-react";
import { HoursByBranchChart } from "../charts/HoursByBranchChart";
import { MonthlyTrendChart } from "../charts/MonthlyTrendChart";

export function OverviewTab({ hoursByBranch, trendByMonth, onExportHours, onExportBoardPDF, isGeneratingPDF }) {
  return (
    <div className="space-y-6 mt-4">
      {/* Board Report Export */}
      {onExportBoardPDF && (
        <div className="bg-white rounded-2xl p-6 border">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-neutral-900">Board-Ready Report</h3>
              <p className="text-sm text-neutral-600 mt-1">Generate a comprehensive PDF report with narratives and insights for board presentations</p>
            </div>
            <button
              onClick={onExportBoardPDF}
              disabled={isGeneratingPDF}
              className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm bg-red-600 text-white hover:bg-red-700 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isGeneratingPDF ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generating PDF Report...
                </>
              ) : (
                <>
                  <FileText className="w-4 h-4" />
                  Generate Board Report PDF
                </>
              )}
            </button>
          </div>
        </div>
      )}
      
      <div className="grid lg:grid-cols-3 gap-6">
        <HoursByBranchChart data={hoursByBranch} onExport={onExportHours} />
        <MonthlyTrendChart data={trendByMonth} />
      </div>
    </div>
  );
}