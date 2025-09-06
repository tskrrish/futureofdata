import React, { useState } from 'react';
import QuestCard from './QuestCard.jsx';
import { QUEST_STATUS } from '../constants.js';

export default function QuestsList({ 
  quests, 
  onStartQuest, 
  onCompleteQuest, 
  onAbandonQuest, 
  getTimeRemainingText,
  totalQuestPoints 
}) {
  const [activeTab, setActiveTab] = useState('active');

  const filterQuests = (status) => {
    switch (status) {
      case 'active':
        return quests.filter(q => q.status === QUEST_STATUS.ACTIVE);
      case 'completed':
        return quests.filter(q => q.status === QUEST_STATUS.COMPLETED);
      case 'available':
        return quests.filter(q => 
          q.status === QUEST_STATUS.ACTIVE && !q.startTime ||
          (q.status !== QUEST_STATUS.COMPLETED && q.status !== QUEST_STATUS.EXPIRED)
        );
      default:
        return quests;
    }
  };

  const filteredQuests = filterQuests(activeTab);
  const activeQuests = quests.filter(q => q.status === QUEST_STATUS.ACTIVE && q.startTime);
  const completedCount = quests.filter(q => q.status === QUEST_STATUS.COMPLETED).length;

  return (
    <div className="quests-container">
      <div className="quests-header">
        <h2 className="quests-title">🏅 Volunteer Quests</h2>
        <div className="quests-stats">
          <div className="stat-item">
            <span className="stat-label">Quest Points:</span>
            <span className="stat-value">{totalQuestPoints}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Active:</span>
            <span className="stat-value">{activeQuests.length}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Completed:</span>
            <span className="stat-value">{completedCount}</span>
          </div>
        </div>
      </div>

      <div className="quests-tabs">
        {[
          { id: 'active', label: 'Active Quests', count: activeQuests.length },
          { id: 'available', label: 'Available', count: quests.filter(q => 
            q.status === QUEST_STATUS.ACTIVE && !q.startTime).length },
          { id: 'completed', label: 'Completed', count: completedCount }
        ].map(tab => (
          <button
            key={tab.id}
            className={`quest-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label} 
            {tab.count > 0 && <span className="tab-count">({tab.count})</span>}
          </button>
        ))}
      </div>

      <div className="quests-content">
        {filteredQuests.length === 0 ? (
          <div className="empty-quests">
            {activeTab === 'active' && (
              <div className="empty-message">
                <span className="empty-icon">🎯</span>
                <h3>No Active Quests</h3>
                <p>Start a quest from the Available tab to begin your adventure!</p>
              </div>
            )}
            {activeTab === 'completed' && (
              <div className="empty-message">
                <span className="empty-icon">🏆</span>
                <h3>No Completed Quests Yet</h3>
                <p>Complete your first quest to see your achievements here!</p>
              </div>
            )}
            {activeTab === 'available' && (
              <div className="empty-message">
                <span className="empty-icon">🔒</span>
                <h3>No Available Quests</h3>
                <p>Keep volunteering to unlock new quests and challenges!</p>
              </div>
            )}
          </div>
        ) : (
          <div className="quests-grid">
            {filteredQuests.map(quest => (
              <QuestCard
                key={quest.id}
                quest={quest}
                onStart={onStartQuest}
                onComplete={onCompleteQuest}
                onAbandon={onAbandonQuest}
                getTimeRemainingText={getTimeRemainingText}
              />
            ))}
          </div>
        )}
      </div>

      {activeTab === 'active' && activeQuests.length > 0 && (
        <div className="active-quests-summary">
          <h3>⚡ Quick Progress</h3>
          <div className="progress-summary">
            {activeQuests.slice(0, 3).map(quest => (
              <div key={quest.id} className="mini-progress">
                <span className="mini-quest-name">{quest.title}</span>
                <div className="mini-progress-bar">
                  <div 
                    className="mini-progress-fill"
                    style={{ width: `${quest.progressPercentage}%` }}
                  />
                </div>
                <span className="mini-progress-text">
                  {quest.progress}/{quest.target}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}