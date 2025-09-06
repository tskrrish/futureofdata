import React, { useState } from "react";
import { DollarSign, TrendingUp, Calculator } from "lucide-react";

export function RoiTab({ volunteerData, totalHours, activeVolunteersCount }) {
  const [hourlyValue, setHourlyValue] = useState(29.95); // Default: Independent Sector 2023 value
  const [operationalCostRate, setOperationalCostRate] = useState(25); // Default: $25/hour operational cost
  const [fundingMultiplier, setFundingMultiplier] = useState(3); // Default: 3x leverage ratio

  // Calculate ROI metrics
  const totalVolunteerValue = totalHours * hourlyValue;
  const costSavings = totalHours * operationalCostRate;
  const fundingLeverage = totalVolunteerValue * fundingMultiplier;
  const netImpact = totalVolunteerValue + fundingLeverage - (totalHours * 5); // Assume $5/hour program costs

  const roiPercentage = totalHours > 0 ? ((netImpact / (totalHours * 5)) - 1) * 100 : 0;

  return (
    <div className="mt-6 space-y-6">
      {/* Configuration Panel */}
      <div className="rounded-2xl border bg-white p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Calculator className="w-5 h-5" />
          ROI Calculator Settings
        </h3>
        <div className="grid md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-2">
              Volunteer Hour Value ($)
            </label>
            <input
              type="number"
              value={hourlyValue}
              onChange={(e) => setHourlyValue(parseFloat(e.target.value) || 0)}
              step="0.01"
              className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="29.95"
            />
            <p className="text-xs text-neutral-500 mt-1">
              Independent Sector 2023: $29.95/hour
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-2">
              Operational Cost Rate ($)
            </label>
            <input
              type="number"
              value={operationalCostRate}
              onChange={(e) => setOperationalCostRate(parseFloat(e.target.value) || 0)}
              step="0.01"
              className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="25.00"
            />
            <p className="text-xs text-neutral-500 mt-1">
              Cost to hire equivalent staff
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-2">
              Funding Leverage Multiplier
            </label>
            <input
              type="number"
              value={fundingMultiplier}
              onChange={(e) => setFundingMultiplier(parseFloat(e.target.value) || 0)}
              step="0.1"
              className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="3.0"
            />
            <p className="text-xs text-neutral-500 mt-1">
              Grant leverage ratio (e.g., 3:1)
            </p>
          </div>
        </div>
      </div>

      {/* ROI Metrics Cards */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="rounded-2xl border bg-white p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-green-100 grid place-items-center">
              <DollarSign className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <div className="text-sm text-neutral-500">Total Volunteer Value</div>
              <div className="text-xl font-semibold">${totalVolunteerValue.toLocaleString()}</div>
              <div className="text-xs text-neutral-500">{totalHours.toFixed(1)} hours × ${hourlyValue}</div>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border bg-white p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-blue-100 grid place-items-center">
              <TrendingUp className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <div className="text-sm text-neutral-500">Cost Savings</div>
              <div className="text-xl font-semibold">${costSavings.toLocaleString()}</div>
              <div className="text-xs text-neutral-500">vs. hiring staff at ${operationalCostRate}/hr</div>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border bg-white p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-purple-100 grid place-items-center">
              <TrendingUp className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <div className="text-sm text-neutral-500">Funding Leverage</div>
              <div className="text-xl font-semibold">${fundingLeverage.toLocaleString()}</div>
              <div className="text-xs text-neutral-500">${fundingMultiplier}x multiplier potential</div>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border bg-white p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-orange-100 grid place-items-center">
              <Calculator className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <div className="text-sm text-neutral-500">ROI Percentage</div>
              <div className="text-xl font-semibold">{roiPercentage.toFixed(0)}%</div>
              <div className="text-xs text-neutral-500">Return on investment</div>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Breakdown */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Impact Summary */}
        <div className="rounded-2xl border bg-white p-6">
          <h3 className="text-lg font-semibold mb-4">Impact Summary</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center py-2 border-b border-neutral-100">
              <span className="text-neutral-700">Total Volunteer Hours</span>
              <span className="font-semibold">{totalHours.toFixed(1)}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-neutral-100">
              <span className="text-neutral-700">Active Volunteers</span>
              <span className="font-semibold">{activeVolunteersCount}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-neutral-100">
              <span className="text-neutral-700">Average Hours per Volunteer</span>
              <span className="font-semibold">{(totalHours / Math.max(activeVolunteersCount, 1)).toFixed(1)}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-neutral-100">
              <span className="text-neutral-700">Economic Value Generated</span>
              <span className="font-semibold text-green-600">${totalVolunteerValue.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-neutral-700">Total Impact Potential</span>
              <span className="font-semibold text-purple-600">${(totalVolunteerValue + fundingLeverage).toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* Value Per Volunteer */}
        <div className="rounded-2xl border bg-white p-6">
          <h3 className="text-lg font-semibold mb-4">Value Per Volunteer</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center py-2 border-b border-neutral-100">
              <span className="text-neutral-700">Average Value per Volunteer</span>
              <span className="font-semibold">${(totalVolunteerValue / Math.max(activeVolunteersCount, 1)).toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-neutral-100">
              <span className="text-neutral-700">Cost Savings per Volunteer</span>
              <span className="font-semibold">${(costSavings / Math.max(activeVolunteersCount, 1)).toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-neutral-100">
              <span className="text-neutral-700">Funding Leverage per Volunteer</span>
              <span className="font-semibold">${(fundingLeverage / Math.max(activeVolunteersCount, 1)).toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-neutral-700">Total Impact per Volunteer</span>
              <span className="font-semibold text-purple-600">${((totalVolunteerValue + fundingLeverage) / Math.max(activeVolunteersCount, 1)).toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Department/Category Breakdown */}
      <div className="rounded-2xl border bg-white p-6">
        <h3 className="text-lg font-semibold mb-4">Value by Category</h3>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(
            volunteerData.reduce((acc, record) => {
              const category = record.category || "Other";
              acc[category] = (acc[category] || 0) + record.hours;
              return acc;
            }, {})
          ).map(([category, hours]) => (
            <div key={category} className="p-4 border rounded-lg">
              <div className="text-sm font-medium text-neutral-700">{category}</div>
              <div className="text-lg font-semibold">{hours.toFixed(1)} hrs</div>
              <div className="text-sm text-green-600">${(hours * hourlyValue).toLocaleString()}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}