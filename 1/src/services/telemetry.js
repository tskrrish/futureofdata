class TelemetryService {
  constructor() {
    this.events = [];
    this.maxBatchSize = 50;
    this.batchTimeout = 10000; // 10 seconds
    this.endpoint = '/api/telemetry';
    this.sessionId = this.generateSessionId();
    this.userId = null;
    this.batchTimer = null;
    
    // Auto-flush on page unload
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => this.flush());
    }
  }

  generateSessionId() {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  setUserId(userId) {
    this.userId = userId;
  }

  track(event, properties = {}) {
    const eventData = {
      id: this.generateEventId(),
      event,
      properties: {
        ...properties,
        timestamp: new Date().toISOString(),
        sessionId: this.sessionId,
        userId: this.userId,
        url: typeof window !== 'undefined' ? window.location.href : null,
        userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : null,
      }
    };

    this.events.push(eventData);

    // Auto-flush if batch is full
    if (this.events.length >= this.maxBatchSize) {
      this.flush();
    } else {
      this.scheduleBatch();
    }

    return eventData;
  }

  generateEventId() {
    return `evt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  scheduleBatch() {
    if (this.batchTimer) return;
    
    this.batchTimer = setTimeout(() => {
      this.flush();
    }, this.batchTimeout);
  }

  async flush() {
    if (this.events.length === 0) return;
    
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
      this.batchTimer = null;
    }

    const batch = [...this.events];
    this.events = [];

    try {
      // In a real implementation, this would send to your analytics backend
      console.log('📊 Telemetry batch sent:', {
        eventCount: batch.length,
        events: batch
      });
      
      // Simulate API call
      if (typeof fetch !== 'undefined') {
        try {
          await fetch(this.endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ events: batch })
          });
        } catch (error) {
          console.warn('Telemetry send failed:', error);
          // Re-queue events on failure
          this.events.unshift(...batch);
        }
      }
    } catch (error) {
      console.error('Failed to send telemetry:', error);
      // Re-queue events on error
      this.events.unshift(...batch);
    }
  }

  // Track specific volunteer dashboard events
  trackPageView(page) {
    this.track('page_view', { page });
  }

  trackVolunteerSearch(searchTerm, resultsCount) {
    this.track('volunteer_search', { searchTerm, resultsCount });
  }

  trackFileUpload(fileType, fileSize, recordCount) {
    this.track('file_upload', { fileType, fileSize, recordCount });
  }

  trackExport(exportType, recordCount) {
    this.track('export', { exportType, recordCount });
  }

  trackFilterChange(filterType, filterValue) {
    this.track('filter_change', { filterType, filterValue });
  }

  trackTabSwitch(fromTab, toTab) {
    this.track('tab_switch', { fromTab, toTab });
  }

  trackFeatureUsage(featureName, action, metadata = {}) {
    this.track('feature_usage', { featureName, action, ...metadata });
  }

  // Performance tracking
  trackPerformance(metricName, value, unit = 'ms') {
    this.track('performance', { metricName, value, unit });
  }

  // Error tracking
  trackError(error, context = {}) {
    this.track('error', {
      message: error.message,
      stack: error.stack,
      name: error.name,
      ...context
    });
  }
}

// Create singleton instance
const telemetry = new TelemetryService();

export default telemetry;