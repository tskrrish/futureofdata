import React, { useEffect, useRef } from 'react'
import confetti from 'canvas-confetti'
import { getTierForHours } from '../constants.js'

export default function EnhancedConfetti({ 
  trigger, 
  volunteerData, 
  achievementType = 'standard',
  duration = 3000 
}) {
  const firedRef = useRef(false)

  const getPersonalizedColors = (volunteer, tier) => {
    // Base colors for different tiers
    const tierColors = {
      legendary: ['#FF6B35', '#FFD700', '#FF1493', '#00CED1', '#32CD32'],
      special: ['#1B1B1B', '#FFD700', '#FF69B4', '#87CEEB'],
      rare: ['#FFD700', '#FFA500', '#FF4500', '#32CD32'],
      uncommon: ['#C0C0C0', '#87CEEB', '#98FB98', '#DDA0DD'],
      common: ['#CD7F32', '#D2691E', '#228B22', '#4682B4'],
      basic: ['#8B4513', '#A0522D', '#556B2F', '#2F4F4F']
    }

    // Add personalization based on volunteer's storyworld or name
    let personalizedColors = [...tierColors[tier]]
    
    if (volunteer?.storyworld) {
      const storyworld = volunteer.storyworld.toLowerCase()
      if (storyworld.includes('youth')) personalizedColors.push('#FFFF00', '#FF69B4')
      if (storyworld.includes('healthy')) personalizedColors.push('#FF0000', '#32CD32')
      if (storyworld.includes('water')) personalizedColors.push('#00CED1', '#0000FF')
      if (storyworld.includes('neighbor')) personalizedColors.push('#32CD32', '#228B22')
      if (storyworld.includes('sports')) personalizedColors.push('#FF4500', '#FFD700')
    }

    return personalizedColors
  }

  const createMeaningfulPattern = (colors, hours, achievementType) => {
    const patterns = {
      'milestone_reached': () => {
        // Celebration burst from multiple points
        const burst = (origin) => confetti({
          particleCount: 50,
          spread: 90,
          origin,
          colors,
          gravity: 0.6,
          ticks: 100,
          scalar: 1.2
        })
        
        burst({ x: 0.2, y: 0.6 })
        burst({ x: 0.8, y: 0.6 })
        setTimeout(() => burst({ x: 0.5, y: 0.3 }), 300)
      },
      
      'progress_celebration': () => {
        // Rising celebration
        let particleCount = Math.max(30, Math.min(100, hours))
        const duration = Math.min(4000, 2000 + hours * 10)
        const end = Date.now() + duration
        
        const frame = () => {
          confetti({
            particleCount: Math.floor(particleCount * 0.3),
            startVelocity: 30,
            spread: 360,
            origin: { x: Math.random(), y: Math.random() * 0.5 + 0.5 },
            colors,
            gravity: 0.5
          })
          
          if (Date.now() < end) {
            requestAnimationFrame(frame)
          }
        }
        frame()
      },
      
      'surprise_achievement': () => {
        // Surprise explosion
        confetti({
          particleCount: 100,
          spread: 160,
          origin: { y: 0.6 },
          colors,
          gravity: 1,
          ticks: 200,
          shapes: ['star', 'circle'],
          scalar: 1.4
        })
        
        // Follow-up smaller bursts
        setTimeout(() => {
          for (let i = 0; i < 3; i++) {
            setTimeout(() => {
              confetti({
                particleCount: 30,
                spread: 60,
                origin: { x: 0.3 + Math.random() * 0.4, y: 0.7 },
                colors,
                gravity: 0.8,
                scalar: 0.8
              })
            }, i * 200)
          }
        }, 500)
      },
      
      'continuous_impact': () => {
        // Steady stream celebrating ongoing impact
        const streamDuration = 2000
        const interval = setInterval(() => {
          confetti({
            particleCount: 10,
            spread: 30,
            origin: { x: 0.5, y: 0.2 },
            colors: colors.slice(0, 3), // Use fewer colors for subtlety
            gravity: 0.4,
            ticks: 80
          })
        }, 150)
        
        setTimeout(() => clearInterval(interval), streamDuration)
      }
    }

    return patterns[achievementType] || patterns['progress_celebration']
  }

  useEffect(() => {
    if (trigger && volunteerData && !firedRef.current) {
      firedRef.current = true
      
      const hours = Number(volunteerData.hours_total) || 0
      const tier = getTierForHours(hours)
      const colors = getPersonalizedColors(volunteerData, tier)
      
      // Create meaningful confetti pattern
      const pattern = createMeaningfulPattern(colors, hours, achievementType)
      pattern()
      
      // Reset after duration to allow re-triggering
      setTimeout(() => {
        firedRef.current = false
      }, duration)
    }
  }, [trigger, volunteerData, achievementType, duration])

  return null // This component only triggers effects, no visual output
}