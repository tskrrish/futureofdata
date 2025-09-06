import React, { useState, useCallback } from 'react';
import { RefreshCw, Download, CheckCircle, AlertCircle, Clock, Settings } from 'lucide-react';
import { useOfflineAttendance } from '../../hooks/useOfflineAttendance';

export const SyncManager = ({ isOpen, onClose }) => {
  const [syncConfig, setSyncConfig] = useState({
    serverUrl: 'https://api.ymca.org/attendance',
    apiKey: '',
    autoSyncInterval: 300000, // 5 minutes
    batchSize: 50
  });
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncResults, setSyncResults] = useState(null);

  const {
    offlineEntries,
    syncToServer,
    clearSyncedEntries,
    exportOfflineData,
    stats
  } = useOfflineAttendance();

  const handleManualSync = useCallback(async () => {
    if (!syncConfig.serverUrl || !syncConfig.apiKey) {
      alert('Please configure server URL and API key first');
      return;
    }

    setIsSyncing(true);
    setSyncResults(null);

    try {
      const result = await syncToServer(syncConfig.serverUrl, syncConfig.apiKey);
      setSyncResults({
        success: true,
        synced: result.synced,
        errors: result.errors,
        timestamp: new Date()
      });
    } catch (error) {
      setSyncResults({
        success: false,
        error: error.message,
        timestamp: new Date()
      });
    } finally {
      setIsSyncing(false);
    }
  }, [syncConfig, syncToServer]);

  const handleClearSynced = useCallback(() => {
    if (window.confirm('Clear all successfully synced entries? This cannot be undone.')) {
      clearSyncedEntries();
    }
  }, [clearSyncedEntries]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'text-orange-600';
      case 'synced': return 'text-green-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending': return <Clock className="w-4 h-4" />;
      case 'synced': return <CheckCircle className="w-4 h-4" />;
      case 'error': return <AlertCircle className="w-4 h-4" />;
      default: return null;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-xl font-semibold">Data Sync Manager</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl"
          >
            ×
          </button>
        </div>

        <div className="p-4 max-h-[80vh] overflow-y-auto">
          {/* Sync Configuration */}
          <div className="mb-6">
            <h3 className="text-lg font-medium mb-3 flex items-center">
              <Settings className="w-5 h-5 mr-2" />
              Sync Configuration
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Server URL
                </label>
                <input
                  type="url"
                  value={syncConfig.serverUrl}
                  onChange={(e) => setSyncConfig(prev => ({ ...prev, serverUrl: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="https://api.ymca.org/attendance"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API Key
                </label>
                <input
                  type="password"
                  value={syncConfig.apiKey}
                  onChange={(e) => setSyncConfig(prev => ({ ...prev, apiKey: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="Enter API key"
                />
              </div>
            </div>
          </div>

          {/* Sync Controls */}
          <div className="mb-6">
            <h3 className="text-lg font-medium mb-3">Sync Actions</h3>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={handleManualSync}
                disabled={isSyncing || stats.pending === 0}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white 
                         rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin' : ''}`} />
                <span>{isSyncing ? 'Syncing...' : 'Sync Now'}</span>
              </button>
              
              <button
                onClick={exportOfflineData}
                className="flex items-center space-x-2 px-4 py-2 bg-green-500 text-white 
                         rounded-md hover:bg-green-600"
              >
                <Download className="w-4 h-4" />
                <span>Export Data</span>
              </button>
              
              <button
                onClick={handleClearSynced}
                disabled={stats.synced === 0}
                className="flex items-center space-x-2 px-4 py-2 bg-gray-500 text-white 
                         rounded-md hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span>Clear Synced ({stats.synced})</span>
              </button>
            </div>
          </div>

          {/* Sync Results */}
          {syncResults && (
            <div className={`mb-6 p-4 rounded-lg ${
              syncResults.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
            } border`}>
              <h4 className="font-medium mb-2">
                {syncResults.success ? 'Sync Completed' : 'Sync Failed'}
              </h4>
              {syncResults.success ? (
                <p className="text-sm text-green-700">
                  Successfully synced {syncResults.synced} entries
                  {syncResults.errors > 0 && ` (${syncResults.errors} errors)`}
                </p>
              ) : (
                <p className="text-sm text-red-700">{syncResults.error}</p>
              )}
              <p className="text-xs text-gray-500 mt-1">
                {syncResults.timestamp.toLocaleString()}
              </p>
            </div>
          )}

          {/* Statistics */}
          <div className="mb-6">
            <h3 className="text-lg font-medium mb-3">Statistics</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 p-3 rounded-lg text-center">
                <div className="text-2xl font-bold text-gray-800">{stats.total}</div>
                <div className="text-sm text-gray-600">Total Entries</div>
              </div>
              <div className="bg-orange-50 p-3 rounded-lg text-center">
                <div className="text-2xl font-bold text-orange-600">{stats.pending}</div>
                <div className="text-sm text-gray-600">Pending Sync</div>
              </div>
              <div className="bg-green-50 p-3 rounded-lg text-center">
                <div className="text-2xl font-bold text-green-600">{stats.synced}</div>
                <div className="text-sm text-gray-600">Synced</div>
              </div>
              <div className="bg-red-50 p-3 rounded-lg text-center">
                <div className="text-2xl font-bold text-red-600">{stats.errors}</div>
                <div className="text-sm text-gray-600">Errors</div>
              </div>
            </div>
          </div>

          {/* Offline Entries List */}
          <div>
            <h3 className="text-lg font-medium mb-3">Offline Entries ({offlineEntries.length})</h3>
            {offlineEntries.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No offline entries</p>
            ) : (
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <div className="max-h-60 overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 sticky top-0">
                      <tr>
                        <th className="px-3 py-2 text-left">Time</th>
                        <th className="px-3 py-2 text-left">Type</th>
                        <th className="px-3 py-2 text-left">Identifier</th>
                        <th className="px-3 py-2 text-left">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {offlineEntries.map((entry) => (
                        <tr key={entry.id}>
                          <td className="px-3 py-2 text-gray-600">
                            {new Date(entry.timestamp).toLocaleString()}
                          </td>
                          <td className="px-3 py-2">
                            <span className="inline-flex px-2 py-1 bg-gray-100 text-gray-700 
                                           rounded text-xs font-medium">
                              {entry.type.toUpperCase()}
                            </span>
                          </td>
                          <td className="px-3 py-2 font-mono text-gray-800">
                            {entry.volunteerName || entry.identifier}
                          </td>
                          <td className="px-3 py-2">
                            <div className={`flex items-center space-x-1 ${getStatusColor(entry.status)}`}>
                              {getStatusIcon(entry.status)}
                              <span className="capitalize">{entry.status}</span>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};