import React, { useState, useMemo } from "react";
import { Calculator, Filter, Save, X, Plus, Trash2, Edit3 } from "lucide-react";

const AVAILABLE_FIELDS = [
  { key: "hours", label: "Total Hours", type: "number" },
  { key: "activeVolunteers", label: "Active Volunteers", type: "number" },
  { key: "memberVolunteers", label: "Member Volunteers", type: "number" },
  { key: "memberRate", label: "Member Rate (%)", type: "percentage" },
  { key: "avgHoursPerVolunteer", label: "Avg Hours/Volunteer", type: "number" },
  { key: "totalProjects", label: "Total Projects", type: "number" }
];

const OPERATORS = [
  { symbol: "+", label: "Add" },
  { symbol: "-", label: "Subtract" },
  { symbol: "*", label: "Multiply" },
  { symbol: "/", label: "Divide" },
  { symbol: "(", label: "Open Parenthesis" },
  { symbol: ")", label: "Close Parenthesis" }
];

const FILTER_FIELDS = [
  { key: "branch", label: "Branch", type: "select" },
  { key: "is_member", label: "Member Status", type: "boolean" },
  { key: "project_tag", label: "Project Tag", type: "text" },
  { key: "date", label: "Date Range", type: "daterange" },
  { key: "department", label: "Department", type: "text" }
];

