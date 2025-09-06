import telemetry from './telemetry.js';

class MetricsService {
  constructor() {
    this.startTime = Date.now();
    this.pageViews = new Map();
    this.featureFlagMetrics = new Map();
    this.performanceMetrics = new Map();
    this.userBehavior = new Map();
    
    this.initializeTracking();
  }

  initializeTracking() {
    if (typeof window !== 'undefined') {
      // Track page load time
      window.addEventListener('load', () => {
        const loadTime = Date.now() - this.startTime;
        this.trackPageLoad(loadTime);
      });

      // Track errors
      window.addEventListener('error', (event) => {
        this.trackError(event.error || new Error(event.message), {
          filename: event.filename,
          line: event.lineno,
          column: event.colno
        });
      });

      // Track unhandled promise rejections
      window.addEventListener('unhandledrejection', (event) => {
        this.trackError(new Error(event.reason), {
          type: 'unhandled_promise_rejection'
        });
      });
    }
  }

  // Page and session metrics
  trackPageView(page, properties = {}) {
    const timestamp = Date.now();
    const sessionData = {
      page,
      timestamp,
      ...properties
    };

    this.pageViews.set(page, sessionData);
    telemetry.trackPageView(page);
    
    return sessionData;
  }

  trackPageLoad(loadTime) {
    telemetry.trackPerformance('page_load_time', loadTime);
    this.performanceMetrics.set('page_load_time', loadTime);
  }

  // Feature flag metrics
  trackFeatureFlagUsage(flagName, enabled, context = {}) {
    const key = `${flagName}_${enabled}`;
    const current = this.featureFlagMetrics.get(key) || 0;
    this.featureFlagMetrics.set(key, current + 1);

    telemetry.track('feature_flag_usage', {
      flagName,
      enabled,
      ...context
    });
  }

  getFeatureFlagMetrics() {
    const metrics = {};
    this.featureFlagMetrics.forEach((count, key) => {
      const [flagName, enabled] = key.split('_');
      if (!metrics[flagName]) {
        metrics[flagName] = { enabled: 0, disabled: 0, total: 0 };
      }
      metrics[flagName][enabled === 'true' ? 'enabled' : 'disabled'] = count;
      metrics[flagName].total += count;
    });
    return metrics;
  }

  // User behavior tracking
  trackUserAction(action, target, metadata = {}) {
    const actionKey = `${action}_${target}`;
    const current = this.userBehavior.get(actionKey) || 0;
    this.userBehavior.set(actionKey, current + 1);

    telemetry.track('user_action', {
      action,
      target,
      ...metadata
    });
  }

  trackTimeSpent(page, duration) {
    telemetry.track('time_spent', { page, duration });
    this.performanceMetrics.set(`time_spent_${page}`, duration);
  }

  // Volunteer dashboard specific metrics
  trackVolunteerInteraction(interaction, volunteer = null, metadata = {}) {
    const data = {
      interaction,
      volunteerId: volunteer?.id,
      volunteerHours: volunteer?.hours_total,
      ...metadata
    };

    this.trackUserAction('volunteer_interaction', interaction, data);
  }

  trackSearchBehavior(query, resultCount, timeToFirst = null) {
    telemetry.track('search_behavior', {
      query: query.length, // Don't track actual search terms for privacy
      resultCount,
      timeToFirst,
      hasResults: resultCount > 0
    });
  }

  trackExportBehavior(type, recordCount, format = 'csv') {
    telemetry.track('export_behavior', {
      type,
      recordCount,
      format,
      timestamp: new Date().toISOString()
    });
  }

  trackFilterUsage(filterType, valueCount, resultCount) {
    telemetry.track('filter_usage', {
      filterType,
      valueCount,
      resultCount,
      effectiveness: resultCount / Math.max(valueCount, 1)
    });
  }

  // Performance monitoring
  measurePerformance(name, fn) {
    const start = performance.now();
    const result = fn();
    const duration = performance.now() - start;
    
    telemetry.trackPerformance(name, duration);
    this.performanceMetrics.set(name, duration);
    
    return result;
  }

  async measureAsyncPerformance(name, asyncFn) {
    const start = performance.now();
    try {
      const result = await asyncFn();
      const duration = performance.now() - start;
      telemetry.trackPerformance(name, duration);
      this.performanceMetrics.set(name, duration);
      return result;
    } catch (error) {
      const duration = performance.now() - start;
      telemetry.trackPerformance(`${name}_error`, duration);
      this.trackError(error, { context: name });
      throw error;
    }
  }

  // Error tracking
  trackError(error, context = {}) {
    telemetry.trackError(error, context);
    
    // Also track error metrics locally
    const errorKey = `${error.name}_${context.type || 'general'}`;
    const current = this.performanceMetrics.get(errorKey) || 0;
    this.performanceMetrics.set(errorKey, current + 1);
  }

  // A/B test tracking
  trackExperiment(experimentName, variant, outcome = null) {
    telemetry.track('experiment', {
      experimentName,
      variant,
      outcome
    });
  }

  // Rollout metrics
  trackRolloutMetrics(flagName, userSegment, success = true) {
    telemetry.track('rollout_metrics', {
      flagName,
      userSegment,
      success,
      timestamp: new Date().toISOString()
    });
  }

  // Get summary metrics
  getSummaryMetrics() {
    return {
      pageViews: Object.fromEntries(this.pageViews),
      featureFlags: this.getFeatureFlagMetrics(),
      performance: Object.fromEntries(this.performanceMetrics),
      userBehavior: Object.fromEntries(this.userBehavior),
      sessionDuration: Date.now() - this.startTime,
      timestamp: new Date().toISOString()
    };
  }

  // Export metrics for analysis
  exportMetrics() {
    const metrics = this.getSummaryMetrics();
    const blob = new Blob([JSON.stringify(metrics, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `metrics-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
}

// Create singleton instance
const metrics = new MetricsService();

export default metrics;