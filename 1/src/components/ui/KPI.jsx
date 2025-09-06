export function KPI({ icon, label, value, sub }) {
  return (
    <div className="rounded-2xl border bg-white p-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-2xl bg-neutral-100 grid place-items-center">
          {icon}
        </div>
        <div>
          <div className="text-sm text-neutral-500">{label}</div>
          <div className="text-xl font-semibold">{value}</div>
          {sub && <div className="text-xs text-neutral-500">{sub}</div>}
        </div>
      </div>
    </div>
  );
}