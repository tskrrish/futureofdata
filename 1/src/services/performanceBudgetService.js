import { BudgetMetrics } from '../types/monitoring';

class PerformanceBudgetService {
  constructor() {
    this.budgetHistory = new Map();
    this.alertCallbacks = [];
  }

  // Validate performance metrics against budget
  validateBudget(budget, metrics) {
    const results = {};
    let overallStatus = 'passing';
    const violations = [];

    for (const [metricKey, metricConfig] of Object.entries(budget.metrics)) {
      if (!metricConfig.enabled) {
        continue;
      }

      const currentValue = metrics[metricKey];
      const threshold = metricConfig.threshold;

      if (currentValue === undefined) {
        results[metricKey] = {
          ...metricConfig,
          current: null,
          status: 'unknown'
        };
        continue;
      }

      let status;
      const withinThreshold = currentValue <= threshold;

      if (withinThreshold) {
        status = 'passing';
      } else {
        status = 'failing';
        violations.push({
          metric: metricKey,
          threshold,
          actual: currentValue,
          deviation: ((currentValue - threshold) / threshold * 100).toFixed(1)
        });
        
        if (overallStatus !== 'failing') {
          overallStatus = 'failing';
        }
      }

      results[metricKey] = {
        ...metricConfig,
        current: currentValue,
        status
      };
    }

    // Check for warnings (within 90% of threshold)
    if (overallStatus === 'passing') {
      for (const [, result] of Object.entries(results)) {
        if (result.enabled && result.current !== null) {
          const utilizationRatio = result.current / result.threshold;
          if (utilizationRatio > 0.9) {
            overallStatus = 'warning';
            break;
          }
        }
      }
    }

    const budgetResult = {
      budgetId: budget.id,
      timestamp: new Date().toISOString(),
      metrics: results,
      overallStatus,
      violations,
      summary: {
        total: Object.keys(results).length,
        passing: Object.values(results).filter(r => r.status === 'passing').length,
        failing: violations.length,
        unknown: Object.values(results).filter(r => r.status === 'unknown').length
      }
    };

    this.recordBudgetResult(budget.id, budgetResult);

    // Trigger alerts for violations
    if (violations.length > 0) {
      this.triggerBudgetAlerts(budget, budgetResult);
    }

    return budgetResult;
  }

