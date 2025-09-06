import React, { useState } from "react";
import { Package, Settings, Calendar, AlertTriangle, CheckCircle, Clock } from "lucide-react";

const STATUS_COLORS = {
  available: { bg: "bg-green-100", text: "text-green-700", icon: CheckCircle },
  assigned: { bg: "bg-blue-100", text: "text-blue-700", icon: Clock },
  maintenance: { bg: "bg-yellow-100", text: "text-yellow-700", icon: Settings },
  retired: { bg: "bg-neutral-100", text: "text-neutral-700", icon: AlertTriangle }
};

const CONDITION_COLORS = {
  excellent: "text-green-600",
  good: "text-blue-600", 
  fair: "text-yellow-600",
  poor: "text-red-600",
  maintenance: "text-orange-600"
};

export function ResourceList({ resources, compact = false, onEdit, onStatusUpdate }) {
  const [sortBy, setSortBy] = useState("name");
  const [filterType, setFilterType] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");

  // Get unique resource types
  const resourceTypes = [...new Set(resources.map(r => r.resource_type))];

  // Filter and sort resources
  const filteredResources = resources
    .filter(resource => {
      if (filterType !== "all" && resource.resource_type !== filterType) return false;
      if (filterStatus !== "all" && resource.status !== filterStatus) return false;
      return true;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case "name":
          return a.name.localeCompare(b.name);
        case "type":
          return a.resource_type.localeCompare(b.resource_type);
        case "status":
          return a.status.localeCompare(b.status);
        case "condition":
          return a.condition.localeCompare(b.condition);
        default:
          return 0;
      }
    });

  const handleStatusChange = async (resourceId, newStatus) => {
    try {
      await onStatusUpdate(resourceId, { status: newStatus });
    } catch (error) {
      console.error('Failed to update resource status:', error);
    }
  };

  if (compact) {
    return (
      <div className="space-y-2">
        {filteredResources.length === 0 ? (
          <div className="text-center py-8 text-neutral-500">
            <Package className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No resources found</p>
          </div>
        ) : (
          filteredResources.map((resource) => {
            const statusInfo = STATUS_COLORS[resource.status] || STATUS_COLORS.available;
            const StatusIcon = statusInfo.icon;
            
            return (
              <div
                key={resource.id}
                className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg hover:bg-neutral-100 cursor-pointer"
                onClick={() => onEdit && onEdit(resource)}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Package className="w-4 h-4 text-blue-600" />
                  </div>
                  <div>
                    <div className="font-medium text-sm">{resource.name}</div>
                    <div className="text-xs text-neutral-500">{resource.resource_type}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <StatusIcon className="w-4 h-4 text-neutral-400" />
                </div>
              </div>
            );
          })
        )}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border">
      <div className="p-6 border-b">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h2 className="text-lg font-semibold">Resources & Equipment</h2>
          
          {/* Filters */}
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="name">Sort by Name</option>
              <option value="type">Sort by Type</option>
              <option value="status">Sort by Status</option>
              <option value="condition">Sort by Condition</option>
            </select>

            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Types</option>
              {resourceTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>

            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Status</option>
              <option value="available">Available</option>
              <option value="assigned">Assigned</option>
              <option value="maintenance">Maintenance</option>
              <option value="retired">Retired</option>
            </select>
          </div>
        </div>
      </div>

      <div className="p-6">
        {filteredResources.length === 0 ? (
          <div className="text-center py-12 text-neutral-500">
            <Package className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p className="text-lg mb-2">No resources found</p>
            <p className="text-sm">Try adjusting your filters or add a new resource</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {filteredResources.map((resource) => {
              const statusInfo = STATUS_COLORS[resource.status] || STATUS_COLORS.available;
              const StatusIcon = statusInfo.icon;
              
              return (
                <div
                  key={resource.id}
                  className="border border-neutral-200 rounded-xl p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                        <Package className="w-6 h-6 text-blue-600" />
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-semibold text-lg">{resource.name}</h3>
                          <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusInfo.bg} ${statusInfo.text}`}>
                            <StatusIcon className="w-3 h-3" />
                            {resource.status}
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <div className="text-neutral-500">Type</div>
                            <div className="font-medium capitalize">{resource.resource_type}</div>
                          </div>
                          
                          <div>
                            <div className="text-neutral-500">Condition</div>
                            <div className={`font-medium capitalize ${CONDITION_COLORS[resource.condition] || 'text-neutral-700'}`}>
                              {resource.condition}
                            </div>
                          </div>
                          
                          <div>
                            <div className="text-neutral-500">Branch</div>
                            <div className="font-medium">{resource.branch}</div>
                          </div>
                          
                          <div>
                            <div className="text-neutral-500">Max Assignments</div>
                            <div className="font-medium">{resource.max_concurrent_assignments}</div>
                          </div>
                        </div>

                        {resource.description && (
                          <p className="text-sm text-neutral-600 mt-2">{resource.description}</p>
                        )}

                        {resource.serial_number && (
                          <div className="text-xs text-neutral-500 mt-2">
                            S/N: {resource.serial_number}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {/* Status Update Dropdown */}
                      <select
                        value={resource.status}
                        onChange={(e) => handleStatusChange(resource.id, e.target.value)}
                        className="px-2 py-1 border border-neutral-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        <option value="available">Available</option>
                        <option value="assigned">Assigned</option>
                        <option value="maintenance">Maintenance</option>
                        <option value="retired">Retired</option>
                      </select>

                      <button
                        onClick={() => onEdit && onEdit(resource)}
                        className="p-2 text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 rounded-lg"
                        title="Edit resource"
                      >
                        <Settings className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Maintenance info */}
                  {resource.next_maintenance_date && (
                    <div className="mt-3 pt-3 border-t border-neutral-100">
                      <div className="flex items-center gap-2 text-sm text-neutral-600">
                        <Calendar className="w-4 h-4" />
                        Next maintenance: {new Date(resource.next_maintenance_date).toLocaleDateString()}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}