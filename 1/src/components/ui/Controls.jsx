import { useTranslation } from "react-i18next";

export function Controls({ branches, branchFilter, onBranchChange, search, onSearchChange }) {
  const { t } = useTranslation();
  return (
    <div className="max-w-7xl mx-auto px-4 py-4 grid md:grid-cols-3 gap-3">
      <div>
        <div className="text-xs mb-1">{t('controls.branch')}</div>
        <select
          className="w-full rounded-2xl border p-2 bg-white"
          value={branchFilter}
          onChange={(e) => onBranchChange(e.target.value)}
        >
          {branches.map((b) => (
            <option key={b}>{b}</option>
          ))}
        </select>
      </div>
      <div className="md:col-span-2">
        <div className="text-xs mb-1">{t('controls.search')}</div>
        <input
          className="w-full rounded-2xl border p-2 bg-white"
          placeholder={t('controls.searchPlaceholder')}
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
        />
      </div>
    </div>
  );
}