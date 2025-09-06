import { CheckStatus, CheckTypes } from '../types/monitoring';

class SyntheticCheckService {
  constructor() {
    this.runningChecks = new Map();
    this.checkHistory = new Map();
  }

  // Execute a single synthetic check
  async executeCheck(check) {
    if (!check.enabled) {
      return { success: false, reason: 'Check is disabled' };
    }

    const startTime = Date.now();
    
    try {
      let result;
      
      switch (check.type) {
        case CheckTypes.HTTP_ENDPOINT:
          result = await this.executeHttpCheck(check);
          break;
        case CheckTypes.PAGE_LOAD:
          result = await this.executePageLoadCheck(check);
          break;
        case CheckTypes.API_RESPONSE:
          result = await this.executeApiCheck(check);
          break;
        case CheckTypes.USER_FLOW:
          result = await this.executeUserFlowCheck(check);
          break;
        default:
          throw new Error(`Unknown check type: ${check.type}`);
      }

      const duration = Date.now() - startTime;
      
      const checkResult = {
        checkId: check.id,
        timestamp: new Date().toISOString(),
        duration,
        status: result.success ? CheckStatus.SUCCESS : CheckStatus.FAILURE,
        responseTime: result.responseTime || duration,
        statusCode: result.statusCode,
        error: result.error,
        metrics: result.metrics || {}
      };

      this.recordCheckResult(check.id, checkResult);
      return checkResult;

    } catch (error) {
      const duration = Date.now() - startTime;
      const checkResult = {
        checkId: check.id,
        timestamp: new Date().toISOString(),
        duration,
        status: CheckStatus.FAILURE,
        error: error.message,
        metrics: {}
      };

      this.recordCheckResult(check.id, checkResult);
      return checkResult;
    }
  }

  // Execute HTTP endpoint check
  async executeHttpCheck(check) {
    const startTime = Date.now();
    
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), check.timeout || 30000);

      const response = await fetch(check.url, {
        method: check.method || 'GET',
        headers: check.headers || {},
        body: check.method !== 'GET' ? check.body : undefined,
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      const responseTime = Date.now() - startTime;

      const success = check.expectedStatus 
        ? response.status === check.expectedStatus
        : response.ok;

      return {
        success,
        statusCode: response.status,
        responseTime,
        error: success ? null : `Expected status ${check.expectedStatus}, got ${response.status}`
      };

    } catch (error) {
      const responseTime = Date.now() - startTime;
      return {
        success: false,
        responseTime,
        error: error.name === 'AbortError' ? 'Request timeout' : error.message
      };
    }
  }

  // Execute page load check (simulated)
  async executePageLoadCheck(check) {
    // In a real implementation, this would use a headless browser
    // For demo purposes, we'll simulate page load metrics
    const startTime = Date.now();
    
    try {
      const response = await fetch(check.url, {
        method: 'GET',
        headers: check.headers || {}
      });

      const responseTime = Date.now() - startTime;
      
      // Simulate performance metrics
      const metrics = {
        firstContentfulPaint: Math.random() * 1500 + 500,
        largestContentfulPaint: Math.random() * 2000 + 1000,
        cumulativeLayoutShift: Math.random() * 0.1,
        totalBlockingTime: Math.random() * 300 + 100
      };

      return {
        success: response.ok,
        statusCode: response.status,
        responseTime,
        metrics,
        error: response.ok ? null : `HTTP ${response.status}`
      };

    } catch (error) {
      const responseTime = Date.now() - startTime;
      return {
        success: false,
        responseTime,
        error: error.message,
        metrics: {}
      };
    }
  }

  // Execute API response check
  async executeApiCheck(check) {
    return this.executeHttpCheck(check);
  }

  // Execute user flow check (simulated)
  async executeUserFlowCheck(check) {
    // In a real implementation, this would automate user interactions
    // For demo purposes, we'll simulate a multi-step process
    const startTime = Date.now();
    
    try {
      // Simulate multiple requests in a user flow
      const steps = [
        { url: check.url, method: 'GET' },
        { url: check.url, method: check.method, body: check.body }
      ];

      let totalTime = 0;
      let lastStatusCode = 200;

      for (const step of steps) {
        const stepStart = Date.now();
        const response = await fetch(step.url, {
          method: step.method,
          headers: check.headers || {},
          body: step.body
        });
        
        totalTime += Date.now() - stepStart;
        lastStatusCode = response.status;
        
        if (!response.ok) {
          throw new Error(`Step failed with status ${response.status}`);
        }

        // Simulate delay between steps
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      const responseTime = Date.now() - startTime;

      return {
        success: true,
        statusCode: lastStatusCode,
        responseTime,
        metrics: { totalStepTime: totalTime, steps: steps.length }
      };

    } catch (error) {
      const responseTime = Date.now() - startTime;
      return {
        success: false,
        responseTime,
        error: error.message,
        metrics: {}
      };
    }
  }

  // Record check result in history
  recordCheckResult(checkId, result) {
    if (!this.checkHistory.has(checkId)) {
      this.checkHistory.set(checkId, []);
    }

    const history = this.checkHistory.get(checkId);
    history.push(result);

    // Keep only last 100 results
    if (history.length > 100) {
      history.shift();
    }
  }

  // Get check history
  getCheckHistory(checkId, limit = 50) {
    const history = this.checkHistory.get(checkId) || [];
    return history.slice(-limit);
  }

  // Calculate success rate for a check
  calculateSuccessRate(checkId, hours = 24) {
    const history = this.checkHistory.get(checkId) || [];
    const cutoff = new Date(Date.now() - hours * 60 * 60 * 1000);
    
    const recentResults = history.filter(result => 
      new Date(result.timestamp) > cutoff
    );

    if (recentResults.length === 0) return 0;

    const successCount = recentResults.filter(result => 
      result.status === CheckStatus.SUCCESS
    ).length;

    return (successCount / recentResults.length) * 100;
  }

  // Start interval checking for a check
  startInterval(check, onResult) {
    if (this.runningChecks.has(check.id)) {
      this.stopInterval(check.id);
    }

    const runCheck = async () => {
      const result = await this.executeCheck(check);
      if (onResult) {
        onResult(result);
      }
    };

    // Run immediately
    runCheck();

    // Schedule recurring checks
    const intervalId = setInterval(runCheck, check.interval);
    this.runningChecks.set(check.id, intervalId);
  }

  // Stop interval checking for a check
  stopInterval(checkId) {
    const intervalId = this.runningChecks.get(checkId);
    if (intervalId) {
      clearInterval(intervalId);
      this.runningChecks.delete(checkId);
    }
  }

  // Stop all running checks
  stopAllIntervals() {
    for (const [, intervalId] of this.runningChecks) {
      clearInterval(intervalId);
    }
    this.runningChecks.clear();
  }
}

export const syntheticCheckService = new SyntheticCheckService();