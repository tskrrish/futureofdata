import { Download, TrendingUp, AlertCircle, CheckCircle } from "lucide-react";
import {
  ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid,
  ResponsiveContainer, Tooltip, Legend, ReferenceLine
} from "recharts";

const ConfidenceTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 border rounded-lg shadow-lg">
        <p className="font-semibold">{label}</p>
        {payload.map((entry, index) => {
          if (entry.dataKey === "predicted") {
            return (
              <div key={index}>
                <p className="text-blue-600">
                  Predicted: {entry.value} hours
                </p>
                {entry.payload.lowerBound !== undefined && (
                  <p className="text-gray-500 text-sm">
                    Range: {entry.payload.lowerBound} - {entry.payload.upperBound} hours
                  </p>
                )}
                {entry.payload.confidence && (
                  <p className="text-sm">
                    Confidence: <span className={`font-medium ${
                      entry.payload.confidence === 'high' ? 'text-green-600' :
                      entry.payload.confidence === 'medium' ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      {entry.payload.confidence}
                    </span>
                  </p>
                )}
              </div>
            );
          }
          return (
            <p key={index} style={{ color: entry.color }}>
              {entry.name}: {entry.value}
            </p>
          );
        })}
      </div>
    );
  }
  return null;
};

export function ForecastChart({ 
  historicalData = [], 
  forecastData = [], 
  title = "Hours Forecast",
  onExport 
}) {
  // Combine historical and forecast data for visualization
  const combinedData = [
    ...historicalData.map(item => ({
      ...item,
      type: 'historical',
      predicted: null,
      lowerBound: null,
      upperBound: null
    })),
    ...forecastData.map(item => ({
      ...item,
      type: 'forecast',
      hours: null
    }))
  ];

  const getConfidenceIcon = (confidence) => {
    switch (confidence) {
      case 'high': return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'medium': return <AlertCircle className="w-4 h-4 text-yellow-600" />;
      case 'low': return <AlertCircle className="w-4 h-4 text-red-600" />;
      default: return null;
    }
  };

  const getConfidenceColor = (confidence) => {
    switch (confidence) {
      case 'high': return 'text-green-600';
      case 'medium': return 'text-yellow-600'; 
      case 'low': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="rounded-2xl border bg-white p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-blue-600" />
          <h3 className="font-semibold">{title}</h3>
        </div>
        {onExport && (
          <button 
            onClick={onExport} 
            className="inline-flex items-center gap-2 text-sm px-2 py-1 rounded-xl hover:bg-neutral-50"
          >
            <Download className="w-4 h-4" /> Export
          </button>
        )}
      </div>

      {forecastData.length > 0 && (
        <div className="mb-4 p-3 bg-blue-50 rounded-lg">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium">Next Month Prediction:</span>
              <p className="text-lg font-semibold text-blue-600">
                {forecastData[0]?.predicted || 0} hours
              </p>
            </div>
            <div>
              <span className="font-medium">Confidence Range:</span>
              <p className="text-sm text-gray-600">
                {forecastData[0]?.lowerBound || 0} - {forecastData[0]?.upperBound || 0} hours
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-medium">Reliability:</span>
              {getConfidenceIcon(forecastData[0]?.confidence)}
              <span className={`font-medium ${getConfidenceColor(forecastData[0]?.confidence)}`}>
                {forecastData[0]?.confidence || 'unknown'}
              </span>
            </div>
          </div>
        </div>
      )}

      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={combinedData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="month" 
              tick={{ fontSize: 12 }}
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip content={<ConfidenceTooltip />} />
            <Legend />
            
            {/* Historical data line */}
            <Line 
              type="monotone" 
              dataKey="hours" 
              stroke="#2563eb" 
              strokeWidth={2}
              name="Historical Hours"
              connectNulls={false}
              dot={{ fill: '#2563eb', strokeWidth: 2, r: 4 }}
            />
            
            {/* Forecast prediction line */}
            <Line 
              type="monotone" 
              dataKey="predicted" 
              stroke="#dc2626" 
              strokeWidth={2}
              strokeDasharray="5 5"
              name="Predicted Hours"
              connectNulls={false}
              dot={{ fill: '#dc2626', strokeWidth: 2, r: 4 }}
            />
            
            {/* Confidence band area */}
            <Area
              type="monotone"
              dataKey="upperBound"
              stackId="1"
              stroke="none"
              fill="#fecaca"
              fillOpacity={0.3}
              name="Upper Confidence"
            />
            <Area
              type="monotone"
              dataKey="lowerBound"
              stackId="1" 
              stroke="none"
              fill="#ffffff"
              fillOpacity={1}
              name="Lower Confidence"
            />
            
            {/* Reference line to separate historical from forecast */}
            {historicalData.length > 0 && forecastData.length > 0 && (
              <ReferenceLine 
                x={historicalData[historicalData.length - 1]?.month} 
                stroke="#6b7280" 
                strokeDasharray="2 2"
                label={{ value: "Forecast Start", position: "top" }}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {forecastData.length > 0 && (
        <div className="mt-4 text-xs text-gray-500">
          <p>
            * Confidence bands represent 95% prediction intervals. 
            Predictions become less reliable further into the future.
          </p>
          <p>
            * Forecast incorporates historical trends and seasonal patterns when available.
          </p>
        </div>
      )}
    </div>
  );
}