import React, { useState, useEffect } from 'react';
import confetti from 'canvas-confetti';
import { playFanfare, playCheer, playMagicalSparkle } from '../utils/audio.js';

export default function QuestRewards({ rewards, questTitle, onClose, isVisible }) {
  const [showRewards, setShowRewards] = useState(false);
  const [currentRewardIndex, setCurrentRewardIndex] = useState(0);

  useEffect(() => {
    if (isVisible && rewards?.length > 0) {
      setShowRewards(true);
      setCurrentRewardIndex(0);
      
      // Quest completion celebration sequence
      playFanfare('rare');
      setTimeout(() => playMagicalSparkle(), 500);
      setTimeout(() => playCheer(1000), 800);
      
      // Confetti celebration
      const duration = 3000;
      const animationEnd = Date.now() + duration;
      const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 999 };

      const interval = setInterval(function() {
        const timeLeft = animationEnd - Date.now();
        if (timeLeft <= 0) {
          clearInterval(interval);
          return;
        }
        const particleCount = 50 * (timeLeft / duration);
        confetti(Object.assign({}, defaults, { 
          particleCount, 
          origin: { x: Math.random(), y: Math.random() * 0.5 + 0.25 }
        }));
      }, 250);

      // Auto-advance through rewards
      if (rewards.length > 1) {
        const rewardInterval = setInterval(() => {
          setCurrentRewardIndex(prev => {
            if (prev >= rewards.length - 1) {
              clearInterval(rewardInterval);
              return prev;
            }
            return prev + 1;
          });
        }, 1500);

        return () => clearInterval(rewardInterval);
      }
    }
  }, [isVisible, rewards]);

  if (!isVisible || !rewards?.length) return null;

  const currentReward = rewards[currentRewardIndex];

  const getRewardIcon = (type) => {
    switch (type) {
      case 'points': return '⭐';
      case 'badge': return '🏅';
      case 'title': return '👑';
      case 'physical': return '🎁';
      default: return '🎉';
    }
  };

  const getRewardDescription = (reward) => {
    switch (reward.type) {
      case 'points':
        return `${reward.value} Quest Points`;
      case 'badge':
        return `New Badge: ${reward.value}`;
      case 'title':
        return `New Title: "${reward.value}"`;
      case 'physical':
        return `Physical Reward: ${reward.value}`;
      default:
        return reward.value;
    }
  };

  return (
    <div className="quest-rewards-overlay">
      <div className="quest-rewards-modal">
        <div className="quest-complete-header">
          <h2 className="quest-complete-title">🏆 Quest Complete!</h2>
          <h3 className="completed-quest-name">"{questTitle}"</h3>
        </div>

        <div className="rewards-showcase">
          <div className="reward-item-display">
            <div className="reward-icon-large">
              {getRewardIcon(currentReward.type)}
            </div>
            <div className="reward-details">
              <h3 className="reward-title">
                {getRewardDescription(currentReward)}
              </h3>
              {currentReward.type === 'points' && (
                <p className="reward-subtitle">
                  Spend points on exclusive rewards!
                </p>
              )}
              {currentReward.type === 'badge' && (
                <p className="reward-subtitle">
                  Badge added to your collection!
                </p>
              )}
              {currentReward.type === 'title' && (
                <p className="reward-subtitle">
                  Show off your new title with pride!
                </p>
              )}
              {currentReward.type === 'physical' && (
                <p className="reward-subtitle">
                  Contact YMCA staff to claim your reward!
                </p>
              )}
            </div>
          </div>

          {rewards.length > 1 && (
            <div className="rewards-progress">
              <span className="rewards-counter">
                {currentRewardIndex + 1} of {rewards.length}
              </span>
              <div className="rewards-dots">
                {rewards.map((_, index) => (
                  <div 
                    key={index}
                    className={`reward-dot ${index <= currentRewardIndex ? 'active' : ''}`}
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="rewards-actions">
          {currentRewardIndex < rewards.length - 1 ? (
            <button 
              className="next-reward-btn"
              onClick={() => setCurrentRewardIndex(prev => prev + 1)}
            >
              Next Reward →
            </button>
          ) : (
            <button 
              className="claim-all-btn"
              onClick={onClose}
            >
              Awesome! 🎉
            </button>
          )}
        </div>

        <div className="celebration-text">
          <p>🌟 Keep up the amazing volunteer work! 🌟</p>
        </div>
      </div>
    </div>
  );
}