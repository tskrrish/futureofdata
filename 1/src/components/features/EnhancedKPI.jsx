import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

export function EnhancedKPI({ icon, label, value, sub, onClick, enhanced = false }) {
  // Mock trend data for demonstration
  const trend = Math.random() > 0.5 ? 'up' : 'down';
  const trendValue = (Math.random() * 20).toFixed(1);

  if (!enhanced) {
    return (
      <div 
        className="bg-white p-4 rounded-2xl border cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={onClick}
      >
        <div className="flex items-center gap-3">
          <div className="text-neutral-600">{icon}</div>
          <div>
            <p className="text-xs text-neutral-500 uppercase tracking-wider font-medium">
              {label}
            </p>
            <p className="text-2xl font-bold text-neutral-900">{value}</p>
            {sub && (
              <p className="text-xs text-neutral-500 mt-1">{sub}</p>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div 
      className="bg-white p-4 rounded-2xl border cursor-pointer hover:bg-gray-50 transition-colors relative overflow-hidden"
      onClick={onClick}
    >
      {/* Enhanced background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50/30 to-purple-50/30 pointer-events-none" />
      
      <div className="relative">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <div className="text-blue-600">{icon}</div>
            <p className="text-xs text-neutral-600 uppercase tracking-wider font-medium">
              {label}
            </p>
          </div>
          
          {/* Trend indicator */}
          <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
            trend === 'up' 
              ? 'bg-green-100 text-green-700' 
              : 'bg-red-100 text-red-700'
          }`}>
            {trend === 'up' ? (
              <TrendingUp className="w-3 h-3" />
            ) : (
              <TrendingDown className="w-3 h-3" />
            )}
            {trendValue}%
          </div>
        </div>

        <div className="flex items-end justify-between">
          <div>
            <p className="text-2xl font-bold text-neutral-900">{value}</p>
            {sub && (
              <p className="text-xs text-neutral-500 mt-1">{sub}</p>
            )}
          </div>
          
          {/* Mini chart placeholder */}
          <div className="flex items-end gap-1 h-8">
            {[...Array(8)].map((_, i) => (
              <div 
                key={i}
                className="bg-blue-200 rounded-sm"
                style={{
                  width: '3px',
                  height: `${Math.random() * 100}%`,
                  minHeight: '4px'
                }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}