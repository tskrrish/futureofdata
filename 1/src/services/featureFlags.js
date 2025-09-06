class FeatureFlagsService {
  constructor() {
    this.flags = new Map();
    this.userAttributes = {};
    this.defaultFlags = {
      newDashboardDesign: { enabled: false, rollout: 0 },
      enhancedReporting: { enabled: false, rollout: 0 },
      realTimeUpdates: { enabled: false, rollout: 0 },
      advancedFiltering: { enabled: false, rollout: 25 },
      exportEnhancements: { enabled: true, rollout: 100 },
      betaFeatures: { enabled: false, rollout: 0 }
    };
    
    this.initialize();
  }

  async initialize() {
    // Load flags from localStorage first
    this.loadFromStorage();
    
    // Then fetch latest from server
    try {
      await this.fetchFlags();
    } catch (error) {
      console.warn('Failed to fetch feature flags from server:', error);
    }
  }

  loadFromStorage() {
    try {
      const stored = localStorage.getItem('featureFlags');
      if (stored) {
        const parsed = JSON.parse(stored);
        Object.entries(parsed).forEach(([key, value]) => {
          this.flags.set(key, value);
        });
      } else {
        // Initialize with defaults
        Object.entries(this.defaultFlags).forEach(([key, value]) => {
          this.flags.set(key, value);
        });
      }
    } catch (error) {
      console.error('Error loading feature flags from storage:', error);
    }
  }

  saveToStorage() {
    try {
      const flagsObject = Object.fromEntries(this.flags);
      localStorage.setItem('featureFlags', JSON.stringify(flagsObject));
    } catch (error) {
      console.error('Error saving feature flags to storage:', error);
    }
  }

  async fetchFlags() {
    try {
      const response = await fetch('/api/feature-flags', {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const serverFlags = await response.json();
        Object.entries(serverFlags).forEach(([key, value]) => {
          this.flags.set(key, value);
        });
        this.saveToStorage();
      }
    } catch {
      // Fail silently and use cached/default values
      console.warn('Feature flags fetch failed, using cached values');
    }
  }

  setUserAttributes(attributes) {
    this.userAttributes = { ...this.userAttributes, ...attributes };
  }

  getUserId() {
    return this.userAttributes.userId || this.userAttributes.id || 'anonymous';
  }

  hashUserId(userId) {
    // Simple hash function for consistent rollout
    let hash = 0;
    for (let i = 0; i < userId.length; i++) {
      const char = userId.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return Math.abs(hash) % 100;
  }

  isEnabled(flagName) {
    const flag = this.flags.get(flagName);
    if (!flag) {
      console.warn(`Feature flag "${flagName}" not found`);
      return false;
    }

    // If flag is completely disabled
    if (!flag.enabled) {
      return false;
    }

    // If rollout is 100%, always enabled
    if (flag.rollout >= 100) {
      return true;
    }

    // If rollout is 0%, always disabled
    if (flag.rollout <= 0) {
      return false;
    }

    // Gradual rollout based on user ID hash
    const userId = this.getUserId();
    const userHash = this.hashUserId(userId);
    
    return userHash < flag.rollout;
  }

  getVariant(flagName, variants = []) {
    if (!this.isEnabled(flagName) || variants.length === 0) {
      return null;
    }

    const userId = this.getUserId();
    const userHash = this.hashUserId(userId);
    const variantIndex = userHash % variants.length;
    
    return variants[variantIndex];
  }

  getAllFlags() {
    const result = {};
    this.flags.forEach((value, key) => {
      result[key] = {
        ...value,
        isEnabled: this.isEnabled(key)
      };
    });
    return result;
  }

  // Admin methods for testing
  forceEnable(flagName) {
    if (this.flags.has(flagName)) {
      const flag = this.flags.get(flagName);
      this.flags.set(flagName, { ...flag, enabled: true, rollout: 100 });
      this.saveToStorage();
    }
  }

  forceDisable(flagName) {
    if (this.flags.has(flagName)) {
      const flag = this.flags.get(flagName);
      this.flags.set(flagName, { ...flag, enabled: false, rollout: 0 });
      this.saveToStorage();
    }
  }

  setRollout(flagName, percentage) {
    if (this.flags.has(flagName)) {
      const flag = this.flags.get(flagName);
      this.flags.set(flagName, { 
        ...flag, 
        rollout: Math.max(0, Math.min(100, percentage))
      });
      this.saveToStorage();
    }
  }

  // Track flag evaluation for metrics
  trackFlagEvaluation(flagName, result) {
    // This would typically send to telemetry
    if (typeof window !== 'undefined' && window.telemetry) {
      window.telemetry.track('feature_flag_evaluation', {
        flagName,
        result,
        userId: this.getUserId(),
        userAttributes: this.userAttributes
      });
    }
  }

  // Wrapper that tracks usage
  evaluate(flagName) {
    const result = this.isEnabled(flagName);
    this.trackFlagEvaluation(flagName, result);
    return result;
  }
}

// Create singleton instance
const featureFlags = new FeatureFlagsService();

export default featureFlags;