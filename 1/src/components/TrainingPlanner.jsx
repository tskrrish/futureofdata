import React, { useState } from 'react';
import { Calendar, Clock, DollarSign, MapPin, Users, AlertTriangle, CheckCircle, Target } from 'lucide-react';

const TrainingPlanner = ({ trainingRecommendations, organizationGaps, volunteers }) => {
  const [plannedTrainings, setPlannedTrainings] = useState([]);
  const [viewMode, setViewMode] = useState('recommendations'); // 'recommendations' or 'planned'

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case 'critical':
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      case 'high':
        return <Target className="w-4 h-4 text-orange-500" />;
      default:
        return <CheckCircle className="w-4 h-4 text-blue-500" />;
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical':
        return 'border-red-200 bg-red-50';
      case 'high':
        return 'border-orange-200 bg-orange-50';
      default:
        return 'border-blue-200 bg-blue-50';
    }
  };

  const getVolunteersNeedingTraining = (skillsAddressed) => {
    return volunteers.filter(volunteer => {
      return skillsAddressed.some(skillId => {
        const hasSkill = Object.values(volunteer.skillsByCategory).some(category => 
          category.skills.some(skill => skill.skillId === skillId)
        );
        if (!hasSkill) return true;
        
        // Check if they need to improve their proficiency
        const skillData = Object.values(volunteer.skillsByCategory)
          .flatMap(category => category.skills)
          .find(skill => skill.skillId === skillId);
        
        return skillData && (skillData.proficiency === 'beginner' || !skillData.certified);
      });
    });
  };

  const addToPlannedTrainings = (training) => {
    const volunteersNeeding = getVolunteersNeedingTraining(training.skillsAddressed);
    const plannedTraining = {
      ...training,
      id: `${training.id}-${Date.now()}`,
      plannedDate: new Date(training.nextAvailable).toISOString().split('T')[0],
      targetVolunteers: volunteersNeeding.slice(0, 12), // Limit to 12 volunteers per training
      estimatedCost: training.cost * Math.min(volunteersNeeding.length, 12),
      status: 'planned'
    };
    
    setPlannedTrainings(prev => [...prev, plannedTraining]);
  };

  const removeFromPlanned = (trainingId) => {
    setPlannedTrainings(prev => prev.filter(t => t.id !== trainingId));
  };

  const getTotalPlannedCost = () => {
    return plannedTrainings.reduce((total, training) => total + training.estimatedCost, 0);
  };

  const TrainingCard = ({ training, isPlanned = false, onAction }) => {
    const volunteersNeeding = getVolunteersNeedingTraining(training.skillsAddressed);
    const impactedSkills = organizationGaps.filter(skill => 
      training.skillsAddressed.includes(skill.id)
    );

    return (
      <div className={`border rounded-lg p-4 ${getPriorityColor(training.priority)}`}>
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-start gap-2">
            {getPriorityIcon(training.priority)}
            <div>
              <h4 className="font-semibold text-gray-900">{training.name}</h4>
              <p className="text-sm text-gray-600">{training.description}</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm font-medium text-gray-900">${training.cost}</div>
            {isPlanned && (
              <div className="text-xs text-gray-500">
                Est. Total: ${training.estimatedCost}
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
          <div className="flex items-center gap-1 text-gray-600">
            <Clock className="w-4 h-4" />
            <span>{training.duration}</span>
          </div>
          <div className="flex items-center gap-1 text-gray-600">
            <MapPin className="w-4 h-4" />
            <span>{training.format}</span>
          </div>
          <div className="flex items-center gap-1 text-gray-600">
            <Calendar className="w-4 h-4" />
            <span>{isPlanned ? training.plannedDate : training.nextAvailable}</span>
          </div>
          <div className="flex items-center gap-1 text-gray-600">
            <Users className="w-4 h-4" />
            <span>
              {isPlanned ? training.targetVolunteers.length : Math.min(volunteersNeeding.length, 12)} volunteers
            </span>
          </div>
        </div>

        <div className="mb-4">
          <div className="text-xs font-medium text-gray-600 mb-2">Skills Addressed:</div>
          <div className="flex flex-wrap gap-1">
            {impactedSkills.map(skill => (
              <span
                key={skill.id}
                className={`px-2 py-1 rounded-full text-xs font-medium ${
                  skill.gapSeverity === 'critical' ? 'bg-red-100 text-red-700' :
                  skill.gapSeverity === 'high' ? 'bg-orange-100 text-orange-700' :
                  'bg-blue-100 text-blue-700'
                }`}
              >
                {skill.name}
              </span>
            ))}
          </div>
        </div>

        <div className="flex justify-between items-center">
          <div className="text-xs text-gray-500">
            Provider: {training.provider}
          </div>
          <button
            onClick={() => onAction(training)}
            className={`px-4 py-2 rounded-md text-sm font-medium ${
              isPlanned 
                ? 'bg-red-100 text-red-700 hover:bg-red-200'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {isPlanned ? 'Remove' : 'Plan Training'}
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header with toggle */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Training Planner</h2>
        <div className="flex bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setViewMode('recommendations')}
            className={`px-4 py-2 rounded text-sm font-medium ${
              viewMode === 'recommendations' 
                ? 'bg-white text-gray-900 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Recommendations ({trainingRecommendations.length})
          </button>
          <button
            onClick={() => setViewMode('planned')}
            className={`px-4 py-2 rounded text-sm font-medium ${
              viewMode === 'planned' 
                ? 'bg-white text-gray-900 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Planned ({plannedTrainings.length})
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      {viewMode === 'planned' && plannedTrainings.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <div className="text-lg font-semibold text-blue-900">{plannedTrainings.length}</div>
              <div className="text-sm text-blue-600">Planned Trainings</div>
            </div>
            <div>
              <div className="text-lg font-semibold text-blue-900">
                {plannedTrainings.reduce((sum, t) => sum + t.targetVolunteers.length, 0)}
              </div>
              <div className="text-sm text-blue-600">Total Volunteers</div>
            </div>
            <div>
              <div className="text-lg font-semibold text-blue-900">${getTotalPlannedCost().toLocaleString()}</div>
              <div className="text-sm text-blue-600">Estimated Cost</div>
            </div>
          </div>
        </div>
      )}

      {/* Training Cards */}
      <div className="grid gap-4">
        {viewMode === 'recommendations' ? (
          trainingRecommendations.length > 0 ? (
            trainingRecommendations.map(training => (
              <TrainingCard
                key={training.id}
                training={training}
                onAction={addToPlannedTrainings}
              />
            ))
          ) : (
            <div className="text-center py-8 text-gray-500">
              <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-500" />
              <p>No training recommendations at this time.</p>
              <p className="text-sm">Your team's skills coverage looks good!</p>
            </div>
          )
        ) : (
          plannedTrainings.length > 0 ? (
            plannedTrainings.map(training => (
              <TrainingCard
                key={training.id}
                training={training}
                isPlanned={true}
                onAction={removeFromPlanned}
              />
            ))
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Calendar className="w-12 h-12 mx-auto mb-3" />
              <p>No trainings planned yet.</p>
              <p className="text-sm">Add trainings from the recommendations tab.</p>
            </div>
          )
        )}
      </div>
    </div>
  );
};

export default TrainingPlanner;