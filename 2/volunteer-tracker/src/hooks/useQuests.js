import { useState, useEffect, useMemo } from 'react';
import { 
  QUESTS_CONFIG, 
  QUEST_STATUS, 
  getAvailableQuests, 
  calculateQuestProgress, 
  isQuestExpired 
} from '../constants.js';

export function useQuests(volunteerData) {
  const [activeQuests, setActiveQuests] = useState({});
  const [completedQuests, setCompletedQuests] = useState([]);
  const [questProgress, setQuestProgress] = useState({});

  const totalHours = volunteerData?.hours_total ? Number(volunteerData.hours_total) : 0;
  const storyworldHours = volunteerData?.storyworld_hours || {};

  const mockUserProgress = useMemo(() => {
    if (!volunteerData) return {};
    
    return {
      hours_milestone: totalHours,
      time_bounded: 0, // Would track weekend/time-specific hours
      streak: 0, // Would track consecutive days
      storyworld_focus: storyworldHours,
      community_challenge: 0 // Would track recruitment referrals
    };
  }, [totalHours, storyworldHours]);

  const availableQuests = useMemo(() => {
    if (!volunteerData) return [];
    return getAvailableQuests(totalHours, completedQuests);
  }, [totalHours, completedQuests, volunteerData]);

  const processedQuests = useMemo(() => {
    return availableQuests.map(quest => {
      const isActive = activeQuests[quest.id];
      const isCompleted = completedQuests.includes(quest.id);
      const progress = calculateQuestProgress(quest, mockUserProgress);
      const isExpired = isActive ? isQuestExpired(quest, activeQuests[quest.id]?.startTime) : false;

      let status = QUEST_STATUS.LOCKED;
      if (isCompleted) {
        status = QUEST_STATUS.COMPLETED;
      } else if (isExpired) {
        status = QUEST_STATUS.EXPIRED;
      } else if (isActive || totalHours >= quest.unlockCondition.minHours) {
        status = QUEST_STATUS.ACTIVE;
      }

      const progressPercentage = (progress / quest.target) * 100;
      const canComplete = progress >= quest.target && status === QUEST_STATUS.ACTIVE;

      return {
        ...quest,
        status,
        progress,
        progressPercentage,
        canComplete,
        timeRemaining: quest.timeLimit && isActive ? 
          Math.max(0, quest.timeLimit - (Date.now() - activeQuests[quest.id]?.startTime)) : 
          quest.timeLimit,
        startTime: isActive ? activeQuests[quest.id]?.startTime : null
      };
    });
  }, [availableQuests, activeQuests, completedQuests, mockUserProgress, totalHours]);

  const startQuest = (questId) => {
    const quest = QUESTS_CONFIG.find(q => q.id === questId);
    if (!quest) return;

    setActiveQuests(prev => ({
      ...prev,
      [questId]: {
        startTime: Date.now(),
        progress: 0
      }
    }));
  };

  const completeQuest = (questId) => {
    const quest = processedQuests.find(q => q.id === questId);
    if (!quest?.canComplete) return;

    setCompletedQuests(prev => [...prev, questId]);
    setActiveQuests(prev => {
      const updated = { ...prev };
      delete updated[questId];
      return updated;
    });

    return quest.rewards;
  };

  const abandonQuest = (questId) => {
    setActiveQuests(prev => {
      const updated = { ...prev };
      delete updated[questId];
      return updated;
    });
  };

  const getTimeRemainingText = (timeRemaining) => {
    if (!timeRemaining) return null;
    
    const days = Math.floor(timeRemaining / (1000 * 60 * 60 * 24));
    const hours = Math.floor((timeRemaining % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((timeRemaining % (1000 * 60 * 60)) / (1000 * 60));
    
    if (days > 0) return `${days}d ${hours}h remaining`;
    if (hours > 0) return `${hours}h ${minutes}m remaining`;
    if (minutes > 0) return `${minutes}m remaining`;
    return 'Expires soon!';
  };

  useEffect(() => {
    const interval = setInterval(() => {
      const expiredQuests = Object.keys(activeQuests).filter(questId => {
        const quest = QUESTS_CONFIG.find(q => q.id === questId);
        return quest && isQuestExpired(quest, activeQuests[questId].startTime);
      });

      if (expiredQuests.length > 0) {
        setActiveQuests(prev => {
          const updated = { ...prev };
          expiredQuests.forEach(questId => delete updated[questId]);
          return updated;
        });
      }
    }, 60000); // Check every minute

    return () => clearInterval(interval);
  }, [activeQuests]);

  return {
    quests: processedQuests,
    activeQuests: processedQuests.filter(q => q.status === QUEST_STATUS.ACTIVE),
    completedQuests: processedQuests.filter(q => q.status === QUEST_STATUS.COMPLETED),
    availableQuests: processedQuests.filter(q => q.status === QUEST_STATUS.ACTIVE && !Object.keys(activeQuests).includes(q.id)),
    startQuest,
    completeQuest,
    abandonQuest,
    getTimeRemainingText,
    totalQuestPoints: completedQuests.reduce((total, questId) => {
      const quest = QUESTS_CONFIG.find(q => q.id === questId);
      return total + (quest?.rewards?.find(r => r.type === 'points')?.value || 0);
    }, 0)
  };
}