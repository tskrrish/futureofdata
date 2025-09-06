import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  calculateVolunteerBadges, 
  getBadgeDisplayData, 
  calculateBadgeScore,
  RARITY_TIERS,
  VOLUNTEER_ROLES
} from '../constants/badgeSystem2';

/**
 * Enhanced Badge Card component for Badge System 2.0
 * Features role-specific badges, rarity tiers, and improved animations
 */
export default function BadgeCard2({ volunteer, showDetails = false }) {
  const [isFlipped, setIsFlipped] = useState(false);
  const [selectedBadge, setSelectedBadge] = useState(null);

  // Calculate all badges for this volunteer
  const allBadges = useMemo(() => {
    return calculateVolunteerBadges({
      hours_total: volunteer.hours_total || 0,
      storyworlds: volunteer.storyworlds || [],
      projects: volunteer.projects || [],
      yearsActive: volunteer.yearsActive || 1,
      assignments_count: volunteer.assignments_count || 0,
      first_activity: volunteer.first_activity
    });
  }, [volunteer]);

  // Calculate badge score and current role
  const badgeScore = useMemo(() => calculateBadgeScore(allBadges.map(b => b.badge)), [allBadges]);
  const currentRole = useMemo(() => {
    const roleBadge = allBadges.find(b => b.type === 'role');
    return roleBadge ? roleBadge.badge : null;
  }, [allBadges]);

  // Group badges by type and rarity
  const badgesByType = useMemo(() => {
    const grouped = {
      role: [],
      storyworld: [],
      special: []
    };
    
    allBadges.forEach(badge => {
      grouped[badge.type].push(getBadgeDisplayData(badge.badge));
    });
    
    // Sort by rarity (legendary first)
    Object.keys(grouped).forEach(type => {
      grouped[type].sort((a, b) => {
        const rarityOrder = { legendary: 5, epic: 4, rare: 3, uncommon: 2, common: 1 };
        return rarityOrder[b.rarity] - rarityOrder[a.rarity];
      });
    });
    
    return grouped;
  }, [allBadges]);

  const fullName = `${volunteer.first_name} ${volunteer.last_name}`;
  const hours = Number(volunteer.hours_total) || 0;

  return (
    <div className="badge-card-container">
      <motion.div
        className={`badge-card-2 ${isFlipped ? 'flipped' : ''}`}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        onClick={() => setIsFlipped(!isFlipped)}
        whileHover={{ scale: 1.02 }}
        style={{ perspective: 1000 }}
      >
        {/* Front of card */}
        <motion.div
          className="card-face card-front"
          animate={{ rotateY: isFlipped ? 180 : 0 }}
          transition={{ duration: 0.6 }}
        >
          {/* Header with role and score */}
          <div className="card-header-2">
            <div className="role-badge">
              {currentRole ? currentRole.name : 'Volunteer'}
            </div>
            <div className="badge-score">
              <span className="score-value">{badgeScore}</span>
              <span className="score-label">Badge Score</span>
            </div>
          </div>

          {/* Volunteer info */}
          <div className="volunteer-info">
            <div className="volunteer-avatar-2">
              <span>{fullName.split(' ').map(n => n[0]).join('')}</span>
            </div>
            <h3 className="volunteer-name-2">{fullName}</h3>
            <div className="volunteer-stats">
              <span>{hours} hours</span>
              <span>•</span>
              <span>{allBadges.length} badges</span>
            </div>
          </div>

          {/* Featured badges showcase */}
          <div className="featured-badges">
            {Object.entries(badgesByType).map(([type, badges]) => (
              badges.slice(0, 3).map((badge, index) => (
                <motion.div
                  key={`${type}-${index}`}
                  className={`featured-badge rarity-${badge.rarity}`}
                  whileHover={{ scale: 1.1, rotate: 5 }}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedBadge(badge);
                  }}
                >
                  <div className="badge-icon">{badge.icon}</div>
                  <div className="badge-glow" style={{ backgroundColor: badge.displayColor }} />
                </motion.div>
              ))
            ))}
          </div>

          <div className="card-footer-2">
            <span>Click to view all badges</span>
          </div>
        </motion.div>

        {/* Back of card */}
        <motion.div
          className="card-face card-back"
          animate={{ rotateY: isFlipped ? 0 : -180 }}
          transition={{ duration: 0.6 }}
        >
          <div className="all-badges-header">
            <h4>{fullName}'s Badge Collection</h4>
            <button 
              className="close-btn"
              onClick={(e) => {
                e.stopPropagation();
                setIsFlipped(false);
              }}
            >
              ×
            </button>
          </div>

          <div className="badges-by-type">
            {Object.entries(badgesByType).map(([type, badges]) => (
              <div key={type} className="badge-type-section">
                <h5 className="type-title">
                  {type === 'role' ? 'Role Badges' : 
                   type === 'storyworld' ? 'Storyworld Badges' : 'Special Badges'}
                </h5>
                <div className="badge-grid">
                  {badges.map((badge, index) => (
                    <motion.div
                      key={index}
                      className={`mini-badge rarity-${badge.rarity}`}
                      whileHover={{ scale: 1.1 }}
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedBadge(badge);
                      }}
                    >
                      <div className="mini-badge-icon">{badge.icon}</div>
                      <div className="mini-badge-name">{badge.name}</div>
                      <div className="rarity-indicator" style={{ backgroundColor: badge.displayColor }} />
                    </motion.div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </motion.div>

      {/* Badge detail modal */}
      <AnimatePresence>
        {selectedBadge && (
          <motion.div
            className="badge-modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSelectedBadge(null)}
          >
            <motion.div
              className="badge-modal"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="badge-modal-header">
                <div className={`large-badge-icon rarity-${selectedBadge.rarity}`}>
                  {selectedBadge.icon}
                </div>
                <h3>{selectedBadge.name}</h3>
                <div className={`rarity-tag rarity-${selectedBadge.rarity}`}>
                  {RARITY_TIERS[selectedBadge.rarity].name}
                </div>
              </div>
              
              <div className="badge-modal-body">
                <p className="badge-description">
                  {selectedBadge.description || `Awarded for excellence in ${selectedBadge.name}`}
                </p>
                
                <div className="badge-stats">
                  <div className="stat">
                    <span className="stat-label">Rarity</span>
                    <span className="stat-value">{RARITY_TIERS[selectedBadge.rarity].name}</span>
                  </div>
                  <div className="stat">
                    <span className="stat-label">Points</span>
                    <span className="stat-value">{RARITY_TIERS[selectedBadge.rarity].points}</span>
                  </div>
                </div>
              </div>
              
              <button 
                className="close-modal-btn"
                onClick={() => setSelectedBadge(null)}
              >
                Close
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Badge progress component for role advancement
export function BadgeProgressCard({ volunteer }) {
  const currentRole = useMemo(() => {
    const hours = volunteer.hours_total || 0;
    const yearsActive = volunteer.yearsActive || 1;
    
    // Find current role
    const roles = Object.values(VOLUNTEER_ROLES);
    let current = null;
    let next = null;
    
    for (let i = 0; i < roles.length; i++) {
      if (hours >= roles[i].requirements.hours) {
        current = roles[i];
      } else if (!next) {
        next = roles[i];
        break;
      }
    }
    
    return { current, next };
  }, [volunteer]);

  if (!currentRole.next) return null;

  const progress = ((volunteer.hours_total || 0) / currentRole.next.requirements.hours) * 100;

  return (
    <motion.div 
      className="badge-progress-card"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.3 }}
    >
      <div className="progress-header">
        <h4>Role Progression</h4>
        <div className="current-role">
          {currentRole.current ? currentRole.current.name : 'New Volunteer'}
        </div>
      </div>
      
      <div className="progress-bar">
        <div className="progress-track">
          <motion.div 
            className="progress-fill"
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(progress, 100)}%` }}
            transition={{ duration: 1, ease: "easeOut" }}
          />
        </div>
        <div className="progress-labels">
          <span>{volunteer.hours_total || 0}h</span>
          <span>{currentRole.next.requirements.hours}h</span>
        </div>
      </div>
      
      <div className="next-role">
        <span>Next: </span>
        <strong>{currentRole.next.name}</strong>
      </div>
    </motion.div>
  );
}