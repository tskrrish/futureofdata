import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'kiosk_offline_attendance';
const SYNC_STATUS_KEY = 'kiosk_sync_status';

export const useOfflineAttendance = () => {
  const [offlineEntries, setOfflineEntries] = useState([]);
  const [syncStatus, setSyncStatus] = useState('idle'); // idle, syncing, success, error
  const [lastSyncTime, setLastSyncTime] = useState(null);

  // Load offline entries from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        setOfflineEntries(Array.isArray(parsed) ? parsed : []);
      }

      const syncData = localStorage.getItem(SYNC_STATUS_KEY);
      if (syncData) {
        const { lastSync } = JSON.parse(syncData);
        setLastSyncTime(lastSync ? new Date(lastSync) : null);
      }
    } catch (error) {
      console.error('Error loading offline attendance data:', error);
    }
  }, []);

  // Save entries to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(offlineEntries));
    } catch (error) {
      console.error('Error saving offline attendance data:', error);
    }
  }, [offlineEntries]);

  const addAttendanceEntry = useCallback((data) => {
    const entry = {
      id: crypto.randomUUID(),
      timestamp: new Date().toISOString(),
      type: data.type, // 'qr', 'pin', 'nfc'
      identifier: data.identifier, // QR data, PIN, or NFC serial
      volunteerId: data.volunteerId || null,
      volunteerName: data.volunteerName || null,
      branch: data.branch || 'Unknown',
      status: 'pending', // pending, synced, error
      checkInTime: new Date().toISOString(),
      deviceInfo: {
        userAgent: navigator.userAgent,
        timestamp: Date.now(),
        online: navigator.onLine
      }
    };

    setOfflineEntries(prev => [entry, ...prev]);
    return entry;
  }, []);

  const removeEntry = useCallback((entryId) => {
    setOfflineEntries(prev => prev.filter(entry => entry.id !== entryId));
  }, []);

  const markEntrySynced = useCallback((entryId) => {
    setOfflineEntries(prev => prev.map(entry => 
      entry.id === entryId ? { ...entry, status: 'synced' } : entry
    ));
  }, []);

  const markEntryError = useCallback((entryId, error) => {
    setOfflineEntries(prev => prev.map(entry => 
      entry.id === entryId ? { ...entry, status: 'error', syncError: error } : entry
    ));
  }, []);

  const getPendingEntries = useCallback(() => {
    return offlineEntries.filter(entry => entry.status === 'pending');
  }, [offlineEntries]);

  const getSyncedEntries = useCallback(() => {
    return offlineEntries.filter(entry => entry.status === 'synced');
  }, [offlineEntries]);

  const getErrorEntries = useCallback(() => {
    return offlineEntries.filter(entry => entry.status === 'error');
  }, [offlineEntries]);

  const clearSyncedEntries = useCallback(() => {
    setOfflineEntries(prev => prev.filter(entry => entry.status !== 'synced'));
  }, []);

  const syncToServer = useCallback(async (serverEndpoint, apiKey) => {
    if (!navigator.onLine) {
      throw new Error('Device is offline');
    }

    const pendingEntries = getPendingEntries();
    if (pendingEntries.length === 0) {
      return { synced: 0, errors: 0 };
    }

    setSyncStatus('syncing');
    let syncedCount = 0;
    let errorCount = 0;

    try {
      for (const entry of pendingEntries) {
        try {
          const response = await fetch(serverEndpoint, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${apiKey}`,
            },
            body: JSON.stringify(entry),
          });

          if (response.ok) {
            markEntrySynced(entry.id);
            syncedCount++;
          } else {
            const errorText = await response.text();
            markEntryError(entry.id, `HTTP ${response.status}: ${errorText}`);
            errorCount++;
          }
        } catch (error) {
          markEntryError(entry.id, error.message);
          errorCount++;
        }
      }

      const now = new Date();
      setLastSyncTime(now);
      localStorage.setItem(SYNC_STATUS_KEY, JSON.stringify({
        lastSync: now.toISOString(),
        syncedCount,
        errorCount
      }));

      setSyncStatus(errorCount === 0 ? 'success' : 'error');
      return { synced: syncedCount, errors: errorCount };

    } catch (error) {
      setSyncStatus('error');
      throw error;
    }
  }, [getPendingEntries, markEntrySynced, markEntryError]);

  const exportOfflineData = useCallback(() => {
    const data = {
      entries: offlineEntries,
      exportTime: new Date().toISOString(),
      totalEntries: offlineEntries.length,
      pendingEntries: getPendingEntries().length,
      syncedEntries: getSyncedEntries().length,
      errorEntries: getErrorEntries().length,
      lastSyncTime: lastSyncTime?.toISOString() || null
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `kiosk-attendance-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [offlineEntries, getPendingEntries, getSyncedEntries, getErrorEntries, lastSyncTime]);

  return {
    offlineEntries,
    addAttendanceEntry,
    removeEntry,
    markEntrySynced,
    markEntryError,
    getPendingEntries,
    getSyncedEntries,
    getErrorEntries,
    clearSyncedEntries,
    syncToServer,
    exportOfflineData,
    syncStatus,
    lastSyncTime,
    stats: {
      total: offlineEntries.length,
      pending: getPendingEntries().length,
      synced: getSyncedEntries().length,
      errors: getErrorEntries().length,
    }
  };
};