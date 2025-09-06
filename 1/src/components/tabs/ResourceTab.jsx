import React, { useState } from "react";
import { Plus, Calendar, Package, Users, Clock, CheckCircle2, AlertCircle } from "lucide-react";
import { KPI } from "../ui/KPI";
import { useResourceData } from "../../hooks/useResourceData";
import { ResourceList } from "../resources/ResourceList";
import { ShiftList } from "../resources/ShiftList";
import { AssignmentManager } from "../resources/AssignmentManager";
import { UsageTracker } from "../resources/UsageTracker";
import { ResourceForm } from "../resources/ResourceForm";
import { ShiftForm } from "../resources/ShiftForm";

export function ResourceTab() {
  const {
    shifts,
    resources,
    assignments,
    branches,
    stats,
    loading,
    error,
    createShift,
    updateShift,
    createResource,
    updateResource,
    createAssignment,
    updateAssignmentStatus,
    fetchUtilizationStats
  } = useResourceData();

  const [activeView, setActiveView] = useState("overview");
  const [selectedBranch, setSelectedBranch] = useState("All");
  const [showResourceForm, setShowResourceForm] = useState(false);
  const [showShiftForm, setShowShiftForm] = useState(false);
  const [editingResource, setEditingResource] = useState(null);
  const [editingShift, setEditingShift] = useState(null);

  // Filter data based on selected branch
  const filteredShifts = selectedBranch === "All" 
    ? shifts 
    : shifts.filter(s => s.branch === selectedBranch);
  
  const filteredResources = selectedBranch === "All" 
    ? resources 
    : resources.filter(r => r.branch === selectedBranch);

  const handleResourceSubmit = async (resourceData) => {
    try {
      if (editingResource) {
        await updateResource(editingResource.id, resourceData);
        setEditingResource(null);
      } else {
        await createResource(resourceData);
      }
      setShowResourceForm(false);
    } catch (error) {
      console.error('Failed to save resource:', error);
    }
  };

  const handleShiftSubmit = async (shiftData) => {
    try {
      if (editingShift) {
        await updateShift(editingShift.id, shiftData);
        setEditingShift(null);
      } else {
        await createShift(shiftData);
      }
      setShowShiftForm(false);
    } catch (error) {
      console.error('Failed to save shift:', error);
    }
  };

  if (loading && (shifts.length === 0 && resources.length === 0)) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-neutral-600">Loading resource data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center text-red-600">
          <AlertCircle className="w-8 h-8 mx-auto mb-4" />
          <p>{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-4 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-4 space-y-6">
      {/* Branch Filter */}
      <div className="flex flex-wrap items-center gap-4 mb-6">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-neutral-700">Branch:</label>
          <select
            value={selectedBranch}
            onChange={(e) => setSelectedBranch(e.target.value)}
            className="px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {branches.map(branch => (
              <option key={branch} value={branch}>{branch}</option>
            ))}
          </select>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPI 
          icon={<Package className="w-5 h-5" />} 
          label="Total Resources" 
          value={stats.totalResources}
          sub={`${stats.availableResources} available`}
        />
        <KPI 
          icon={<Calendar className="w-5 h-5" />} 
          label="Active Shifts" 
          value={stats.activeShifts} 
        />
        <KPI 
          icon={<Users className="w-5 h-5" />} 
          label="Active Assignments" 
          value={stats.activeAssignments} 
        />
        <KPI 
          icon={<CheckCircle2 className="w-5 h-5" />} 
          label="Utilization Rate" 
          value={`${stats.utilizationRate}%`} 
        />
      </div>

      {/* View Navigation */}
      <div className="inline-flex rounded-2xl border bg-white overflow-hidden text-sm">
        {[
          ["overview", "Overview"],
          ["shifts", "Shifts"],
          ["resources", "Resources"],
          ["assignments", "Assignments"],
          ["usage", "Usage Tracking"],
        ].map(([id, label]) => (
          <button
            key={id}
            className={`px-4 py-2 ${activeView === id ? "bg-neutral-100" : "hover:bg-neutral-50"}`}
            onClick={() => setActiveView(id)}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setShowResourceForm(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Add Resource
        </button>
        <button
          onClick={() => setShowShiftForm(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
        >
          <Plus className="w-4 h-4" />
          Add Shift
        </button>
      </div>

      {/* Content based on active view */}
      <div className="min-h-[400px]">
        {activeView === "overview" && (
          <div className="grid lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-2xl border p-6">
              <h3 className="font-semibold text-lg mb-4">Recent Shifts</h3>
              <ShiftList 
                shifts={filteredShifts.slice(0, 5)} 
                compact={true}
                onEdit={(shift) => {
                  setEditingShift(shift);
                  setShowShiftForm(true);
                }}
              />
            </div>
            <div className="bg-white rounded-2xl border p-6">
              <h3 className="font-semibold text-lg mb-4">Resources by Type</h3>
              <ResourceList 
                resources={filteredResources.slice(0, 5)} 
                compact={true}
                onEdit={(resource) => {
                  setEditingResource(resource);
                  setShowResourceForm(true);
                }}
              />
            </div>
          </div>
        )}

        {activeView === "shifts" && (
          <ShiftList 
            shifts={filteredShifts}
            onEdit={(shift) => {
              setEditingShift(shift);
              setShowShiftForm(true);
            }}
            onStatusUpdate={updateShift}
          />
        )}

        {activeView === "resources" && (
          <ResourceList 
            resources={filteredResources}
            onEdit={(resource) => {
              setEditingResource(resource);
              setShowResourceForm(true);
            }}
            onStatusUpdate={updateResource}
          />
        )}

        {activeView === "assignments" && (
          <AssignmentManager 
            shifts={filteredShifts}
            resources={filteredResources}
            assignments={assignments}
            onCreateAssignment={createAssignment}
            onUpdateStatus={updateAssignmentStatus}
          />
        )}

        {activeView === "usage" && (
          <UsageTracker 
            resources={filteredResources}
            assignments={assignments}
            onFetchStats={fetchUtilizationStats}
          />
        )}
      </div>

      {/* Modals */}
      {showResourceForm && (
        <ResourceForm
          resource={editingResource}
          branches={branches.filter(b => b !== 'All')}
          onSubmit={handleResourceSubmit}
          onClose={() => {
            setShowResourceForm(false);
            setEditingResource(null);
          }}
        />
      )}

      {showShiftForm && (
        <ShiftForm
          shift={editingShift}
          branches={branches.filter(b => b !== 'All')}
          onSubmit={handleShiftSubmit}
          onClose={() => {
            setShowShiftForm(false);
            setEditingShift(null);
          }}
        />
      )}
    </div>
  );
}