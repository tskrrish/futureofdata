import React, { useState } from "react";
import { Plus, Link, Package, Calendar, User, Clock } from "lucide-react";

const STATUS_COLORS = {
  assigned: { bg: "bg-blue-100", text: "text-blue-700" },
  checked_out: { bg: "bg-yellow-100", text: "text-yellow-700" },
  in_use: { bg: "bg-green-100", text: "text-green-700" },
  returned: { bg: "bg-neutral-100", text: "text-neutral-700" },
  damaged: { bg: "bg-red-100", text: "text-red-700" },
  lost: { bg: "bg-red-100", text: "text-red-700" }
};

export function AssignmentManager({ shifts, resources, assignments, onCreateAssignment, onUpdateStatus }) {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedShift, setSelectedShift] = useState("");
  const [selectedResource, setSelectedResource] = useState("");
  const [assignmentNotes, setAssignmentNotes] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  const handleCreateAssignment = async (e) => {
    e.preventDefault();
    
    if (!selectedShift || !selectedResource) {
      return;
    }

    setIsCreating(true);
    
    try {
      await onCreateAssignment({
        shift_id: selectedShift,
        resource_id: selectedResource,
        assignment_notes: assignmentNotes,
        quantity_assigned: 1
      });
      
      // Reset form
      setSelectedShift("");
      setSelectedResource("");
      setAssignmentNotes("");
      setShowCreateForm(false);
    } catch (error) {
      console.error('Failed to create assignment:', error);
    } finally {
      setIsCreating(false);
    }
  };

  const handleStatusUpdate = async (assignmentId, newStatus, additionalData = {}) => {
    try {
      await onUpdateStatus(assignmentId, {
        status: newStatus,
        ...additionalData
      });
    } catch (error) {
      console.error('Failed to update assignment status:', error);
    }
  };

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  // Get available resources (not assigned or returned)
  const availableResources = resources.filter(resource => 
    resource.status === 'available' &&
    !assignments.some(assignment => 
      assignment.resource_id === resource.id && 
      ['assigned', 'checked_out', 'in_use'].includes(assignment.status)
    )
  );

  // Group assignments by shift
  const assignmentsByShift = assignments.reduce((acc, assignment) => {
    const shiftId = assignment.shift_id;
    if (!acc[shiftId]) {
      acc[shiftId] = [];
    }
    acc[shiftId].push(assignment);
    return acc;
  }, {});

  return (
    <div className="bg-white rounded-2xl border">
      <div className="p-6 border-b">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Resource Assignments</h2>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" />
            New Assignment
          </button>
        </div>
      </div>

      {/* Create Assignment Form */}
      {showCreateForm && (
        <div className="p-6 border-b bg-blue-50">
          <form onSubmit={handleCreateAssignment} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">
                  Select Shift
                </label>
                <select
                  value={selectedShift}
                  onChange={(e) => setSelectedShift(e.target.value)}
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Choose a shift...</option>
                  {shifts
                    .filter(shift => shift.status === 'scheduled' || shift.status === 'active')
                    .map(shift => (
                    <option key={shift.id} value={shift.id}>
                      {shift.name} - {formatDateTime(shift.start_time)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">
                  Select Resource
                </label>
                <select
                  value={selectedResource}
                  onChange={(e) => setSelectedResource(e.target.value)}
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Choose a resource...</option>
                  {availableResources.map(resource => (
                    <option key={resource.id} value={resource.id}>
                      {resource.name} ({resource.resource_type})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Assignment Notes
              </label>
              <textarea
                value={assignmentNotes}
                onChange={(e) => setAssignmentNotes(e.target.value)}
                rows={2}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Optional notes about this assignment..."
              />
            </div>

            <div className="flex items-center gap-2">
              <button
                type="submit"
                disabled={isCreating || !selectedShift || !selectedResource}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isCreating ? 'Creating...' : 'Create Assignment'}
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 text-neutral-600 bg-neutral-100 rounded-lg hover:bg-neutral-200"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="p-6">
        {assignments.length === 0 ? (
          <div className="text-center py-12 text-neutral-500">
            <Link className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p className="text-lg mb-2">No assignments yet</p>
            <p className="text-sm">Create your first resource assignment</p>
          </div>
        ) : (
          <div className="space-y-6">
            {shifts
              .filter(shift => assignmentsByShift[shift.id])
              .map(shift => {
                const shiftAssignments = assignmentsByShift[shift.id] || [];
                
                return (
                  <div key={shift.id} className="border border-neutral-200 rounded-xl">
                    <div className="p-4 bg-neutral-50 border-b">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                          <Calendar className="w-4 h-4 text-green-600" />
                        </div>
                        <div>
                          <h3 className="font-semibold">{shift.name}</h3>
                          <p className="text-sm text-neutral-600">
                            {formatDateTime(shift.start_time)} - {shift.branch}
                          </p>
                        </div>
                        <div className="ml-auto text-sm text-neutral-500">
                          {shiftAssignments.length} resource{shiftAssignments.length !== 1 ? 's' : ''}
                        </div>
                      </div>
                    </div>

                    <div className="p-4 space-y-3">
                      {shiftAssignments.map(assignment => {
                        const resource = resources.find(r => r.id === assignment.resource_id);
                        const statusInfo = STATUS_COLORS[assignment.status] || STATUS_COLORS.assigned;
                        
                        return (
                          <div
                            key={assignment.id}
                            className="flex items-center justify-between p-3 bg-white border border-neutral-200 rounded-lg"
                          >
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                                <Package className="w-5 h-5 text-blue-600" />
                              </div>
                              <div>
                                <div className="font-medium">{resource?.name || 'Unknown Resource'}</div>
                                <div className="text-sm text-neutral-500">
                                  {resource?.resource_type} • {resource?.branch}
                                </div>
                                {assignment.assignment_notes && (
                                  <div className="text-xs text-neutral-500 mt-1">
                                    {assignment.assignment_notes}
                                  </div>
                                )}
                              </div>
                            </div>

                            <div className="flex items-center gap-3">
                              {/* Status Badge */}
                              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${statusInfo.bg} ${statusInfo.text}`}>
                                {assignment.status.replace('_', ' ')}
                              </span>

                              {/* Status Update Actions */}
                              <div className="flex items-center gap-1">
                                {assignment.status === 'assigned' && (
                                  <button
                                    onClick={() => handleStatusUpdate(assignment.id, 'checked_out', {
                                      condition_at_checkout: 'good'
                                    })}
                                    className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200"
                                  >
                                    Check Out
                                  </button>
                                )}

                                {assignment.status === 'checked_out' && (
                                  <>
                                    <button
                                      onClick={() => handleStatusUpdate(assignment.id, 'in_use')}
                                      className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200"
                                    >
                                      In Use
                                    </button>
                                    <button
                                      onClick={() => handleStatusUpdate(assignment.id, 'returned', {
                                        condition_at_return: 'good',
                                        return_notes: 'Returned in good condition'
                                      })}
                                      className="px-2 py-1 text-xs bg-neutral-100 text-neutral-700 rounded hover:bg-neutral-200"
                                    >
                                      Return
                                    </button>
                                  </>
                                )}

                                {assignment.status === 'in_use' && (
                                  <button
                                    onClick={() => handleStatusUpdate(assignment.id, 'returned', {
                                      condition_at_return: 'good',
                                      return_notes: 'Returned after use'
                                    })}
                                    className="px-2 py-1 text-xs bg-neutral-100 text-neutral-700 rounded hover:bg-neutral-200"
                                  >
                                    Return
                                  </button>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })}
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