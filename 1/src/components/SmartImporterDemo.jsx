import React, { useState } from 'react';
import { SmartImporter } from '../utils/smartImporter';

export function SmartImporterDemo() {
  const [importResult, setImportResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    setError(null);
    setImportResult(null);

    try {
      const importer = new SmartImporter({
        autoMapHeaders: true,
        normalizeData: true,
        validateData: true,
        skipEmptyRows: true,
        requireMandatoryFields: false
      });

      const result = await importer.importFile(file);
      const stats = importer.getImportStats();

      setImportResult({
        ...result,
        stats
      });

    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const renderHeaderMappings = () => {
    if (!importResult?.metadata?.headerMapping) return null;

    return (
      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="font-semibold mb-2">Header Mappings</h4>
        <div className="grid grid-cols-2 gap-2 text-sm">
          {Object.entries(importResult.metadata.headerMapping).map(([original, mapped]) => (
            <div key={original} className="flex justify-between">
              <span className="text-gray-600">"{original}"</span>
              <span className="font-medium">→ {mapped}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderImportStats = () => {
    if (!importResult?.stats) return null;

    const { stats } = importResult;

    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div className="bg-blue-100 p-3 rounded-lg">
          <div className="text-2xl font-bold text-blue-800">{stats.totalRows}</div>
          <div className="text-sm text-blue-600">Total Rows</div>
        </div>
        <div className="bg-green-100 p-3 rounded-lg">
          <div className="text-2xl font-bold text-green-800">{stats.validRows}</div>
          <div className="text-sm text-green-600">Valid Rows</div>
        </div>
        <div className="bg-yellow-100 p-3 rounded-lg">
          <div className="text-2xl font-bold text-yellow-800">{stats.skippedRows}</div>
          <div className="text-sm text-yellow-600">Skipped</div>
        </div>
        <div className="bg-purple-100 p-3 rounded-lg">
          <div className="text-2xl font-bold text-purple-800">
            {Math.round(stats.confidence * 100)}%
          </div>
          <div className="text-sm text-purple-600">Confidence</div>
        </div>
      </div>
    );
  };

  const renderDataPreview = () => {
    if (!importResult?.data || importResult.data.length === 0) return null;

    const previewData = importResult.data.slice(0, 5);
    const columns = Object.keys(previewData[0]);

    return (
      <div className="bg-white border rounded-lg overflow-hidden">
        <h4 className="font-semibold p-4 bg-gray-50 border-b">Data Preview (first 5 rows)</h4>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                {columns.map(column => (
                  <th key={column} className="px-4 py-2 text-left font-medium text-gray-700">
                    {column}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {previewData.map((row, index) => (
                <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  {columns.map(column => (
                    <td key={column} className="px-4 py-2 text-gray-900">
                      {typeof row[column] === 'boolean' ? (row[column] ? 'Yes' : 'No') : String(row[column] || '')}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Smart CSV/Excel Importer Demo</h2>
        <p className="text-gray-600">
          Upload a CSV or Excel file to see automatic header detection, mapping, and data normalization in action.
        </p>
      </div>

      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Choose CSV or Excel file
        </label>
        <input
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={handleFileUpload}
          disabled={isLoading}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 disabled:opacity-50"
        />
      </div>

      {isLoading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Processing file...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          <strong>Error:</strong> {error}
        </div>
      )}

      {importResult && (
        <div className="space-y-6">
          {renderImportStats()}
          
          {renderHeaderMappings()}

          {importResult.warnings && importResult.warnings.length > 0 && (
            <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded">
              <strong>Warnings:</strong>
              <ul className="mt-2 list-disc list-inside">
                {importResult.warnings.map((warning, index) => (
                  <li key={index}>{warning}</li>
                ))}
              </ul>
            </div>
          )}

          {importResult.errors && importResult.errors.length > 0 && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              <strong>Errors:</strong>
              <ul className="mt-2 list-disc list-inside">
                {importResult.errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </div>
          )}

          {renderDataPreview()}
        </div>
      )}
    </div>
  );
}