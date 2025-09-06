import React, { useMemo } from "react";
import { Calculator, Filter, AlertTriangle } from "lucide-react";

const AVAILABLE_FIELDS = [
  { key: "hours", label: "Total Hours", type: "number" },
  { key: "activeVolunteers", label: "Active Volunteers", type: "number" },
  { key: "memberVolunteers", label: "Member Volunteers", type: "number" },
  { key: "memberRate", label: "Member Rate (%)", type: "percentage" },
  { key: "avgHoursPerVolunteer", label: "Avg Hours/Volunteer", type: "number" },
  { key: "totalProjects", label: "Total Projects", type: "number" }
];

export function CustomKPI({ kpi, volunteerData, className = "" }) {
  // Calculate field values from data
  const fieldValues = useMemo(() => {
    if (!volunteerData) return {};
    
    return {
      hours: volunteerData.totalHours,
      activeVolunteers: volunteerData.activeVolunteersCount,
      memberVolunteers: volunteerData.memberVolunteersCount,
      memberRate: volunteerData.activeVolunteersCount > 0 
        ? ((volunteerData.memberVolunteersCount / volunteerData.activeVolunteersCount) * 100) 
        : 0,
      avgHoursPerVolunteer: volunteerData.activeVolunteersCount > 0 
        ? (volunteerData.totalHours / volunteerData.activeVolunteersCount) 
        : 0,
      totalProjects: new Set(volunteerData.filtered?.map(r => `${r.project}||${r.branch}`)).size
    };
  }, [volunteerData]);

  // Apply filters to data and recalculate values
  const filteredFieldValues = useMemo(() => {
    if (!volunteerData?.filtered || !kpi.filters || kpi.filters.length === 0) return fieldValues;
    
    let filteredData = volunteerData.filtered;
    
    kpi.filters.forEach(filter => {
      switch (filter.field) {
        case "branch":
          if (filter.value && filter.value !== "All") {
            filteredData = filteredData.filter(r => r.branch === filter.value);
          }
          break;
        case "is_member":
          if (filter.value !== null) {
            filteredData = filteredData.filter(r => r.is_member === filter.value);
          }
          break;
        case "project_tag":
          if (filter.value) {
            filteredData = filteredData.filter(r => 
              r.project_tag?.toLowerCase().includes(filter.value.toLowerCase())
            );
          }
          break;
        case "department":
          if (filter.value) {
            filteredData = filteredData.filter(r => 
              r.department?.toLowerCase().includes(filter.value.toLowerCase())
            );
          }
          break;
        case "date":
          if (filter.startDate && filter.endDate) {
            filteredData = filteredData.filter(r => {
              const recordDate = new Date(r.date);
              return recordDate >= new Date(filter.startDate) && recordDate <= new Date(filter.endDate);
            });
          }
          break;
      }
    });

    const activeVolunteersCount = new Set(
      filteredData.map(r => `${r.assignee}||${r.branch}`)
    ).size;
    
    const memberVolunteersCount = new Set(
      filteredData.filter(r => r.is_member).map(r => `${r.assignee}||${r.branch}`)
    ).size;

    const totalHours = filteredData.reduce((acc, r) => acc + (Number(r.hours) || 0), 0);
    
    return {
      hours: totalHours,
      activeVolunteers: activeVolunteersCount,
      memberVolunteers: memberVolunteersCount,
      memberRate: activeVolunteersCount > 0 ? ((memberVolunteersCount / activeVolunteersCount) * 100) : 0,
      avgHoursPerVolunteer: activeVolunteersCount > 0 ? (totalHours / activeVolunteersCount) : 0,
      totalProjects: new Set(filteredData.map(r => `${r.project}||${r.branch}`)).size
    };
  }, [volunteerData, kpi.filters, fieldValues]);

  // Evaluate formula
  const { value, error } = useMemo(() => {
    if (!kpi.formula) return { value: null, error: "No formula" };
    
    try {
      let processedFormula = kpi.formula;
      
      // Replace field names with actual values
      AVAILABLE_FIELDS.forEach(field => {
        const regex = new RegExp(`\\b${field.key}\\b`, 'g');
        processedFormula = processedFormula.replace(regex, filteredFieldValues[field.key] || 0);
      });
      
      // Basic safety check - only allow numbers, operators, and parentheses
      if (!/^[0-9+\-*/.() ]+$/.test(processedFormula)) {
        throw new Error("Invalid formula");
      }
      
      // Evaluate the expression
      const result = Function('"use strict"; return (' + processedFormula + ')')();
      if (isNaN(result)) throw new Error("Result is NaN");
      
      return { value: Number(result.toFixed(2)), error: null };
    } catch (err) {
      return { value: null, error: err.message };
    }
  }, [kpi.formula, filteredFieldValues]);

  const hasFilters = kpi.filters && kpi.filters.length > 0;

  return (
    <div className={`rounded-2xl border bg-white p-4 ${className}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3 flex-1">
          <div className="w-10 h-10 rounded-2xl bg-purple-100 grid place-items-center">
            <Calculator className="w-5 h-5 text-purple-600" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm text-neutral-500 truncate">{kpi.name}</div>
            <div className="text-xl font-semibold">
              {error ? (
                <div className="flex items-center gap-1 text-red-500">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="text-sm">Error</span>
                </div>
              ) : (
                value !== null ? value : "—"
              )}
            </div>
            {hasFilters && (
              <div className="flex items-center gap-1 mt-1">
                <Filter className="w-3 h-3 text-blue-500" />
                <span className="text-xs text-blue-600">
                  {kpi.filters.length} filter{kpi.filters.length !== 1 ? 's' : ''} applied
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Show formula on hover/expansion */}
      <div className="mt-2 pt-2 border-t border-gray-100">
        <div className="text-xs text-gray-500 font-mono truncate" title={kpi.formula}>
          {kpi.formula}
        </div>
      </div>
    </div>
  );
}

// Grid component for displaying multiple custom KPIs
export function CustomKPIGrid({ kpis = [], volunteerData, className = "" }) {
  if (!kpis.length) return null;

  return (
    <div className={`grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 ${className}`}>
      {kpis.map(kpi => (
        <CustomKPI 
          key={kpi.id} 
          kpi={kpi} 
          volunteerData={volunteerData}
        />
      ))}
    </div>
  );
}