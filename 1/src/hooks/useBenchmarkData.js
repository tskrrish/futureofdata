import { useMemo, useState, useCallback } from 'react';
import { 
  calculateBenchmarkComparison,
  getAvailablePeriods,
  calculateDefaultTargets,
  generateBenchmarkInsights
} from '../utils/benchmarkUtils';

/**
 * Hook for managing benchmark comparison data and state
 * @param {Array} data - Raw volunteer data
 * @returns {Object} Benchmark data and control functions
 */
export function useBenchmarkData(data) {
  // Get available periods for selection
  const availablePeriods = useMemo(() => {
    return getAvailablePeriods(data);
  }, [data]);

  // Set default periods (current = latest, prior = second latest)
  const [currentPeriod, setCurrentPeriod] = useState(() => {
    return availablePeriods.length > 0 ? availablePeriods[availablePeriods.length - 1] : '';
  });

  const [priorPeriod, setPriorPeriod] = useState(() => {
    return availablePeriods.length > 1 ? availablePeriods[availablePeriods.length - 2] : '';
  });

  // Calculate default targets based on historical data
  const defaultTargets = useMemo(() => {
    return calculateDefaultTargets(data);
  }, [data]);

  // Custom targets state (can be overridden by user)
  const [customTargets, setCustomTargets] = useState({});

  // Determine which targets to use
  const activeTargets = useMemo(() => {
    return { ...defaultTargets, ...customTargets };
  }, [defaultTargets, customTargets]);

  // Main benchmark calculation
  const benchmarkData = useMemo(() => {
    if (!currentPeriod || !priorPeriod || data.length === 0) {
      return null;
    }

    return calculateBenchmarkComparison(data, currentPeriod, priorPeriod, activeTargets);
  }, [data, currentPeriod, priorPeriod, activeTargets]);

  // Generate insights
  const insights = useMemo(() => {
    if (!benchmarkData) return [];
    return generateBenchmarkInsights(benchmarkData);
  }, [benchmarkData]);

  // Performance summary for quick overview
  const performanceSummary = useMemo(() => {
    if (!benchmarkData) return null;

    const { comparisons } = benchmarkData;
    const metrics = Object.values(comparisons);
    
    const statusCounts = metrics.reduce((acc, metric) => {
      acc[metric.status] = (acc[metric.status] || 0) + 1;
      return acc;
    }, {});

    const totalMetrics = metrics.length;
    const excellentCount = statusCounts.excellent || 0;
    const goodCount = statusCounts.good || 0;
    const averageCount = statusCounts.average || 0;
    const poorCount = statusCounts.poor || 0;
    const belowTargetCount = statusCounts['below-target'] || 0;

    // Calculate overall score
    const overallScore = (
      (excellentCount * 4) + 
      (goodCount * 3) + 
      (averageCount * 2) + 
      (poorCount * 1) + 
      (belowTargetCount * 1)
    ) / (totalMetrics * 4) * 100;

    return {
      overallScore: Number(overallScore.toFixed(1)),
      statusCounts,
      totalMetrics,
      overallStatus: getOverallStatus(overallScore)
    };
  }, [benchmarkData]);

  // Branch-level benchmark comparisons
  const branchBenchmarks = useMemo(() => {
    if (!currentPeriod || !priorPeriod || data.length === 0) {
      return [];
    }

    const branches = [...new Set(data.map(r => r.branch || 'Unknown'))];
    
    return branches.map(branch => {
      const branchData = data.filter(r => (r.branch || 'Unknown') === branch);
      const benchmark = calculateBenchmarkComparison(
        branchData, 
        currentPeriod, 
        priorPeriod, 
        {} // No branch-specific targets for now
      );
      
      return {
        branch,
        ...benchmark
      };
    }).sort((a, b) => b.current.totalHours - a.current.totalHours);
  }, [data, currentPeriod, priorPeriod]);

  // Update target values
  const updateTarget = useCallback((metric, value) => {
    setCustomTargets(prev => ({
      ...prev,
      [metric]: Number(value)
    }));
  }, []);

  // Reset targets to defaults
  const resetTargets = useCallback(() => {
    setCustomTargets({});
  }, []);

  // Get period comparison options (exclude current period from prior options)
  const priorPeriodOptions = useMemo(() => {
    return availablePeriods.filter(period => period !== currentPeriod);
  }, [availablePeriods, currentPeriod]);

  return {
    // Data
    benchmarkData,
    insights,
    performanceSummary,
    branchBenchmarks,
    
    // Period management
    availablePeriods,
    currentPeriod,
    priorPeriod,
    priorPeriodOptions,
    setCurrentPeriod,
    setPriorPeriod,
    
    // Target management
    defaultTargets,
    customTargets,
    activeTargets,
    updateTarget,
    resetTargets,
    
    // State
    isReady: Boolean(currentPeriod && priorPeriod && data.length > 0)
  };
}

/**
 * Get overall performance status based on score
 */
function getOverallStatus(score) {
  if (score >= 85) return 'excellent';
  if (score >= 70) return 'good';
  if (score >= 55) return 'average';
  return 'poor';
}