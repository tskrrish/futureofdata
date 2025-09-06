import { useState, useEffect, useRef, useCallback } from 'react';
import { LiveSyncService } from '../services/liveSyncService.js';

export function useGoogleSheetsSync(config = {}) {
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [error, setError] = useState(null);
  const [syncStatus, setSyncStatus] = useState(null);
  const [lastSync, setLastSync] = useState(null);
  const [changes, setChanges] = useState(null);
  const [conflicts, setConflicts] = useState([]);
  
  const syncServiceRef = useRef(null);
  const unsubscribeRefs = useRef([]);

  const defaultConfig = {
    pollInterval: 30000,
    maxRetries: 3,
    conflictStrategy: 'latest_wins',
    enableWebhooks: false,
    autoStart: false
  };

  const finalConfig = { ...defaultConfig, ...config };

  // Initialize sync service
  useEffect(() => {
    if (!syncServiceRef.current) {
      syncServiceRef.current = new LiveSyncService(finalConfig);
      setupEventListeners();
    }

    return () => {
      cleanup();
    };
  }, []);

  const setupEventListeners = useCallback(() => {
    if (!syncServiceRef.current) return;

    const service = syncServiceRef.current;

    // Subscribe to sync events
    const unsubscribes = [
      service.subscribe('initial_sync', (eventData) => {
        setData(eventData.data);
        setLastSync(eventData.timestamp);
        setIsLoading(false);
      }),

      service.subscribe('data_changed', (eventData) => {
        if (eventData.resolved) {
          const resolvedData = eventData.resolved.map(item => item.resolved.data);
          setData(resolvedData);
        } else {
          // Handle simple changes without conflicts
          const updatedData = [...data];
          
          // Apply changes
          eventData.added.forEach(change => {
            updatedData.push(change.data);
          });
          
          eventData.modified.forEach(change => {
            const index = updatedData.findIndex(item => 
              item.assignee === change.data.assignee && 
              item.date === change.data.date
            );
            if (index !== -1) {
              updatedData[index] = change.data;
            }
          });
          
          eventData.deleted.forEach(change => {
            const index = updatedData.findIndex(item => 
              item.assignee === change.data.assignee && 
              item.date === change.data.date
            );
            if (index !== -1) {
              updatedData.splice(index, 1);
            }
          });
          
          setData(updatedData);
        }
        
        setChanges(eventData);
        setConflicts(eventData.conflicts || []);
        setLastSync(eventData.metadata?.timestamp || new Date().toISOString());
      }),

      service.subscribe('sync_started', () => {
        setIsSyncing(true);
        setSyncStatus('running');
        setError(null);
      }),

      service.subscribe('sync_stopped', () => {
        setIsSyncing(false);
        setSyncStatus('stopped');
      }),

      service.subscribe('sync_error', (eventData) => {
        setError(eventData.error);
        setSyncStatus('error');
      }),

      service.subscribe('sync_failed', (eventData) => {
        setError(eventData.error);
        setSyncStatus('failed');
        setIsSyncing(false);
      })
    ];

    unsubscribeRefs.current = unsubscribes;
  }, [data]);

  const cleanup = useCallback(() => {
    if (unsubscribeRefs.current) {
      unsubscribeRefs.current.forEach(unsubscribe => unsubscribe());
      unsubscribeRefs.current = [];
    }
    if (syncServiceRef.current) {
      syncServiceRef.current.destroy();
      syncServiceRef.current = null;
    }
  }, []);

  // Initialize connection to Google Sheets
  const connect = useCallback(async (credentials, spreadsheetConfig) => {
    if (!syncServiceRef.current) {
      throw new Error('Sync service not initialized');
    }

    setIsLoading(true);
    setError(null);

    try {
      await syncServiceRef.current.initialize(credentials, spreadsheetConfig);
      setIsConnected(true);
      
      if (finalConfig.autoStart) {
        syncServiceRef.current.startSync();
      }
      
    } catch (err) {
      setError(err.message);
      setIsConnected(false);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [finalConfig.autoStart]);

  // Start syncing
  const startSync = useCallback(() => {
    if (!syncServiceRef.current || !isConnected) {
      throw new Error('Not connected to Google Sheets');
    }
    syncServiceRef.current.startSync();
  }, [isConnected]);

  // Stop syncing
  const stopSync = useCallback(() => {
    if (!syncServiceRef.current) return;
    syncServiceRef.current.stopSync();
  }, []);

  // Manual sync trigger
  const triggerSync = useCallback(async () => {
    if (!syncServiceRef.current || !isConnected) {
      throw new Error('Not connected to Google Sheets');
    }
    
    setIsLoading(true);
    try {
      const result = await syncServiceRef.current.triggerSync();
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [isConnected]);

  // Update configuration
  const updateConfig = useCallback((newConfig) => {
    if (!syncServiceRef.current) return;
    syncServiceRef.current.updateConfig(newConfig);
  }, []);

  // Update spreadsheet configuration
  const updateSpreadsheet = useCallback((spreadsheetConfig) => {
    if (!syncServiceRef.current) return;
    syncServiceRef.current.updateSpreadsheetConfig(spreadsheetConfig);
  }, []);

  // Get sync statistics
  const getSyncStats = useCallback(() => {
    if (!syncServiceRef.current) return null;
    
    return {
      status: syncServiceRef.current.getStatus(),
      history: syncServiceRef.current.getSyncHistory(),
      changeStats: syncServiceRef.current.getChangeDetectorStats(),
      conflictStats: syncServiceRef.current.getConflictStats()
    };
  }, []);

  // Resolve conflicts manually
  const resolveConflicts = useCallback((resolutions) => {
    // This would allow manual conflict resolution
    // Implementation depends on specific requirements
    setConflicts([]);
  }, []);

  // Disconnect
  const disconnect = useCallback(() => {
    stopSync();
    setIsConnected(false);
    setData([]);
    setChanges(null);
    setConflicts([]);
    setLastSync(null);
    setSyncStatus(null);
  }, [stopSync]);

  return {
    // Data
    data,
    changes,
    conflicts,
    
    // Status
    isLoading,
    isConnected,
    isSyncing,
    error,
    syncStatus,
    lastSync,
    
    // Actions
    connect,
    disconnect,
    startSync,
    stopSync,
    triggerSync,
    updateConfig,
    updateSpreadsheet,
    resolveConflicts,
    
    // Utilities
    getSyncStats
  };
}