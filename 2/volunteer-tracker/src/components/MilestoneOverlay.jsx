import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { getTierForHours, MILESTONE_DETAILS } from '../constants.js'

export default function MilestoneOverlay({ show, milestone, hours, onComplete }) {
  const [showContent, setShowContent] = useState(false)
  const tier = getTierForHours(hours)
  const details = MILESTONE_DETAILS[milestone?.label] || {}

  useEffect(() => {
    if (show) {
      setTimeout(() => setShowContent(true), 500)
      setTimeout(() => {
        setShowContent(false)
        setTimeout(() => onComplete?.(), 500)
      }, 4000)
    }
  }, [show, onComplete])

  const getMilestoneIcon = (label) => {
    switch (label) {
      case "Commitment Champion": return "🏆"
      case "Passion In Action Award": return "🌟"
      case "Guiding Light Award": return "✨"
      default: return "🎉"
    }
  }

  const getMilestoneColor = (label) => {
    switch (label) {
      case "Commitment Champion": return "#FFD700"
      case "Passion In Action Award": return "#1B1B1B"
      case "Guiding Light Award": return "#FF6B35"
      default: return "#FFD700"
    }
  }

  if (!show || !milestone) return null

  const icon = getMilestoneIcon(milestone.label)
  const color = getMilestoneColor(milestone.label)

  return (
    <AnimatePresence>
      {show && (
        <motion.div 
          className="milestone-overlay-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div 
            className="milestone-celebration-container"
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            exit={{ scale: 0, rotate: 180 }}
            transition={{ type: 'spring', stiffness: 100, damping: 15 }}
          >
            <motion.div 
              className="milestone-icon-container"
              animate={{ 
                scale: [1, 1.2, 1],
                rotate: [0, 360]
              }}
              transition={{ 
                scale: { duration: 2, repeat: Infinity },
                rotate: { duration: 3, repeat: Infinity, ease: 'linear' }
              }}
              style={{ color }}
            >
              {icon}
            </motion.div>

            <AnimatePresence mode="wait">
              {showContent && (
                <motion.div 
                  className="milestone-content"
                  initial={{ y: 50, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  exit={{ y: -50, opacity: 0 }}
                  transition={{ delay: 0.3 }}
                >
                  <motion.h1 
                    className="milestone-title"
                    initial={{ scale: 0.8 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.5, type: 'spring' }}
                  >
                    MILESTONE ACHIEVED!
                  </motion.h1>
                  
                  <motion.h2 
                    className="milestone-name"
                    initial={{ x: -100, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: 0.7 }}
                    style={{ color }}
                  >
                    {milestone.label}
                  </motion.h2>
                  
                  <motion.div 
                    className="milestone-hours"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.9, type: 'spring', stiffness: 200 }}
                  >
                    <span className="hours-number">{milestone.threshold}</span>
                    <span className="hours-label">HOURS</span>
                  </motion.div>

                  <motion.p 
                    className="milestone-description"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 1.1 }}
                  >
                    {details.description}
                  </motion.p>

                  <motion.div 
                    className="milestone-reward"
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 1.3 }}
                  >
                    <span className="reward-label">REWARD:</span>
                    <span className="reward-value">{details.reward}</span>
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>

            <motion.div 
              className="milestone-rays"
              animate={{ rotate: 360 }}
              transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
            />

            <motion.div 
              className="milestone-particles"
              initial={{ opacity: 0 }}
              animate={{ opacity: [0, 1, 0] }}
              transition={{ duration: 2, repeat: Infinity, repeatDelay: 0.5 }}
            />
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}