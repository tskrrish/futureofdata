import { MILESTONES, getTierForHours } from '../constants.js'

// Track micro-achievements and meaningful moments
export class MicroAchievementTracker {
  constructor() {
    this.sessionTracking = {
      searchCount: 0,
      lastSearchTime: null,
      viewedVolunteers: new Set(),
      sessionStartTime: Date.now()
    }
  }

  // Check for various micro-achievements
  checkAchievements(volunteerData, context = {}) {
    const achievements = []
    
    if (!volunteerData) return achievements

    const hours = Number(volunteerData.hours_total) || 0
    const tier = getTierForHours(hours)

    // First-time discovery
    if (this.sessionTracking.searchCount === 1) {
      achievements.push({
        type: 'first_search',
        priority: 'high',
        volunteer: volunteerData
      })
    }

    // Milestone proximity celebrations
    const milestoneProgress = this.getMilestoneProgress(hours)
    if (milestoneProgress.nearMilestone) {
      achievements.push({
        type: 'milestone_progress',
        priority: 'medium',
        volunteer: volunteerData,
        data: milestoneProgress
      })
    }

    // Special hour milestones (not just main milestones)
    if (this.isSpecialHourMilestone(hours)) {
      achievements.push({
        type: 'hours_milestone',
        priority: 'high',
        volunteer: volunteerData,
        data: { hours, specialType: this.getHoursMilestoneType(hours) }
      })
    }

    // Dedication patterns
    if (this.detectDedicationPattern(volunteerData)) {
      achievements.push({
        type: 'dedication_streak',
        priority: 'medium',
        volunteer: volunteerData
      })
    }

    // Community impact recognition
    if (this.isCommunityImpactWorthy(volunteerData)) {
      achievements.push({
        type: 'community_impact',
        priority: 'high',
        volunteer: volunteerData
      })
    }

    // Surprise achievements for unique combinations
    const surpriseAchievement = this.checkSurpriseAchievements(volunteerData)
    if (surpriseAchievement) {
      achievements.push(surpriseAchievement)
    }

    return achievements
  }

  // Track search interactions
  trackSearch(volunteerData) {
    this.sessionTracking.searchCount++
    this.sessionTracking.lastSearchTime = Date.now()
    
    if (volunteerData) {
      const volunteerId = `${volunteerData.first_name}_${volunteerData.last_name}`
      this.sessionTracking.viewedVolunteers.add(volunteerId)
    }

    return this.checkAchievements(volunteerData, { action: 'search' })
  }

  // Calculate milestone progress and proximity
  getMilestoneProgress(hours) {
    const nextMilestone = MILESTONES.find(m => hours < m.threshold)
    
    if (!nextMilestone) {
      return { nearMilestone: false, progress: 100 }
    }

    const prevMilestone = MILESTONES.find(m => hours >= m.threshold) || { threshold: 0 }
    const progress = ((hours - prevMilestone.threshold) / (nextMilestone.threshold - prevMilestone.threshold)) * 100

    return {
      nearMilestone: progress >= 75, // Celebrate when 75% to next milestone
      progress: Math.round(progress),
      nextMilestone: nextMilestone.label,
      hoursToNext: nextMilestone.threshold - hours
    }
  }

  // Check for special hour milestones (not just the main ones)
  isSpecialHourMilestone(hours) {
    const specialMilestones = [5, 15, 35, 75, 150, 250, 350, 450, 750, 1000]
    return specialMilestones.includes(hours)
  }

  getHoursMilestoneType(hours) {
    if (hours >= 1000) return 'legendary_milestone'
    if (hours >= 500) return 'major_milestone' 
    if (hours >= 100) return 'significant_milestone'
    if (hours >= 25) return 'achievement_milestone'
    return 'early_milestone'
  }

  // Detect dedication patterns based on volunteer data
  detectDedicationPattern(volunteerData) {
    const hours = Number(volunteerData.hours_total) || 0
    
    // High dedication indicators
    if (hours >= 200) return true
    
    // Multiple storyworlds = versatile dedication
    if (volunteerData.storyworld && volunteerData.storyworld.includes(',')) return true
    
    // Long-term volunteer (this is simplified - in real app, would check date patterns)
    if (hours >= 50 && volunteerData.first_name) return true
    
    return false
  }

  // Determine if volunteer deserves community impact recognition
  isCommunityImpactWorthy(volunteerData) {
    const hours = Number(volunteerData.hours_total) || 0
    
    // High-impact volunteers
    if (hours >= 100) return true
    
    // Volunteers in critical areas
    if (volunteerData.storyworld) {
      const storyworld = volunteerData.storyworld.toLowerCase()
      if (storyworld.includes('healthy') || storyworld.includes('youth')) return true
    }
    
    return false
  }

  // Check for surprise achievements based on unique combinations
  checkSurpriseAchievements(volunteerData) {
    const hours = Number(volunteerData.hours_total) || 0
    const name = `${volunteerData.first_name || ''} ${volunteerData.last_name || ''}`.toLowerCase()

    // Perfect numbers (mathematically perfect)
    if ([28, 496].includes(hours)) {
      return {
        type: 'surprise_perfect_number',
        priority: 'high',
        volunteer: volunteerData,
        data: { specialType: 'perfect_number', hours }
      }
    }

    // Fibonacci sequence hours
    const fibonacci = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610]
    if (fibonacci.includes(hours)) {
      return {
        type: 'surprise_fibonacci',
        priority: 'medium', 
        volunteer: volunteerData,
        data: { specialType: 'fibonacci', hours }
      }
    }

    // Triple digit repeating numbers
    if (hours.toString().match(/^(\d)\1\1$/)) {
      return {
        type: 'surprise_triple_digits',
        priority: 'medium',
        volunteer: volunteerData,
        data: { specialType: 'triple_digits', hours }
      }
    }

    return null
  }

  // Get celebration configuration for an achievement
  getCelebrationConfig(achievement) {
    const configs = {
      first_search: {
        intensity: 'light',
        duration: 2000,
        confettiType: 'milestone_reached',
        sounds: ['magical_sparkle']
      },
      milestone_progress: {
        intensity: 'medium',
        duration: 3000,
        confettiType: 'progress_celebration',
        sounds: ['magical_sparkle', 'cheer']
      },
      hours_milestone: {
        intensity: 'high',
        duration: 4000,
        confettiType: 'milestone_reached',
        sounds: ['fanfare', 'cheer']
      },
      dedication_streak: {
        intensity: 'medium',
        duration: 3500,
        confettiType: 'continuous_impact',
        sounds: ['magical_sparkle']
      },
      community_impact: {
        intensity: 'high',
        duration: 4000,
        confettiType: 'surprise_achievement',
        sounds: ['fanfare', 'cheer']
      },
      surprise_perfect_number: {
        intensity: 'epic',
        duration: 6000,
        confettiType: 'surprise_achievement',
        sounds: ['fanfare', 'magical_sparkle', 'cheer']
      },
      surprise_fibonacci: {
        intensity: 'high',
        duration: 4000,
        confettiType: 'surprise_achievement', 
        sounds: ['magical_sparkle', 'cheer']
      },
      surprise_triple_digits: {
        intensity: 'medium',
        duration: 3000,
        confettiType: 'milestone_reached',
        sounds: ['magical_sparkle']
      }
    }

    return configs[achievement.type] || configs.milestone_progress
  }
}

// Singleton instance
export const microAchievementTracker = new MicroAchievementTracker()