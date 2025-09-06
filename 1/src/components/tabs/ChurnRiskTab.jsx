import React from "react";
import { NaturalLanguageQuery } from "../NaturalLanguageQuery";

export function ChurnRiskTab({ data }) {
  return (
    <div className="py-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Churn Risk Analysis</h2>
        <p className="text-gray-600">
          Use natural language to analyze volunteer churn risk patterns and identify at-risk volunteers.
        </p>
      </div>
      
      <NaturalLanguageQuery data={data} />
      
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
        <h3 className="font-medium text-blue-900 mb-2">How to use Natural Language Queries:</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Ask about specific branches: "Who's at churn risk in Blue Ash?"</li>
          <li>• Filter by risk level: "Show me high risk volunteers"</li>
          <li>• Find inactive volunteers: "Which volunteers are inactive?"</li>
          <li>• Identify declining engagement: "Who has declining engagement?"</li>
          <li>• Discover new volunteers: "Show new volunteers at Campbell County"</li>
        </ul>
      </div>
    </div>
  );
}