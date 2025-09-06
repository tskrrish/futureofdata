import { useState, useEffect, useCallback } from 'react';
import { NPS_SURVEY_RESPONSES, calculateNPS, categorizeNPSScore } from '../data/npsData';

export function useNPSSurvey(volunteerData = []) {
  const [surveyResponses, setSurveyResponses] = useState(NPS_SURVEY_RESPONSES);
  const [postEventTriggers, setPostEventTriggers] = useState([]);

  // Detect volunteers who completed activities in the last 1-3 days and haven't been surveyed
  const detectPostEventTriggers = useCallback(() => {
    const triggers = volunteerData.filter(volunteer => {
      const volunteerDate = new Date(volunteer.date);
      const now = new Date();
      const daysSinceEvent = Math.floor((now - volunteerDate) / (1000 * 60 * 60 * 24));
      
      // Trigger surveys 1-3 days after volunteer activity
      const isInTriggerWindow = daysSinceEvent >= 1 && daysSinceEvent <= 3;
      
      // Check if volunteer hasn't been surveyed for this specific activity
      const hasNotBeenSurveyed = !surveyResponses.some(response => 
        response.volunteerName === volunteer.assignee && 
        response.projectName === volunteer.project &&
        response.eventDate === volunteer.date
      );
      
      return isInTriggerWindow && hasNotBeenSurveyed;
    });
    
    setPostEventTriggers(triggers);
  }, [volunteerData, surveyResponses]);

  useEffect(() => {
    detectPostEventTriggers();
  }, [detectPostEventTriggers]);

  // Add a new survey response
  const addSurveyResponse = useCallback((responseData) => {
    const newResponse = {
      ...responseData,
      id: `nps-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      category: categorizeNPSScore(responseData.npsScore),
      surveyDate: new Date().toISOString().split('T')[0],
      responseTime: responseData.responseTime || Math.floor(Math.random() * 180) + 60,
      isPostEvent: true
    };
    
    setSurveyResponses(prev => [...prev, newResponse]);
    
    // Remove from post-event triggers if this was triggered
    setPostEventTriggers(prev => prev.filter(trigger => 
      !(trigger.assignee === responseData.volunteerName && 
        trigger.project === responseData.projectName &&
        trigger.date === responseData.eventDate)
    ));
    
    return newResponse;
  }, []);

  // Calculate analytics
  const analytics = {
    overallNPS: calculateNPS(surveyResponses),
    totalResponses: surveyResponses.length,
    responseRate: volunteerData.length > 0 ? 
      Math.round((surveyResponses.length / volunteerData.length) * 100) : 0,
    
    // Category breakdown
    categoryBreakdown: {
      promoters: surveyResponses.filter(r => r.npsScore >= 9).length,
      passives: surveyResponses.filter(r => r.npsScore >= 7 && r.npsScore <= 8).length,
      detractors: surveyResponses.filter(r => r.npsScore <= 6).length
    },
    
    // Branch performance
    branchPerformance: surveyResponses.reduce((acc, response) => {
      if (!acc[response.branch]) {
        acc[response.branch] = [];
      }
      acc[response.branch].push(response);
      return acc;
    }, {}),
    
    // Volunteer retention indicator
    volunteerRetentionRate: surveyResponses.length > 0 ? 
      Math.round((surveyResponses.filter(r => r.wouldVolunteerAgain).length / surveyResponses.length) * 100) : 0,
    
    // Average response time
    avgResponseTime: surveyResponses.length > 0 ?
      Math.round(surveyResponses.reduce((sum, r) => sum + r.responseTime, 0) / surveyResponses.length) : 0,
    
    // Common improvement areas
    improvementAreas: surveyResponses.reduce((acc, response) => {
      response.improvementAreas.forEach(area => {
        acc[area] = (acc[area] || 0) + 1;
      });
      return acc;
    }, {}),
    
    // Recent feedback (last 5)
    recentFeedback: surveyResponses
      .sort((a, b) => new Date(b.surveyDate) - new Date(a.surveyDate))
      .slice(0, 5)
  };

  // Send automated survey prompt (simulation)
  const sendSurveyPrompt = useCallback((volunteerInfo, promptType = 'postEvent') => {
    console.log(`Sending ${promptType} survey prompt to:`, volunteerInfo);
    
    // In a real implementation, this would:
    // - Send an email/SMS to the volunteer
    // - Create a notification in the system
    // - Log the prompt attempt
    
    return {
      success: true,
      message: `Survey prompt sent to ${volunteerInfo.assignee}`,
      promptType,
      volunteerInfo
    };
  }, []);

  // Bulk send surveys to all pending triggers
  const sendBulkSurveyPrompts = useCallback(() => {
    const results = postEventTriggers.map(trigger => sendSurveyPrompt(trigger));
    
    console.log(`Sent ${results.length} survey prompts`);
    return results;
  }, [postEventTriggers, sendSurveyPrompt]);

  return {
    surveyResponses,
    postEventTriggers,
    analytics,
    addSurveyResponse,
    sendSurveyPrompt,
    sendBulkSurveyPrompts,
    detectPostEventTriggers
  };
}