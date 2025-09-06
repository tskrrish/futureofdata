import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  ResponsiveContainer, Tooltip, Legend
} from "recharts";

export function MonthlyTrendChart({ data }) {
  return (
    <div className="rounded-2xl border bg-white p-4">
      <h3 className="font-semibold mb-2">Monthly Trend</h3>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="hours" name="Hours" />
            <Line type="monotone" dataKey="active" name="Active" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}