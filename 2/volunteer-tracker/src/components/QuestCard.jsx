import React from 'react';
import { QUEST_STATUS, getDifficultyColor, getQuestStatusColor } from '../constants.js';

export default function QuestCard({ quest, onStart, onComplete, onAbandon, getTimeRemainingText }) {
  const statusColor = getQuestStatusColor(quest.status);
  const difficultyColor = getDifficultyColor(quest.difficulty);
  
  const getStatusText = () => {
    switch (quest.status) {
      case QUEST_STATUS.ACTIVE:
        return quest.canComplete ? 'Ready to Complete!' : 'In Progress';
      case QUEST_STATUS.COMPLETED:
        return 'Completed';
      case QUEST_STATUS.EXPIRED:
        return 'Expired';
      case QUEST_STATUS.LOCKED:
        return `Unlock at ${quest.unlockCondition.minHours} hours`;
      default:
        return 'Available';
    }
  };

  const getRewardsText = () => {
    return quest.rewards.map(reward => {
      switch (reward.type) {
        case 'points':
          return `${reward.value} pts`;
        case 'badge':
          return `🏅 ${reward.value}`;
        case 'title':
          return `👑 "${reward.value}"`;
        case 'physical':
          return `🎁 ${reward.value}`;
        default:
          return reward.value;
      }
    }).join(', ');
  };

  const canStart = quest.status === QUEST_STATUS.ACTIVE && !quest.startTime;
  const isActive = quest.status === QUEST_STATUS.ACTIVE && quest.startTime;
  const isCompleted = quest.status === QUEST_STATUS.COMPLETED;
  const isExpired = quest.status === QUEST_STATUS.EXPIRED;
  const isLocked = quest.status === QUEST_STATUS.LOCKED;

  return (
    <div className={`quest-card ${quest.status.toLowerCase()}`}>
      <div className="quest-header">
        <div className="quest-icon">{quest.icon}</div>
        <div className="quest-title-section">
          <h3 className="quest-title">{quest.title}</h3>
          <div className="quest-meta">
            <span 
              className="difficulty-badge" 
              style={{ backgroundColor: difficultyColor }}
            >
              {quest.difficulty.toUpperCase()}
            </span>
            <span 
              className="status-badge"
              style={{ color: statusColor }}
            >
              {getStatusText()}
            </span>
          </div>
        </div>
      </div>

      <div className="quest-description">
        {quest.description}
      </div>

      {(isActive || isCompleted) && (
        <div className="progress-section">
          <div className="progress-bar-container">
            <div 
              className="progress-bar" 
              style={{ 
                width: `${quest.progressPercentage}%`,
                backgroundColor: quest.canComplete ? '#10B981' : statusColor 
              }}
            />
          </div>
          <div className="progress-text">
            {quest.progress} / {quest.target} {quest.type.replace('_', ' ')}
          </div>
        </div>
      )}

      {quest.timeRemaining && isActive && (
        <div className="time-remaining">
          ⏰ {getTimeRemainingText(quest.timeRemaining)}
        </div>
      )}

      <div className="quest-rewards">
        <strong>Rewards:</strong> {getRewardsText()}
      </div>

      <div className="quest-actions">
        {canStart && (
          <button 
            className="quest-btn start-btn"
            onClick={() => onStart(quest.id)}
          >
            Start Quest
          </button>
        )}
        
        {isActive && quest.canComplete && (
          <button 
            className="quest-btn complete-btn"
            onClick={() => onComplete(quest.id)}
          >
            Claim Rewards!
          </button>
        )}
        
        {isActive && !quest.canComplete && (
          <button 
            className="quest-btn abandon-btn"
            onClick={() => onAbandon(quest.id)}
          >
            Abandon
          </button>
        )}

        {isCompleted && (
          <div className="completed-checkmark">✅ Completed</div>
        )}

        {isExpired && (
          <div className="expired-notice">❌ Expired</div>
        )}

        {isLocked && (
          <div className="locked-notice">🔒 Locked</div>
        )}
      </div>
    </div>
  );
}