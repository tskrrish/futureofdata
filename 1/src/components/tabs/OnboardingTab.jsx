import React, { useState } from 'react';
import { 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  Users, 
  FileSignature, 
  GraduationCap, 
  Shield,
  User,
  ChevronDown,
  ChevronRight,
  Calendar,
  Download,
  Eye
} from 'lucide-react';
import VolunteerDetail from '../onboarding/VolunteerDetail';

const OnboardingTab = ({ 
  volunteers, 
  overallStats, 
  stepStats, 
  categoryStats, 
  recentActivity, 
  upcomingTasks,
  onUpdateVolunteerStep,
  onExportProgress
}) => {
  const [selectedView, setSelectedView] = useState('overview');
  const [expandedVolunteer, setExpandedVolunteer] = useState(null);
  const [selectedVolunteer, setSelectedVolunteer] = useState(null);

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'basic': return <User className="w-4 h-4" />;
      case 'verification': return <Shield className="w-4 h-4" />;
      case 'signature': return <FileSignature className="w-4 h-4" />;
      case 'training': return <GraduationCap className="w-4 h-4" />;
      default: return <AlertCircle className="w-4 h-4" />;
    }
  };

  const getCategoryColor = (category) => {
    switch (category) {
      case 'basic': return 'bg-blue-100 text-blue-800';
      case 'verification': return 'bg-red-100 text-red-800';
      case 'signature': return 'bg-purple-100 text-purple-800';
      case 'training': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (isCompleted, isRequired) => {
    if (isCompleted) return 'text-green-600';
    if (isRequired) return 'text-red-600';
    return 'text-yellow-600';
  };

  const handleUpdateStep = (volunteerId, stepId, stepData) => {
    if (onUpdateVolunteerStep) {
      onUpdateVolunteerStep(volunteerId, stepId, stepData);
    }
  };

  if (selectedVolunteer) {
    return (
      <VolunteerDetail
        volunteer={selectedVolunteer}
        onBack={() => setSelectedVolunteer(null)}
        onUpdateStep={handleUpdateStep}
      />
    );
  }

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-xl border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Volunteers</p>
              <p className="text-3xl font-bold text-gray-900">{overallStats.totalVolunteers}</p>
            </div>
            <Users className="w-8 h-8 text-blue-600" />
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-xl border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Fully Onboarded</p>
              <p className="text-3xl font-bold text-green-600">{overallStats.fullyOnboarded}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-xl border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">In Progress</p>
              <p className="text-3xl font-bold text-yellow-600">{overallStats.inProgress}</p>
            </div>
            <Clock className="w-8 h-8 text-yellow-600" />
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-xl border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Progress</p>
              <p className="text-3xl font-bold text-blue-600">{overallStats.avgProgress}%</p>
            </div>
            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
              <span className="text-blue-600 text-xs font-bold">%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Category Breakdown */}
      <div className="bg-white p-6 rounded-xl border">
        <h3 className="text-lg font-semibold mb-4">Completion by Category</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.values(categoryStats).map((category) => (
            <div key={category.name} className="p-4 border rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                {getCategoryIcon(category.name)}
                <span className="font-medium capitalize">{category.name}</span>
              </div>
              <div className="text-2xl font-bold mb-1">{category.completionRate}%</div>
              <div className="text-sm text-gray-600">
                {category.completed} of {category.total} completed
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full" 
                  style={{ width: `${category.completionRate}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white p-6 rounded-xl border">
        <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
        <div className="space-y-3 max-h-64 overflow-y-auto">
          {recentActivity.slice(0, 10).map((activity) => (
            <div key={activity.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <div className={`p-1.5 rounded-full ${getCategoryColor(activity.category)}`}>
                {getCategoryIcon(activity.category)}
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">{activity.volunteerName}</p>
                <p className="text-xs text-gray-600">completed {activity.stepTitle}</p>
              </div>
              <div className="text-xs text-gray-500 flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                {new Date(activity.completedDate).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderVolunteerList = () => (
    <div className="bg-white rounded-xl border">
      <div className="p-6 border-b">
        <h3 className="text-lg font-semibold">Volunteer Progress</h3>
      </div>
      <div className="divide-y max-h-96 overflow-y-auto">
        {volunteers.map((volunteer) => (
          <div key={volunteer.id} className="p-4">
            <div 
              className="flex items-center justify-between cursor-pointer"
              onClick={() => setExpandedVolunteer(
                expandedVolunteer === volunteer.id ? null : volunteer.id
              )}
            >
              <div className="flex items-center gap-3">
                {expandedVolunteer === volunteer.id ? 
                  <ChevronDown className="w-4 h-4" /> : 
                  <ChevronRight className="w-4 h-4" />
                }
                <div>
                  <p className="font-medium">{volunteer.name}</p>
                  <p className="text-sm text-gray-600">{volunteer.branch}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <p className="text-sm font-medium">
                    {volunteer.progress.requiredComplete}/{volunteer.progress.requiredTotal} Required
                  </p>
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        volunteer.progress.isFullyOnboarded ? 'bg-green-600' : 'bg-blue-600'
                      }`}
                      style={{ width: `${volunteer.progress.progressPercentage}%` }}
                    />
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedVolunteer(volunteer);
                  }}
                  className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                  title="View Details"
                >
                  <Eye className="w-4 h-4" />
                </button>
                {volunteer.progress.isFullyOnboarded && 
                  <CheckCircle className="w-5 h-5 text-green-600" />
                }
              </div>
            </div>
            
            {expandedVolunteer === volunteer.id && (
              <div className="mt-4 ml-7 space-y-2">
                {Object.entries(volunteer.steps).map(([stepId, stepData]) => {
                  const stepInfo = stepStats[stepId];
                  if (!stepInfo) return null;
                  
                  return (
                    <div 
                      key={stepId} 
                      className="flex items-center justify-between p-2 bg-gray-50 rounded"
                    >
                      <div className="flex items-center gap-2">
                        <div className={`p-1 rounded-full ${getCategoryColor(stepInfo.category)}`}>
                          {getCategoryIcon(stepInfo.category)}
                        </div>
                        <span className="text-sm">{stepInfo.title}</span>
                        {stepInfo.required && (
                          <span className="text-xs bg-red-100 text-red-800 px-1.5 py-0.5 rounded-full">
                            Required
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        {stepData.completed ? (
                          <>
                            <CheckCircle className="w-4 h-4 text-green-600" />
                            <span className="text-xs text-gray-600">
                              {new Date(stepData.completedDate).toLocaleDateString()}
                            </span>
                          </>
                        ) : (
                          <Clock className={`w-4 h-4 ${getStatusColor(false, stepInfo.required)}`} />
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  const renderTasks = () => (
    <div className="bg-white rounded-xl border">
      <div className="p-6 border-b">
        <h3 className="text-lg font-semibold">Upcoming Tasks</h3>
        <p className="text-sm text-gray-600 mt-1">
          {upcomingTasks.filter(t => t.required).length} required tasks, {upcomingTasks.filter(t => !t.required).length} optional
        </p>
      </div>
      <div className="divide-y max-h-96 overflow-y-auto">
        {upcomingTasks.slice(0, 50).map((task) => (
          <div key={task.id} className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`p-1.5 rounded-full ${getCategoryColor(task.category)}`}>
                {getCategoryIcon(task.category)}
              </div>
              <div>
                <p className="font-medium text-sm">{task.volunteerName}</p>
                <p className="text-sm text-gray-600">{task.stepTitle}</p>
                <p className="text-xs text-gray-500">{task.branch}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {task.required && (
                <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded-full">
                  Required
                </span>
              )}
              <span className={`px-2 py-1 rounded-full text-xs ${
                task.priority === 'high' 
                  ? 'bg-red-100 text-red-800' 
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {task.priority}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="mt-6 space-y-6">
      {/* Tab Navigation */}
      <div className="flex justify-between items-center border-b">
        <div className="flex gap-4">
          {[
            ['overview', 'Overview'],
            ['volunteers', 'Volunteers'],
            ['tasks', 'Tasks']
          ].map(([id, label]) => (
            <button
              key={id}
              className={`pb-2 px-1 font-medium text-sm border-b-2 ${
                selectedView === id 
                  ? 'border-blue-600 text-blue-600' 
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
              onClick={() => setSelectedView(id)}
            >
              {label}
            </button>
          ))}
        </div>
        
        {onExportProgress && (
          <button
            onClick={onExportProgress}
            className="flex items-center gap-2 px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded-lg"
          >
            <Download className="w-4 h-4" />
            Export Progress
          </button>
        )}
      </div>

      {/* Content */}
      {selectedView === 'overview' && renderOverview()}
      {selectedView === 'volunteers' && renderVolunteerList()}
      {selectedView === 'tasks' && renderTasks()}
    </div>
  );
};

export default OnboardingTab;