import { Download, AlertTriangle, Clock, CheckCircle } from "lucide-react";
import { getStatusColor, getStatusLabel, getCriticalityColor } from "../../utils/certificationUtils";

export function CertificationExpiryRadarChart({ data, onExport }) {
  const { summary, upcomingExpirations, byBranch, byCriticality } = data;

  return (
    <div className="col-span-full">
      <div className="rounded-2xl border bg-white p-4">
        <div className="flex items-center justify-between mb-6">
          <h3 className="font-semibold flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-orange-500" />
            Certification Expiry Radar
          </h3>
          <button
            onClick={onExport}
            className="inline-flex items-center gap-2 rounded-xl border px-3 py-1.5 text-sm hover:bg-neutral-50"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>

        <div className="grid lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-red-50 border border-red-200 rounded-xl p-4">
            <div className="text-2xl font-bold text-red-600">{summary.expired + summary.urgent}</div>
            <div className="text-sm text-red-600">Critical Action Needed</div>
            <div className="text-xs text-red-500 mt-1">Expired + Urgent (≤7 days)</div>
          </div>
          <div className="bg-orange-50 border border-orange-200 rounded-xl p-4">
            <div className="text-2xl font-bold text-orange-600">{summary.warning}</div>
            <div className="text-sm text-orange-600">Warning</div>
            <div className="text-xs text-orange-500 mt-1">Expires within 30 days</div>
          </div>
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
            <div className="text-2xl font-bold text-yellow-600">{summary.attention}</div>
            <div className="text-sm text-yellow-600">Attention</div>
            <div className="text-xs text-yellow-500 mt-1">Expires within 60 days</div>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-xl p-4">
            <div className="text-2xl font-bold text-green-600">{summary.valid}</div>
            <div className="text-sm text-green-600">Valid</div>
            <div className="text-xs text-green-500 mt-1">Good standing</div>
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium mb-3 flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Upcoming Expirations
            </h4>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {upcomingExpirations.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-500" />
                  No urgent certifications expiring soon
                </div>
              ) : (
                upcomingExpirations.map((cert) => (
                  <div key={cert.id} className="border rounded-lg p-3 bg-gray-50">
                    <div className="flex items-center justify-between mb-1">
                      <div className="font-medium text-sm">{cert.certification}</div>
                      <div className={`px-2 py-1 rounded text-xs border ${getCriticalityColor(cert.criticality)}`}>
                        {cert.criticality}
                      </div>
                    </div>
                    <div className="text-xs text-gray-600 mb-2">
                      {cert.volunteer} • {cert.branch}
                    </div>
                    <div className="flex items-center justify-between">
                      <div className={`px-2 py-1 rounded-full text-xs text-white ${getStatusColor(cert.status)}`}>
                        {cert.daysUntilExpiry < 0 
                          ? `Expired ${Math.abs(cert.daysUntilExpiry)} days ago`
                          : cert.daysUntilExpiry === 0
                          ? 'Expires today'
                          : `${cert.daysUntilExpiry} days left`
                        }
                      </div>
                      <div className="text-xs text-gray-500">
                        Expires: {new Date(cert.expiry_date).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div>
            <h4 className="font-medium mb-3">Expiry Status by Branch</h4>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {Object.entries(byBranch).map(([branch, stats]) => (
                <div key={branch} className="border rounded-lg p-3">
                  <div className="font-medium text-sm mb-2">{branch}</div>
                  <div className="flex items-center gap-1 mb-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-red-500 h-2 rounded-l-full"
                        style={{ 
                          width: `${((stats.expired + stats.urgent) / stats.total) * 100}%` 
                        }}
                      ></div>
                    </div>
                    <div className="text-xs text-gray-600 w-12">
                      {stats.total} total
                    </div>
                  </div>
                  <div className="grid grid-cols-4 gap-2 text-xs">
                    <div className="text-red-600">
                      Critical: {stats.expired + stats.urgent}
                    </div>
                    <div className="text-orange-600">
                      Warning: {stats.warning}
                    </div>
                    <div className="text-yellow-600">
                      Attention: {stats.attention}
                    </div>
                    <div className="text-green-600">
                      Valid: {stats.valid}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-6">
          <h4 className="font-medium mb-3">Status by Criticality Level</h4>
          <div className="grid md:grid-cols-3 gap-4">
            {Object.entries(byCriticality).map(([criticality, stats]) => (
              <div key={criticality} className={`border rounded-xl p-4 ${getCriticalityColor(criticality)}`}>
                <div className="font-medium mb-2 capitalize">{criticality} Priority</div>
                <div className="text-sm space-y-1">
                  <div>Critical: {stats.expired + stats.urgent}</div>
                  <div>Warning: {stats.warning}</div>
                  <div>Valid: {stats.valid}</div>
                  <div className="font-medium pt-1 border-t">
                    Total: {stats.total}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}