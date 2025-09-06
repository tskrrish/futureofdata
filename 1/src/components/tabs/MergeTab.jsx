import React, { useState, useCallback } from 'react';
import { Upload, FileText, Download, Eye, Users, CheckCircle2, X } from 'lucide-react';
import Papa from 'papaparse';
import { exportCSV } from '../../utils/csvUtils';
import { findBestMatches } from '../../utils/fuzzyMatcher';

const FileUploadZone = ({ onFileUpload, label, fileData }) => {
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      onFileUpload(files[0]);
    }
  }, [onFileUpload]);

  const handleFileChange = useCallback((e) => {
    const file = e.target.files[0];
    if (file) {
      onFileUpload(file);
    }
  }, [onFileUpload]);

  return (
    <div
      className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors"
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
      onDragEnter={(e) => e.preventDefault()}
    >
      <input
        type="file"
        accept=".csv,.json"
        onChange={handleFileChange}
        className="hidden"
        id={`file-${label}`}
      />
      <label htmlFor={`file-${label}`} className="cursor-pointer">
        {fileData ? (
          <div className="space-y-2">
            <FileText className="w-8 h-8 mx-auto text-green-600" />
            <p className="text-sm font-medium text-green-600">{fileData.name}</p>
            <p className="text-xs text-gray-500">{fileData.records} records</p>
          </div>
        ) : (
          <div className="space-y-2">
            <Upload className="w-8 h-8 mx-auto text-gray-400" />
            <p className="text-sm text-gray-600">{label}</p>
            <p className="text-xs text-gray-400">CSV or JSON files</p>
          </div>
        )}
      </label>
    </div>
  );
};

