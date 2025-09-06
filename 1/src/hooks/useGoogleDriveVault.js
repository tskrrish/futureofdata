import { useState, useEffect, useCallback } from 'react';
import { googleDriveService } from '../services/googleDriveService';

export function useGoogleDriveVault() {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const categories = [
    'Reports',
    'Volunteer_Data',
    'Branch_Analytics',
    'Member_Reports',
    'Event_Documents',
    'Training_Materials',
    'Policy_Documents',
    'Archive'
  ];

  useEffect(() => {
    const checkConnection = async () => {
      try {
        const connected = googleDriveService.isConnected();
        setIsConnected(connected);
      } catch (error) {
        console.error('Error checking connection:', error);
        setIsConnected(false);
      }
    };

    checkConnection();
  }, []);

  const connect = useCallback(async (clientId, apiKey) => {
    setIsConnecting(true);
    setError(null);
    
    try {
      const initialized = await googleDriveService.initialize(clientId, apiKey);
      if (!initialized) {
        throw new Error('Failed to initialize Google Drive service');
      }

      const authenticated = await googleDriveService.authenticate();
      if (!authenticated) {
        throw new Error('Failed to authenticate with Google Drive');
      }

      setIsConnected(true);
      await refreshDocuments();
    } catch (error) {
      console.error('Connection failed:', error);
      setError(error.message);
      setIsConnected(false);
    } finally {
      setIsConnecting(false);
    }
  }, []);

  const disconnect = useCallback(() => {
    googleDriveService.disconnect();
    setIsConnected(false);
    setDocuments([]);
    setError(null);
  }, []);

  const refreshDocuments = useCallback(async (category = null) => {
    if (!isConnected) return;

    setIsLoading(true);
    setError(null);

    try {
      const docs = await googleDriveService.listDocuments(category);
      const processedDocs = docs.map(doc => ({
        ...doc,
        metadata: doc.description ? JSON.parse(doc.description) : {},
        sizeFormatted: formatFileSize(doc.size),
        createdTimeFormatted: new Date(doc.createdTime).toLocaleDateString()
      }));
      setDocuments(processedDocs);
    } catch (error) {
      console.error('Failed to refresh documents:', error);
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  }, [isConnected]);

  const uploadDocument = useCallback(async (file, category, metadata = {}) => {
    if (!isConnected) {
      throw new Error('Not connected to Google Drive');
    }

    setError(null);

    try {
      const result = await googleDriveService.uploadDocument(file, category, metadata);
      await refreshDocuments();
      return result;
    } catch (error) {
      console.error('Upload failed:', error);
      setError(error.message);
      throw error;
    }
  }, [isConnected, refreshDocuments]);

  const downloadDocument = useCallback(async (fileId, fileName) => {
    if (!isConnected) {
      throw new Error('Not connected to Google Drive');
    }

    setError(null);

    try {
      const data = await googleDriveService.downloadDocument(fileId);
      
      const blob = new Blob([data]);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
      setError(error.message);
      throw error;
    }
  }, [isConnected]);

  const deleteDocument = useCallback(async (fileId) => {
    if (!isConnected) {
      throw new Error('Not connected to Google Drive');
    }

    setError(null);

    try {
      await googleDriveService.deleteDocument(fileId);
      await refreshDocuments();
    } catch (error) {
      console.error('Delete failed:', error);
      setError(error.message);
      throw error;
    }
  }, [isConnected, refreshDocuments]);

  const exportToGoogleSheets = useCallback(async (data, filename, category = 'Reports') => {
    if (!isConnected) {
      throw new Error('Not connected to Google Drive');
    }

    setError(null);

    try {
      const result = await googleDriveService.exportToGoogleSheets(data, filename, category);
      await refreshDocuments();
      return result;
    } catch (error) {
      console.error('Export failed:', error);
      setError(error.message);
      throw error;
    }
  }, [isConnected, refreshDocuments]);

  const exportReportToVault = useCallback(async (reportData, reportName, category = 'Reports') => {
    try {
      const result = await exportToGoogleSheets(reportData, reportName, category);
      return {
        success: true,
        fileId: result.id,
        fileName: result.name,
        webViewLink: result.webViewLink
      };
    } catch (error) {
      console.error('Export to vault failed:', error);
      throw error;
    }
  }, [exportToGoogleSheets]);

  const getStorageStats = useCallback(() => {
    const stats = {
      totalDocuments: documents.length,
      categories: {},
      totalSize: 0
    };

    documents.forEach(doc => {
      const category = doc.metadata?.category || 'Unknown';
      if (!stats.categories[category]) {
        stats.categories[category] = 0;
      }
      stats.categories[category]++;
      stats.totalSize += parseInt(doc.size || 0);
    });

    stats.totalSizeFormatted = formatFileSize(stats.totalSize);
    return stats;
  }, [documents]);

  return {
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
    exportToGoogleSheets,
    exportReportToVault,
    getStorageStats
  };
}

function formatFileSize(bytes) {
  if (!bytes) return '0 B';
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
}