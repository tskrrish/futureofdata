import { useState } from "react";
import { TrendingUp, BarChart3, Info, Calendar } from "lucide-react";
import { ForecastChart } from "../charts/ForecastChart";
import { exportCSV } from "../../utils";

export function ForecastTab({ 
  trendByMonth, 
  branchForecasts, 
  organizationForecast
}) {
  const [forecastMonths, setForecastMonths] = useState(6);
  const [selectedBranch, setSelectedBranch] = useState("all");

  // Get branch options for forecast selection
  const branchOptions = [
    { value: "all", label: "Organization-wide" },
    ...branchForecasts.map(forecast => ({ 
      value: forecast.branch, 
      label: forecast.branch 
    }))
  ];

  // Get current forecast data to display
  const getCurrentForecastData = () => {
    if (selectedBranch === "all") {
      return {
        historical: trendByMonth,
        forecast: organizationForecast.slice(0, forecastMonths),
        title: "Organization-wide Hours Forecast"
      };
    }
    
    const branchData = branchForecasts.find(b => b.branch === selectedBranch);
    if (branchData) {
      return {
        historical: branchData.historicalData || [],
        forecast: branchData.forecasts.slice(0, forecastMonths),
        title: `${selectedBranch} Hours Forecast`
      };
    }
    
    return {
      historical: [],
      forecast: [],
      title: "No Forecast Available"
    };
  };

  const currentForecast = getCurrentForecastData();

  const exportBranchForecasts = () => {
    const exportData = [];
    branchForecasts.forEach(branch => {
      branch.forecasts.forEach(forecast => {
        exportData.push({
          branch: branch.branch,
          month: forecast.month,
          predicted: forecast.predicted,
          lowerBound: forecast.lowerBound,
          upperBound: forecast.upperBound,
          confidence: forecast.confidence,
          trendSlope: branch.trendSlope,
          r2Score: branch.r2,
          historicalMonths: branch.historicalMonths
        });
      });
    });
    exportCSV("branch_forecasts.csv", exportData);
  };

  const exportOrganizationForecast = () => {
    exportCSV("organization_forecast.csv", organizationForecast.map(f => ({
      month: f.month,
      predicted: f.predicted,
      lowerBound: f.lowerBound,
      upperBound: f.upperBound,
      branchesContributing: f.branchesContributing,
      totalBranches: f.totalBranches
    })));
  };

  // Calculate summary stats
  const summaryStats = {
    totalBranches: branchForecasts.length,
    highConfidenceBranches: branchForecasts.filter(b => b.confidence === 'high').length,
    mediumConfidenceBranches: branchForecasts.filter(b => b.confidence === 'medium').length,
    lowConfidenceBranches: branchForecasts.filter(b => b.confidence === 'low').length,
    avgTrendSlope: branchForecasts.length > 0 
      ? (branchForecasts.reduce((sum, b) => sum + b.trendSlope, 0) / branchForecasts.length).toFixed(2)
      : 0
  };

  return (
    <div className="space-y-6 mt-6">
      {/* Controls */}
      <div className="bg-white rounded-2xl border p-4">
        <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold">Predictive Hours Forecast</h2>
          </div>
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Branch:</label>
              <select 
                value={selectedBranch} 
                onChange={(e) => setSelectedBranch(e.target.value)}
                className="px-3 py-1 border rounded-lg text-sm"
              >
                {branchOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Forecast Period:</label>
              <select 
                value={forecastMonths} 
                onChange={(e) => setForecastMonths(Number(e.target.value))}
                className="px-3 py-1 border rounded-lg text-sm"
              >
                <option value={3}>3 months</option>
                <option value={6}>6 months</option>
                <option value={12}>12 months</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border p-4 text-center">
          <div className="text-2xl font-bold text-blue-600">{summaryStats.totalBranches}</div>
          <div className="text-sm text-gray-600">Branches with Forecasts</div>
        </div>
        <div className="bg-white rounded-xl border p-4 text-center">
          <div className="text-2xl font-bold text-green-600">{summaryStats.highConfidenceBranches}</div>
          <div className="text-sm text-gray-600">High Confidence</div>
        </div>
        <div className="bg-white rounded-xl border p-4 text-center">
          <div className="text-2xl font-bold text-yellow-600">{summaryStats.mediumConfidenceBranches}</div>
          <div className="text-sm text-gray-600">Medium Confidence</div>
        </div>
        <div className="bg-white rounded-xl border p-4 text-center">
          <div className="text-2xl font-bold text-red-600">{summaryStats.lowConfidenceBranches}</div>
          <div className="text-sm text-gray-600">Low Confidence</div>
        </div>
      </div>

      {/* Main Forecast Chart */}
      <ForecastChart
        historicalData={currentForecast.historical}
        forecastData={currentForecast.forecast}
        title={currentForecast.title}
        onExport={selectedBranch === "all" ? exportOrganizationForecast : exportBranchForecasts}
      />

      {/* Forecast Analysis Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Branch Forecast Summary Table */}
        <div className="bg-white rounded-2xl border p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Branch Forecast Summary
            </h3>
            <button 
              onClick={exportBranchForecasts}
              className="text-xs px-2 py-1 bg-blue-50 text-blue-600 rounded hover:bg-blue-100"
            >
              Export All
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Branch</th>
                  <th className="text-right py-2">Next Month</th>
                  <th className="text-center py-2">Confidence</th>
                  <th className="text-right py-2">Trend</th>
                </tr>
              </thead>
              <tbody>
                {branchForecasts.slice(0, 8).map(branch => (
                  <tr key={branch.branch} className="border-b hover:bg-gray-50">
                    <td className="py-2 font-medium">{branch.branch}</td>
                    <td className="py-2 text-right">
                      {branch.forecasts.length > 0 ? `${branch.forecasts[0].predicted}h` : 'N/A'}
                    </td>
                    <td className="py-2 text-center">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        branch.confidence === 'high' ? 'bg-green-100 text-green-800' :
                        branch.confidence === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {branch.confidence}
                      </span>
                    </td>
                    <td className="py-2 text-right">
                      <span className={branch.trendSlope > 0 ? 'text-green-600' : 'text-red-600'}>
                        {branch.trendSlope > 0 ? '+' : ''}{branch.trendSlope}h/mo
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Methodology Information */}
        <div className="bg-blue-50 rounded-2xl border p-4">
          <h3 className="font-semibold flex items-center gap-2 mb-4">
            <Info className="w-4 h-4" />
            Forecast Methodology
          </h3>
          <div className="space-y-3 text-sm">
            <div>
              <h4 className="font-medium">Linear Trend Analysis</h4>
              <p className="text-gray-600">
                Historical data is analyzed using linear regression to identify growth/decline trends.
              </p>
            </div>
            <div>
              <h4 className="font-medium">Seasonal Adjustments</h4>
              <p className="text-gray-600">
                Monthly patterns are detected and applied to improve prediction accuracy.
              </p>
            </div>
            <div>
              <h4 className="font-medium">Confidence Bands</h4>
              <p className="text-gray-600">
                95% prediction intervals calculated from historical forecast errors.
              </p>
            </div>
            <div>
              <h4 className="font-medium">Reliability Scoring</h4>
              <ul className="text-gray-600 space-y-1 ml-4">
                <li>• <span className="font-medium text-green-600">High:</span> R² &gt; 0.7</li>
                <li>• <span className="font-medium text-yellow-600">Medium:</span> R² = 0.4-0.7</li>
                <li>• <span className="font-medium text-red-600">Low:</span> R² &lt; 0.4</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {organizationForecast.length > 0 && (
        <div className="bg-white rounded-2xl border p-4">
          <h3 className="font-semibold flex items-center gap-2 mb-4">
            <Calendar className="w-4 h-4" />
            Next 6 Months Outlook
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {organizationForecast.slice(0, 6).map((forecast) => (
              <div key={forecast.month} className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-sm font-medium text-gray-600">{forecast.month}</div>
                <div className="text-lg font-bold text-blue-600">{forecast.predicted}h</div>
                <div className="text-xs text-gray-500">
                  {forecast.lowerBound} - {forecast.upperBound}h
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}