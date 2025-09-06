import React, { useState } from 'react';
import { X, Star, Heart, ThumbsUp, MessageCircle } from 'lucide-react';
import { SURVEY_PROMPTS, USER_PROMPTS, categorizeNPSScore } from '../../data/npsData';

export function NPSSurveyModal({ isOpen, onClose, volunteerData, onSubmit }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [surveyData, setSurveyData] = useState({
    npsScore: null,
    feedback: '',
    improvementAreas: [],
    recommendationText: '',
    wouldVolunteerAgain: null
  });

  const steps = [
    { id: 'nps', title: 'Rate Your Experience', icon: Star },
    { id: 'feedback', title: 'Share Your Thoughts', icon: MessageCircle },
    { id: 'improvements', title: 'Suggestions', icon: ThumbsUp },
    { id: 'future', title: 'Future Volunteering', icon: Heart }
  ];

  if (!isOpen) return null;

  const handleNPSSelect = (score) => {
    setSurveyData(prev => ({ ...prev, npsScore: score }));
  };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = () => {
    const submissionData = {
      ...surveyData,
      category: categorizeNPSScore(surveyData.npsScore),
      volunteerId: volunteerData?.assignee || 'anonymous',
      volunteerName: volunteerData?.assignee || 'Anonymous',
      branch: volunteerData?.branch || 'Unknown',
      projectName: volunteerData?.project || 'Unknown Project',
      eventDate: volunteerData?.date || new Date().toISOString().split('T')[0],
      surveyDate: new Date().toISOString().split('T')[0],
      isPostEvent: true,
      responseTime: Math.floor(Math.random() * 200) + 60 // Mock response time
    };
    
    onSubmit(submissionData);
    onClose();
  };

  const renderNPSStep = () => (
    <div className="text-center">
      <h3 className="text-xl font-semibold mb-4">{SURVEY_PROMPTS.npsQuestion}</h3>
      <div className="grid grid-cols-11 gap-2 mb-6">
        {[...Array(11)].map((_, i) => (
          <button
            key={i}
            onClick={() => handleNPSSelect(i)}
            className={`aspect-square rounded-lg border-2 font-medium transition-all ${
              surveyData.npsScore === i
                ? 'border-blue-500 bg-blue-500 text-white'
                : 'border-gray-300 hover:border-blue-300 hover:bg-blue-50'
            }`}
          >
            {i}
          </button>
        ))}
      </div>
      <div className="flex justify-between text-sm text-gray-600 mb-4">
        <span>Not likely at all</span>
        <span>Extremely likely</span>
      </div>
      {surveyData.npsScore !== null && (
        <div className="text-center">
          <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
            surveyData.npsScore >= 9 ? 'bg-green-100 text-green-800' :
            surveyData.npsScore >= 7 ? 'bg-yellow-100 text-yellow-800' :
            'bg-red-100 text-red-800'
          }`}>
            {categorizeNPSScore(surveyData.npsScore)}
          </span>
        </div>
      )}
    </div>
  );

  const renderFeedbackStep = () => (
    <div>
      <h3 className="text-xl font-semibold mb-4">{SURVEY_PROMPTS.feedbackPrompt}</h3>
      <textarea
        value={surveyData.feedback}
        onChange={(e) => setSurveyData(prev => ({ ...prev, feedback: e.target.value }))}
        placeholder="Tell us about your volunteer experience..."
        className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      />
    </div>
  );

  const renderImprovementsStep = () => {
    const commonImprovements = [
      'Better communication beforehand',
      'More volunteer orientation',
      'Clearer instructions',
      'Better organization',
      'Provide adequate materials',
      'More staff support'
    ];

    return (
      <div>
        <h3 className="text-xl font-semibold mb-4">{SURVEY_PROMPTS.improvementPrompt}</h3>
        <div className="grid grid-cols-2 gap-3 mb-4">
          {commonImprovements.map((improvement) => (
            <button
              key={improvement}
              onClick={() => {
                setSurveyData(prev => ({
                  ...prev,
                  improvementAreas: prev.improvementAreas.includes(improvement)
                    ? prev.improvementAreas.filter(i => i !== improvement)
                    : [...prev.improvementAreas, improvement]
                }));
              }}
              className={`p-3 text-sm rounded-lg border-2 transition-all ${
                surveyData.improvementAreas.includes(improvement)
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-300 hover:border-blue-300'
              }`}
            >
              {improvement}
            </button>
          ))}
        </div>
        <textarea
          value={surveyData.recommendationText}
          onChange={(e) => setSurveyData(prev => ({ ...prev, recommendationText: e.target.value }))}
          placeholder="Additional suggestions or recommendations..."
          className="w-full h-24 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
    );
  };

  const renderFutureStep = () => (
    <div className="text-center">
      <h3 className="text-xl font-semibold mb-6">{SURVEY_PROMPTS.volunteerAgainPrompt}</h3>
      <div className="flex justify-center gap-4">
        <button
          onClick={() => setSurveyData(prev => ({ ...prev, wouldVolunteerAgain: true }))}
          className={`px-6 py-3 rounded-lg border-2 font-medium transition-all ${
            surveyData.wouldVolunteerAgain === true
              ? 'border-green-500 bg-green-500 text-white'
              : 'border-gray-300 hover:border-green-300 hover:bg-green-50'
          }`}
        >
          Yes, I'd love to!
        </button>
        <button
          onClick={() => setSurveyData(prev => ({ ...prev, wouldVolunteerAgain: false }))}
          className={`px-6 py-3 rounded-lg border-2 font-medium transition-all ${
            surveyData.wouldVolunteerAgain === false
              ? 'border-red-500 bg-red-500 text-white'
              : 'border-gray-300 hover:border-red-300 hover:bg-red-50'
          }`}
        >
          Not at this time
        </button>
      </div>
    </div>
  );

  const renderStep = () => {
    switch (currentStep) {
      case 0: return renderNPSStep();
      case 1: return renderFeedbackStep();
      case 2: return renderImprovementsStep();
      case 3: return renderFutureStep();
      default: return renderNPSStep();
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 0: return surveyData.npsScore !== null;
      case 1: return true; // Optional
      case 2: return true; // Optional
      case 3: return surveyData.wouldVolunteerAgain !== null;
      default: return false;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-auto">
        <div className="p-6 border-b">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold">{USER_PROMPTS.postEvent.title}</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
          <p className="text-gray-600">{USER_PROMPTS.postEvent.subtitle}</p>
          
          {/* Progress bar */}
          <div className="flex items-center mt-6 gap-2">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center">
                <div className={`flex items-center justify-center w-8 h-8 rounded-full ${
                  index <= currentStep ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-500'
                }`}>
                  <step.icon className="w-4 h-4" />
                </div>
                {index < steps.length - 1 && (
                  <div className={`w-8 h-1 mx-1 ${
                    index < currentStep ? 'bg-blue-500' : 'bg-gray-200'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="p-6">
          {renderStep()}
        </div>

        <div className="p-6 border-t flex justify-between">
          <button
            onClick={handlePrev}
            disabled={currentStep === 0}
            className={`px-4 py-2 rounded-lg ${
              currentStep === 0
                ? 'text-gray-400 cursor-not-allowed'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            Previous
          </button>
          
          {currentStep < steps.length - 1 ? (
            <button
              onClick={handleNext}
              disabled={!canProceed()}
              className={`px-6 py-2 rounded-lg ${
                canProceed()
                  ? 'bg-blue-500 text-white hover:bg-blue-600'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              Next
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!canProceed()}
              className={`px-6 py-2 rounded-lg ${
                canProceed()
                  ? 'bg-green-500 text-white hover:bg-green-600'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              Submit Survey
            </button>
          )}
        </div>
      </div>
    </div>
  );
}