  // Simulate performance metrics collection
  async collectPerformanceMetrics(url) {
    // In a real implementation, this would use tools like Lighthouse, WebPageTest, or browser APIs
    // For demo purposes, we'll simulate realistic performance metrics
    
    try {
      await fetch(url, { method: 'GET' });
      
      // Simulate realistic performance metrics with some randomness
      const baseResponseTime = Math.random() * 500 + 300;
      const networkLatency = Math.random() * 200 + 100;
      
      const metrics = {
        [BudgetMetrics.RESPONSE_TIME]: Math.round(baseResponseTime),
        [BudgetMetrics.PAGE_LOAD_TIME]: Math.round(baseResponseTime + networkLatency + Math.random() * 1000),
        [BudgetMetrics.FIRST_CONTENTFUL_PAINT]: Math.round(baseResponseTime + Math.random() * 800 + 200),
        [BudgetMetrics.LARGEST_CONTENTFUL_PAINT]: Math.round(baseResponseTime + Math.random() * 1200 + 800),
        [BudgetMetrics.CUMULATIVE_LAYOUT_SHIFT]: Math.round((Math.random() * 0.15) * 1000) / 1000,
        [BudgetMetrics.TOTAL_BLOCKING_TIME]: Math.round(Math.random() * 400 + 50)
      };

      // Add some variability based on URL complexity
      if (url.includes('dashboard') || url.includes('app')) {
        metrics[BudgetMetrics.PAGE_LOAD_TIME] *= 1.2;
        metrics[BudgetMetrics.TOTAL_BLOCKING_TIME] *= 1.5;
      }

      if (url.includes('api')) {
        metrics[BudgetMetrics.PAGE_LOAD_TIME] = metrics[BudgetMetrics.RESPONSE_TIME];
        metrics[BudgetMetrics.FIRST_CONTENTFUL_PAINT] = 0;
        metrics[BudgetMetrics.LARGEST_CONTENTFUL_PAINT] = 0;
        metrics[BudgetMetrics.CUMULATIVE_LAYOUT_SHIFT] = 0;
      }

      return {
        success: true,
        url,
        metrics,
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      return {
        success: false,
        url,
        error: error.message,
        metrics: {},
        timestamp: new Date().toISOString()
      };
    }
  }

  // Check all budgets
  async checkAllBudgets(budgets) {
    const results = [];

    for (const budget of budgets) {
      if (!budget.enabled) {
        continue;
      }

      try {
        const metricsResult = await this.collectPerformanceMetrics(budget.url);
        
        if (metricsResult.success) {
          const budgetResult = this.validateBudget(budget, metricsResult.metrics);
          results.push(budgetResult);
        } else {
          results.push({
            budgetId: budget.id,
            timestamp: new Date().toISOString(),
            error: metricsResult.error,
            overallStatus: 'error'
          });
        }
      } catch (error) {
        results.push({
          budgetId: budget.id,
          timestamp: new Date().toISOString(),
          error: error.message,
          overallStatus: 'error'
        });
      }
    }

    return results;
  }

  // Record budget result in history
  recordBudgetResult(budgetId, result) {
    if (!this.budgetHistory.has(budgetId)) {
      this.budgetHistory.set(budgetId, []);
    }

    const history = this.budgetHistory.get(budgetId);
    history.push(result);

    // Keep only last 100 results
    if (history.length > 100) {
      history.shift();
    }
  }

  // Get budget history
  getBudgetHistory(budgetId, limit = 50) {
    const history = this.budgetHistory.get(budgetId) || [];
    return history.slice(-limit);
  }

  // Trigger alerts for budget violations
  triggerBudgetAlerts(budget, result) {
    const alerts = result.violations.map(violation => ({
      id: `budget_${budget.id}_${violation.metric}_${Date.now()}`,
      type: 'performance_budget',
      title: 'Performance Budget Violation',
      message: `${budget.name}: ${this.getMetricDisplayName(violation.metric)} exceeds budget`,
      severity: 'warning',
      timestamp: new Date().toISOString(),
      resolved: false,
      budgetId: budget.id,
      metric: violation.metric,
      threshold: violation.threshold,
      actual: violation.actual,
      deviation: violation.deviation
    }));

    this.alertCallbacks.forEach(callback => {
      alerts.forEach(alert => callback(alert));
    });

    return alerts;
  }

  // Subscribe to budget alerts
  onAlert(callback) {
    this.alertCallbacks.push(callback);
    return () => {
      const index = this.alertCallbacks.indexOf(callback);
      if (index > -1) {
        this.alertCallbacks.splice(index, 1);
      }
    };
  }

  // Get metric display name
  getMetricDisplayName(metricKey) {
    const names = {
      [BudgetMetrics.RESPONSE_TIME]: 'Response Time',
      [BudgetMetrics.PAGE_LOAD_TIME]: 'Page Load Time',
      [BudgetMetrics.FIRST_CONTENTFUL_PAINT]: 'First Contentful Paint',
      [BudgetMetrics.LARGEST_CONTENTFUL_PAINT]: 'Largest Contentful Paint',
      [BudgetMetrics.CUMULATIVE_LAYOUT_SHIFT]: 'Cumulative Layout Shift',
      [BudgetMetrics.TOTAL_BLOCKING_TIME]: 'Total Blocking Time'
    };
    return names[metricKey] || metricKey;
  }

  // Calculate budget score over time
  calculateBudgetScore(budgetId, hours = 24) {
    const history = this.getBudgetHistory(budgetId);
    const cutoff = new Date(Date.now() - hours * 60 * 60 * 1000);
    
    const recentResults = history.filter(result => 
      new Date(result.timestamp) > cutoff
    );

    if (recentResults.length === 0) return { score: 0, trend: 'stable' };

    const totalChecks = recentResults.length;
    const passingChecks = recentResults.filter(result => 
      result.overallStatus === 'passing'
    ).length;

    const score = (passingChecks / totalChecks) * 100;

    // Calculate trend
    const halfPoint = Math.floor(recentResults.length / 2);
    const firstHalf = recentResults.slice(0, halfPoint);
    const secondHalf = recentResults.slice(halfPoint);

    const firstHalfScore = firstHalf.length > 0 
      ? (firstHalf.filter(r => r.overallStatus === 'passing').length / firstHalf.length) * 100
      : 0;
    
    const secondHalfScore = secondHalf.length > 0
      ? (secondHalf.filter(r => r.overallStatus === 'passing').length / secondHalf.length) * 100
      : 0;

    let trend = 'stable';
    const scoreDiff = secondHalfScore - firstHalfScore;
    if (Math.abs(scoreDiff) > 10) {
      trend = scoreDiff > 0 ? 'improving' : 'degrading';
    }

    return { score: score.toFixed(1), trend };
  }
}

export const performanceBudgetService = new PerformanceBudgetService();