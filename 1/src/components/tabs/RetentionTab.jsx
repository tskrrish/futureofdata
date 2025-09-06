import { CohortRetentionChart } from "../charts/CohortRetentionChart";

export function RetentionTab({ cohortData, cohortInsights }) {
  return (
    <div className="mt-4 space-y-6">
      {/* Insights Cards */}
      {cohortInsights && cohortInsights.length > 0 && (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {cohortInsights.map((insight, index) => (
            <div 
              key={index}
              className={`rounded-2xl border p-4 ${
                insight.type === 'success' ? 'bg-green-50 border-green-200' :
                insight.type === 'warning' ? 'bg-amber-50 border-amber-200' :
                'bg-blue-50 border-blue-200'
              }`}
            >
              <h4 className={`font-semibold text-sm mb-1 ${
                insight.type === 'success' ? 'text-green-800' :
                insight.type === 'warning' ? 'text-amber-800' :
                'text-blue-800'
              }`}>
                {insight.title}
              </h4>
              <p className={`text-xs ${
                insight.type === 'success' ? 'text-green-700' :
                insight.type === 'warning' ? 'text-amber-700' :
                'text-blue-700'
              }`}>
                {insight.message}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Cohort Retention Chart */}
      <div className="grid grid-cols-1">
        <CohortRetentionChart data={cohortData} />
      </div>

      {/* About Cohort Analysis */}
      <div className="rounded-2xl border bg-white p-4">
        <h3 className="font-semibold mb-2">About Cohort Retention Analysis</h3>
        <div className="text-sm text-gray-600 space-y-2">
          <p>
            <strong>What is Cohort Analysis?</strong> A cohort is a group of volunteers who first became active in the same month. 
            This analysis tracks how many volunteers from each monthly cohort return to volunteer in subsequent months.
          </p>
          <p>
            <strong>How to Read the Chart:</strong> Each line represents a different monthly cohort. The Y-axis shows the retention percentage, 
            and the X-axis shows time periods after their first volunteer activity.
          </p>
          <p>
            <strong>Key Metrics:</strong>
          </p>
          <ul className="list-disc list-inside ml-4 space-y-1">
            <li><strong>Month 0:</strong> Always 100% - all volunteers are active in their first month</li>
            <li><strong>Month 1:</strong> What percentage returned the following month?</li>
            <li><strong>Month 3:</strong> Short-term retention indicator</li>
            <li><strong>Month 6:</strong> Medium-term engagement</li>
            <li><strong>Month 12:</strong> Long-term volunteer loyalty</li>
          </ul>
          <p>
            <strong>Why This Matters:</strong> Understanding retention patterns helps identify when volunteers are most likely to drop off 
            and can guide targeted engagement strategies to improve long-term volunteer retention.
          </p>
        </div>
      </div>
    </div>
  );
}