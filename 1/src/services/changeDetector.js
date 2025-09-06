export class ChangeDetector {
  constructor() {
    this.previousData = new Map();
    this.lastSyncTimestamp = new Map();
    this.checksums = new Map();
  }

  generateChecksum(data) {
    // Simple checksum based on stringified data
    const str = JSON.stringify(data);
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return hash.toString();
  }

  generateRowChecksum(row) {
    // Generate checksum for a single row
    const rowData = Object.entries(row)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([key, value]) => `${key}:${value}`)
      .join('|');
    
    let hash = 0;
    for (let i = 0; i < rowData.length; i++) {
      const char = rowData.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return hash.toString();
  }

  detectChanges(spreadsheetId, newData, metadata = {}) {
    const currentChecksum = this.generateChecksum(newData);
    const previousChecksum = this.checksums.get(spreadsheetId);
    const previousRows = this.previousData.get(spreadsheetId) || [];
    
    const changes = {
      hasChanges: false,
      added: [],
      modified: [],
      deleted: [],
      metadata: {
        totalRows: newData.length,
        previousRows: previousRows.length,
        timestamp: new Date().toISOString(),
        ...metadata
      }
    };

    // Quick check - if checksums match, no changes
    if (previousChecksum && currentChecksum === previousChecksum) {
      return changes;
    }

    changes.hasChanges = true;

    // Create maps for efficient lookups
    const previousRowsMap = new Map();
    const newRowsMap = new Map();

    // For volunteer data, we'll use assignee + date + project as unique identifier
    const getRowId = (row) => {
      return `${row.assignee || ''}|${row.date || ''}|${row.project || ''}|${row.branch || ''}`;
    };

    // Build maps with checksums
    previousRows.forEach((row, index) => {
      const id = getRowId(row);
      const checksum = this.generateRowChecksum(row);
      previousRowsMap.set(id, { ...row, _index: index, _checksum: checksum });
    });

    newData.forEach((row, index) => {
      const id = getRowId(row);
      const checksum = this.generateRowChecksum(row);
      newRowsMap.set(id, { ...row, _index: index, _checksum: checksum });
    });

    // Find added and modified rows
    newRowsMap.forEach((newRow, id) => {
      const previousRow = previousRowsMap.get(id);
      
      if (!previousRow) {
        // New row
        changes.added.push({
          id,
          data: newRow,
          index: newRow._index
        });
      } else if (newRow._checksum !== previousRow._checksum) {
        // Modified row
        const fieldChanges = this.detectFieldChanges(previousRow, newRow);
        changes.modified.push({
          id,
          data: newRow,
          previousData: previousRow,
          fieldChanges,
          index: newRow._index
        });
      }
    });

    // Find deleted rows
    previousRowsMap.forEach((previousRow, id) => {
      if (!newRowsMap.has(id)) {
        changes.deleted.push({
          id,
          data: previousRow,
          index: previousRow._index
        });
      }
    });

    // Update stored data
    this.previousData.set(spreadsheetId, newData);
    this.checksums.set(spreadsheetId, currentChecksum);
    this.lastSyncTimestamp.set(spreadsheetId, new Date().toISOString());

    return changes;
  }

  detectFieldChanges(oldRow, newRow) {
    const changes = {};
    const allKeys = new Set([...Object.keys(oldRow), ...Object.keys(newRow)]);
    
    allKeys.forEach(key => {
      if (key.startsWith('_')) return; // Skip internal fields
      
      const oldValue = oldRow[key];
      const newValue = newRow[key];
      
      if (oldValue !== newValue) {
        changes[key] = {
          from: oldValue,
          to: newValue
        };
      }
    });
    
    return changes;
  }

  getLastSyncTime(spreadsheetId) {
    return this.lastSyncTimestamp.get(spreadsheetId);
  }

  reset(spreadsheetId) {
    if (spreadsheetId) {
      this.previousData.delete(spreadsheetId);
      this.checksums.delete(spreadsheetId);
      this.lastSyncTimestamp.delete(spreadsheetId);
    } else {
      this.previousData.clear();
      this.checksums.clear();
      this.lastSyncTimestamp.clear();
    }
  }

  // Method to handle initial data load
  initializeData(spreadsheetId, data) {
    this.previousData.set(spreadsheetId, data);
    this.checksums.set(spreadsheetId, this.generateChecksum(data));
    this.lastSyncTimestamp.set(spreadsheetId, new Date().toISOString());
  }

  // Get statistics about tracked sheets
  getStats() {
    const stats = {
      trackedSheets: this.previousData.size,
      sheets: []
    };

    this.previousData.forEach((data, spreadsheetId) => {
      stats.sheets.push({
        spreadsheetId,
        rowCount: data.length,
        lastSync: this.lastSyncTimestamp.get(spreadsheetId),
        checksum: this.checksums.get(spreadsheetId)
      });
    });

    return stats;
  }
}