import React, { useState } from 'react';
import { Target, TrendingUp, Users, BookOpen, BarChart3, Settings } from 'lucide-react';
import { useSkillsMatrix } from '../../hooks/useSkillsMatrix';
import SkillsHeatmapChart from '../charts/SkillsHeatmapChart';
import SkillsGapChart from '../charts/SkillsGapChart';
import SkillsCategoryChart from '../charts/SkillsCategoryChart';
import TrainingPlanner from '../TrainingPlanner';
import SkillsManager from '../SkillsManager';

const SkillsMatrixTab = ({ volunteerData }) => {
  const [activeSubTab, setActiveSubTab] = useState('overview');
  const [selectedVolunteer, setSelectedVolunteer] = useState(null);
  
  const {
    volunteers,
    organizationGaps,
    categoryStats,
    trainingRecommendations,
    totalSkills,
    totalVolunteers
  } = useSkillsMatrix(volunteerData);

  const subTabs = [
    { id: 'overview', label: 'Overview', icon: <BarChart3 className="w-4 h-4" /> },
    { id: 'heatmap', label: 'Skills Matrix', icon: <Target className="w-4 h-4" /> },
    { id: 'gaps', label: 'Gap Analysis', icon: <TrendingUp className="w-4 h-4" /> },
    { id: 'training', label: 'Training Planner', icon: <BookOpen className="w-4 h-4" /> },
    { id: 'manage', label: 'Manage Skills', icon: <Settings className="w-4 h-4" /> }
  ];

  const criticalGaps = organizationGaps.filter(skill => skill.gapSeverity === 'critical').length;
  const highPriorityTrainings = trainingRecommendations.filter(t => t.priority === 'critical').length;
  const averageSkillsPerVolunteer = volunteers.length > 0 
    ? volunteers.reduce((sum, v) => sum + v.totalSkills, 0) / volunteers.length 
    : 0;

  const OverviewTab = () => (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Users className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">{totalVolunteers}</div>
              <div className="text-sm text-gray-600">Total Volunteers</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Target className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">{totalSkills}</div>
              <div className="text-sm text-gray-600">Available Skills</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <TrendingUp className="w-6 h-6 text-red-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">{criticalGaps}</div>
              <div className="text-sm text-gray-600">Critical Gaps</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <BookOpen className="w-6 h-6 text-orange-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">{highPriorityTrainings}</div>
              <div className="text-sm text-gray-600">Priority Trainings</div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SkillsCategoryChart categoryStats={categoryStats} viewMode="coverage" />
        <SkillsCategoryChart categoryStats={categoryStats} viewMode="gaps" />
      </div>

      {/* Summary Stats */}
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold mb-4">Skills Coverage Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <div className="text-3xl font-bold text-blue-600 mb-1">
              {averageSkillsPerVolunteer.toFixed(1)}
            </div>
            <div className="text-sm text-gray-600">Avg Skills per Volunteer</div>
            <div className="text-xs text-gray-500 mt-1">
              Range: {Math.min(...volunteers.map(v => v.totalSkills))} - {Math.max(...volunteers.map(v => v.totalSkills))}
            </div>
          </div>
          
          <div>
            <div className="text-3xl font-bold text-green-600 mb-1">
              {Math.round(categoryStats.reduce((sum, cat) => sum + cat.averageCoverage, 0) / categoryStats.length)}%
            </div>
            <div className="text-sm text-gray-600">Avg Category Coverage</div>
            <div className="text-xs text-gray-500 mt-1">
              Across all skill categories
            </div>
          </div>

          <div>
            <div className="text-3xl font-bold text-purple-600 mb-1">
              {organizationGaps.filter(skill => ['critical', 'high'].includes(skill.gapSeverity)).length}
            </div>
            <div className="text-sm text-gray-600">High Priority Gaps</div>
            <div className="text-xs text-gray-500 mt-1">
              Requiring immediate attention
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Sub-navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {subTabs.map(subTab => (
            <button
              key={subTab.id}
              onClick={() => setActiveSubTab(subTab.id)}
              className={`flex items-center gap-2 py-2 px-1 border-b-2 font-medium text-sm ${
                activeSubTab === subTab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {subTab.icon}
              {subTab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-[500px]">
        {activeSubTab === 'overview' && <OverviewTab />}
        
        {activeSubTab === 'heatmap' && (
          <SkillsHeatmapChart 
            volunteers={volunteers}
            onVolunteerClick={setSelectedVolunteer}
          />
        )}
        
        {activeSubTab === 'gaps' && (
          <SkillsGapChart organizationGaps={organizationGaps} />
        )}
        
        {activeSubTab === 'training' && (
          <TrainingPlanner
            trainingRecommendations={trainingRecommendations}
            organizationGaps={organizationGaps}
            volunteers={volunteers}
          />
        )}
        
        {activeSubTab === 'manage' && (
          <SkillsManager
            volunteers={volunteers}
            onUpdateVolunteerSkills={(volunteerId, skills) => {
              // This would integrate with your data management system
              console.log('Update volunteer skills:', volunteerId, skills);
            }}
          />
        )}
      </div>

      {/* Volunteer Detail Modal */}
      {selectedVolunteer && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold">{selectedVolunteer.name}</h3>
              <button
                onClick={() => setSelectedVolunteer(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div>
                <div className="text-sm text-gray-600">Branch</div>
                <div className="font-medium">{selectedVolunteer.branch}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Total Hours</div>
                <div className="font-medium">{selectedVolunteer.totalHours.toFixed(1)}h</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Total Skills</div>
                <div className="font-medium">{selectedVolunteer.totalSkills}</div>
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="font-semibold">Skills by Category</h4>
              {Object.entries(selectedVolunteer.skillsByCategory).map(([category, data]) => (
                <div key={category} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h5 className="font-medium">{category}</h5>
                    <span className="text-sm text-gray-600">
                      {data.covered}/{data.total} ({Math.round(data.coverage)}%)
                    </span>
                  </div>
                  {data.skills.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {data.skills.map(skill => (
                        <span
                          key={skill.skillId}
                          className={`px-2 py-1 rounded text-xs ${
                            skill.proficiency === 'expert' 
                              ? 'bg-green-100 text-green-800'
                              : skill.proficiency === 'proficient'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-yellow-100 text-yellow-800'
                          }`}
                        >
                          {skill.name} ({skill.proficiency})
                          {skill.certified && ' ✓'}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SkillsMatrixTab;