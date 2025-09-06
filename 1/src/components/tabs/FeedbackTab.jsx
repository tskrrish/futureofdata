import React, { useState, useEffect } from 'react';
import { MessageCircle, Plus, BarChart3, Users, Clock, AlertCircle } from 'lucide-react';
import { NPSSurveyModal } from '../surveys/NPSSurveyModal';
import { NPSAnalytics } from '../analytics/NPSAnalytics';
import { NPS_SURVEY_RESPONSES, calculateNPS, USER_PROMPTS } from '../../data/npsData';
import { exportCSV } from '../../utils/csvUtils';

export function FeedbackTab({ volunteerData = [] }) {
  const [surveyResponses, setSurveyResponses] = useState(NPS_SURVEY_RESPONSES);
  const [showSurveyModal, setShowSurveyModal] = useState(false);
  const [selectedVolunteer, setSelectedVolunteer] = useState(null);
  const [view, setView] = useState('analytics'); // 'analytics' or 'responses'
  
  // Simulate post-event trigger - show survey for recent volunteers
  const [postEventTriggers, setPostEventTriggers] = useState([]);
  
  useEffect(() => {
    // Simulate detecting recent completed volunteer activities
    const recentVolunteers = volunteerData.filter(volunteer => {
      const volunteerDate = new Date(volunteer.date);
      const daysSinceEvent = Math.floor((new Date() - volunteerDate) / (1000 * 60 * 60 * 24));
      return daysSinceEvent <= 2 && !surveyResponses.some(response => 
        response.volunteerName === volunteer.assignee && 
        response.projectName === volunteer.project
      );
    });
    
    setPostEventTriggers(recentVolunteers);
  }, [volunteerData, surveyResponses]);

  const handleSurveySubmit = (newResponse) => {
    const responseWithId = {
      ...newResponse,
      id: `nps-${Date.now()}`,
      surveyDate: new Date().toISOString().split('T')[0]
    };
    
    setSurveyResponses(prev => [...prev, responseWithId]);
    
    // Remove from post-event triggers
    setPostEventTriggers(prev => prev.filter(v => 
      !(v.assignee === newResponse.volunteerName && v.project === newResponse.projectName)
    ));
  };

  const handleTriggerSurvey = (volunteerInfo) => {
    setSelectedVolunteer(volunteerInfo);
    setShowSurveyModal(true);
  };

  const exportHandlers = {
    nps_categories: () => {
      const categoryData = surveyResponses.reduce((acc, response) => {
        acc[response.category] = (acc[response.category] || 0) + 1;
        return acc;
      }, {});
      exportCSV('nps_categories.csv', Object.entries(categoryData).map(([category, count]) => ({ category, count })));
    },
    branch_nps: () => {
      const branchData = surveyResponses.reduce((acc, response) => {
        if (!acc[response.branch]) {
          acc[response.branch] = [];
        }
        acc[response.branch].push(response);
        return acc;
      }, {});
      
      const branchNPSData = Object.entries(branchData).map(([branch, responses]) => ({
        branch,
        nps: calculateNPS(responses),
        responseCount: responses.length,
        avgScore: (responses.reduce((sum, r) => sum + r.npsScore, 0) / responses.length).toFixed(1)
      }));
      
      exportCSV('branch_nps.csv', branchNPSData);
    },
    nps_trend: () => {
      // Group by month
      const monthlyData = surveyResponses.reduce((acc, response) => {
        const month = new Date(response.surveyDate).toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
        if (!acc[month]) {
          acc[month] = [];
        }
        acc[month].push(response);
        return acc;
      }, {});
      
      const trendData = Object.entries(monthlyData).map(([month, responses]) => ({
        month,
        nps: calculateNPS(responses),
        responseCount: responses.length
      }));
      
      exportCSV('nps_trend.csv', trendData);
    },
    improvement_areas: () => {
      const improvements = surveyResponses.reduce((acc, response) => {
        response.improvementAreas.forEach(area => {
          acc[area] = (acc[area] || 0) + 1;
        });
        return acc;
      }, {});
      
      const improvementData = Object.entries(improvements).map(([area, mentions]) => ({ area, mentions }));
      exportCSV('improvement_areas.csv', improvementData);
    },
    recent_feedback: () => {
      exportCSV('all_survey_responses.csv', surveyResponses);
    }
  };


  return (
    <div className="bg-white rounded-2xl p-6 mt-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <MessageCircle className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h2 className="text-xl font-semibold">Post-Event Feedback Surveys</h2>
            <p className="text-sm text-gray-600">NPS tracking with analytics and user prompts</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setView(view === 'analytics' ? 'responses' : 'analytics')}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            {view === 'analytics' ? (
              <>
                <Users className="w-4 h-4" />
                View Responses
              </>
            ) : (
              <>
                <BarChart3 className="w-4 h-4" />
                View Analytics
              </>
            )}
          </button>
          <button
            onClick={() => setShowSurveyModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Test Survey
          </button>
        </div>
      </div>

      {/* Post-Event Triggers Alert */}
      {postEventTriggers.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-medium text-yellow-800 mb-2">
                Post-Event Survey Triggers ({postEventTriggers.length})
              </h3>
              <p className="text-sm text-yellow-700 mb-3">
                Recent volunteers ready for feedback collection:
              </p>
              <div className="grid gap-2">
                {postEventTriggers.slice(0, 3).map((volunteer, index) => (
                  <div key={index} className="flex items-center justify-between bg-white p-3 rounded border">
                    <div>
                      <p className="font-medium text-sm">{volunteer.assignee}</p>
                      <p className="text-xs text-gray-600">
                        {volunteer.project} • {volunteer.branch} • {volunteer.date}
                      </p>
                    </div>
                    <button
                      onClick={() => handleTriggerSurvey(volunteer)}
                      className="px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 transition-colors"
                    >
                      Send Survey
                    </button>
                  </div>
                ))}
              </div>
              {postEventTriggers.length > 3 && (
                <p className="text-sm text-yellow-600 mt-2">
                  +{postEventTriggers.length - 3} more volunteers pending survey
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {view === 'analytics' ? (
        <NPSAnalytics surveyResponses={surveyResponses} onExport={exportHandlers} />
      ) : (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">All Survey Responses</h3>
            <button
              onClick={() => exportCSV('all_survey_responses.csv', surveyResponses)}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Export All Responses
            </button>
          </div>
          
          <div className="grid gap-4">
            {surveyResponses.map((response) => (
              <div key={response.id} className="border rounded-lg p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium">{response.volunteerName}</h4>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        response.npsScore >= 9 ? 'bg-green-100 text-green-800' :
                        response.npsScore >= 7 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {response.npsScore}/10 • {response.category}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">
                      {response.projectName} • {response.branch} • {response.eventDate}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-500">Survey: {response.surveyDate}</p>
                    <div className="flex items-center gap-1 text-xs text-gray-400 mt-1">
                      <Clock className="w-3 h-3" />
                      {Math.floor(response.responseTime / 60)}m {response.responseTime % 60}s
                    </div>
                  </div>
                </div>
                
                {response.feedback && (
                  <div className="mb-3">
                    <p className="text-sm font-medium text-gray-700 mb-1">Feedback:</p>
                    <p className="text-sm text-gray-600 italic">"{response.feedback}"</p>
                  </div>
                )}
                
                {response.improvementAreas.length > 0 && (
                  <div className="mb-3">
                    <p className="text-sm font-medium text-gray-700 mb-1">Improvement Areas:</p>
                    <div className="flex flex-wrap gap-1">
                      {response.improvementAreas.map((area, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-red-50 text-red-700 text-xs rounded"
                        >
                          {area}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {response.recommendationText && (
                  <div className="mb-3">
                    <p className="text-sm font-medium text-gray-700 mb-1">Recommendations:</p>
                    <p className="text-sm text-gray-600">"{response.recommendationText}"</p>
                  </div>
                )}
                
                <div className="flex items-center justify-between pt-2 border-t">
                  <span className={`text-sm font-medium ${
                    response.wouldVolunteerAgain ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {response.wouldVolunteerAgain ? '✓ Would volunteer again' : '✗ Would not volunteer again'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Survey Modal */}
      <NPSSurveyModal
        isOpen={showSurveyModal}
        onClose={() => {
          setShowSurveyModal(false);
          setSelectedVolunteer(null);
        }}
        volunteerData={selectedVolunteer}
        onSubmit={handleSurveySubmit}
      />
    </div>
  );
}