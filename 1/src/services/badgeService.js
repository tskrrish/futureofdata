/**
 * Badge Service - Badge System 2.0
 * Handles badge calculation, achievement tracking, and role progression
 */

import { 
  VOLUNTEER_ROLES,
  BRANCH_BADGE_CATEGORIES, 
  SPECIAL_BADGES,
  RARITY_TIERS,
  calculateVolunteerBadges,
  getBadgeDisplayData
} from '../constants/badgeSystem2';

export class BadgeService {
  constructor() {
    this.achievementHistory = new Map(); // Store achievement history
    this.roleProgress = new Map(); // Track role progression
  }

  /**
   * Calculate comprehensive badge data for a volunteer
   */
  calculateVolunteerProfile(volunteerData) {
    const profile = {
      volunteer: volunteerData,
      badges: [],
      currentRole: null,
      nextRole: null,
      roleProgress: 0,
      badgeScore: 0,
      achievements: [],
      recommendations: []
    };

    // Calculate all earned badges
    profile.badges = calculateVolunteerBadges(volunteerData);
    profile.badgeScore = this.calculateBadgeScore(profile.badges);

    // Determine current role and progression
    const roleData = this.calculateRoleProgression(volunteerData);
    profile.currentRole = roleData.current;
    profile.nextRole = roleData.next;
    profile.roleProgress = roleData.progress;

    // Generate achievements and recommendations
    profile.achievements = this.generateAchievements(volunteerData, profile.badges);
    profile.recommendations = this.generateRecommendations(volunteerData, profile);

    return profile;
  }

  /**
   * Calculate badge score based on rarity points
   */
  calculateBadgeScore(badges) {
    return badges.reduce((total, badge) => {
      const rarity = RARITY_TIERS[badge.badge.rarity] || RARITY_TIERS.common;
      return total + rarity.points;
    }, 0);
  }

  /**
   * Determine current role and progression to next role
   */
  calculateRoleProgression(volunteerData) {
    const hours = volunteerData.hours_total || 0;
    const yearsActive = volunteerData.yearsActive || 1;
    const training = volunteerData.training || [];

    const roles = Object.values(VOLUNTEER_ROLES).sort((a, b) => a.level - b.level);
    
    let current = null;
    let next = null;
    let progress = 0;

    // Find current role
    for (const role of roles) {
      if (this.meetsRoleRequirements(volunteerData, role)) {
        current = role;
      } else if (!next) {
        next = role;
        break;
      }
    }

    // Calculate progress to next role
    if (next) {
      const hoursProgress = Math.min(hours / next.requirements.hours, 1);
      const trainingProgress = next.requirements.training ? 
        training.filter(t => next.requirements.training.includes(t)).length / next.requirements.training.length : 1;
      const yearsProgress = next.requirements.yearsActive ? 
        Math.min(yearsActive / next.requirements.yearsActive, 1) : 1;

      progress = (hoursProgress + trainingProgress + yearsProgress) / 3;
    }

    return { current, next, progress: Math.round(progress * 100) };
  }

  /**
   * Check if volunteer meets role requirements
   */
  meetsRoleRequirements(volunteerData, role) {
    const requirements = role.requirements;
    const hours = volunteerData.hours_total || 0;
    const yearsActive = volunteerData.yearsActive || 1;
    const training = volunteerData.training || [];

    // Check hour requirement
    if (hours < requirements.hours) return false;

    // Check years active requirement
    if (requirements.yearsActive && yearsActive < requirements.yearsActive) return false;

    // Check training requirements
    if (requirements.training) {
      const hasRequiredTraining = requirements.training.every(t => training.includes(t));
      if (!hasRequiredTraining) return false;
    }

    // Check previous role requirement
    if (requirements.previousRole) {
      const previousRole = VOLUNTEER_ROLES[requirements.previousRole];
      if (!this.meetsRoleRequirements(volunteerData, previousRole)) return false;
    }

    return true;
  }

