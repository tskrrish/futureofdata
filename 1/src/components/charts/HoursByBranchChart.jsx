import { Download } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  ResponsiveContainer, Tooltip, Legend
} from "recharts";

export function HoursByBranchChart({ data, onExport }) {
  return (
    <div className="lg:col-span-2 rounded-2xl border bg-white p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold">Hours by Branch</h3>
        <button 
          onClick={onExport} 
          className="inline-flex items-center gap-2 text-sm px-2 py-1 rounded-xl hover:bg-neutral-50"
        >
          <Download className="w-4 h-4" /> CSV
        </button>
      </div>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="branch" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="hours" name="Hours" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}