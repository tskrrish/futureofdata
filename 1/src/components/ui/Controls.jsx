export function Controls({ branches, branchFilter, onBranchChange, search, onSearchChange, readOnly = false }) {
  return (
    <div className="max-w-7xl mx-auto px-4 py-4 grid md:grid-cols-3 gap-3">
      <div>
        <div className="text-xs mb-1 flex items-center">
          Branch
          {readOnly && <span className="ml-2 text-orange-600 text-xs">(Read Only)</span>}
        </div>
        <select
          className={`w-full rounded-2xl border p-2 ${readOnly ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}`}
          value={branchFilter}
          onChange={onBranchChange ? (e) => onBranchChange(e.target.value) : undefined}
          disabled={readOnly || !onBranchChange}
        >
          {branches.map((b) => (
            <option key={b}>{b}</option>
          ))}
        </select>
      </div>
      <div className="md:col-span-2">
        <div className="text-xs mb-1 flex items-center">
          Search
          {readOnly && <span className="ml-2 text-orange-600 text-xs">(Read Only)</span>}
        </div>
        <input
          className={`w-full rounded-2xl border p-2 ${readOnly ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}`}
          placeholder="Find name, branch, date…"
          value={search}
          onChange={onSearchChange ? (e) => onSearchChange(e.target.value) : undefined}
          disabled={readOnly || !onSearchChange}
          readOnly={readOnly}
        />
      </div>
    </div>
  );
}