export function KPIBuilder({ isOpen, onClose, volunteerData, onSaveKPI, customKPIs = [] }) {
  const [kpiName, setKpiName] = useState("");
  const [formula, setFormula] = useState("");
  const [filters, setFilters] = useState([]);
  const [previewValue, setPreviewValue] = useState(null);
  const [editingKPI, setEditingKPI] = useState(null);

  // Available filter values based on data
  const filterOptions = useMemo(() => {
    if (!volunteerData?.filtered) return {};
    
    return {
      branch: [...new Set(volunteerData.filtered.map(r => r.branch))].sort(),
      project_tag: [...new Set(volunteerData.filtered.map(r => r.project_tag))].sort(),
      department: [...new Set(volunteerData.filtered.map(r => r.department))].sort()
    };
  }, [volunteerData]);

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
    if (!volunteerData?.filtered || filters.length === 0) return fieldValues;
    
    let filteredData = volunteerData.filtered;
    
    filters.forEach(filter => {
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
  }, [volunteerData, filters, fieldValues]);

  // Evaluate formula
  const evaluateFormula = React.useCallback((formulaStr) => {
    if (!formulaStr) return null;
    
    try {
      let processedFormula = formulaStr;
      
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
      return isNaN(result) ? null : Number(result.toFixed(2));
    } catch {
      return null;
    }
  }, [filteredFieldValues]);

  // Update preview when formula or filters change
  React.useEffect(() => {
    setPreviewValue(evaluateFormula(formula));
  }, [formula, evaluateFormula]);

  const addFilter = () => {
    setFilters([...filters, { field: "branch", operator: "equals", value: "" }]);
  };

  const updateFilter = (index, updates) => {
    const newFilters = [...filters];
    newFilters[index] = { ...newFilters[index], ...updates };
    setFilters(newFilters);
  };

  const removeFilter = (index) => {
    setFilters(filters.filter((_, i) => i !== index));
  };

  const insertFormulaToken = (token) => {
    setFormula(prev => prev + token);
  };

  const handleSave = () => {
    if (!kpiName.trim() || !formula.trim()) return;
    
    const kpi = {
      id: editingKPI ? editingKPI.id : Date.now().toString(),
      name: kpiName,
      formula,
      filters: [...filters],
      createdAt: editingKPI ? editingKPI.createdAt : new Date().toISOString()
    };
    
    onSaveKPI(kpi, editingKPI ? 'edit' : 'create');
    resetForm();
  };

  const resetForm = () => {
    setKpiName("");
    setFormula("");
    setFilters([]);
    setEditingKPI(null);
    onClose();
  };

  const loadKPIForEdit = (kpi) => {
    setEditingKPI(kpi);
    setKpiName(kpi.name);
    setFormula(kpi.formula);
    setFilters([...kpi.filters]);
  };

  const deleteKPI = (kpiId) => {
    onSaveKPI({ id: kpiId }, 'delete');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <Calculator className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-semibold">
              {editingKPI ? 'Edit Custom KPI' : 'Custom KPI Builder'}
            </h2>
          </div>
          <button onClick={resetForm} className="p-2 hover:bg-gray-100 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="overflow-y-auto max-h-[calc(90vh-80px)]">
          <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Left Column - Builder */}
            <div className="space-y-6">
              
              {/* KPI Name */}
              <div>
                <label className="block text-sm font-medium mb-2">KPI Name</label>
                <input
                  type="text"
                  value={kpiName}
                  onChange={(e) => setKpiName(e.target.value)}
                  placeholder="e.g., Member Engagement Rate"
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Formula Builder */}
              <div>
                <label className="block text-sm font-medium mb-2">Formula</label>
                <textarea
                  value={formula}
                  onChange={(e) => setFormula(e.target.value)}
                  placeholder="e.g., (memberVolunteers / activeVolunteers) * 100"
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                  rows={3}
                />
                
                {/* Formula Helpers */}
                <div className="mt-3 space-y-3">
                  <div>
                    <p className="text-sm font-medium mb-2">Available Fields:</p>
                    <div className="flex flex-wrap gap-1">
                      {AVAILABLE_FIELDS.map(field => (
                        <button
                          key={field.key}
                          onClick={() => insertFormulaToken(field.key)}
                          className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                        >
                          {field.label}
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <p className="text-sm font-medium mb-2">Operators:</p>
                    <div className="flex flex-wrap gap-1">
                      {OPERATORS.map(op => (
                        <button
                          key={op.symbol}
                          onClick={() => insertFormulaToken(op.symbol)}
                          className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                        >
                          {op.symbol}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Filters */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <label className="text-sm font-medium">Filters</label>
                  <button
                    onClick={addFilter}
                    className="flex items-center gap-1 px-3 py-1 text-sm bg-green-100 text-green-700 rounded-lg hover:bg-green-200"
                  >
                    <Plus className="w-4 h-4" />
                    Add Filter
                  </button>
                </div>
                
                <div className="space-y-2">
                  {filters.map((filter, index) => (
                    <div key={index} className="flex items-center gap-2 p-3 border rounded-lg">
                      <Filter className="w-4 h-4 text-gray-400" />
                      
                      <select
                        value={filter.field}
                        onChange={(e) => updateFilter(index, { field: e.target.value, value: "" })}
                        className="px-2 py-1 border rounded text-sm"
                      >
                        {FILTER_FIELDS.map(field => (
                          <option key={field.key} value={field.key}>{field.label}</option>
                        ))}
                      </select>
                      
                      {filter.field === "branch" && (
                        <select
                          value={filter.value}
                          onChange={(e) => updateFilter(index, { value: e.target.value })}
                          className="px-2 py-1 border rounded text-sm flex-1"
                        >
                          <option value="">Select Branch</option>
                          {filterOptions.branch?.map(branch => (
                            <option key={branch} value={branch}>{branch}</option>
                          ))}
                        </select>
                      )}
                      
                      {filter.field === "is_member" && (
                        <select
                          value={filter.value}
                          onChange={(e) => updateFilter(index, { value: e.target.value === "true" })}
                          className="px-2 py-1 border rounded text-sm flex-1"
                        >
                          <option value="">All</option>
                          <option value="true">Members Only</option>
                          <option value="false">Non-Members Only</option>
                        </select>
                      )}
                      
                      {(filter.field === "project_tag" || filter.field === "department") && (
                        <input
                          type="text"
                          value={filter.value}
                          onChange={(e) => updateFilter(index, { value: e.target.value })}
                          placeholder={`Enter ${filter.field.replace('_', ' ')}`}
                          className="px-2 py-1 border rounded text-sm flex-1"
                        />
                      )}
                      
                      {filter.field === "date" && (
                        <div className="flex gap-2 flex-1">
                          <input
                            type="date"
                            value={filter.startDate || ""}
                            onChange={(e) => updateFilter(index, { startDate: e.target.value })}
                            className="px-2 py-1 border rounded text-sm"
                          />
                          <span className="self-center text-sm text-gray-500">to</span>
                          <input
                            type="date"
                            value={filter.endDate || ""}
                            onChange={(e) => updateFilter(index, { endDate: e.target.value })}
                            className="px-2 py-1 border rounded text-sm"
                          />
                        </div>
                      )}
                      
                      <button
                        onClick={() => removeFilter(index)}
                        className="p-1 text-red-500 hover:bg-red-50 rounded"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

            </div>

            {/* Right Column - Preview & Saved KPIs */}
            <div className="space-y-6">
              
              {/* Preview */}
              <div>
                <label className="block text-sm font-medium mb-2">Preview</label>
                <div className="p-4 border rounded-lg bg-gray-50">
                  <div className="text-2xl font-bold text-center">
                    {previewValue !== null ? previewValue : "—"}
                  </div>
                  <div className="text-sm text-gray-600 text-center mt-1">
                    {kpiName || "Custom KPI"}
                  </div>
                </div>
              </div>

              {/* Current Values */}
              <div>
                <label className="block text-sm font-medium mb-2">Current Values</label>
                <div className="space-y-2 text-sm">
                  {AVAILABLE_FIELDS.map(field => (
                    <div key={field.key} className="flex justify-between">
                      <span className="text-gray-600">{field.label}:</span>
                      <span className="font-medium">
                        {filteredFieldValues[field.key]?.toFixed(field.type === 'percentage' ? 1 : 2) || 0}
                        {field.type === 'percentage' ? '%' : ''}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Saved KPIs */}
              <div>
                <label className="block text-sm font-medium mb-2">Saved Custom KPIs</label>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {customKPIs.length > 0 ? customKPIs.map(kpi => (
                    <div key={kpi.id} className="flex items-center justify-between p-2 border rounded-lg">
                      <div className="flex-1">
                        <div className="font-medium text-sm">{kpi.name}</div>
                        <div className="text-xs text-gray-500 font-mono">{kpi.formula}</div>
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => loadKPIForEdit(kpi)}
                          className="p-1 text-blue-500 hover:bg-blue-50 rounded"
                        >
                          <Edit3 className="w-3 h-3" />
                        </button>
                        <button
                          onClick={() => deleteKPI(kpi.id)}
                          className="p-1 text-red-500 hover:bg-red-50 rounded"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  )) : (
                    <div className="text-sm text-gray-500 text-center py-4">
                      No custom KPIs saved yet
                    </div>
                  )}
                </div>
              </div>

            </div>

          </div>

          {/* Footer */}
          <div className="px-6 py-4 bg-gray-50 border-t flex justify-between">
            <button
              onClick={resetForm}
              className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={!kpiName.trim() || !formula.trim() || previewValue === null}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-4 h-4" />
              {editingKPI ? 'Update KPI' : 'Save KPI'}
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}