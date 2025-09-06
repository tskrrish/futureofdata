import { useMemo } from 'react';
import { ONBOARDING_STEPS, getVolunteerProgress, getStepsByCategory } from '../data/onboardingData';

export const useOnboardingData = (volunteers, branchFilter = 'All', searchQuery = '') => {
  const filteredVolunteers = useMemo(() => {
    return volunteers.filter(volunteer => {
      const matchesBranch = branchFilter === 'All' || volunteer.branch === branchFilter;
      const matchesSearch = searchQuery === '' || 
        volunteer.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        volunteer.email.toLowerCase().includes(searchQuery.toLowerCase());
      
      return matchesBranch && matchesSearch;
    });
  }, [volunteers, branchFilter, searchQuery]);

  const volunteerProgressData = useMemo(() => {
    return filteredVolunteers.map(volunteer => ({
      ...volunteer,
      progress: getVolunteerProgress(volunteer)
    }));
  }, [filteredVolunteers]);

  const overallStats = useMemo(() => {
    const totalVolunteers = volunteerProgressData.length;
    const fullyOnboarded = volunteerProgressData.filter(v => v.progress.isFullyOnboarded).length;
    const inProgress = totalVolunteers - fullyOnboarded;
    
    const avgProgress = totalVolunteers > 0 
      ? volunteerProgressData.reduce((sum, v) => sum + v.progress.progressPercentage, 0) / totalVolunteers
      : 0;

    return {
      totalVolunteers,
      fullyOnboarded,
      inProgress,
      avgProgress: Math.round(avgProgress)
    };
  }, [volunteerProgressData]);

  const stepStats = useMemo(() => {
    const stats = {};
    
    ONBOARDING_STEPS.forEach(step => {
      const completed = volunteerProgressData.filter(v => 
        v.steps[step.id]?.completed
      ).length;
      
      const pending = volunteerProgressData.length - completed;
      
      stats[step.id] = {
        ...step,
        completed,
        pending,
        completionRate: volunteerProgressData.length > 0 
          ? Math.round((completed / volunteerProgressData.length) * 100)
          : 0
      };
    });
    
    return stats;
  }, [volunteerProgressData]);

  const categoryStats = useMemo(() => {
    const categories = getStepsByCategory();
    const stats = {};
    
    Object.keys(categories).forEach(categoryName => {
      const categorySteps = categories[categoryName];
      let totalCompleted = 0;
      let totalPossible = 0;
      
      categorySteps.forEach(step => {
        totalCompleted += volunteerProgressData.filter(v => 
          v.steps[step.id]?.completed
        ).length;
        totalPossible += volunteerProgressData.length;
      });
      
      stats[categoryName] = {
        name: categoryName,
        steps: categorySteps.length,
        completed: totalCompleted,
        total: totalPossible,
        completionRate: totalPossible > 0 ? Math.round((totalCompleted / totalPossible) * 100) : 0
      };
    });
    
    return stats;
  }, [volunteerProgressData]);

  const recentActivity = useMemo(() => {
    const activities = [];
    
    volunteerProgressData.forEach(volunteer => {
      Object.keys(volunteer.steps).forEach(stepId => {
        const step = volunteer.steps[stepId];
        if (step.completed && step.completedDate) {
          const stepInfo = ONBOARDING_STEPS.find(s => s.id === stepId);
          activities.push({
            id: `${volunteer.id}-${stepId}`,
            volunteerId: volunteer.id,
            volunteerName: volunteer.name,
            stepId,
            stepTitle: stepInfo?.title || stepId,
            completedDate: step.completedDate,
            completedBy: step.completedBy,
            category: stepInfo?.category || 'other'
          });
        }
      });
    });
    
    return activities
      .sort((a, b) => new Date(b.completedDate) - new Date(a.completedDate))
      .slice(0, 20);
  }, [volunteerProgressData]);

  const upcomingTasks = useMemo(() => {
    const tasks = [];
    
    volunteerProgressData.forEach(volunteer => {
      ONBOARDING_STEPS
        .filter(step => !volunteer.steps[step.id]?.completed)
        .forEach(step => {
          tasks.push({
            id: `${volunteer.id}-${step.id}`,
            volunteerId: volunteer.id,
            volunteerName: volunteer.name,
            stepId: step.id,
            stepTitle: step.title,
            stepDescription: step.description,
            category: step.category,
            required: step.required,
            priority: step.required ? 'high' : 'medium',
            branch: volunteer.branch
          });
        });
    });
    
    return tasks.sort((a, b) => {
      if (a.required && !b.required) return -1;
      if (!a.required && b.required) return 1;
      return a.stepTitle.localeCompare(b.stepTitle);
    });
  }, [volunteerProgressData]);

  return {
    volunteers: volunteerProgressData,
    overallStats,
    stepStats,
    categoryStats,
    recentActivity,
    upcomingTasks,
    onboardingSteps: ONBOARDING_STEPS
  };
};