  /**
   * Generate recent achievements for display
   */
  generateAchievements(volunteerData, badges) {
    const achievements = [];
    const currentTime = new Date();

    // Recent badge achievements (simulated - in real app would track actual earn dates)
    badges.slice(-3).forEach(badge => {
      achievements.push({
        type: 'badge_earned',
        title: `Earned ${badge.badge.name}!`,
        description: `Unlocked a ${badge.badge.rarity} badge`,
        earnedAt: new Date(currentTime - Math.random() * 30 * 24 * 60 * 60 * 1000), // Last 30 days
        icon: badge.badge.icon,
        rarity: badge.badge.rarity
      });
    });

    // Hour milestones
    const hours = volunteerData.hours_total || 0;
    const milestones = [10, 25, 50, 100, 200, 500];
    const recentMilestone = milestones.filter(m => hours >= m).pop();
    
    if (recentMilestone) {
      achievements.push({
        type: 'milestone',
        title: `${recentMilestone} Hour Milestone!`,
        description: `Reached ${recentMilestone} total volunteer hours`,
        earnedAt: new Date(currentTime - Math.random() * 60 * 24 * 60 * 60 * 1000), // Last 60 days
        icon: '🎯',
        rarity: 'rare'
      });
    }

    // Sort by most recent
    return achievements.sort((a, b) => b.earnedAt - a.earnedAt).slice(0, 5);
  }

  /**
   * Generate personalized recommendations
   */
  generateRecommendations(volunteerData, profile) {
    const recommendations = [];
    const hours = volunteerData.hours_total || 0;
    const storyworlds = volunteerData.storyworlds || [];

    // Role progression recommendations
    if (profile.nextRole && profile.roleProgress < 100) {
      const nextRole = profile.nextRole;
      const missingHours = Math.max(0, nextRole.requirements.hours - hours);
      
      if (missingHours > 0) {
        recommendations.push({
          type: 'role_progress',
          title: `Advance to ${nextRole.name}`,
          description: `Complete ${missingHours} more volunteer hours`,
          action: 'volunteer_more',
          priority: 'high'
        });
      }

      if (nextRole.requirements.training) {
        const currentTraining = volunteerData.training || [];
        const missingTraining = nextRole.requirements.training.filter(t => !currentTraining.includes(t));
        
        if (missingTraining.length > 0) {
          recommendations.push({
            type: 'training',
            title: 'Complete Required Training',
            description: `Finish: ${missingTraining.join(', ')}`,
            action: 'complete_training',
            priority: 'high'
          });
        }
      }
    }

    // Storyworld diversification
    if (storyworlds.length === 1) {
      const categories = Object.keys(BRANCH_BADGE_CATEGORIES);
      const currentCategory = this.getStoryworldCategory(storyworlds[0]);
      const otherCategories = categories.filter(c => c !== currentCategory);
      
      if (otherCategories.length > 0) {
        const suggestedCategory = otherCategories[Math.floor(Math.random() * otherCategories.length)];
        const categoryData = BRANCH_BADGE_CATEGORIES[suggestedCategory];
        
        recommendations.push({
          type: 'diversification',
          title: 'Explore New Areas',
          description: `Try volunteering in ${categoryData.name} to earn new badges`,
          action: 'explore_storyworld',
          priority: 'medium'
        });
      }
    }

    // Special badge opportunities
    const specialBadgeOps = this.findSpecialBadgeOpportunities(volunteerData);
    recommendations.push(...specialBadgeOps);

    // Consistency recommendations
    if (hours > 0 && !this.hasConsistencyBadge(profile.badges)) {
      recommendations.push({
        type: 'consistency',
        title: 'Build Consistency',
        description: 'Volunteer regularly to earn consistency badges',
        action: 'volunteer_regularly',
        priority: 'medium'
      });
    }

    return recommendations.slice(0, 5);
  }

