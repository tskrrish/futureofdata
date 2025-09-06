import React, { useState } from 'react';
import { 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  FileText, 
  Calendar, 
  User, 
  Upload,
  Download,
  ExternalLink
} from 'lucide-react';

const StepTracker = ({ step, volunteerStep, onUpdateStep, volunteer }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    completed: volunteerStep?.completed || false,
    completedDate: volunteerStep?.completedDate || '',
    completedBy: volunteerStep?.completedBy || '',
    notes: volunteerStep?.notes || '',
    signatureUrl: volunteerStep?.signatureUrl || '',
    certificateUrl: volunteerStep?.certificateUrl || ''
  });

  const handleSave = () => {
    onUpdateStep(volunteer.id, step.id, {
      ...formData,
      completedDate: formData.completed ? (formData.completedDate || new Date().toISOString().split('T')[0]) : null
    });
    setIsEditing(false);
  };

  const handleCancel = () => {
    setFormData({
      completed: volunteerStep?.completed || false,
      completedDate: volunteerStep?.completedDate || '',
      completedBy: volunteerStep?.completedBy || '',
      notes: volunteerStep?.notes || '',
      signatureUrl: volunteerStep?.signatureUrl || '',
      certificateUrl: volunteerStep?.certificateUrl || ''
    });
    setIsEditing(false);
  };

  const getStatusIcon = () => {
    if (volunteerStep?.completed) {
      return <CheckCircle className="w-5 h-5 text-green-600" />;
    }
    if (step.required) {
      return <AlertCircle className="w-5 h-5 text-red-600" />;
    }
    return <Clock className="w-5 h-5 text-yellow-600" />;
  };

  const getStatusColor = () => {
    if (volunteerStep?.completed) return 'bg-green-50 border-green-200';
    if (step.required) return 'bg-red-50 border-red-200';
    return 'bg-yellow-50 border-yellow-200';
  };

  const renderViewMode = () => (
    <div className={`p-4 rounded-lg border ${getStatusColor()}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3 flex-1">
          {getStatusIcon()}
          <div className="flex-1">
            <h4 className="font-medium text-gray-900">{step.title}</h4>
            <p className="text-sm text-gray-600 mt-1">{step.description}</p>
            
            {step.required && (
              <span className="inline-block mt-2 text-xs bg-red-100 text-red-800 px-2 py-1 rounded-full">
                Required
              </span>
            )}

            {volunteerStep?.completed && (
              <div className="mt-3 space-y-2">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Calendar className="w-4 h-4" />
                  <span>Completed: {new Date(volunteerStep.completedDate).toLocaleDateString()}</span>
                </div>
                
                {volunteerStep.completedBy && (
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <User className="w-4 h-4" />
                    <span>Completed by: {volunteerStep.completedBy}</span>
                  </div>
                )}
                
                {volunteerStep.notes && (
                  <div className="text-sm text-gray-700">
                    <FileText className="w-4 h-4 inline mr-2" />
                    {volunteerStep.notes}
                  </div>
                )}
                
                {(volunteerStep.signatureUrl || volunteerStep.certificateUrl) && (
                  <div className="flex gap-2 mt-2">
                    {volunteerStep.signatureUrl && (
                      <a 
                        href={volunteerStep.signatureUrl}
                        className="inline-flex items-center gap-1 text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full hover:bg-purple-200"
                        target="_blank" 
                        rel="noopener noreferrer"
                      >
                        <FileText className="w-3 h-3" />
                        Signature
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                    {volunteerStep.certificateUrl && (
                      <a 
                        href={volunteerStep.certificateUrl}
                        className="inline-flex items-center gap-1 text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full hover:bg-green-200"
                        target="_blank" 
                        rel="noopener noreferrer"
                      >
                        <Download className="w-3 h-3" />
                        Certificate
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
        
        <button
          onClick={() => setIsEditing(true)}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          Edit
        </button>
      </div>
    </div>
  );

  const renderEditMode = () => (
    <div className="p-4 rounded-lg border bg-white">
      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <h4 className="font-medium text-gray-900">{step.title}</h4>
            <p className="text-sm text-gray-600">{step.description}</p>
          </div>
          {step.required && (
            <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded-full">
              Required
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.completed}
                onChange={(e) => setFormData(prev => ({ ...prev, completed: e.target.checked }))}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm font-medium">Completed</span>
            </label>
          </div>

          {formData.completed && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Completion Date
                </label>
                <input
                  type="date"
                  value={formData.completedDate}
                  onChange={(e) => setFormData(prev => ({ ...prev, completedDate: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Completed By
                </label>
                <input
                  type="text"
                  value={formData.completedBy}
                  onChange={(e) => setFormData(prev => ({ ...prev, completedBy: e.target.value }))}
                  placeholder="Enter name or ID"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes
                </label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                  placeholder="Additional notes or comments"
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              {(step.category === 'signature' || step.category === 'training') && (
                <>
                  {step.category === 'signature' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Signature Document URL
                      </label>
                      <input
                        type="url"
                        value={formData.signatureUrl}
                        onChange={(e) => setFormData(prev => ({ ...prev, signatureUrl: e.target.value }))}
                        placeholder="https://..."
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  )}
                  
                  {step.category === 'training' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Certificate URL
                      </label>
                      <input
                        type="url"
                        value={formData.certificateUrl}
                        onChange={(e) => setFormData(prev => ({ ...prev, certificateUrl: e.target.value }))}
                        placeholder="https://..."
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  )}
                </>
              )}
            </>
          )}
        </div>

        <div className="flex justify-end gap-2 pt-4 border-t">
          <button
            onClick={handleCancel}
            className="px-4 py-2 text-sm text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-md"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );

  return isEditing ? renderEditMode() : renderViewMode();
};

export default StepTracker;