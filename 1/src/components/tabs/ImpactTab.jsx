import React from "react";
import { Leaf, Heart, TreePine, Users2 } from "lucide-react";

const ImpactMetric = ({ icon, title, value, subtitle, color }) => (
  <div className={`bg-white rounded-2xl shadow-sm p-6 border-l-4 ${color}`}>
    <div className="flex items-center gap-3 mb-2">
      <div className={`p-2 rounded-lg ${color.replace('border-l-', 'bg-').replace('-500', '-100')}`}>
        {icon}
      </div>
      <h3 className="font-semibold text-neutral-800">{title}</h3>
    </div>
    <div className="text-3xl font-bold text-neutral-900 mb-1">{value}</div>
    <p className="text-sm text-neutral-600">{subtitle}</p>
  </div>
);

export function ImpactTab({ totalHours, activeVolunteersCount }) {
  // CO2 calculations based on volunteer activities
  const calculateCO2Saved = (hours) => {
    // Assumptions for CO2 savings:
    // - Transportation replacement: 0.5 lbs CO2 per hour (volunteers helping locally vs driving)
    // - Educational/Youth programs: 0.8 lbs CO2 per hour (behavioral change impact)
    // - Community services: 0.3 lbs CO2 per hour (resource sharing/efficiency)
    // - Senior services: 0.2 lbs CO2 per hour (local support reducing travel)
    const avgCO2PerHour = 0.45; // Average across all volunteer activities
    return (hours * avgCO2PerHour).toFixed(1);
  };

  // Lives impacted calculations
  const calculateLivesImpacted = (hours, volunteers) => {
    // Assumptions for lives touched:
    // - Youth programs: ~3 people per volunteer hour
    // - Senior programs: ~2 people per volunteer hour  
    // - Community services: ~4 people per volunteer hour
    // - Average impact: ~2.5 people per volunteer hour
    const avgImpactPerHour = 2.5;
    const directImpact = Math.round(hours * avgImpactPerHour);
    
    // Ripple effect: each volunteer influences family/friends
    const rippleEffect = Math.round(volunteers * 3.2); // Each volunteer influences ~3 others
    
    return {
      direct: directImpact,
      total: directImpact + rippleEffect
    };
  };

  const co2Saved = calculateCO2Saved(totalHours);
  const livesImpact = calculateLivesImpacted(totalHours, activeVolunteersCount);
  
  // Convert CO2 to trees equivalent (1 tree absorbs ~48 lbs CO2/year)
  const treesEquivalent = (co2Saved / 48).toFixed(1);
  
  return (
    <div className="mt-6 space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-neutral-900 mb-2">
          Volunteer Impact Dashboard
        </h2>
        <p className="text-neutral-600 max-w-2xl mx-auto">
          Measuring the environmental and community impact of our volunteer efforts. 
          Every hour volunteered creates ripple effects that benefit our planet and people.
        </p>
      </div>

      {/* Impact Metrics Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        <ImpactMetric
          icon={<Leaf className="w-5 h-5 text-green-600" />}
          title="CO₂ Saved"
          value={`${co2Saved} lbs`}
          subtitle="Carbon footprint reduction through local volunteer efforts"
          color="border-l-green-500"
        />
        
        <ImpactMetric
          icon={<TreePine className="w-5 h-5 text-emerald-600" />}
          title="Trees Equivalent"
          value={treesEquivalent}
          subtitle="Annual CO₂ absorption equivalent in trees"
          color="border-l-emerald-500"
        />
        
        <ImpactMetric
          icon={<Heart className="w-5 h-5 text-rose-600" />}
          title="Lives Directly Impacted"
          value={livesImpact.direct.toLocaleString()}
          subtitle="People directly served through volunteer programs"
          color="border-l-rose-500"
        />
        
        <ImpactMetric
          icon={<Users2 className="w-5 h-5 text-blue-600" />}
          title="Total Lives Touched"
          value={livesImpact.total.toLocaleString()}
          subtitle="Including ripple effects on families & communities"
          color="border-l-blue-500"
        />
      </div>

      {/* Impact Breakdown */}
      <div className="bg-white rounded-2xl shadow-sm p-6 mt-8">
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">Impact Methodology</h3>
        <div className="grid md:grid-cols-2 gap-8 text-sm">
          <div>
            <h4 className="font-medium text-green-700 mb-3 flex items-center gap-2">
              <Leaf className="w-4 h-4" />
              Environmental Impact
            </h4>
            <ul className="space-y-2 text-neutral-600">
              <li>• Reduced transportation emissions from local volunteer support</li>
              <li>• Educational programs promoting sustainable behaviors</li>
              <li>• Community resource sharing and efficiency improvements</li>
              <li>• Local food systems support reducing supply chain emissions</li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-medium text-rose-700 mb-3 flex items-center gap-2">
              <Heart className="w-4 h-4" />
              Community Impact
            </h4>
            <ul className="space-y-2 text-neutral-600">
              <li>• Direct service to youth, seniors, and families</li>
              <li>• Educational support and skill development</li>
              <li>• Health and wellness program assistance</li>
              <li>• Ripple effects through volunteer networks and families</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Personal Impact Message */}
      <div className="bg-gradient-to-r from-blue-50 to-green-50 rounded-2xl p-6 text-center">
        <div className="text-2xl font-bold text-neutral-900 mb-2">
          Together We're Making a Difference
        </div>
        <p className="text-neutral-700 max-w-3xl mx-auto">
          Our {activeVolunteersCount} active volunteers have contributed {totalHours.toFixed(1)} hours, 
          creating measurable environmental and social impact. Every volunteer hour matters in building 
          stronger, more sustainable communities.
        </p>
      </div>
    </div>
  );
}