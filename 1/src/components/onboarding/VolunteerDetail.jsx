import React, { useState } from 'react';
import { 
  ArrowLeft, 
  User, 
  Mail, 
  Phone, 
  MapPin, 
  Calendar,
  CheckCircle,
  Clock,
  AlertTriangle
} from 'lucide-react';
import StepTracker from './StepTracker';
import { ONBOARDING_STEPS } from '../../data/onboardingData';

const VolunteerDetail = ({ volunteer, onBack, onUpdateStep }) => {
  const [filter, setFilter] = useState('all');

  const getFilteredSteps = () => {
    const steps = ONBOARDING_STEPS.sort((a, b) => a.order - b.order);
    
    if (filter === 'completed') {
      return steps.filter(step => volunteer.steps[step.id]?.completed);
    }
    if (filter === 'pending') {
      return steps.filter(step => !volunteer.steps[step.id]?.completed);
    }
    if (filter === 'required') {
      return steps.filter(step => step.required);
    }
    return steps;
  };

  const getProgressStats = () => {
    const totalSteps = ONBOARDING_STEPS.length;
    const requiredSteps = ONBOARDING_STEPS.filter(step => step.required).length;
    const completedSteps = ONBOARDING_STEPS.filter(step => volunteer.steps[step.id]?.completed).length;
    const completedRequired = ONBOARDING_STEPS.filter(step => 
      step.required && volunteer.steps[step.id]?.completed
    ).length;

    return {
      totalSteps,
      requiredSteps,
      completedSteps,
      completedRequired,
      progressPercentage: Math.round((completedSteps / totalSteps) * 100),
      requiredProgressPercentage: Math.round((completedRequired / requiredSteps) * 100)
    };
  };

  const stats = getProgressStats();
  const filteredSteps = getFilteredSteps();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={onBack}
          className="p-2 hover:bg-gray-100 rounded-lg"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h2 className="text-2xl font-bold text-gray-900">{volunteer.name}</h2>
          <p className="text-gray-600">Onboarding Progress</p>
        </div>
      </div>

      {/* Volunteer Info Card */}
      <div className="bg-white p-6 rounded-xl border">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="flex items-center gap-3">
            <User className="w-5 h-5 text-gray-500" />
            <div>
              <p className="text-sm text-gray-600">Name</p>
              <p className="font-medium">{volunteer.name}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <Mail className="w-5 h-5 text-gray-500" />
            <div>
              <p className="text-sm text-gray-600">Email</p>
              <p className="font-medium">{volunteer.email}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <Phone className="w-5 h-5 text-gray-500" />
            <div>
              <p className="text-sm text-gray-600">Phone</p>
              <p className="font-medium">{volunteer.phone}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <MapPin className="w-5 h-5 text-gray-500" />
            <div>
              <p className="text-sm text-gray-600">Branch</p>
              <p className="font-medium">{volunteer.branch}</p>
            </div>
          </div>
        </div>

        <div className="mt-6 pt-6 border-t">
          <div className="flex items-center gap-3 mb-3">
            <Calendar className="w-5 h-5 text-gray-500" />
            <div>
              <p className="text-sm text-gray-600">Start Date</p>
              <p className="font-medium">{new Date(volunteer.startDate).toLocaleDateString()}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Progress Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-6 rounded-xl border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Overall Progress</h3>
            <CheckCircle className="w-5 h-5 text-blue-600" />
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Completed</span>
              <span>{stats.completedSteps} of {stats.totalSteps}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full" 
                style={{ width: `${stats.progressPercentage}%` }}
              />
            </div>
            <p className="text-lg font-bold text-blue-600">{stats.progressPercentage}%</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Required Steps</h3>
            <AlertTriangle className="w-5 h-5 text-red-600" />
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Completed</span>
              <span>{stats.completedRequired} of {stats.requiredSteps}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full ${
                  stats.requiredProgressPercentage === 100 ? 'bg-green-600' : 'bg-red-600'
                }`}
                style={{ width: `${stats.requiredProgressPercentage}%` }}
              />
            </div>
            <p className={`text-lg font-bold ${
              stats.requiredProgressPercentage === 100 ? 'text-green-600' : 'text-red-600'
            }`}>
              {stats.requiredProgressPercentage}%
            </p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Status</h3>
            {stats.requiredProgressPercentage === 100 ? (
              <CheckCircle className="w-5 h-5 text-green-600" />
            ) : (
              <Clock className="w-5 h-5 text-yellow-600" />
            )}
          </div>
          <p className={`text-lg font-bold ${
            stats.requiredProgressPercentage === 100 ? 'text-green-600' : 'text-yellow-600'
          }`}>
            {stats.requiredProgressPercentage === 100 ? 'Fully Onboarded' : 'In Progress'}
          </p>
          {stats.requiredProgressPercentage !== 100 && (
            <p className="text-sm text-gray-600 mt-1">
              {stats.requiredSteps - stats.completedRequired} required steps remaining
            </p>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-xl border">
        <div className="flex gap-2">
          {[
            ['all', 'All Steps'],
            ['pending', 'Pending'],
            ['completed', 'Completed'],
            ['required', 'Required Only']
          ].map(([value, label]) => (
            <button
              key={value}
              onClick={() => setFilter(value)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === value 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {label}
              {value !== 'all' && (
                <span className="ml-2 px-2 py-0.5 bg-white/20 rounded-full text-xs">
                  {value === 'pending' && ONBOARDING_STEPS.filter(step => !volunteer.steps[step.id]?.completed).length}
                  {value === 'completed' && stats.completedSteps}
                  {value === 'required' && stats.requiredSteps}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Onboarding Steps ({filteredSteps.length})
        </h3>
        
        {filteredSteps.length === 0 ? (
          <div className="bg-white p-8 rounded-xl border text-center">
            <p className="text-gray-500">No steps match the current filter.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredSteps.map((step) => (
              <StepTracker
                key={step.id}
                step={step}
                volunteerStep={volunteer.steps[step.id]}
                volunteer={volunteer}
                onUpdateStep={onUpdateStep}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default VolunteerDetail;