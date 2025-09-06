import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import confetti from 'canvas-confetti'
import { playMagicalSparkle, playCheer } from '../utils/audio.js'

export default function MicroCelebration({ trigger, volunteerData, achievementType }) {
  const [showMicro, setShowMicro] = useState(false)
  const [achievement, setAchievement] = useState(null)

  const microAchievements = {
    'first_search': {
      title: '🔍 First Discovery!',
      message: 'Welcome to your volunteer journey',
      confettiConfig: { colors: ['#FFD700', '#FFA500', '#FF69B4'], particleCount: 30 }
    },
    'milestone_progress': {
      title: '⭐ Progress Made!',
      message: `You're ${achievementType?.progress || 0}% to your next milestone`,
      confettiConfig: { colors: ['#00CED1', '#32CD32', '#FFD700'], particleCount: 40 }
    },
    'hours_milestone': {
      title: '🎯 Hours Milestone!',
      message: `${achievementType?.hours || 0} hours of amazing impact!`,
      confettiConfig: { colors: ['#FF6B35', '#FFD700', '#32CD32'], particleCount: 50 }
    },
    'dedication_streak': {
      title: '🔥 Dedication Streak!',
      message: 'Consistent volunteer engagement detected',
      confettiConfig: { colors: ['#FF4500', '#FFD700', '#DC143C'], particleCount: 35 }
    },
    'community_impact': {
      title: '💖 Community Hero!',
      message: 'Making a real difference in lives',
      confettiConfig: { colors: ['#FF69B4', '#87CEEB', '#98FB98'], particleCount: 45 }
    }
  }

  const runMicroConfetti = (config) => {
    const defaults = {
      startVelocity: 25,
      spread: 70,
      ticks: 60,
      gravity: 0.8,
      scalar: 0.8,
      zIndex: 100,
      ...config
    }

    // Burst from center
    confetti({
      ...defaults,
      origin: { x: 0.5, y: 0.6 }
    })

    // Side bursts for extra celebration
    setTimeout(() => {
      confetti({
        ...defaults,
        origin: { x: 0.3, y: 0.7 },
        angle: 60
      })
      confetti({
        ...defaults,
        origin: { x: 0.7, y: 0.7 },
        angle: 120
      })
    }, 200)
  }

  useEffect(() => {
    if (trigger && microAchievements[trigger]) {
      const selectedAchievement = microAchievements[trigger]
      setAchievement(selectedAchievement)
      setShowMicro(true)
      
      // Audio feedback
      playMagicalSparkle()
      setTimeout(() => playCheer(400), 300)
      
      // Visual confetti
      runMicroConfetti(selectedAchievement.confettiConfig)
      
      // Auto-hide after 3 seconds
      setTimeout(() => {
        setShowMicro(false)
        setTimeout(() => setAchievement(null), 500)
      }, 3000)
    }
  }, [trigger])

  return (
    <AnimatePresence>
      {showMicro && achievement && (
        <motion.div
          className="micro-celebration-popup"
          initial={{ scale: 0, opacity: 0, y: 50 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0, opacity: 0, y: -50 }}
          transition={{ 
            type: "spring", 
            stiffness: 300, 
            damping: 20 
          }}
          style={{
            position: 'fixed',
            top: '20%',
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 1000,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderRadius: '20px',
            padding: '20px 30px',
            boxShadow: '0 20px 40px rgba(0,0,0,0.3)',
            border: '2px solid rgba(255,255,255,0.2)',
            backdropFilter: 'blur(10px)',
            maxWidth: '400px',
            textAlign: 'center'
          }}
        >
          <motion.div
            className="achievement-content"
            initial={{ y: 10 }}
            animate={{ y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <div style={{
              fontSize: '24px',
              fontWeight: 'bold',
              color: 'white',
              marginBottom: '8px',
              textShadow: '0 2px 4px rgba(0,0,0,0.3)'
            }}>
              {achievement.title}
            </div>
            <div style={{
              fontSize: '16px',
              color: 'rgba(255,255,255,0.9)',
              lineHeight: '1.4'
            }}>
              {achievement.message}
            </div>
          </motion.div>
          
          {/* Sparkle particles around the popup */}
          <motion.div
            className="sparkle-particles"
            style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}
          >
            {[...Array(8)].map((_, i) => (
              <motion.div
                key={i}
                className="sparkle"
                initial={{ 
                  scale: 0,
                  x: Math.cos(i * Math.PI / 4) * 40,
                  y: Math.sin(i * Math.PI / 4) * 40
                }}
                animate={{ 
                  scale: [0, 1, 0],
                  x: Math.cos(i * Math.PI / 4) * 60,
                  y: Math.sin(i * Math.PI / 4) * 60,
                }}
                transition={{ 
                  duration: 2,
                  delay: i * 0.1,
                  repeat: Infinity,
                  repeatDelay: 1
                }}
                style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  width: '4px',
                  height: '4px',
                  background: '#FFD700',
                  borderRadius: '50%',
                  boxShadow: '0 0 6px #FFD700'
                }}
              />
            ))}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}