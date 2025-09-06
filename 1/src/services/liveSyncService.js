import GoogleSheetsClient from './googleSheetsClient.js';
import { ChangeDetector } from './changeDetector.js';
import { ConflictResolver } from './conflictResolver.js';

export class LiveSyncService {
  constructor(options = {}) {
    this.client = new GoogleSheetsClient();
    this.changeDetector = new ChangeDetector();
    this.conflictResolver = new ConflictResolver(options.conflictResolution);
    
    this.config = {
      pollInterval: options.pollInterval || 30000, // 30 seconds default
      maxRetries: options.maxRetries || 3,
      backoffMultiplier: options.backoffMultiplier || 2,
      enableWebhooks: options.enableWebhooks || false,
      ...options
    };
    
    this.isRunning = false;
    this.intervalId = null;
    this.subscribers = new Map();
    this.syncHistory = [];
    this.errorCount = 0;
    this.lastError = null;
    
    // Bind methods
    this.handleSync = this.handleSync.bind(this);
  }

  async initialize(credentials, spreadsheetConfig) {
    try {
      const success = await this.client.authenticate(credentials);
      if (!success) {
        throw new Error('Authentication failed');
      }

      this.spreadsheetConfig = spreadsheetConfig;
      
      // Initial data load
      if (spreadsheetConfig.spreadsheetId) {
        await this.performInitialSync();
      }

      return true;
    } catch (error) {
      console.error('LiveSync initialization failed:', error);
      this.lastError = error;
      throw error;
    }
  }

  async performInitialSync() {
    try {
      const { spreadsheetId, range, sheetName } = this.spreadsheetConfig;
      const actualRange = range || `${sheetName || 'Sheet1'}!A:Z`;
      
      const { headers, data } = await this.client.getSpreadsheetData(spreadsheetId, actualRange);
      const transformedData = this.client.transformToVolunteerData(headers, data);
      
      // Initialize change detector with initial data
      this.changeDetector.initializeData(spreadsheetId, transformedData);
      
      // Notify subscribers of initial data
      this.notifySubscribers('initial_sync', {
        data: transformedData,
        timestamp: new Date().toISOString(),
        source: 'sheets'
      });

      this.addToSyncHistory({
        type: 'initial_sync',
        success: true,
        rowCount: transformedData.length,
        timestamp: new Date().toISOString()
      });

      return transformedData;
    } catch (error) {
      console.error('Initial sync failed:', error);
      this.addToSyncHistory({
        type: 'initial_sync',
        success: false,
        error: error.message,
        timestamp: new Date().toISOString()
      });
      throw error;
    }
  }

  startSync() {
    if (this.isRunning) {
      console.warn('Sync is already running');
      return;
    }

    this.isRunning = true;
    this.errorCount = 0;
    this.intervalId = setInterval(this.handleSync, this.config.pollInterval);
    
    console.log(`Live sync started with ${this.config.pollInterval}ms interval`);
    this.notifySubscribers('sync_started', { timestamp: new Date().toISOString() });
  }

  stopSync() {
    if (!this.isRunning) {
      console.warn('Sync is not running');
      return;
    }

    this.isRunning = false;
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }

