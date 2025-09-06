import { toMonth } from "./dateUtils";

/**
 * Calculates mean and standard deviation for an array of numbers
 */
function calculateStats(values) {
  if (values.length === 0) return { mean: 0, stdDev: 0 };
  
  const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
  const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
  const stdDev = Math.sqrt(variance);
  
  return { mean, stdDev };
}

/**
 * Performs linear regression on time series data
 */
function linearRegression(dataPoints) {
  const n = dataPoints.length;
  if (n === 0) return { slope: 0, intercept: 0, r2: 0 };
  
  const xSum = dataPoints.reduce((sum, point) => sum + point.x, 0);
  const ySum = dataPoints.reduce((sum, point) => sum + point.y, 0);
  const xySum = dataPoints.reduce((sum, point) => sum + (point.x * point.y), 0);
  const x2Sum = dataPoints.reduce((sum, point) => sum + (point.x * point.x), 0);
  
  const slope = (n * xySum - xSum * ySum) / (n * x2Sum - xSum * xSum);
  const intercept = (ySum - slope * xSum) / n;
  
  // Calculate R-squared
  const yMean = ySum / n;
  const ssRes = dataPoints.reduce((sum, point) => {
    const predicted = slope * point.x + intercept;
    return sum + Math.pow(point.y - predicted, 2);
  }, 0);
  const ssTot = dataPoints.reduce((sum, point) => {
    return sum + Math.pow(point.y - yMean, 2);
  }, 0);
  const r2 = ssTot === 0 ? 1 : 1 - (ssRes / ssTot);
  
  return { slope, intercept, r2: Math.max(0, r2) };
}

/**
 * Applies seasonal adjustment using historical monthly patterns
 */
function calculateSeasonalFactors(monthlyData) {
  const monthlyTotals = new Map();
  const monthCounts = new Map();
  
  monthlyData.forEach(data => {
    const date = new Date(data.month + " 01");
    const monthKey = date.getMonth(); // 0-11
    
    if (!monthlyTotals.has(monthKey)) {
      monthlyTotals.set(monthKey, 0);
      monthCounts.set(monthKey, 0);
    }
    
    monthlyTotals.set(monthKey, monthlyTotals.get(monthKey) + data.hours);
    monthCounts.set(monthKey, monthCounts.get(monthKey) + 1);
  });
  
  // Calculate average hours per month
  const monthlyAverages = new Map();
  const overallAverage = Array.from(monthlyTotals.values()).reduce((sum, val) => sum + val, 0) / 
                        Array.from(monthCounts.values()).reduce((sum, val) => sum + val, 0);
  
  for (let month = 0; month < 12; month++) {
    if (monthlyTotals.has(month) && monthCounts.get(month) > 0) {
      const avgForMonth = monthlyTotals.get(month) / monthCounts.get(month);
      monthlyAverages.set(month, avgForMonth / overallAverage);
    } else {
      monthlyAverages.set(month, 1.0); // No seasonal adjustment if no data
    }
  }
  
  return monthlyAverages;
}

/**
 * Generates per-branch monthly hours forecast with confidence bands
 */
