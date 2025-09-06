import React, { useState } from 'react';
import { useGoogleSheetsSync } from '../hooks/useGoogleSheetsSync.js';

const GoogleSheetsSync = ({ onDataUpdate }) => {
  const [credentials, setCredentials] = useState({
    apiKey: '',
    accessToken: ''
  });
  
  const [spreadsheetConfig, setSpreadsheetConfig] = useState({
    spreadsheetId: '',
    sheetName: 'Sheet1',
    range: 'A:Z'
  });

  const [showCredentials, setShowCredentials] = useState(false);
  const [conflictStrategy, setConflictStrategy] = useState('latest_wins');

  const {
    data,
    changes,
    conflicts,
    isLoading,
    isConnected,
    isSyncing,
    error,
    syncStatus,
    lastSync,
    connect,
    disconnect,
    startSync,
    stopSync,
    triggerSync,
    updateConfig,
    getSyncStats
  } = useGoogleSheetsSync({
    pollInterval: 30000,
    conflictStrategy: conflictStrategy,
    autoStart: true
  });

  // Update parent component when data changes
  React.useEffect(() => {
    if (data && data.length > 0 && onDataUpdate) {
      onDataUpdate(data);
    }
  }, [data, onDataUpdate]);

  const handleConnect = async () => {
    try {
      await connect(credentials, spreadsheetConfig);
    } catch (err) {
      console.error('Connection failed:', err);
    }
  };

  const handleCredentialsChange = (field, value) => {
    setCredentials(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSpreadsheetConfigChange = (field, value) => {
    setSpreadsheetConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleManualSync = async () => {
    try {
      await triggerSync();
    } catch (err) {
      console.error('Manual sync failed:', err);
    }
  };

  const formatLastSync = (timestamp) => {
    if (!timestamp) return 'Never';
    return new Date(timestamp).toLocaleString();
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'text-green-600';
      case 'stopped': return 'text-gray-600';
      case 'error': return 'text-red-600';
      case 'failed': return 'text-red-800';
      default: return 'text-gray-600';
    }
  };

  const stats = getSyncStats();

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Google Sheets Live Sync</h2>
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-400' : 'bg-gray-400'}`}></div>
          <span className="text-sm font-medium">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Connection Configuration */}
      {!isConnected && (
        <div className="space-y-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Spreadsheet ID
              </label>
              <input
                type="text"
                placeholder="Enter Google Sheets ID"
                value={spreadsheetConfig.spreadsheetId}
                onChange={(e) => handleSpreadsheetConfigChange('spreadsheetId', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sheet Name
              </label>
              <input
                type="text"
                value={spreadsheetConfig.sheetName}
                onChange={(e) => handleSpreadsheetConfigChange('sheetName', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Range (optional)
            </label>
            <input
              type="text"
              placeholder="A:Z"
              value={spreadsheetConfig.range}
              onChange={(e) => handleSpreadsheetConfigChange('range', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <button
              onClick={() => setShowCredentials(!showCredentials)}
              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              {showCredentials ? 'Hide' : 'Show'} Authentication Credentials
            </button>
          </div>

          {showCredentials && (
            <div className="space-y-3 bg-gray-50 p-4 rounded-md">
              <div className="text-sm text-gray-600 mb-2">
                Choose one authentication method:
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Google API Key (for public sheets)
                </label>
                <input
                  type="password"
                  placeholder="Enter your Google API Key"
                  value={credentials.apiKey}
                  onChange={(e) => handleCredentialsChange('apiKey', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Get your API key from Google Cloud Console → Credentials
                </p>
              </div>

              <div className="text-center text-gray-400">OR</div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  OAuth2 Access Token (for private sheets)
                </label>
                <input
                  type="password"
                  placeholder="Enter your OAuth2 access token"
                  value={credentials.accessToken}
                  onChange={(e) => handleCredentialsChange('accessToken', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Obtain token through OAuth2 flow with sheets.readonly scope
                </p>
              </div>
            </div>
          )}

          <button
            onClick={handleConnect}
            disabled={isLoading || !spreadsheetConfig.spreadsheetId || (!credentials.apiKey && !credentials.accessToken)}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Connecting...' : 'Connect to Google Sheets'}
          </button>
        </div>
      )}

      {/* Connected Status and Controls */}
      {isConnected && (
        <div className="space-y-4">
          {/* Status Bar */}
          <div className="bg-gray-50 p-4 rounded-md">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="font-medium">Status:</span>
                <span className={`ml-2 ${getStatusColor(syncStatus)}`}>
                  {syncStatus || 'idle'}
                </span>
              </div>
              <div>
                <span className="font-medium">Last Sync:</span>
                <span className="ml-2 text-gray-600">{formatLastSync(lastSync)}</span>
              </div>
              <div>
                <span className="font-medium">Records:</span>
                <span className="ml-2 text-gray-600">{data.length}</span>
              </div>
            </div>
          </div>

          {/* Controls */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={isSyncing ? stopSync : startSync}
              className={`px-4 py-2 rounded-md text-white ${
                isSyncing 
                  ? 'bg-red-600 hover:bg-red-700' 
                  : 'bg-green-600 hover:bg-green-700'
              }`}
            >
              {isSyncing ? 'Stop Sync' : 'Start Sync'}
            </button>
            
            <button
              onClick={handleManualSync}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
            >
              Manual Sync
            </button>

            <select
              value={conflictStrategy}
              onChange={(e) => {
                setConflictStrategy(e.target.value);
                updateConfig({ conflictStrategy: e.target.value });
              }}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="latest_wins">Latest Wins</option>
              <option value="remote_wins">Remote Wins</option>
              <option value="local_wins">Local Wins</option>
              <option value="merge_fields">Merge Fields</option>
              <option value="hours_sum">Sum Hours</option>
            </select>

            <button
              onClick={disconnect}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
            >
              Disconnect
            </button>
          </div>

          {/* Recent Changes */}
          {changes && changes.hasChanges && (
            <div className="bg-blue-50 p-4 rounded-md">
              <h3 className="font-medium text-blue-800 mb-2">Recent Changes</h3>
              <div className="text-sm text-blue-700">
                Added: {changes.added?.length || 0}, 
                Modified: {changes.modified?.length || 0}, 
                Deleted: {changes.deleted?.length || 0}
                {conflicts.length > 0 && (
                  <span className="text-orange-600 ml-2">
                    ({conflicts.length} conflicts resolved)
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Conflicts */}
          {conflicts.length > 0 && (
            <div className="bg-yellow-50 p-4 rounded-md">
              <h3 className="font-medium text-yellow-800 mb-2">
                Conflicts Detected ({conflicts.length})
              </h3>
              <div className="text-sm text-yellow-700">
                Conflicts have been automatically resolved using the "{conflictStrategy}" strategy.
              </div>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 p-4 rounded-md">
              <h3 className="font-medium text-red-800 mb-2">Error</h3>
              <div className="text-sm text-red-700">{error}</div>
            </div>
          )}

          {/* Statistics */}
          {stats && (
            <details className="bg-gray-50 p-4 rounded-md">
              <summary className="font-medium cursor-pointer">Sync Statistics</summary>
              <div className="mt-2 text-sm space-y-1">
                <div>Tracked Sheets: {stats.changeStats?.trackedSheets || 0}</div>
                <div>Total Conflicts: {stats.conflictStats?.totalConflicts || 0}</div>
                <div>Recent Syncs: {stats.history?.length || 0}</div>
              </div>
            </details>
          )}
        </div>
      )}
    </div>
  );
};

export default GoogleSheetsSync;