const MatchPreview = ({ matches, onConfirmMatch, onRejectMatch }) => {
  if (!matches || matches.length === 0) return null;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
        <Eye className="w-5 h-5" />
        Match Preview ({matches.length} potential matches)
      </h3>
      
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {matches.map((match, index) => (
          <div key={index} className="border rounded-lg p-4 bg-white">
            <div className="flex justify-between items-start mb-3">
              <div className="flex-1">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <h4 className="font-medium text-blue-600">File A Record</h4>
                    <p><strong>Name:</strong> {match.recordA.name || 'N/A'}</p>
                    <p><strong>Email:</strong> {match.recordA.email || 'N/A'}</p>
                    <p><strong>Phone:</strong> {match.recordA.phone || 'N/A'}</p>
                  </div>
                  <div>
                    <h4 className="font-medium text-green-600">File B Record</h4>
                    <p><strong>Name:</strong> {match.recordB.name || 'N/A'}</p>
                    <p><strong>Email:</strong> {match.recordB.email || 'N/A'}</p>
                    <p><strong>Phone:</strong> {match.recordB.phone || 'N/A'}</p>
                  </div>
                </div>
              </div>
              
              <div className="flex flex-col items-end gap-2">
                <div className={`px-2 py-1 rounded text-xs font-medium ${
                  match.confidence > 0.8 ? 'bg-green-100 text-green-800' :
                  match.confidence > 0.6 ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {Math.round(match.confidence * 100)}% match
                </div>
                
                <div className="flex gap-2">
                  <button
                    onClick={() => onConfirmMatch(index)}
                    className="p-1 rounded bg-green-100 text-green-600 hover:bg-green-200"
                    title="Confirm match"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => onRejectMatch(index)}
                    className="p-1 rounded bg-red-100 text-red-600 hover:bg-red-200"
                    title="Reject match"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
            
            <div className="text-xs text-gray-500 space-y-1">
              {match.details.name && <p>Name similarity: {Math.round(match.details.name * 100)}%</p>}
              {match.details.email && <p>Email similarity: {Math.round(match.details.email * 100)}%</p>}
              {match.details.phone && <p>Phone similarity: {Math.round(match.details.phone * 100)}%</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export const MergeTab = () => {
  const [fileA, setFileA] = useState(null);
  const [fileB, setFileB] = useState(null);
  const [dataA, setDataA] = useState(null);
  const [dataB, setDataB] = useState(null);
  const [matches, setMatches] = useState([]);
  const [confirmedMatches, setConfirmedMatches] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [mergeResults, setMergeResults] = useState(null);

  const parseFile = useCallback((file, setData, setFileInfo) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target.result;
      
      try {
        if (file.name.endsWith('.json')) {
          const data = JSON.parse(content);
          setData(Array.isArray(data) ? data : [data]);
          setFileInfo({
            name: file.name,
            records: Array.isArray(data) ? data.length : 1
          });
        } else {
          Papa.parse(content, {
            header: true,
            skipEmptyLines: true,
            complete: (results) => {
              setData(results.data);
              setFileInfo({
                name: file.name,
                records: results.data.length
              });
            },
            error: (error) => {
              console.error('CSV parsing error:', error);
            }
          });
        }
      } catch (error) {
        console.error('File parsing error:', error);
      }
    };
    reader.readAsText(file);
  }, []);

  const handleFileAUpload = useCallback((file) => {
    parseFile(file, setDataA, setFileA);
    setMatches([]);
    setConfirmedMatches([]);
    setMergeResults(null);
  }, [parseFile]);

  const handleFileBUpload = useCallback((file) => {
    parseFile(file, setDataB, setFileB);
    setMatches([]);
    setConfirmedMatches([]);
    setMergeResults(null);
  }, [parseFile]);

  const findMatches = useCallback(async () => {
    if (!dataA || !dataB) return;
    
    setIsProcessing(true);
    
    try {
      const potentialMatches = findBestMatches(dataA, dataB, {
        threshold: 0.5,
        maxMatches: 100
      });
      
      setMatches(potentialMatches);
    } catch (error) {
      console.error('Error finding matches:', error);
    } finally {
      setIsProcessing(false);
    }
  }, [dataA, dataB]);

  const confirmMatch = useCallback((index) => {
    const match = matches[index];
    setConfirmedMatches(prev => [...prev, match]);
    setMatches(prev => prev.filter((_, i) => i !== index));
  }, [matches]);

  const rejectMatch = useCallback((index) => {
    setMatches(prev => prev.filter((_, i) => i !== index));
  }, []);

  const executeMerge = useCallback(() => {
    if (confirmedMatches.length === 0) return;

    const mergedData = [];
    const processedIndicesB = new Set();

    confirmedMatches.forEach(match => {
      const mergedRecord = {
        ...match.recordA,
        ...match.recordB,
        _merge_confidence: match.confidence,
        _merge_source: 'both'
      };
      mergedData.push(mergedRecord);
      processedIndicesB.add(match.indexB);
    });

    dataA.forEach((record, index) => {
      const isMatched = confirmedMatches.some(match => match.indexA === index);
      if (!isMatched) {
        mergedData.push({
          ...record,
          _merge_source: 'file_a'
        });
      }
    });

    dataB.forEach((record, index) => {
      if (!processedIndicesB.has(index)) {
        mergedData.push({
          ...record,
          _merge_source: 'file_b'
        });
      }
    });

    setMergeResults({
      data: mergedData,
      stats: {
        totalRecords: mergedData.length,
        mergedRecords: confirmedMatches.length,
        fileAOnly: dataA.length - confirmedMatches.length,
        fileBOnly: dataB.length - confirmedMatches.length
      }
    });
  }, [confirmedMatches, dataA, dataB]);

  const exportMergedData = useCallback(() => {
    if (!mergeResults) return;
    exportCSV('merged_data.csv', mergeResults.data);
  }, [mergeResults]);

  const canFindMatches = dataA && dataB && dataA.length > 0 && dataB.length > 0;
  const canExecuteMerge = confirmedMatches.length > 0;

  return (
    <div className="space-y-6 py-6">
      <div className="bg-white rounded-2xl p-6 shadow-sm">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
          <Users className="w-6 h-6 text-blue-600" />
          Multi-File Merge Wizard
        </h2>
        
        <p className="text-gray-600 mb-6">
          Upload two files to merge them using fuzzy matching on name, email, and phone fields. 
          Preview potential matches before confirming the merge.
        </p>

        <div className="grid md:grid-cols-2 gap-6 mb-6">
          <div>
            <h3 className="text-lg font-semibold mb-3">File A (Primary)</h3>
            <FileUploadZone 
              onFileUpload={handleFileAUpload}
              label="Upload primary file"
              fileData={fileA}
            />
          </div>
          
          <div>
            <h3 className="text-lg font-semibold mb-3">File B (Secondary)</h3>
            <FileUploadZone 
              onFileUpload={handleFileBUpload}
              label="Upload secondary file"
              fileData={fileB}
            />
          </div>
        </div>

        <div className="flex gap-4 flex-wrap">
          <button
            onClick={findMatches}
            disabled={!canFindMatches || isProcessing}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Eye className="w-4 h-4" />
            {isProcessing ? 'Finding Matches...' : 'Find Matches'}
          </button>
          
          <button
            onClick={executeMerge}
            disabled={!canExecuteMerge}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Users className="w-4 h-4" />
            Execute Merge ({confirmedMatches.length} matches)
          </button>

          {mergeResults && (
            <button
              onClick={exportMergedData}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Export Merged Data
            </button>
          )}
        </div>
      </div>

      {matches.length > 0 && (
        <div className="bg-white rounded-2xl p-6 shadow-sm">
          <MatchPreview 
            matches={matches}
            onConfirmMatch={confirmMatch}
            onRejectMatch={rejectMatch}
          />
        </div>
      )}

      {confirmedMatches.length > 0 && (
        <div className="bg-white rounded-2xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-green-600" />
            Confirmed Matches ({confirmedMatches.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {confirmedMatches.map((match, index) => (
              <div key={index} className="border rounded-lg p-3 bg-green-50">
                <div className="text-sm">
                  <p className="font-medium">{match.recordA.name || 'N/A'}</p>
                  <p className="text-gray-600">{match.recordA.email || match.recordB.email || 'N/A'}</p>
                  <div className="mt-2">
                    <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                      {Math.round(match.confidence * 100)}% confidence
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {mergeResults && (
        <div className="bg-white rounded-2xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-green-600" />
            Merge Results
          </h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{mergeResults.stats.totalRecords}</div>
              <div className="text-sm text-gray-600">Total Records</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{mergeResults.stats.mergedRecords}</div>
              <div className="text-sm text-gray-600">Merged Records</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{mergeResults.stats.fileAOnly}</div>
              <div className="text-sm text-gray-600">File A Only</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{mergeResults.stats.fileBOnly}</div>
              <div className="text-sm text-gray-600">File B Only</div>
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium mb-2">Sample of merged data:</h4>
            <div className="text-sm space-y-1 max-h-40 overflow-y-auto">
              {mergeResults.data.slice(0, 5).map((record, index) => (
                <div key={index} className="flex justify-between">
                  <span>{record.name || 'N/A'}</span>
                  <span className={`px-2 py-1 rounded text-xs ${
                    record._merge_source === 'both' ? 'bg-green-100 text-green-800' :
                    record._merge_source === 'file_a' ? 'bg-blue-100 text-blue-800' :
                    'bg-purple-100 text-purple-800'
                  }`}>
                    {record._merge_source}
                  </span>
                </div>
              ))}
              {mergeResults.data.length > 5 && (
                <div className="text-gray-500 text-center">
                  ... and {mergeResults.data.length - 5} more records
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};