    console.log('Live sync stopped');
    this.notifySubscribers('sync_stopped', { timestamp: new Date().toISOString() });
  }

  async handleSync() {
    if (!this.spreadsheetConfig?.spreadsheetId) {
      console.warn('No spreadsheet configured for sync');
      return;
    }

    try {
      const syncResult = await this.performSync();
      this.errorCount = 0; // Reset error count on success
      
      if (syncResult.hasChanges) {
        this.notifySubscribers('data_changed', syncResult);
      }
      
    } catch (error) {
      this.errorCount++;
      this.lastError = error;
      
      console.error(`Sync failed (attempt ${this.errorCount}):`, error);
      
      this.notifySubscribers('sync_error', {
        error: error.message,
        errorCount: this.errorCount,
        timestamp: new Date().toISOString()
      });

      // Stop sync after max retries
      if (this.errorCount >= this.config.maxRetries) {
        console.error(`Max retries (${this.config.maxRetries}) exceeded. Stopping sync.`);
        this.stopSync();
        this.notifySubscribers('sync_failed', {
          error: 'Max retries exceeded',
          lastError: error.message,
          timestamp: new Date().toISOString()
        });
      } else {
        // Exponential backoff
        const backoffDelay = this.config.pollInterval * 
          Math.pow(this.config.backoffMultiplier, this.errorCount - 1);
        
        setTimeout(() => {
          if (this.isRunning && this.errorCount < this.config.maxRetries) {
            this.handleSync();
          }
        }, backoffDelay);
      }
    }
  }

  async performSync() {
    const { spreadsheetId, range, sheetName } = this.spreadsheetConfig;
    const actualRange = range || `${sheetName || 'Sheet1'}!A:Z`;
    
    // Fetch current data from sheets
    const { headers, data } = await this.client.getSpreadsheetData(spreadsheetId, actualRange);
    const currentData = this.client.transformToVolunteerData(headers, data);
    
    // Detect changes
    const changes = this.changeDetector.detectChanges(spreadsheetId, currentData);
    
    // If no changes, return early
    if (!changes.hasChanges) {
      this.addToSyncHistory({
        type: 'sync',
        success: true,
        hasChanges: false,
        timestamp: new Date().toISOString()
      });
      return changes;
    }

    // Handle conflicts if there are local changes
    let resolvedChanges = changes;
    if (this.hasLocalChanges()) {
      const localChanges = this.getLocalChanges();
      const conflictResolution = this.conflictResolver.resolveConflicts(
        localChanges,
        [...changes.added, ...changes.modified],
        this.config.conflictStrategy
      );
      
      resolvedChanges = {
        ...changes,
        conflicts: conflictResolution.conflicts,
        resolved: conflictResolution.resolved
      };
    }

    this.addToSyncHistory({
      type: 'sync',
      success: true,
      hasChanges: true,
      addedCount: changes.added.length,
      modifiedCount: changes.modified.length,
      deletedCount: changes.deleted.length,
      conflictsCount: resolvedChanges.conflicts?.length || 0,
      timestamp: new Date().toISOString()
    });

    return resolvedChanges;
  }

  // Subscription system for components to listen to sync events
  subscribe(eventType, callback) {
    if (!this.subscribers.has(eventType)) {
      this.subscribers.set(eventType, new Set());
    }
    this.subscribers.get(eventType).add(callback);
    
    return () => {
      this.subscribers.get(eventType)?.delete(callback);
    };
  }

  notifySubscribers(eventType, data) {
    const callbacks = this.subscribers.get(eventType);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in subscriber callback for ${eventType}:`, error);
        }
      });
    }
  }

  // Manual sync trigger
  async triggerSync() {
    if (!this.isRunning) {
      throw new Error('Sync service is not running');
    }
    return await this.performSync();
  }

  // Configuration updates
  updateConfig(newConfig) {
    const wasRunning = this.isRunning;
    
    if (wasRunning) {
      this.stopSync();
    }
    
    this.config = { ...this.config, ...newConfig };
    
    if (wasRunning) {
      this.startSync();
    }
  }

  updateSpreadsheetConfig(newSpreadsheetConfig) {
    this.spreadsheetConfig = { ...this.spreadsheetConfig, ...newSpreadsheetConfig };
    
    // Reset change detector for new spreadsheet
    if (newSpreadsheetConfig.spreadsheetId !== this.spreadsheetConfig?.spreadsheetId) {
      this.changeDetector.reset();
    }
  }

  // Status and monitoring
  getStatus() {
    return {
      isRunning: this.isRunning,
      lastSync: this.changeDetector.getLastSyncTime(this.spreadsheetConfig?.spreadsheetId),
      errorCount: this.errorCount,
      lastError: this.lastError?.message,
      config: this.config,
      spreadsheetConfig: this.spreadsheetConfig,
      isAuthenticated: this.client.isAuthenticated
    };
  }

  getSyncHistory(limit = 20) {
    return this.syncHistory.slice(-limit);
  }

  getChangeDetectorStats() {
    return this.changeDetector.getStats();
  }

  getConflictStats() {
    return this.conflictResolver.getConflictStats();
  }

  // Helper methods for local changes (to be implemented based on app needs)
  hasLocalChanges() {
    // This would check if there are pending local changes
    // Implementation depends on how local changes are stored
    return false;
  }

  getLocalChanges() {
    // This would return local changes that haven't been synced
    // Implementation depends on how local changes are stored
    return [];
  }

  addToSyncHistory(entry) {
    this.syncHistory.push(entry);
    
    // Keep only recent history (last 50 entries)
    if (this.syncHistory.length > 50) {
      this.syncHistory = this.syncHistory.slice(-50);
    }
  }

  // Cleanup
  destroy() {
    this.stopSync();
    this.subscribers.clear();
    this.changeDetector.reset();
    this.conflictResolver.clearHistory();
    this.syncHistory = [];
  }
}