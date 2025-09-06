import React, { useState, useEffect } from 'react';
import { 
  Cloud, 
  Upload, 
  Download, 
  Trash2, 
  FileText, 
  FolderOpen, 
  Settings, 
  RefreshCw,
  AlertCircle,
  CheckCircle,
  ExternalLink
} from 'lucide-react';
import { useGoogleDriveVault } from '../../hooks/useGoogleDriveVault';

export function GoogleDriveVault({ onExportToVault }) {
  const {
    isConnected,
    isConnecting,
    documents,
    isLoading,
    error,
    categories,
    connect,
    disconnect,
    refreshDocuments,
    uploadDocument,
    downloadDocument,
    deleteDocument,
    exportReportToVault,
    getStorageStats
  } = useGoogleDriveVault();

  const [selectedCategory, setSelectedCategory] = useState('');
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadCategory, setUploadCategory] = useState('Reports');
  const [showSettings, setShowSettings] = useState(false);
  const [clientId, setClientId] = useState(localStorage.getItem('gdrive_client_id') || '');
  const [apiKey, setApiKey] = useState(localStorage.getItem('gdrive_api_key') || '');

  const stats = getStorageStats();

  useEffect(() => {
    if (onExportToVault) {
      onExportToVault(exportReportToVault);
    }
  }, [onExportToVault, exportReportToVault]);

  const handleConnect = async () => {
    if (!clientId || !apiKey) {
      alert('Please enter Google Drive Client ID and API Key in settings');
      setShowSettings(true);
      return;
    }

    localStorage.setItem('gdrive_client_id', clientId);
    localStorage.setItem('gdrive_api_key', apiKey);
    await connect(clientId, apiKey);
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const metadata = {
        uploadedBy: 'YMCA Dashboard',
        category: uploadCategory,
        originalSize: file.size
      };

      await uploadDocument(file, uploadCategory, metadata);
      setUploadFile(null);
      e.target.value = '';
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  const handleDownload = async (fileId, fileName) => {
    try {
      await downloadDocument(fileId, fileName);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const handleDelete = async (fileId, fileName) => {
    if (confirm(`Are you sure you want to delete "${fileName}"?`)) {
      try {
        await deleteDocument(fileId);
      } catch (error) {
        console.error('Delete failed:', error);
      }
    }
  };

  const filteredDocuments = selectedCategory 
    ? documents.filter(doc => doc.metadata?.category === selectedCategory)
    : documents;

  if (showSettings) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-3 mb-6">
          <Settings className="w-6 h-6 text-blue-600" />
          <h3 className="text-lg font-semibold">Google Drive Settings</h3>
        </div>

        <div className="space-y-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Google Drive Client ID
            </label>
            <input
              type="text"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              placeholder="Your Google Drive Client ID"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Google Drive API Key
            </label>
            <input
              type="text"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Your Google Drive API Key"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="bg-blue-50 p-4 rounded-md">
            <h4 className="font-medium text-blue-800 mb-2">Setup Instructions:</h4>
            <ol className="text-sm text-blue-700 space-y-1">
              <li>1. Go to Google Cloud Console</li>
              <li>2. Create a new project or select existing</li>
              <li>3. Enable Google Drive API</li>
              <li>4. Create credentials (API Key and OAuth 2.0 Client ID)</li>
              <li>5. Add your domain to authorized origins</li>
            </ol>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => setShowSettings(false)}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            Cancel
          </button>
          <button
            onClick={() => {
              setShowSettings(false);
              if (clientId && apiKey) {
                handleConnect();
              }
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Save & Connect
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Cloud className="w-6 h-6 text-blue-600" />
            <h3 className="text-lg font-semibold">Google Drive File Vault</h3>
            {isConnected && (
              <CheckCircle className="w-5 h-5 text-green-600" />
            )}
          </div>

          <div className="flex items-center gap-2">
            {!isConnected ? (
              <>
                <button
                  onClick={() => setShowSettings(true)}
                  className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
                >
                  <Settings className="w-4 h-4" />
                </button>
                <button
                  onClick={handleConnect}
                  disabled={isConnecting}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {isConnecting ? 'Connecting...' : 'Connect Drive'}
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => refreshDocuments(selectedCategory)}
                  disabled={isLoading}
                  className="px-3 py-1 text-gray-600 hover:text-gray-800"
                >
                  <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                </button>
                <button
                  onClick={disconnect}
                  className="px-3 py-1 text-red-600 hover:text-red-800"
                >
                  Disconnect
                </button>
              </>
            )}
          </div>
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-50 rounded-md flex items-center gap-2 text-red-700">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">{error}</span>
          </div>
        )}
      </div>

      {isConnected && (
        <div className="p-6">
          {/* Storage Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Total Documents</div>
              <div className="text-2xl font-bold text-gray-900">{stats.totalDocuments}</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Categories</div>
              <div className="text-2xl font-bold text-gray-900">{Object.keys(stats.categories).length}</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Total Storage</div>
              <div className="text-2xl font-bold text-gray-900">{stats.totalSizeFormatted}</div>
            </div>
          </div>

          {/* Upload Section */}
          <div className="mb-6">
            <h4 className="font-medium mb-3">Upload Document</h4>
            <div className="flex gap-4 items-end">
              <div className="flex-1">
                <label className="block text-sm text-gray-600 mb-1">Category</label>
                <select
                  value={uploadCategory}
                  onChange={(e) => setUploadCategory(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {categories.map(category => (
                    <option key={category} value={category}>
                      {category.replace('_', ' ')}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex-1">
                <label className="block text-sm text-gray-600 mb-1">File</label>
                <input
                  type="file"
                  onChange={handleFileUpload}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Filter Section */}
          <div className="mb-4">
            <label className="block text-sm text-gray-600 mb-2">Filter by Category</label>
            <select
              value={selectedCategory}
              onChange={(e) => {
                setSelectedCategory(e.target.value);
                refreshDocuments(e.target.value || null);
              }}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Categories</option>
              {categories.map(category => (
                <option key={category} value={category}>
                  {category.replace('_', ' ')}
                </option>
              ))}
            </select>
          </div>

          {/* Documents List */}
          <div className="space-y-2">
            {isLoading && (
              <div className="text-center py-8 text-gray-500">
                <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
                Loading documents...
              </div>
            )}

            {!isLoading && filteredDocuments.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <FolderOpen className="w-12 h-12 mx-auto mb-4 opacity-50" />
                No documents found
              </div>
            )}

            {!isLoading && filteredDocuments.map((doc) => (
              <div key={doc.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <FileText className="w-5 h-5 text-blue-600 flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <div className="font-medium text-gray-900 truncate">{doc.name}</div>
                      <div className="text-sm text-gray-500 flex items-center gap-4">
                        <span>{doc.sizeFormatted}</span>
                        <span>{doc.createdTimeFormatted}</span>
                        {doc.metadata?.category && (
                          <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                            {doc.metadata.category.replace('_', ' ')}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {doc.mimeType === 'application/vnd.google-apps.spreadsheet' && (
                      <button
                        onClick={() => window.open(`https://docs.google.com/spreadsheets/d/${doc.id}`, '_blank')}
                        className="p-1 text-gray-500 hover:text-blue-600"
                        title="Open in Google Sheets"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => handleDownload(doc.id, doc.name)}
                      className="p-1 text-gray-500 hover:text-green-600"
                      title="Download"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(doc.id, doc.name)}
                      className="p-1 text-gray-500 hover:text-red-600"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}