import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  ResponsiveContainer, Tooltip, Legend, Cell
} from "recharts";

const COLORS = [
  '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', 
  '#ec4899', '#6b7280', '#059669', '#dc2626', '#7c3aed'
];

export function CohortRetentionChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="rounded-2xl border bg-white p-4">
        <h3 className="font-semibold mb-2">Monthly Cohort Retention</h3>
        <div className="h-72 flex items-center justify-center text-gray-500">
          No cohort data available
        </div>
      </div>
    );
  }

  // Transform data for line chart - each cohort becomes a line
  const chartData = [];
  const months = ['month0', 'month1', 'month2', 'month3', 'month6', 'month12'];
  const monthLabels = ['Month 0', 'Month 1', 'Month 2', 'Month 3', 'Month 6', 'Month 12'];

  // Create data points for each month
  monthLabels.forEach((label, index) => {
    const monthKey = months[index];
    const dataPoint = { month: label };
    
    data.forEach((cohort, cohortIndex) => {
      dataPoint[cohort.cohort] = cohort[monthKey];
    });
    
    chartData.push(dataPoint);
  });

  return (
    <div className="rounded-2xl border bg-white p-4">
      <div className="mb-4">
        <h3 className="font-semibold mb-1">Monthly Cohort Retention</h3>
        <p className="text-sm text-gray-600">
          Track how volunteers from each starting month continue to engage over time
        </p>
      </div>
      
      {/* Cohort Summary Table */}
      <div className="mb-4 overflow-x-auto">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="bg-gray-50">
              <th className="border p-2 text-left">Cohort</th>
              <th className="border p-2">Size</th>
              <th className="border p-2">Month 1</th>
              <th className="border p-2">Month 3</th>
              <th className="border p-2">Month 6</th>
              <th className="border p-2">Month 12</th>
            </tr>
          </thead>
          <tbody>
            {data.map((cohort, index) => (
              <tr key={cohort.cohort}>
                <td className="border p-2 font-medium">
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-3 h-3 rounded" 
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    ></div>
                    {cohort.cohort}
                  </div>
                </td>
                <td className="border p-2 text-center">{cohort.cohortSize}</td>
                <td className="border p-2 text-center">{cohort.month1.toFixed(1)}%</td>
                <td className="border p-2 text-center">{cohort.month3.toFixed(1)}%</td>
                <td className="border p-2 text-center">{cohort.month6.toFixed(1)}%</td>
                <td className="border p-2 text-center">{cohort.month12.toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Line Chart */}
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis 
              label={{ value: 'Retention %', angle: -90, position: 'insideLeft' }}
              domain={[0, 100]}
            />
            <Tooltip 
              formatter={(value, name) => [`${value?.toFixed(1) || 0}%`, name]}
            />
            <Legend />
            {data.map((cohort, index) => (
              <Line
                key={cohort.cohort}
                type="monotone"
                dataKey={cohort.cohort}
                name={`${cohort.cohort} (${cohort.cohortSize})`}
                stroke={COLORS[index % COLORS.length]}
                strokeWidth={2}
                dot={{ fill: COLORS[index % COLORS.length], strokeWidth: 2, r: 4 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}