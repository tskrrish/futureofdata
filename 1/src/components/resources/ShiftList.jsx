import React, { useState } from "react";
import { Calendar, Clock, Users, MapPin, Settings, Play, Square, CheckCircle, X } from "lucide-react";

const STATUS_COLORS = {
  scheduled: { bg: "bg-blue-100", text: "text-blue-700", icon: Calendar },
  active: { bg: "bg-green-100", text: "text-green-700", icon: Play },
  completed: { bg: "bg-neutral-100", text: "text-neutral-700", icon: CheckCircle },
  cancelled: { bg: "bg-red-100", text: "text-red-700", icon: X }
};

export function ShiftList({ shifts, compact = false, onEdit, onStatusUpdate }) {
  const [sortBy, setSortBy] = useState("start_time");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterBranch, setFilterBranch] = useState("all");

  // Get unique branches from shifts
  const branches = [...new Set(shifts.map(s => s.branch))];

  // Filter and sort shifts
  const filteredShifts = shifts
    .filter(shift => {
      if (filterStatus !== "all" && shift.status !== filterStatus) return false;
      if (filterBranch !== "all" && shift.branch !== filterBranch) return false;
      return true;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case "start_time":
          return new Date(a.start_time) - new Date(b.start_time);
        case "name":
          return a.name.localeCompare(b.name);
        case "branch":
          return a.branch.localeCompare(b.branch);
        default:
          return 0;
      }
    });

  const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return {
      date: date.toLocaleDateString(),
      time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
  };

  const getDuration = (startTime, endTime) => {
    const start = new Date(startTime);
    const end = new Date(endTime);
    const diff = end - start;
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours}h ${minutes}m`;
  };

  const handleStatusChange = async (shiftId, newStatus) => {
    try {
      await onStatusUpdate(shiftId, { status: newStatus });
    } catch (error) {
      console.error('Failed to update shift status:', error);
    }
  };

  if (compact) {
    return (
      <div className="space-y-2">
        {filteredShifts.length === 0 ? (
          <div className="text-center py-8 text-neutral-500">
            <Calendar className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No shifts found</p>
          </div>
        ) : (
          filteredShifts.map((shift) => {
            const startDateTime = formatDateTime(shift.start_time);
            const statusInfo = STATUS_COLORS[shift.status] || STATUS_COLORS.scheduled;
            const StatusIcon = statusInfo.icon;
            
            return (
              <div
                key={shift.id}
                className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg hover:bg-neutral-100 cursor-pointer"
                onClick={() => onEdit && onEdit(shift)}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                    <Calendar className="w-4 h-4 text-green-600" />
                  </div>
                  <div>
                    <div className="font-medium text-sm">{shift.name}</div>
                    <div className="text-xs text-neutral-500">
                      {startDateTime.date} • {startDateTime.time}
                    </div>
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
          <h2 className="text-lg font-semibold">Shifts Schedule</h2>
          
          {/* Filters */}
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="start_time">Sort by Date</option>
              <option value="name">Sort by Name</option>
              <option value="branch">Sort by Branch</option>
            </select>

            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Status</option>
              <option value="scheduled">Scheduled</option>
              <option value="active">Active</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>

            <select
              value={filterBranch}
              onChange={(e) => setFilterBranch(e.target.value)}
              className="px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Branches</option>
              {branches.map(branch => (
                <option key={branch} value={branch}>{branch}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="p-6">
        {filteredShifts.length === 0 ? (
          <div className="text-center py-12 text-neutral-500">
            <Calendar className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p className="text-lg mb-2">No shifts found</p>
            <p className="text-sm">Try adjusting your filters or add a new shift</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {filteredShifts.map((shift) => {
              const startDateTime = formatDateTime(shift.start_time);
              const endDateTime = formatDateTime(shift.end_time);
              const duration = getDuration(shift.start_time, shift.end_time);
              const statusInfo = STATUS_COLORS[shift.status] || STATUS_COLORS.scheduled;
              const StatusIcon = statusInfo.icon;
              
              return (
                <div
                  key={shift.id}
                  className="border border-neutral-200 rounded-xl p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4 flex-1">
                      <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                        <Calendar className="w-6 h-6 text-green-600" />
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-semibold text-lg">{shift.name}</h3>
                          <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusInfo.bg} ${statusInfo.text}`}>
                            <StatusIcon className="w-3 h-3" />
                            {shift.status}
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm mb-3">
                          <div className="flex items-center gap-2">
                            <Clock className="w-4 h-4 text-neutral-400" />
                            <div>
                              <div className="font-medium">
                                {startDateTime.date}
                              </div>
                              <div className="text-neutral-500">
                                {startDateTime.time} - {endDateTime.time} ({duration})
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <MapPin className="w-4 h-4 text-neutral-400" />
                            <div>
                              <div className="font-medium">{shift.branch}</div>
                              {shift.category && (
                                <div className="text-neutral-500">{shift.category}</div>
                              )}
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <Users className="w-4 h-4 text-neutral-400" />
                            <div>
                              <div className="font-medium">Max {shift.max_volunteers} volunteers</div>
                            </div>
                          </div>
                        </div>

                        {shift.description && (
                          <p className="text-sm text-neutral-600 mb-3">{shift.description}</p>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {/* Status Update Dropdown */}
                      <select
                        value={shift.status}
                        onChange={(e) => handleStatusChange(shift.id, e.target.value)}
                        className="px-2 py-1 border border-neutral-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        <option value="scheduled">Scheduled</option>
                        <option value="active">Active</option>
                        <option value="completed">Completed</option>
                        <option value="cancelled">Cancelled</option>
                      </select>

                      <button
                        onClick={() => onEdit && onEdit(shift)}
                        className="p-2 text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 rounded-lg"
                        title="Edit shift"
                      >
                        <Settings className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}