export function generateBranchForecast(historicalData, monthsAhead = 6) {
  const branchForecasts = new Map();
  
  // Group data by branch
  const branchData = new Map();
  historicalData.forEach(record => {
    const branch = record.branch || "Unknown";
    if (!branchData.has(branch)) {
      branchData.set(branch, []);
    }
    branchData.get(branch).push(record);
  });
  
  branchData.forEach((records, branch) => {
    // Aggregate monthly data for this branch
    const monthlyData = new Map();
    records.forEach(record => {
      const month = toMonth(record.date);
      if (!monthlyData.has(month)) {
        monthlyData.set(month, 0);
      }
      monthlyData.set(month, monthlyData.get(month) + (Number(record.hours) || 0));
    });
    
    // Convert to sorted array of monthly data
    const monthlyArray = Array.from(monthlyData.entries())
      .map(([month, hours]) => ({ month, hours }))
      .sort((a, b) => new Date(a.month) - new Date(b.month));
    
    if (monthlyArray.length < 2) {
      // Not enough data for forecasting
      branchForecasts.set(branch, {
        branch,
        forecasts: [],
        confidence: "low",
        historicalMonths: monthlyArray.length
      });
      return;
    }
    
    // Prepare data for regression (x = month index, y = hours)
    const regressionData = monthlyArray.map((data, index) => ({
      x: index,
      y: data.hours
    }));
    
    // Perform linear regression
    const regression = linearRegression(regressionData);
    
    // Calculate seasonal factors
    const seasonalFactors = calculateSeasonalFactors(monthlyArray);
    
    // Calculate residuals for confidence band estimation
    const residuals = regressionData.map(point => {
      const predicted = regression.slope * point.x + regression.intercept;
      return Math.abs(point.y - predicted);
    });
    const { mean: residualMean, stdDev: residualStdDev } = calculateStats(residuals);
    
    // Generate forecasts
    const forecasts = [];
    const currentDate = new Date();
    
    for (let i = 1; i <= monthsAhead; i++) {
      const futureDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + i, 1);
      const futureMonth = toMonth(futureDate.toISOString());
      const monthIndex = monthlyArray.length + i - 1;
      
      // Base prediction from linear trend
      let basePrediction = regression.slope * monthIndex + regression.intercept;
      
      // Apply seasonal adjustment
      const seasonalFactor = seasonalFactors.get(futureDate.getMonth()) || 1.0;
      basePrediction *= seasonalFactor;
      
      // Ensure non-negative prediction
      basePrediction = Math.max(0, basePrediction);
      
      // Calculate confidence bands (95% confidence interval)
      // Confidence decreases with distance into future
      const distanceDecay = Math.sqrt(i);
      const confidenceMargin = (residualStdDev * 1.96 * distanceDecay) + (residualMean * distanceDecay);
      
      const lowerBound = Math.max(0, basePrediction - confidenceMargin);
      const upperBound = basePrediction + confidenceMargin;
      
      forecasts.push({
        month: futureMonth,
        predicted: Number(basePrediction.toFixed(1)),
        lowerBound: Number(lowerBound.toFixed(1)),
        upperBound: Number(upperBound.toFixed(1)),
        confidence: regression.r2 > 0.7 ? "high" : regression.r2 > 0.4 ? "medium" : "low",
        seasonalFactor: Number(seasonalFactor.toFixed(2))
      });
    }
    
    branchForecasts.set(branch, {
      branch,
      forecasts,
      trendSlope: Number(regression.slope.toFixed(2)),
      r2: Number(regression.r2.toFixed(3)),
      confidence: regression.r2 > 0.7 ? "high" : regression.r2 > 0.4 ? "medium" : "low",
      historicalMonths: monthlyArray.length,
      historicalData: monthlyArray
    });
  });
  
  return Array.from(branchForecasts.values())
    .sort((a, b) => b.historicalMonths - a.historicalMonths);
}

/**
 * Generates organization-wide forecast aggregating all branches
 */
export function generateOrganizationForecast(historicalData, monthsAhead = 6) {
  const branchForecasts = generateBranchForecast(historicalData, monthsAhead);
  
  const organizationForecast = [];
  
  for (let i = 0; i < monthsAhead; i++) {
    let totalPredicted = 0;
    let totalLowerBound = 0;
    let totalUpperBound = 0;
    let validForecasts = 0;
    let month = "";
    
    branchForecasts.forEach(branchData => {
      if (branchData.forecasts.length > i) {
        const forecast = branchData.forecasts[i];
        totalPredicted += forecast.predicted;
        totalLowerBound += forecast.lowerBound;
        totalUpperBound += forecast.upperBound;
        validForecasts++;
        month = forecast.month;
      }
    });
    
    if (validForecasts > 0) {
      organizationForecast.push({
        month,
        predicted: Number(totalPredicted.toFixed(1)),
        lowerBound: Number(totalLowerBound.toFixed(1)),
        upperBound: Number(totalUpperBound.toFixed(1)),
        branchesContributing: validForecasts,
        totalBranches: branchForecasts.length
      });
    }
  }
  
  return organizationForecast;
}

/**
 * Calculates forecast accuracy metrics when actual data becomes available
 */
export function calculateForecastAccuracy(forecasts, actualData) {
  const comparisons = [];
  
  forecasts.forEach(forecast => {
    const actual = actualData.find(data => data.month === forecast.month);
    if (actual) {
      const error = Math.abs(forecast.predicted - actual.hours);
      const percentError = actual.hours > 0 ? (error / actual.hours) * 100 : 0;
      const withinBounds = actual.hours >= forecast.lowerBound && actual.hours <= forecast.upperBound;
      
      comparisons.push({
        month: forecast.month,
        predicted: forecast.predicted,
        actual: actual.hours,
        error: Number(error.toFixed(1)),
        percentError: Number(percentError.toFixed(1)),
        withinBounds
      });
    }
  });
  
  if (comparisons.length === 0) {
    return { accuracy: 0, meanError: 0, boundsAccuracy: 0 };
  }
  
  const meanPercentError = comparisons.reduce((sum, comp) => sum + comp.percentError, 0) / comparisons.length;
  const boundsAccuracy = (comparisons.filter(comp => comp.withinBounds).length / comparisons.length) * 100;
  
  return {
    accuracy: Number((100 - meanPercentError).toFixed(1)),
    meanError: Number(meanPercentError.toFixed(1)),
    boundsAccuracy: Number(boundsAccuracy.toFixed(1)),
    comparisons
  };
}