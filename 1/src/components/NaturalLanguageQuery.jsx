import React, { useState, useMemo } from 'react';
import { Search, AlertTriangle, TrendingDown, Users, Clock } from 'lucide-react';
import { calculateChurnRisk, processNaturalLanguageQuery } from '../utils/churnAnalysis';

export function NaturalLanguageQuery({ data }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Calculate churn risk data
  const churnData = useMemo(() => {
    if (!data || data.length === 0) return [];
    return calculateChurnRisk(data);
  }, [data]);

  // Example queries for user guidance
  const exampleQueries = [
    "Who's at churn risk in Blue Ash?",
    "Show me high risk volunteers",
    "Which volunteers are inactive?",
    "Who has declining engagement?",
    "Show new volunteers at Campbell County"
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setIsLoading(true);
    
    // Simulate processing time for better UX
    setTimeout(() => {
      const queryResults = processNaturalLanguageQuery(query, churnData);
      setResults(queryResults);
      setIsLoading(false);
    }, 300);
  };

  const handleExampleClick = (exampleQuery) => {
    setQuery(exampleQuery);
    const queryResults = processNaturalLanguageQuery(exampleQuery, churnData);
    setResults(queryResults);
  };

  const getRiskColor = (riskLevel) => {
    switch (riskLevel) {
      case 'High': return 'text-red-600 bg-red-50';
      case 'Medium': return 'text-yellow-600 bg-yellow-50';
      case 'Low': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getRiskIcon = (riskLevel) => {
    switch (riskLevel) {
      case 'High': return <AlertTriangle className="w-4 h-4" />;
      case 'Medium': return <TrendingDown className="w-4 h-4" />;
      case 'Low': return <Users className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          Natural Language Queries
        </h2>
        <p className="text-gray-600 text-sm">
          Ask questions about volunteer churn risk using natural language
        </p>
      </div>

      {/* Query Input */}
      <form onSubmit={handleSubmit} className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about churn risk... (e.g., 'Who's at churn risk in Blue Ash?')"
            className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? 'Processing...' : 'Ask Question'}
        </button>
      </form>

      {/* Example Queries */}
      {!results && (
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Example queries:</h3>
          <div className="flex flex-wrap gap-2">
            {exampleQueries.map((example, index) => (
              <button
                key={index}
                onClick={() => handleExampleClick(example)}
                className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
              >
                "{example}"
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      {results && (
        <div>
          <div className="mb-4 p-3 bg-blue-50 rounded-lg">
            <p className="text-blue-800 text-sm">
              <strong>Query:</strong> "{query}"
            </p>
            <p className="text-blue-700 text-sm mt-1">
              {results.summary}
            </p>
          </div>

          {results.results.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 px-3 font-medium text-gray-700">Risk</th>
                    <th className="text-left py-2 px-3 font-medium text-gray-700">Volunteer</th>
                    <th className="text-left py-2 px-3 font-medium text-gray-700">Branch</th>
                    <th className="text-left py-2 px-3 font-medium text-gray-700">Hours</th>
                    <th className="text-left py-2 px-3 font-medium text-gray-700">Last Active</th>
                    <th className="text-left py-2 px-3 font-medium text-gray-700">Risk Factors</th>
                  </tr>
                </thead>
                <tbody>
                  {results.results.map((volunteer, index) => (
                    <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-2 px-3">
                        <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(volunteer.riskLevel)}`}>
                          {getRiskIcon(volunteer.riskLevel)}
                          {volunteer.riskLevel}
                        </div>
                      </td>
                      <td className="py-2 px-3">
                        <div>
                          <div className="font-medium text-gray-900">{volunteer.assignee}</div>
                          {volunteer.is_member && (
                            <div className="text-xs text-green-600">Member</div>
                          )}
                        </div>
                      </td>
                      <td className="py-2 px-3 text-gray-700">{volunteer.branch}</td>
                      <td className="py-2 px-3 text-gray-700">{volunteer.totalHours}h</td>
                      <td className="py-2 px-3">
                        <div className="text-gray-700">{volunteer.lastActiveMonth}</div>
                        {volunteer.monthsSinceActive > 0 && (
                          <div className="text-xs text-gray-500">
                            {volunteer.monthsSinceActive} month{volunteer.monthsSinceActive !== 1 ? 's' : ''} ago
                          </div>
                        )}
                      </td>
                      <td className="py-2 px-3">
                        <div className="space-y-1">
                          {volunteer.riskFactors.slice(0, 2).map((factor, i) => (
                            <div key={i} className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">
                              {factor}
                            </div>
                          ))}
                          {volunteer.riskFactors.length > 2 && (
                            <div className="text-xs text-gray-500">
                              +{volunteer.riskFactors.length - 2} more
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {results.totalFound > results.results.length && (
            <div className="mt-3 text-sm text-gray-600 text-center">
              Showing top {results.results.length} of {results.totalFound} results
            </div>
          )}

          <button
            onClick={() => setResults(null)}
            className="mt-4 text-sm text-gray-600 hover:text-gray-800 underline"
          >
            Clear results
          </button>
        </div>
      )}

      {/* Overall Stats */}
      {churnData.length > 0 && !results && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Churn Risk Overview</h3>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-lg font-semibold text-red-600">
                {churnData.filter(v => v.riskLevel === 'High').length}
              </div>
              <div className="text-xs text-gray-600">High Risk</div>
            </div>
            <div>
              <div className="text-lg font-semibold text-yellow-600">
                {churnData.filter(v => v.riskLevel === 'Medium').length}
              </div>
              <div className="text-xs text-gray-600">Medium Risk</div>
            </div>
            <div>
              <div className="text-lg font-semibold text-green-600">
                {churnData.filter(v => v.riskLevel === 'Low').length}
              </div>
              <div className="text-xs text-gray-600">Low Risk</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}