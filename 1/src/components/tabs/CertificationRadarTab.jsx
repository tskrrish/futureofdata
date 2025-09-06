import { CertificationExpiryRadarChart } from "../charts/CertificationExpiryRadarChart";
import { Filter } from "lucide-react";

export function CertificationRadarTab({ 
  certificationData, 
  branches, 
  criticalityFilter, 
  onCriticalityChange,
  onExport 
}) {
  const criticalities = ['all', 'critical', 'high', 'medium', 'low'];

  return (
    <div className="mt-4 space-y-4">
      <div className="flex items-center gap-4 p-4 bg-white rounded-2xl border">
        <Filter className="w-5 h-5 text-gray-400" />
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Criticality Filter:</label>
          <select
            value={criticalityFilter}
            onChange={(e) => onCriticalityChange(e.target.value)}
            className="rounded-xl border px-3 py-1.5 text-sm"
          >
            {criticalities.map((criticality) => (
              <option key={criticality} value={criticality}>
                {criticality === 'all' ? 'All Criticalities' : `${criticality.charAt(0).toUpperCase() + criticality.slice(1)} Priority`}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid gap-6">
        <CertificationExpiryRadarChart 
          data={certificationData} 
          onExport={onExport}
        />
      </div>
    </div>
  );
}