import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Award, TrendingUp, Users, Crown, Star, Target } from 'lucide-react';
import { badgeService } from '../services/badgeService';
import BadgeCard2, { BadgeProgressCard } from './BadgeCard2';
import { RARITY_TIERS, VOLUNTEER_ROLES } from '../constants/badgeSystem2';

/**
 * Badge Dashboard - Central management for Badge System 2.0
 * Displays leaderboards, statistics, and badge management features
 */
export default function BadgeDashboard({ volunteers = [] }) {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedVolunteer, setSelectedVolunteer] = useState(null);
  const [filterRarity, setFilterRarity] = useState('all');

  // Calculate badge statistics
  const badgeStats = useMemo(() => {
    return badgeService.getBadgeStatistics(volunteers);
  }, [volunteers]);

  // Generate leaderboard
  const leaderboard = useMemo(() => {
    return badgeService.generateBadgeLeaderboard(volunteers);
  }, [volunteers]);

  // Filter volunteers by rarity
  const filteredVolunteers = useMemo(() => {
    if (filterRarity === 'all') return volunteers;
    
    return volunteers.filter(volunteer => {
      const profile = badgeService.calculateVolunteerProfile(volunteer);
      return profile.badges.some(badge => badge.badge.rarity === filterRarity);
    });
  }, [volunteers, filterRarity]);

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Award },
    { id: 'leaderboard', label: 'Leaderboard', icon: Crown },
    { id: 'badges', label: 'All Badges', icon: Star },
    { id: 'roles', label: 'Role Progress', icon: TrendingUp },
    { id: 'analytics', label: 'Analytics', icon: Users }
  ];

  return (
    <div className="badge-dashboard">
      <div className="dashboard-header">
        <div className="header-content">
          <h1 className="dashboard-title">
            <Award className="w-8 h-8 mr-3" />
            Badge System 2.0
          </h1>
          <p className="dashboard-subtitle">
            Role-specific badges with rarity tiers and achievement tracking
          </p>
        </div>
        
        <div className="quick-stats">
          <div className="quick-stat">
            <div className="stat-value">{badgeStats.totalBadgesEarned}</div>
            <div className="stat-label">Total Badges</div>
          </div>
          <div className="quick-stat">
            <div className="stat-value">{Math.round(badgeStats.averageBadgeScore)}</div>
            <div className="stat-label">Avg Score</div>
          </div>
          <div className="quick-stat">
            <div className="stat-value">{leaderboard.filter(l => l.legendaryBadges > 0).length}</div>
            <div className="stat-label">Legends</div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="tab-navigation">
        {tabs.map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <Icon className="w-5 h-5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        <AnimatePresence mode="wait">
          {activeTab === 'overview' && (
            <OverviewTab 
              key="overview"
              badgeStats={badgeStats} 
              leaderboard={leaderboard.slice(0, 5)} 
            />
          )}
          
          {activeTab === 'leaderboard' && (
            <LeaderboardTab 
              key="leaderboard"
              leaderboard={leaderboard}
              onSelectVolunteer={setSelectedVolunteer}
            />
          )}
          
          {activeTab === 'badges' && (
            <BadgesTab 
              key="badges"
              volunteers={filteredVolunteers}
              filterRarity={filterRarity}
              onFilterChange={setFilterRarity}
            />
          )}
          
          {activeTab === 'roles' && (
            <RoleProgressTab 
              key="roles"
              volunteers={volunteers}
              badgeStats={badgeStats}
            />
          )}
          
          {activeTab === 'analytics' && (
            <AnalyticsTab 
              key="analytics"
              badgeStats={badgeStats}
              volunteers={volunteers}
            />
          )}
        </AnimatePresence>
      </div>

      {/* Volunteer Detail Modal */}
      <AnimatePresence>
        {selectedVolunteer && (
          <VolunteerDetailModal 
            volunteer={selectedVolunteer}
            onClose={() => setSelectedVolunteer(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

// Overview Tab Component
function OverviewTab({ badgeStats, leaderboard }) {
  return (
    <motion.div
      className="overview-tab"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      <div className="overview-grid">
        {/* Badge Distribution Chart */}
        <div className="stat-card large">
          <h3>Badge Distribution by Rarity</h3>
          <div className="rarity-distribution">
            {Object.entries(badgeStats.badgesByRarity).map(([rarity, count]) => (
              <div key={rarity} className="rarity-bar">
                <div className="rarity-info">
                  <span className={`rarity-dot rarity-${rarity}`} />
                  <span className="rarity-name">{RARITY_TIERS[rarity].name}</span>
                  <span className="rarity-count">{count}</span>
                </div>
                <div className="bar-track">
                  <motion.div 
                    className={`bar-fill rarity-${rarity}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${(count / badgeStats.totalBadgesEarned) * 100}%` }}
                    transition={{ delay: 0.2, duration: 0.8 }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Performers */}
        <div className="stat-card">
          <h3>Top Badge Earners</h3>
          <div className="top-performers">
            {leaderboard.map((entry, index) => (
              <div key={index} className="performer-item">
                <div className="performer-rank">{index + 1}</div>
                <div className="performer-info">
                  <div className="performer-name">
                    {entry.volunteer.first_name} {entry.volunteer.last_name}
                  </div>
                  <div className="performer-stats">
                    <span>{entry.badgeScore} pts</span>
                    <span>•</span>
                    <span>{entry.totalBadges} badges</span>
                  </div>
                </div>
                <div className="performer-badges">
                  {entry.topBadges.slice(0, 3).map((badge, i) => (
                    <div key={i} className={`mini-badge-icon rarity-${badge.badge.rarity}`}>
                      {badge.badge.icon}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Role Distribution */}
        <div className="stat-card">
          <h3>Role Distribution</h3>
          <div className="role-distribution">
            {Object.entries(badgeStats.roleDistribution).map(([roleKey, count]) => {
              const role = VOLUNTEER_ROLES[roleKey];
              if (!role || count === 0) return null;
              
              return (
                <div key={roleKey} className="role-item">
                  <div className="role-info">
                    <span className="role-name">{role.name}</span>
                    <span className="role-count">{count}</span>
                  </div>
                  <div className="role-level">Level {role.level}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

// Leaderboard Tab Component
function LeaderboardTab({ leaderboard, onSelectVolunteer }) {
  return (
    <motion.div
      className="leaderboard-tab"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      <div className="leaderboard-list">
        {leaderboard.map((entry, index) => (
          <motion.div
            key={index}
            className={`leaderboard-item ${index < 3 ? 'podium' : ''}`}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            onClick={() => onSelectVolunteer(entry.volunteer)}
          >
            <div className="leaderboard-rank">
              {index < 3 ? (
                <div className={`medal medal-${index === 0 ? 'gold' : index === 1 ? 'silver' : 'bronze'}`}>
                  {index + 1}
                </div>
              ) : (
                <div className="rank-number">{index + 1}</div>
              )}
            </div>
            
            <div className="volunteer-summary">
              <div className="volunteer-name">
                {entry.volunteer.first_name} {entry.volunteer.last_name}
              </div>
              <div className="volunteer-role">
                {entry.currentRole ? entry.currentRole.name : 'Volunteer'}
              </div>
            </div>
            
            <div className="badge-showcase">
              {entry.topBadges.map((badge, i) => (
                <div key={i} className={`showcase-badge rarity-${badge.badge.rarity}`}>
                  {badge.badge.icon}
                </div>
              ))}
            </div>
            
            <div className="score-section">
              <div className="badge-score">{entry.badgeScore}</div>
              <div className="badge-count">{entry.totalBadges} badges</div>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}

// Badges Tab Component
function BadgesTab({ volunteers, filterRarity, onFilterChange }) {
  return (
    <motion.div
      className="badges-tab"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      <div className="badges-controls">
        <div className="filter-section">
          <label>Filter by Rarity:</label>
          <select value={filterRarity} onChange={(e) => onFilterChange(e.target.value)}>
            <option value="all">All Rarities</option>
            {Object.entries(RARITY_TIERS).map(([key, tier]) => (
              <option key={key} value={key}>{tier.name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="badge-cards-grid">
        {volunteers.map(volunteer => (
          <BadgeCard2 
            key={`${volunteer.first_name}-${volunteer.last_name}`}
            volunteer={volunteer} 
          />
        ))}
      </div>
    </motion.div>
  );
}

// Role Progress Tab Component
function RoleProgressTab({ volunteers, badgeStats }) {
  const roleProgress = useMemo(() => {
    return volunteers.map(volunteer => {
      const profile = badgeService.calculateVolunteerProfile(volunteer);
      return {
        volunteer,
        profile
      };
    }).filter(item => item.profile.nextRole);
  }, [volunteers]);

  return (
    <motion.div
      className="roles-tab"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      <div className="role-progress-grid">
        {roleProgress.map((item, index) => (
          <div key={index} className="volunteer-progress">
            <div className="volunteer-header">
              <h4>{item.volunteer.first_name} {item.volunteer.last_name}</h4>
              <div className="hours-info">{item.volunteer.hours_total || 0} hours</div>
            </div>
            <BadgeProgressCard volunteer={item.volunteer} />
          </div>
        ))}
      </div>
    </motion.div>
  );
}

// Analytics Tab Component
function AnalyticsTab({ badgeStats, volunteers }) {
  const insights = useMemo(() => {
    const insights = [];
    
    // Most popular badge type
    const maxType = Object.entries(badgeStats.badgesByType)
      .reduce((max, [type, count]) => count > max.count ? { type, count } : max, { count: 0 });
    
    if (maxType.type) {
      insights.push({
        title: 'Most Popular Badge Type',
        value: `${maxType.type.replace('_', ' ')} badges`,
        description: `${maxType.count} badges earned`,
        trend: 'up'
      });
    }

    // Rarity distribution insight
    const legendaryCount = badgeStats.badgesByRarity.legendary || 0;
    const totalBadges = badgeStats.totalBadgesEarned;
    const legendaryPercent = totalBadges > 0 ? (legendaryCount / totalBadges * 100).toFixed(1) : 0;
    
    insights.push({
      title: 'Legendary Achievement Rate',
      value: `${legendaryPercent}%`,
      description: `${legendaryCount} legendary badges earned`,
      trend: legendaryPercent > 5 ? 'up' : 'down'
    });

    return insights;
  }, [badgeStats]);

  return (
    <motion.div
      className="analytics-tab"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      <div className="analytics-grid">
        <div className="insights-section">
          <h3>Key Insights</h3>
          <div className="insights-list">
            {insights.map((insight, index) => (
              <div key={index} className="insight-card">
                <div className="insight-header">
                  <h4>{insight.title}</h4>
                  <TrendingUp className={`trend-icon ${insight.trend}`} />
                </div>
                <div className="insight-value">{insight.value}</div>
                <div className="insight-description">{insight.description}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="detailed-stats">
          <h3>Detailed Statistics</h3>
          <div className="stats-grid">
            <div className="stat-item">
              <div className="stat-label">Total Volunteers</div>
              <div className="stat-value">{volunteers.length}</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">Average Badge Score</div>
              <div className="stat-value">{Math.round(badgeStats.averageBadgeScore)}</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">Badge Completion Rate</div>
              <div className="stat-value">
                {volunteers.length > 0 ? Math.round(badgeStats.totalBadgesEarned / volunteers.length) : 0}%
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

// Volunteer Detail Modal Component
function VolunteerDetailModal({ volunteer, onClose }) {
  const profile = useMemo(() => {
    return badgeService.calculateVolunteerProfile(volunteer);
  }, [volunteer]);

  return (
    <motion.div
      className="modal-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="volunteer-detail-modal"
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2>{volunteer.first_name} {volunteer.last_name}</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <div className="modal-body">
          <div className="profile-overview">
            <div className="profile-stat">
              <Target className="w-5 h-5" />
              <span>Badge Score: {profile.badgeScore}</span>
            </div>
            <div className="profile-stat">
              <Award className="w-5 h-5" />
              <span>Total Badges: {profile.badges.length}</span>
            </div>
            <div className="profile-stat">
              <Crown className="w-5 h-5" />
              <span>Role: {profile.currentRole ? profile.currentRole.name : 'Volunteer'}</span>
            </div>
          </div>

          <div className="achievements-section">
            <h3>Recent Achievements</h3>
            <div className="achievements-list">
              {profile.achievements.map((achievement, index) => (
                <div key={index} className="achievement-item">
                  <div className="achievement-icon">{achievement.icon}</div>
                  <div className="achievement-info">
                    <div className="achievement-title">{achievement.title}</div>
                    <div className="achievement-description">{achievement.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="recommendations-section">
            <h3>Recommendations</h3>
            <div className="recommendations-list">
              {profile.recommendations.map((rec, index) => (
                <div key={index} className={`recommendation-item priority-${rec.priority}`}>
                  <div className="recommendation-title">{rec.title}</div>
                  <div className="recommendation-description">{rec.description}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}