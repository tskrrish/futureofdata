import React from 'react';
import { Calendar, Clock, Users, MapPin, AlertTriangle, CheckCircle } from 'lucide-react';

export const EventCard = ({ event, onEdit, onAssignStaff, recommendations = [] }) => {
  const statusConfig = {
    optimal: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-800', icon: CheckCircle },
    understaffed: { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-800', icon: AlertTriangle },
    critically_understaffed: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-800', icon: AlertTriangle },
    overstaffed: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-800', icon: Users }
  };

  const config = statusConfig[event.status] || statusConfig.optimal;
  const StatusIcon = config.icon;

  const totalRequired = event.requiredStaffRoles.reduce((sum, role) => sum + role.required, 0);
  const totalAssigned = event.requiredStaffRoles.reduce((sum, role) => sum + role.assigned, 0);

  return (
    <div className={`p-4 rounded-lg border-2 ${config.bg} ${config.border}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-gray-900">{event.name}</h3>
            <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
              <StatusIcon className="w-3 h-3" />
              {event.status.replace('_', ' ')}
            </div>
          </div>
          
          <div className="flex items-center gap-4 text-sm text-gray-600 mb-2">
            <div className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              {new Date(event.date).toLocaleDateString()}
            </div>
            <div className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              {event.startTime} - {event.endTime}
            </div>
            <div className="flex items-center gap-1">
              <MapPin className="w-4 h-4" />
              {event.branch}
            </div>
          </div>
          
          <div className="flex items-center gap-2 text-sm text-gray-700">
            <Users className="w-4 h-4" />
            <span>Expected: {event.estimatedAttendees} attendees</span>
          </div>
        </div>
        
        {onEdit && (
          <button
            onClick={() => onEdit(event)}
            className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-md"
          >
            Edit
          </button>
        )}
      </div>

      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-medium text-gray-900">Staff Requirements</h4>
          <span className={`text-sm font-medium ${config.text}`}>
            {totalAssigned}/{totalRequired} assigned ({Math.round((totalAssigned/totalRequired) * 100)}%)
          </span>
        </div>
        
        <div className="space-y-2">
          {event.requiredStaffRoles.map((role, index) => (
            <div key={index} className="flex items-center justify-between p-2 bg-white rounded border">
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-sm">{role.role}</span>
                  <span className="text-sm text-gray-600">
                    {role.assigned}/{role.required}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                  <div 
                    className={`h-1.5 rounded-full ${
                      role.assigned >= role.required ? 'bg-green-500' : 
                      role.assigned === 0 ? 'bg-red-500' : 'bg-yellow-500'
                    }`}
                    style={{ width: `${Math.min((role.assigned / role.required) * 100, 100)}%` }}
                  />
                </div>
              </div>
              
              {role.assigned < role.required && onAssignStaff && (
                <button
                  onClick={() => onAssignStaff(event.id, role.role)}
                  className="ml-2 px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  Assign
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {recommendations.length > 0 && (
        <div className="mt-4 p-3 bg-white rounded border">
          <h5 className="font-medium text-sm text-gray-900 mb-2">Recommendations</h5>
          <div className="space-y-1">
            {recommendations.slice(0, 2).map((rec, index) => (
              <div key={index} className="text-sm text-gray-600">
                {rec.type === 'shortage' ? (
                  <span className="text-red-600">
                    • Need {rec.shortage} more {rec.role}
                  </span>
                ) : (
                  <span className="text-blue-600">
                    • {rec.excess} excess {rec.role} - consider reallocating
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};