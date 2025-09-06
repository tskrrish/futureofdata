import { STREAK_TYPES, getStreakIcon, getStreakColor } from '../constants.js';

function StreakBadge({ streaks }) {
  if (!streaks) return null;

  return (
    <div className="streak-badges">
      {Object.entries(streaks).map(([streakType, streakData]) => {
        const config = STREAK_TYPES[streakType];
        if (!config) return null;

        const hasActiveStreak = streakData.current_streak > 0;
        const isInGracePeriod = streakData.grace_days_remaining > 0;
        
        return (
          <div
            key={streakType}
            className={`streak-badge ${hasActiveStreak ? 'active' : ''} ${isInGracePeriod ? 'grace' : ''}`}
            style={{ '--streak-color': getStreakColor(streakType) }}
          >
            <div className="streak-icon">{getStreakIcon(streakType)}</div>
            <div className="streak-info">
              <div className="streak-type">{config.name}</div>
              <div className="streak-stats">
                <span className="current-streak">
                  {streakData.current_streak} current
                </span>
                {streakData.longest_streak > streakData.current_streak && (
                  <span className="longest-streak">
                    ({streakData.longest_streak} best)
                  </span>
                )}
              </div>
              {streakData.is_active && isInGracePeriod && (
                <div className="grace-period">
                  {streakData.grace_days_remaining} grace days left
                </div>
              )}
              {streakData.milestones.length > 0 && (
                <div className="streak-milestones">
                  {streakData.milestones.slice(-1)[0]} {/* Show latest milestone */}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default StreakBadge;