  /**
   * Find opportunities for special badge achievements
   */
  findSpecialBadgeOpportunities(volunteerData) {
    const opportunities = [];
    const storyworlds = volunteerData.storyworlds || [];
    const hours = volunteerData.hours_total || 0;

    // Multi-talent opportunity
    if (storyworlds.length >= 2 && hours >= 50) {
      opportunities.push({
        type: 'special_badge',
        title: 'Multi-Talent Master',
        description: `Volunteer in one more storyworld to earn this epic badge (${storyworlds.length}/3)`,
        action: 'diversify_activities',
        priority: 'medium'
      });
    }

    return opportunities;
  }

  /**
   * Check if volunteer has consistency-related badges
   */
  hasConsistencyBadge(badges) {
    return badges.some(badge => 
      badge.badge.name.toLowerCase().includes('consistency') ||
      badge.badge.name.toLowerCase().includes('regular')
    );
  }

  /**
   * Get storyworld category from name
   */
  getStoryworldCategory(storyworldName) {
    const name = storyworldName.toLowerCase();
    
    if (name.includes('youth')) return 'YOUTH_SPARK';
    if (name.includes('healthy') || name.includes('fitness')) return 'HEALTHY_TOGETHER';
    if (name.includes('water') || name.includes('aquatic')) return 'WATER_WELLNESS';
    if (name.includes('neighbor') || name.includes('community')) return 'NEIGHBOR_POWER';
    if (name.includes('sports')) return 'SPORTS';
    
    return null;
  }

  /**
   * Generate leaderboard with badge scores
   */
  generateBadgeLeaderboard(volunteers) {
    const leaderboard = volunteers.map(volunteer => {
      const profile = this.calculateVolunteerProfile(volunteer);
      return {
        volunteer: volunteer,
        badgeScore: profile.badgeScore,
        totalBadges: profile.badges.length,
        legendaryBadges: profile.badges.filter(b => b.badge.rarity === 'legendary').length,
        currentRole: profile.currentRole,
        topBadges: profile.badges
          .sort((a, b) => RARITY_TIERS[b.badge.rarity].points - RARITY_TIERS[a.badge.rarity].points)
          .slice(0, 3)
      };
    });

    return leaderboard
      .sort((a, b) => b.badgeScore - a.badgeScore)
      .slice(0, 20);
  }

  /**
   * Get badge statistics for analytics
   */
  getBadgeStatistics(volunteers) {
    const stats = {
      totalBadgesEarned: 0,
      badgesByRarity: {},
      badgesByType: {},
      averageBadgeScore: 0,
      topPerformers: [],
      roleDistribution: {}
    };

    // Initialize counters
    Object.keys(RARITY_TIERS).forEach(rarity => {
      stats.badgesByRarity[rarity] = 0;
    });

    Object.keys(VOLUNTEER_ROLES).forEach(role => {
      stats.roleDistribution[role] = 0;
    });

    let totalBadgeScore = 0;

    volunteers.forEach(volunteer => {
      const profile = this.calculateVolunteerProfile(volunteer);
      
      stats.totalBadgesEarned += profile.badges.length;
      totalBadgeScore += profile.badgeScore;

      // Count badges by rarity
      profile.badges.forEach(badge => {
        stats.badgesByRarity[badge.badge.rarity]++;
        
        const type = badge.type;
        stats.badgesByType[type] = (stats.badgesByType[type] || 0) + 1;
      });

      // Count role distribution
      if (profile.currentRole) {
        const roleKey = Object.keys(VOLUNTEER_ROLES).find(key => 
          VOLUNTEER_ROLES[key].name === profile.currentRole.name
        );
        if (roleKey) {
          stats.roleDistribution[roleKey]++;
        }
      }
    });

    stats.averageBadgeScore = volunteers.length > 0 ? totalBadgeScore / volunteers.length : 0;
    stats.topPerformers = this.generateBadgeLeaderboard(volunteers).slice(0, 10);

    return stats;
  }
}

// Export singleton instance
export const badgeService = new BadgeService();