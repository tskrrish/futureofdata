import React, { useState } from 'react';
import { FileText, Download, Copy } from 'lucide-react';
import { getTemplateOptions, getTemplateById } from '../../data/grantTemplates';
import { prefillTemplateData, exportTemplateAsText, exportTemplateAsCSV } from '../../utils/grantUtils';

export function GrantReportingTab({ volunteerData }) {
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [formValues, setFormValues] = useState({});
  const [prefilledTemplate, setPrefilledTemplate] = useState(null);

  const handleTemplateChange = (templateId) => {
    setSelectedTemplate(templateId);
    if (templateId) {
      const template = getTemplateById(templateId);
      const prefilled = prefillTemplateData(template, volunteerData);
      setPrefilledTemplate(prefilled);
      
      // Initialize form values with prefilled data
      const initialValues = {};
      prefilled.fields.forEach(field => {
        initialValues[field.id] = field.value;
      });
      setFormValues(initialValues);
    } else {
      setPrefilledTemplate(null);
      setFormValues({});
    }
  };

  const handleFieldChange = (fieldId, value) => {
    setFormValues(prev => ({
      ...prev,
      [fieldId]: value
    }));
  };

  const handleExportText = () => {
    if (prefilledTemplate) {
      const textContent = exportTemplateAsText(prefilledTemplate, formValues);
      const blob = new Blob([textContent], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${prefilledTemplate.name.replace(/\s+/g, '_').toLowerCase()}_report.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  const handleExportCSV = () => {
    if (prefilledTemplate) {
      const csvContent = exportTemplateAsCSV(prefilledTemplate, formValues);
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${prefilledTemplate.name.replace(/\s+/g, '_').toLowerCase()}_report.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  const handleCopyToClipboard = () => {
    if (prefilledTemplate) {
      const textContent = exportTemplateAsText(prefilledTemplate, formValues);
      navigator.clipboard.writeText(textContent).then(() => {
        alert('Report copied to clipboard!');
      });
    }
  };

  const templateOptions = getTemplateOptions();

  return (
    <div className="space-y-6 mt-6">
      <div className="bg-white rounded-2xl border p-6">
        <div className="flex items-center gap-3 mb-6">
          <FileText className="w-6 h-6 text-blue-600" />
          <div>
            <h2 className="text-xl font-semibold">Grant Reporting Templates</h2>
            <p className="text-sm text-neutral-600">
              Generate pre-filled grant reports using your volunteer data
            </p>
          </div>
        </div>

        {/* Template Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-neutral-700 mb-2">
            Select Grant Template
          </label>
          <select
            value={selectedTemplate}
            onChange={(e) => handleTemplateChange(e.target.value)}
            className="w-full p-3 border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Choose a template...</option>
            {templateOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label} - {option.description}
              </option>
            ))}
          </select>
        </div>

        {/* Template Form */}
        {prefilledTemplate && (
          <div className="space-y-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 mb-2">
                {prefilledTemplate.name}
              </h3>
              <p className="text-sm text-blue-700">
                {prefilledTemplate.description}
              </p>
            </div>

            {/* Export Actions */}
            <div className="flex flex-wrap gap-3">
              <button
                onClick={handleExportText}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                <Download className="w-4 h-4" />
                Export as Text
              </button>
              <button
                onClick={handleExportCSV}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Download className="w-4 h-4" />
                Export as CSV
              </button>
              <button
                onClick={handleCopyToClipboard}
                className="flex items-center gap-2 px-4 py-2 bg-neutral-600 text-white rounded-lg hover:bg-neutral-700 transition-colors"
              >
                <Copy className="w-4 h-4" />
                Copy to Clipboard
              </button>
            </div>

            {/* Form Fields */}
            <div className="space-y-4">
              <h4 className="font-medium text-neutral-900">Report Fields</h4>
              {prefilledTemplate.fields.map(field => (
                <div key={field.id} className="space-y-2">
                  <label className="block text-sm font-medium text-neutral-700">
                    {field.label}
                    {field.required && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  
                  {field.type === 'textarea' ? (
                    <textarea
                      value={formValues[field.id] || ''}
                      onChange={(e) => handleFieldChange(field.id, e.target.value)}
                      rows={4}
                      className="w-full p-3 border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required={field.required}
                    />
                  ) : (
                    <input
                      type={field.type}
                      value={formValues[field.id] || ''}
                      onChange={(e) => handleFieldChange(field.id, e.target.value)}
                      className="w-full p-3 border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required={field.required}
                    />
                  )}
                  
                  {field.prefill && field.prefill.startsWith('auto:') && (
                    <p className="text-xs text-green-600">
                      ✓ Auto-filled from volunteer data
                    </p>
                  )}
                </div>
              ))}
            </div>

            {/* Data Summary */}
            <div className="bg-neutral-50 rounded-lg p-4">
              <h4 className="font-medium text-neutral-900 mb-3">
                Current Volunteer Data Summary
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-neutral-600">Total Volunteers:</span>
                  <div className="font-medium">{volunteerData.activeVolunteersCount}</div>
                </div>
                <div>
                  <span className="text-neutral-600">Total Hours:</span>
                  <div className="font-medium">{volunteerData.totalHours.toFixed(1)}</div>
                </div>
                <div>
                  <span className="text-neutral-600">Member Volunteers:</span>
                  <div className="font-medium">{volunteerData.memberVolunteersCount}</div>
                </div>
                <div>
                  <span className="text-neutral-600">Locations Served:</span>
                  <div className="font-medium">{volunteerData.hoursByBranch.length}</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {!selectedTemplate && (
          <div className="text-center py-8 text-neutral-500">
            <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>Select a grant template to begin generating your report</p>
          </div>
        )}
      </div>
    </div>
  );
}