import { useState, useEffect, useCallback } from 'react';
import { syntheticCheckService } from '../services/syntheticCheckService';
import { performanceBudgetService } from '../services/performanceBudgetService';
import { CheckStatus } from '../types/monitoring';

export function useMonitoring(initialChecks = [], initialBudgets = [], initialAlerts = []) {
  const [syntheticChecks, setSyntheticChecks] = useState(initialChecks);
  const [performanceBudgets, setPerformanceBudgets] = useState(initialBudgets);
  const [alerts, setAlerts] = useState(initialAlerts);
  const [isLoading, setIsLoading] = useState(false);

  // Update check with latest result
  const updateCheckResult = useCallback((checkResult) => {
    setSyntheticChecks(checks => 
      checks.map(check => {
        if (check.id === checkResult.checkId) {
          const successRate = syntheticCheckService.calculateSuccessRate(check.id);
          return {
            ...check,
            lastRun: checkResult.timestamp,
            status: checkResult.status,
            lastDuration: checkResult.responseTime,
            successRate
          };
        }
        return check;
      })
    );

    // Generate alert if check failed
    if (checkResult.status === CheckStatus.FAILURE) {
      const check = syntheticChecks.find(c => c.id === checkResult.checkId);
      if (check) {
        const alert = {
          id: `check_${checkResult.checkId}_${Date.now()}`,
          type: 'synthetic_check',
          title: 'Synthetic Check Failed',
          message: `${check.name}: ${checkResult.error || 'Check failed'}`,
          severity: 'error',
          timestamp: checkResult.timestamp,
          resolved: false,
          checkId: check.id,
          error: checkResult.error
        };
        
        setAlerts(prevAlerts => [alert, ...prevAlerts]);
      }
    }
  }, [syntheticChecks]);

  // Update budget with latest result
  const updateBudgetResult = useCallback((budgetResult) => {
    setPerformanceBudgets(budgets =>
      budgets.map(budget => {
        if (budget.id === budgetResult.budgetId) {
          return {
            ...budget,
            lastCheck: budgetResult.timestamp,
            overallStatus: budgetResult.overallStatus,
            metrics: Object.entries(budget.metrics).reduce((acc, [key, config]) => {
              acc[key] = budgetResult.metrics[key] || config;
              return acc;
            }, {})
          };
        }
        return budget;
      })
    );

    // Generate alerts for budget violations
    if (budgetResult.violations && budgetResult.violations.length > 0) {
      const budget = performanceBudgets.find(b => b.id === budgetResult.budgetId);
      if (budget) {
        const budgetAlerts = budgetResult.violations.map(violation => ({
          id: `budget_${budgetResult.budgetId}_${violation.metric}_${Date.now()}`,
          type: 'performance_budget',
          title: 'Performance Budget Violation',
          message: `${budget.name}: ${violation.metric.replace('_', ' ')} exceeds threshold`,
          severity: 'warning',
          timestamp: budgetResult.timestamp,
          resolved: false,
          budgetId: budget.id,
          metric: violation.metric,
          threshold: violation.threshold,
          actual: violation.actual
        }));
        
        setAlerts(prevAlerts => [...budgetAlerts, ...prevAlerts]);
      }
    }
  }, [performanceBudgets]);

  // Start monitoring for all enabled checks
  const startMonitoring = useCallback(() => {
    syntheticChecks.forEach(check => {
      if (check.enabled) {
        syntheticCheckService.startInterval(check, updateCheckResult);
      }
    });
  }, [syntheticChecks, updateCheckResult]);

  // Stop all monitoring
  const stopMonitoring = useCallback(() => {
    syntheticCheckService.stopAllIntervals();
  }, []);

  // Run all performance budget checks
  const runBudgetChecks = useCallback(async () => {
    setIsLoading(true);
    try {
      const results = await performanceBudgetService.checkAllBudgets(
        performanceBudgets.filter(budget => budget.enabled)
      );
      
      results.forEach(updateBudgetResult);
    } catch (error) {
      console.error('Error running budget checks:', error);
    } finally {
      setIsLoading(false);
    }
  }, [performanceBudgets, updateBudgetResult]);

  // Run a specific synthetic check
  const runSyntheticCheck = useCallback(async (checkId) => {
    const check = syntheticChecks.find(c => c.id === checkId);
    if (!check) return;

    setIsLoading(true);
    try {
      const result = await syntheticCheckService.executeCheck(check);
      updateCheckResult(result);
      return result;
    } catch (error) {
      console.error('Error running synthetic check:', error);
    } finally {
      setIsLoading(false);
    }
  }, [syntheticChecks, updateCheckResult]);

  // Toggle check enabled state
  const toggleCheck = useCallback((checkId) => {
    setSyntheticChecks(checks =>
      checks.map(check => {
        if (check.id === checkId) {
          const updatedCheck = { ...check, enabled: !check.enabled };
          
          if (updatedCheck.enabled) {
            syntheticCheckService.startInterval(updatedCheck, updateCheckResult);
          } else {
            syntheticCheckService.stopInterval(checkId);
          }
          
          return updatedCheck;
        }
        return check;
      })
    );
  }, [updateCheckResult]);

  // Toggle budget enabled state
  const toggleBudget = useCallback((budgetId) => {
    setPerformanceBudgets(budgets =>
      budgets.map(budget =>
        budget.id === budgetId ? { ...budget, enabled: !budget.enabled } : budget
      )
    );
  }, []);

  // Add new check
  const addCheck = useCallback((check) => {
    setSyntheticChecks(checks => [...checks, check]);
  }, []);

  // Add new budget
  const addBudget = useCallback((budget) => {
    setPerformanceBudgets(budgets => [...budgets, budget]);
  }, []);

  // Delete check
  const deleteCheck = useCallback((checkId) => {
    syntheticCheckService.stopInterval(checkId);
    setSyntheticChecks(checks => checks.filter(check => check.id !== checkId));
  }, []);

  // Delete budget
  const deleteBudget = useCallback((budgetId) => {
    setPerformanceBudgets(budgets => budgets.filter(budget => budget.id !== budgetId));
  }, []);

  // Resolve alert
  const resolveAlert = useCallback((alertId) => {
    setAlerts(alerts =>
      alerts.map(alert =>
        alert.id === alertId ? { ...alert, resolved: true } : alert
      )
    );
  }, []);

  // Dismiss alert
  const dismissAlert = useCallback((alertId) => {
    setAlerts(alerts => alerts.filter(alert => alert.id !== alertId));
  }, []);

  // Get monitoring statistics
  const getStats = useCallback(() => {
    const activeChecks = syntheticChecks.filter(check => check.enabled);
    const activeBudgets = performanceBudgets.filter(budget => budget.enabled);
    const activeAlerts = alerts.filter(alert => !alert.resolved);

    const checkStats = {
      total: activeChecks.length,
      passing: activeChecks.filter(check => check.status === CheckStatus.SUCCESS).length,
      failing: activeChecks.filter(check => check.status === CheckStatus.FAILURE).length,
      warning: activeChecks.filter(check => check.status === CheckStatus.WARNING).length
    };

    const budgetStats = {
      total: activeBudgets.length,
      passing: activeBudgets.filter(budget => budget.overallStatus === 'passing').length,
      failing: activeBudgets.filter(budget => budget.overallStatus === 'failing').length,
      warning: activeBudgets.filter(budget => budget.overallStatus === 'warning').length
    };

    const alertStats = {
      active: activeAlerts.length,
      critical: activeAlerts.filter(alert => alert.severity === 'error').length,
      warnings: activeAlerts.filter(alert => alert.severity === 'warning').length
    };

    return { checkStats, budgetStats, alertStats };
  }, [syntheticChecks, performanceBudgets, alerts]);

  // Setup alert subscription on mount
  useEffect(() => {
    const unsubscribe = performanceBudgetService.onAlert((alert) => {
      setAlerts(prevAlerts => [alert, ...prevAlerts]);
    });

    return unsubscribe;
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopMonitoring();
    };
  }, [stopMonitoring]);

  return {
    // State
    syntheticChecks,
    performanceBudgets,
    alerts,
    isLoading,
    
    // Actions
    startMonitoring,
    stopMonitoring,
    runBudgetChecks,
    runSyntheticCheck,
    toggleCheck,
    toggleBudget,
    addCheck,
    addBudget,
    deleteCheck,
    deleteBudget,
    resolveAlert,
    dismissAlert,
    
    // Computed
    stats: getStats()
  };
}